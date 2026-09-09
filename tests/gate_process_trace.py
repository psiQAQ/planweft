"""Fail-closed attribution for the bounded Linux stopping experiment.

This is not a general strace reader. The caller must trace the syscalls listed
in TRACE_SYSCALLS, retain process-exit records, and start in /workspace. Raw
trace text stays private: the result contains no argv, buffers or environment.
"""
import ast
import hashlib
import os
from pathlib import Path
import re

TRACE_SYSCALLS = 'execve,clone,clone3,fork,vfork,open,openat,openat2,read,close,close_range,dup,dup2,dup3,fcntl,chdir,fchdir'
COUNTERS = {'/workspace/.stop_blocks', '/workspace/.gate_last_ledger'}
ALL_FDS = (0, 4294967295)


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


def _ambiguous(accesses):
    # Events have already been sorted by start. Grouping by resource also
    # catches threads born inside an unfinished operation's interval.
    groups={}
    for start,end,pid,resource,write,span in accesses:
        group=groups.setdefault(id(resource),[])
        group[:]=[entry for entry in group if entry[0]>=start]
        for other_end,other_pid,other_write,other_span in group:
            if pid!=other_pid and (write or other_write) and max(span[0],other_span[0])<=min(span[1],other_span[1]):
                return True
        group.append((end,pid,write,span))
    return False


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
    pending={}; events=[]; errors=[]
    for index,line in enumerate(text.splitlines()):
        match=re.match(r'^(\d+)(?:<[^>]*>)?\s+(.*)$',line)
        if not match:
            if line.strip(): errors.append('unrecognized trace line')
            continue
        pid=int(match[1]); call=match[2]; finished=index
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
    return sorted(events),errors


def attributed_gate_reads(text, expected_script_hash, *, read_script=None):
    """Return evidence bound to script bytes, process generation and exact files.

    read_script(path) is injectable for offline tests and returns bytes. A trace
    with lost, unsupported or malformed relevant events cannot prove absence.
    """
    reader=read_script or (lambda path: Path(path).read_bytes())
    events,errors=_events(text)
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
        directory=state['cwd'][0]
        if dirfd is not None and dirfd!='AT_FDCWD':
            opened=state['fds'].get(_number(dirfd))
            if not opened: raise ValueError('unresolved openat dirfd')
            directory=opened[0]
        if directory is None: raise ValueError('unknown cwd')
        return os.path.normpath(os.path.join(directory,path))

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
        if result.startswith('-1 ') or result.startswith('? ERESTART'): continue
        if result.startswith('?'):
            errors.append('unresolved syscall result'); continue
        try:
            returned=_return_number(result); args=_arguments(body)
            for resource,write,span in _footprint(name,args,returned,body,state):
                accesses.append((index,finished,pid,resource,write,span))
            if name in {'clone','clone3','fork','vfork'}:
                if returned>0:
                    if returned in processes: errors.append('child PID already active')
                    fresh(returned,state,body)
            elif name=='execve' and returned==0:
                root_execs.add((pid,state['generation']))
                # execve unshares FDs, while CLONE_FS sharing remains in effect.
                state['fds']={fd:value for fd,value in state['fds'].items() if not value[1]}
                filename=absolute(_string(args[0]),state)
                argv=ast.literal_eval(args[1])
                if not isinstance(argv,list) or not all(isinstance(a,str) for a in argv):
                    raise ValueError('truncated exec argv')
                candidate=None
                if Path(filename).name=='check-complete.sh' and argv[1:]==['--gate']:
                    candidate=filename
                elif Path(filename).name in {'bash','sh','dash'} and len(argv)==3 and argv[2]=='--gate':
                    candidate=absolute(argv[1],state)
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
                except ValueError:
                    # Unknown unrelated directories cannot label counter FDs.
                    if Path(path).name in {'.stop_blocks','.gate_last_ledger'}: raise
                    path=None
                state['fds'][returned]=(path,'O_CLOEXEC' in body)
            elif name=='close' and returned==0:
                state['fds'].pop(_number(args[0]),None)
            elif name=='close_range' and returned==0:
                low=_number(args[0]); high=_number(args[1].replace('~0U','4294967295'))
                if 'CLOSE_RANGE_UNSHARE' in body: state['fds']=dict(state['fds'])
                for fd,value in list(state['fds'].items()):
                    if low<=fd<=high:
                        if 'CLOSE_RANGE_CLOEXEC' in body: state['fds'][fd]=(value[0],True)
                        else: del state['fds'][fd]
            elif name in {'dup','dup2','dup3'} and returned>=0:
                source=_number(args[0]); value=state['fds'].get(source)
                if name=='dup2' and source==returned: continue
                state['fds'].pop(returned,None)
                if value: state['fds'][returned]=(value[0],name=='dup3' and 'O_CLOEXEC' in body)
            elif name=='fcntl' and returned>=0:
                source=_number(args[0]); value=state['fds'].get(source)
                if args[1] in {'F_DUPFD','F_DUPFD_CLOEXEC'}:
                    state['fds'].pop(returned,None)
                    if value: state['fds'][returned]=(value[0],args[1]=='F_DUPFD_CLOEXEC')
                elif args[1]=='F_SETFD' and value:
                    state['fds'][source]=(value[0],'FD_CLOEXEC' in args[2])
            elif name=='chdir' and returned==0:
                state['cwd'][0]=absolute(_string(args[0]),state)
            elif name=='fchdir' and returned==0:
                value=state['fds'].get(_number(args[0])); state['cwd'][0]=value[0] if value else None
            elif name=='read' and returned>0:
                value=state['fds'].get(_number(args[0]))
                if value and value[0] in COUNTERS:
                    reads.append({'pid':pid,'generation':state['generation'],
                                  'file':Path(value[0]).name,'bytes':returned,'gate':state['gate']})
            elif name not in TRACE_SYSCALLS.split(','):
                errors.append('unexpected traced syscall')
        except (ValueError,SyntaxError,IndexError,TypeError):
            errors.append('unsupported or malformed syscall arguments')
    if not events or not roots: errors.append('empty process trace')
    if _ambiguous(accesses): errors.append('ambiguous concurrent shared descriptor or cwd operation')
    if roots-root_execs: errors.append('root process lacks successful exec record')
    if processes: errors.append('missing process exit records')
    return {'kind':'script-digest-bound process-generation counter I/O',
            'trace_complete':not errors,'errors':sorted(set(errors)),
            'source_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'source_bytes':len(text.encode()),'gates':gates,'reads':reads,
            'attributed_files':sorted({r['file'] for r in reads if r['gate']})}
