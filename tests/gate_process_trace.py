"""Fail-closed attribution for the bounded Linux stopping experiment.

This is not a general strace reader. The caller must trace the syscalls listed
in TRACE_SYSCALLS, retain process-exit records, and start in /workspace. Raw
trace text stays private: the result contains no argv, buffers or environment.
"""
import ast
import bisect
import hashlib
import os
from pathlib import Path
import re

TRACE_SYSCALLS = 'execve,clone,clone3,fork,vfork,open,openat,openat2,read,close,close_range,dup,dup2,dup3,fcntl,chdir,fchdir'
COUNTERS = {'/workspace/.stop_blocks', '/workspace/.gate_last_ledger'}
ALL_FDS = (0, 4294967295)
UNKNOWN = object()
UNKNOWN_FD = (UNKNOWN, UNKNOWN)


def _footprint(name, args, returned, body, state):
    """Bindings read/written by a successful call, not file contents or offsets.

    clone(2) copies non-shared tables; execve(2) unshares only the FD table.
    Ranges avoid expanding close_range(~0U) and retain actual resource objects
    so their Python ids cannot be reused after a process exits.
    """
    items=[]
    def fd(number, write=False):
        items.append((state['fds'], write, (number,number)))
    def all_fds(write=False): items.append((state['fds'],write,ALL_FDS))
    def cwd(write=False): items.append((state['cwd'],write,(0,0)))
    def path(value, dirfd='AT_FDCWD'):
        if not os.path.isabs(_string(value)):
            if dirfd=='AT_FDCWD': cwd()
            else: fd(_number(dirfd))
    if name in {'clone','clone3','fork','vfork'} and returned>0:
        if 'CLONE_FILES' not in body: all_fds()
        if 'CLONE_FS' not in body: cwd()
    elif name=='execve' and returned==0:
        all_fds(); path(args[0])
        # Shell script argv is resolved relative to cwd after exec as well.
        cwd()
    elif name in {'open','openat','openat2'} and returned>=0:
        path(args[0] if name=='open' else args[1],
             'AT_FDCWD' if name=='open' else args[0])
        fd(returned,True)
    elif name=='read' and returned>=0: fd(_number(args[0]))
    elif name=='close' and returned==0: fd(_number(args[0]),True)
    elif name=='close_range' and returned==0:
        if 'CLOSE_RANGE_UNSHARE' in body:
            # Only the snapshot touches the old shared table; changes are
            # applied to the caller's newly private table.
            all_fds()
        else:
            items.append((state['fds'],True,(_number(args[0]),_number(args[1].replace('~0U','4294967295')))))
    elif name in {'dup','dup2','dup3'} and returned>=0:
        fd(_number(args[0])); fd(returned,True)
    elif name=='fcntl' and returned>=0:
        fd(_number(args[0]), args[1]=='F_SETFD')
        if args[1] in {'F_DUPFD','F_DUPFD_CLOEXEC'}: fd(returned,True)
    elif name=='chdir' and returned==0:
        path(args[0]); cwd(True)
    elif name=='fchdir' and returned==0:
        fd(_number(args[0])); cwd(True)
    return items


def _conflicts(accesses):
    # Events have already been sorted by start. Grouping by resource also
    # catches threads born inside an unfinished operation's interval.
    groups={}; samples=[]; count=0; hazards={}
    def hazard(index,kind,span,write):
        hazards.setdefault((index,kind,write),[]).append(span)
    for start,end,pid,resource,write,span,operation in accesses:
        group=groups.setdefault(id(resource),[])
        group[:]=[entry for entry in group if entry[1]>=start]
        kind='fds' if isinstance(resource,dict) else 'cwd'
        for other_start,other_end,other_pid,other_write,other_span,other_operation in group:
            if pid!=other_pid and (write or other_write) and max(span[0],other_span[0])<=min(span[1],other_span[1]):
                count+=1
                overlap=(max(span[0],other_span[0]),min(span[1],other_span[1]))
                # A reader overlapping a write cannot know which binding it
                # observed. A writer's resulting binding is uncertain only
                # when another writer races it, not merely a concurrent read.
                if not write or other_write: hazard(start,kind,overlap,write)
                if not other_write or write: hazard(other_start,kind,overlap,other_write)
                if len(samples)<12:
                    samples.append({'resource':'fds' if isinstance(resource,dict) else 'cwd',
                        'operations':[other_operation,operation], 'pids':[other_pid,pid],
                        'ranges':[other_span,span]})
        group.append((start,end,pid,write,span,operation))
    return {'count':count,'samples':samples},hazards


def _arguments(value):
    """Split only top-level commas; strace strings use C-style escapes."""
    pieces=[]; start=0; depth=0; quoted=False; escaped=False
    for i,char in enumerate(value):
        if quoted:
            if escaped: escaped=False
            elif char=='\\': escaped=True
            elif char=='"': quoted=False
        elif char=='"': quoted=True
        elif char in '[{(': depth+=1
        elif char in ']})': depth-=1
        elif char==',' and depth==0:
            pieces.append(value[start:i].strip()); start=i+1
    if quoted or depth: raise ValueError('incomplete arguments')
    return pieces+[value[start:].strip()]


def _string(value):
    result=ast.literal_eval(value)
    if not isinstance(result,str): raise ValueError('not a string')
    return result


def _number(value):
    # --decode-pids=comm annotates clone/vfork return values too.
    return int(re.sub(r'<[^>]*>$','',value), 0)


def _return_number(value):
    # comm can contain spaces (e.g. 21<Bun Pool 0>); splitting on whitespace
    # first truncates the annotation and loses the child's process identity.
    match=re.match(r'^(-?(?:0x[0-9a-fA-F]+|[0-9]+))(?:<[^>]*>)?(?=\s|$)',value)
    if not match: raise ValueError('invalid syscall return token')
    return int(match[1],0)


def _events(text):
    pending={}; events=[]; errors=[]; exits={}
    for index,line in enumerate(text.splitlines()):
        match=re.match(r'^(\d+)(?:<[^>]*>)?\s+(.*)$',line)
        if not match:
            if line.strip(): errors.append('unrecognized trace line')
            continue
        pid=int(match[1]); call=match[2]; finished=index
        if call.startswith('+++ exited with ') or call.startswith('+++ killed by '):
            exits[pid]=index
        if call.endswith('<unfinished ...>'):
            if pid in pending: errors.append('overlapping unfinished syscall')
            pending[pid]=(index,call[:-len('<unfinished ...>')]); continue
        resumed=re.match(r'^<\.\.\. (\w+) resumed>(.*)$',call)
        if resumed:
            saved=pending.pop(pid,None)
            if saved is None or not saved[1].startswith(resumed[1]+'('):
                errors.append('unmatched resumed syscall'); continue
            index,first=saved; call=first+resumed[2]
        events.append((index,pid,call,finished))
    if pending: errors.append('unfinished syscalls at EOF')
    # A child can run before its parent's clone return is printed. A completed
    # clone belongs at its start, before the child's exec/open/read events.
    # Keep bounded numeric diagnostics after the private trace is destroyed.
    # A later exit does not resolve the missing return value or make it safe.
    samples=[]
    for pid,(start,call) in sorted(pending.items())[:32]:
        name=call.split('(',1)[0]
        item={'pid':pid,'start_event':start,
              'operation':name if name in TRACE_SYSCALLS.split(',') else 'unknown',
              'later_exit_event':exits[pid] if exits.get(pid,-1)>start else None}
        if name in {'read','close','dup','dup2','dup3','fcntl','fchdir'}:
            match=re.match(r'^\w+\((0x[0-9a-fA-F]+|[0-9]+)(?=[,\s)])',call)
            if match: item['descriptor']=int(match[1],0)
        samples.append(item)
    return sorted(events),errors,{'count':len(pending),'samples':samples}


def _replay(text, expected_script_hash, *, read_script=None, hazards=None, fd_numbers=None):
    """Return evidence bound to script bytes, process generation and exact files.

    read_script(path) is injectable for offline tests and returns bytes. A trace
    with lost, unsupported or malformed relevant events cannot prove absence.
    """
    reader=read_script or (lambda path: Path(path).read_bytes())
    events,errors,unfinished=_events(text)
    hazards=hazards or {}
    process_events={}
    for index,pid,_,_ in events:
        process_events.setdefault(pid,[]).append(index)
    accesses=[]
    processes={}; generations={}; reads=[]; gates=[]; roots=set(); root_execs=set()
    if not re.fullmatch(r'[0-9a-f]{64}',expected_script_hash):
        errors.append('invalid expected script digest')

    def fresh(pid,parent=None,flags=''):
        generations[pid]=generations.get(pid,0)+1
        state={'generation':generations[pid], 'gate':None, 'fds':{}, 'cwd':['/workspace']}
        if parent:
            state['gate']=parent['gate']
            state['fds']=parent['fds'] if 'CLONE_FILES' in flags else dict(parent['fds'])
            state['cwd']=parent['cwd'] if 'CLONE_FS' in flags else list(parent['cwd'])
        processes[pid]=state
        return state

    def absolute(path,state,dirfd=None):
        if os.path.isabs(path): return os.path.normpath(path)
        directory=cwd_value(state)
        if dirfd is not None and dirfd!='AT_FDCWD':
            opened=fd_value(state,_number(dirfd))
            if not opened: raise ValueError('unresolved openat dirfd')
            directory=opened[0]
        if directory is None or directory is UNKNOWN: raise ValueError('unknown cwd')
        return os.path.normpath(os.path.join(directory,path))

    def uncertain(kind,number=0,write=False):
        return any(low<=number<=high for low,high in hazards.get((index,kind,write),()))

    def fd_value(state,number):
        return UNKNOWN_FD if uncertain('fds',number) else state['fds'].get(number)

    def cwd_value(state):
        return UNKNOWN if uncertain('cwd') else state['cwd'][0]

    def set_fd(state,number,value):
        value=UNKNOWN_FD if uncertain('fds',number,True) else value
        if value is None: state['fds'].pop(number,None)
        else: state['fds'][number]=value

    def slots(state):
        return tuple(state['fds']) if fd_numbers is None else fd_numbers

    for index,pid,call,finished in events:
        state=processes.get(pid)
        if state is None:
            state=fresh(pid); roots.add((pid,state['generation']))
        if call.startswith('+++ exited with ') or call.startswith('+++ killed by '):
            del processes[pid]; continue
        if call.startswith('--- '): continue
        parsed=re.match(r'^(\w+)\((.*)\)\s+=\s+(.+)$',call)
        if not parsed:
            errors.append('unrecognized syscall record'); continue
        name,body,result=parsed.groups()
        # Failed calls do not change successful syscall state.
        if result.startswith('-1 '):
            # Linux may release an FD even when close reports an I/O error.
            # EBADF alone proves that no valid descriptor was closed.
            if name=='close' and not result.startswith('-1 EBADF'):
                errors.append('failed close may have released descriptor')
            continue
        if result.startswith('? ERESTART'): continue
        if result.startswith('?'):
            errors.append('unresolved syscall result'); continue
        try:
            returned=_return_number(result); args=_arguments(body)
            footprint_end=finished
            if name in {'clone','clone3','fork','vfork'} and returned>0:
                child_events=process_events.get(returned,[])
                next_child=bisect.bisect_right(child_events,index)
                if next_child<len(child_events):
                    # A child's first observed event is after its inherited
                    # tables were copied. In particular, vfork can leave the
                    # parent blocked until much later (child exec or exit).
                    # Only copy footprints exist here: CLONE_FILES/CLONE_FS
                    # sharing is handled by subsequent accesses to the same
                    # resource object, with their full syscall intervals.
                    footprint_end=min(finished,child_events[next_child]-1)
            for resource,write,span in _footprint(name,args,returned,body,state):
                accesses.append((index,footprint_end,pid,resource,write,span,name))
            if name in {'clone','clone3','fork','vfork'}:
                if returned>0:
                    if returned in processes: errors.append('child PID already active')
                    child=fresh(returned,state,body)
                    if 'CLONE_FILES' not in body:
                        child['fds']={n:value for n in slots(state) if (value:=fd_value(state,n)) is not None}
                    if 'CLONE_FS' not in body: child['cwd']=[cwd_value(state)]
            elif name=='execve' and returned==0:
                root_execs.add((pid,state['generation']))
                # execve unshares FDs, while CLONE_FS sharing remains in effect.
                # Unknown CLOEXEC is not proof that the descriptor was closed.
                state['fds']={n:value for n in slots(state)
                              if (value:=fd_value(state,n)) is not None and value[1] is not True}
                filename=absolute(_string(args[0]),state)
                argv=ast.literal_eval(args[1])
                if not isinstance(argv,list) or not all(isinstance(a,str) for a in argv):
                    raise ValueError('truncated exec argv')
                candidate=None
                gate_args=[]
                if Path(filename).name=='check-complete.sh':
                    candidate=filename; gate_args=argv[1:]
                elif Path(filename).name in {'bash','sh','dash'} and len(argv)>=3 and Path(argv[1]).name=='check-complete.sh':
                    candidate=absolute(argv[1],state); gate_args=argv[2:]
                if candidate:
                    # Codex's native Stop adapter supplies the resolved plan
                    # as one extra positional argument. This bounded probe only
                    # owns the root plan and its two counters, not other tasks.
                    valid=(gate_args==['--gate'] or len(gate_args)==2 and gate_args[0]=='--gate'
                           and absolute(gate_args[1],state)=='/workspace/task_plan.md')
                    if not valid:
                        if '--gate' in gate_args: errors.append('unsupported gate plan arguments')
                        candidate=None
                if candidate and Path(candidate).name=='check-complete.sh':
                    try: matched=hashlib.sha256(reader(candidate)).hexdigest()==expected_script_hash
                    except OSError: matched=False
                    if not matched: errors.append('gate candidate digest mismatch or unavailable')
                    else:
                        gate={'pid':pid,'generation':state['generation'],'script_sha256':expected_script_hash}
                        state['gate']=gate; gates.append(gate)
            elif name in {'open','openat','openat2'} and returned>=0:
                path_arg=0 if name=='open' else 1
                path=_string(args[path_arg])
                try: path=absolute(path,state,None if name=='open' else args[0])
                except ValueError: path=UNKNOWN
                set_fd(state,returned,(path,'O_CLOEXEC' in body))
            elif name=='close' and returned==0:
                set_fd(state,_number(args[0]),None)
            elif name=='close_range' and returned==0:
                low=_number(args[0]); high=_number(args[1].replace('~0U','4294967295'))
                if 'CLOSE_RANGE_UNSHARE' in body:
                    state['fds']={n:value for n in slots(state) if (value:=fd_value(state,n)) is not None}
                for fd in slots(state):
                    if low<=fd<=high:
                        value=state['fds'].get(fd)
                        if 'CLOSE_RANGE_CLOEXEC' in body:
                            if value: set_fd(state,fd,(value[0],True))
                        else: set_fd(state,fd,None)
            elif name in {'dup','dup2','dup3'} and returned>=0:
                source=_number(args[0]); value=fd_value(state,source)
                if name=='dup2' and source==returned: continue
                set_fd(state,returned,(value[0],name=='dup3' and 'O_CLOEXEC' in body) if value else None)
            elif name=='fcntl' and returned>=0:
                source=_number(args[0]); value=fd_value(state,source)
                if args[1] in {'F_DUPFD','F_DUPFD_CLOEXEC'}:
                    set_fd(state,returned,(value[0],args[1]=='F_DUPFD_CLOEXEC') if value else None)
                elif args[1]=='F_SETFD' and value:
                    set_fd(state,source,(value[0],'FD_CLOEXEC' in args[2]))
            elif name=='chdir' and returned==0:
                try: directory=absolute(_string(args[0]),state)
                except ValueError: directory=UNKNOWN
                state['cwd'][0]=UNKNOWN if uncertain('cwd',write=True) else directory
            elif name=='fchdir' and returned==0:
                value=fd_value(state,_number(args[0]))
                state['cwd'][0]=UNKNOWN if uncertain('cwd',write=True) else value[0] if value else None
            elif name=='read' and returned>0:
                value=fd_value(state,_number(args[0]))
                if state['gate'] and value and value[0] is UNKNOWN:
                    errors.append('gate read depends on ambiguous descriptor binding')
                if value and value[0] in COUNTERS:
                    reads.append({'pid':pid,'generation':state['generation'],
                                  'file':Path(value[0]).name,'bytes':returned,'gate':state['gate']})
            elif name not in TRACE_SYSCALLS.split(','):
                errors.append('unexpected traced syscall')
        except (ValueError,SyntaxError,IndexError,TypeError):
            errors.append('unsupported or malformed syscall arguments')
    if not events or not roots: errors.append('empty process trace')
    if roots-root_execs: errors.append('root process lacks successful exec record')
    if processes: errors.append('missing process exit records')
    return {'kind':'script-digest-bound process-generation counter I/O',
            'trace_complete':not errors,'errors':sorted(set(errors)),
            'unfinished_syscalls':unfinished,
            'source_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'source_bytes':len(text.encode()),'gates':gates,'reads':reads,
            'attributed_files':sorted({r['file'] for r in reads if r['gate']})},accesses


def attributed_gate_reads(text, expected_script_hash, *, read_script=None):
    """Prove bounded gate identity/I/O, retaining unrelated host races.

    The first replay records physical sharing and syscall intervals. The second
    uses all overlaps, including future resumed calls, before copying bindings.
    Unknown bindings survive fork/exec/dup and are cleared only by an unopposed
    definite overwrite; they never serve as proof of a gate read or its absence.
    """
    source=read_script or (lambda path: Path(path).read_bytes())
    scripts={}
    def frozen_script(path):
        if path not in scripts: scripts[path]=source(path)
        return scripts[path]
    initial,accesses=_replay(text,expected_script_hash,read_script=frozen_script)
    conflicts,hazards=_conflicts(accesses)
    numbers={n for _,_,_,resource,_,span,_ in accesses if isinstance(resource,dict)
             and span[0]==span[1] for n in span}
    if len(numbers)>4096:
        initial['trace_complete']=False
        initial['errors'].append('descriptor bound exceeded')
        result=initial
    else:
        result,_=_replay(text,expected_script_hash,read_script=frozen_script,
                         hazards=hazards,fd_numbers=numbers)
        result['errors']=sorted(set(initial['errors']+result['errors']))
        result['trace_complete']=not result['errors']
    result['conflicts']=conflicts
    result['proof_scope']='gate identity and counter I/O; unrelated host binding races retained'
    return result
