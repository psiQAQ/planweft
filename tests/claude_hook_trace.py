"""Bounded, offline Claude command-hook stdout attribution (Linux strace 6.1).

Input is private: argv is required for identity, but data syscalls MUST use
RAW_SYSCALLS. Only numeric facts, fixed labels and hashes leave this module.
This proves process/output observations, not model delivery or reminder dedup.
The caller owns authenticated collection, redaction, limits and trace disposal.
"""
import ast
import bisect
import hashlib
import importlib.util
import os
from pathlib import Path
import re

_spec = importlib.util.spec_from_file_location('_claude_gate_trace_base', Path(__file__).with_name('gate_process_trace.py'))
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

DATA_SYSCALLS = 'read,readv,write,writev,recvfrom,sendto,recvmsg,sendmsg,recvmmsg,sendmmsg'
TRANSFER_SYSCALLS = 'sendfile,splice,tee,vmsplice,copy_file_range,pread64,pwrite64,preadv,pwritev,preadv2,pwritev2'
EXTRA_SYSCALLS = 'pipe,pipe2,socketpair,socket,connect,accept,accept4,shutdown,execveat,pidfd_getfd,unshare,io_uring_setup,io_uring_enter,io_uring_register,inotify_init,inotify_init1'
TRACE_SYSCALLS = ','.join(dict.fromkeys((base.TRACE_SYSCALLS + ',' + DATA_SYSCALLS + ',' + TRANSFER_SYSCALLS + ',' + EXTRA_SYSCALLS).split(',')))
RAW_SYSCALLS = ','.join(dict.fromkeys((DATA_SYSCALLS + ',' + TRANSFER_SYSCALLS + ',connect,pidfd_getfd,io_uring_setup,io_uring_enter,io_uring_register').split(',')))
EVENTS = {'session-start', 'user-prompt-submit', 'pre-tool-use', 'post-tool-use', 'pre-compact', 'stop'}
REQUIRED = ('hooks/claude-hook.sh', 'scripts/inject-plan.py')
UNKNOWN = base.UNKNOWN
UNKNOWN_FD = (UNKNOWN, None)
READS = {'read', 'readv', 'recvfrom'}
WRITES = {'write', 'writev', 'sendto'}
TRANSFERS = {'recvmsg', 'sendmsg', 'recvmmsg', 'sendmmsg'} | set(TRANSFER_SYSCALLS.split(','))
TRANSFER_FDS = {'sendfile': (0, 1), 'splice': (0, 2), 'tee': (0, 1), 'copy_file_range': (0, 2)}
DIAGNOSTIC_LIMIT = 32


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _pair(args):
    pair = ast.literal_eval(args)
    if not isinstance(pair, list) or len(pair) != 2 or any(type(v) is not int or v < 0 for v in pair) or pair[0] == pair[1]:
        raise ValueError('invalid pair')
    return pair


def _raw(args):
    # A quoted decoded buffer, iovec or sockaddr is never acceptable input.
    return all(re.fullmatch(r'(?:0x[0-9a-fA-F]+|[0-9]+|NULL)', value) for value in args)


def _replay(text, native_root, digests, expected_host_executable, allowed_interpreters, *, hazards=None, fd_numbers=None):
    # Optional strace -ttt timestamps retain the original line indices used by
    # native/debug correlation. Timestamp absence is not fabricated as zero.
    normalized = []; timestamps = {}
    for number, line in enumerate(text.splitlines()):
        matched = re.fullmatch(r'(\d+(?:<[^>]*>)?\s+)([0-9]{10}\.[0-9]{1,9})\s+(.*)', line)
        if matched:
            timestamps[number] = matched[2]; line = matched[1] + matched[3]
        normalized.append(line)
    events, errors = base._events('\n'.join(normalized))
    hazards = hazards or {}
    if len(events) > 250000:
        return {'errors': ['trace event budget exceeded'], 'hooks': []}, []
    process_events = {}
    for index, pid, _, _ in events:
        process_events.setdefault(pid, []).append(index)
    processes = {}; generations = {}; roots = []; root_execs = set(); hooks = []; channels = []
    accesses = []; io = []; exits = []; unsupported = []
    fd_history = {}; uncertain_io = []; auxiliary_reads = []; network_reads = []
    close_bindings = {}; socketpair_events = set(); guard_accesses = []
    diagnostics = []; diagnostic_count = 0
    paths = {str(Path(native_root) / rel): rel for rel in REQUIRED}

    def diagnostic(kind, **fields):
        nonlocal diagnostic_count
        diagnostic_count += 1
        if len(diagnostics) < DIAGNOSTIC_LIMIT:
            diagnostics.append({'kind': kind, 'pid': pid, 'generation': state['generation'],
                                'sequence': index, **fields})

    def path_hash(path):
        # Hash the normalized path spelling, not file contents. The caller can
        # compare known controlled paths without exporting arbitrary paths.
        return _hash(path.encode('utf-8', errors='surrogatepass'))

    def fresh(pid, parent=None, flags=''):
        generations[pid] = generations.get(pid, 0) + 1
        state = {'generation': generations[pid], 'fds': {}, 'cwd': ['/workspace'], 'hook': None, 'script': None,
                 'host': parent is None, 'exec_generation': 0, 'execution': None}
        if parent:
            state['fds'] = parent['fds'] if 'CLONE_FILES' in flags else dict(parent['fds'])
            state['cwd'] = parent['cwd'] if 'CLONE_FS' in flags else list(parent['cwd'])
            state['hook'] = parent['hook']
            state['host'] = parent['host'] and 'CLONE_THREAD' in flags
        processes[pid] = state
        return state

    def uncertain(kind, number=0, write=False):
        return any(low <= number <= high for low, high in hazards.get((index, kind, write), ()))

    def get_fd(state, number):
        remember(state, number, state['fds'].get(number))
        return UNKNOWN_FD if uncertain('fds', number) else state['fds'].get(number)

    def set_fd(state, number, value):
        if number == 1 and value and isinstance(value[0], dict) and value[0]['kind'] == 'inotify':
            value[0]['stdout_alias'] = True
        remember(state, number, value)
        if uncertain('fds', number, True):
            value = UNKNOWN_FD
        if value is None:
            state['fds'].pop(number, None)
        else:
            state['fds'][number] = value

    def remember(state, number, value):
        if value and isinstance(value[0], dict) and 'channels' in value[0]:
            fd_history.setdefault((id(state['fds']), number), set()).update(value[0]['channels'])

    def slots(state):
        return tuple(state['fds']) if fd_numbers is None else fd_numbers

    def absolute(value, state, dirfd=None):
        if os.path.isabs(value):
            return os.path.normpath(value)
        directory = UNKNOWN if uncertain('cwd') else state['cwd'][0]
        if dirfd is not None and dirfd != 'AT_FDCWD':
            opened = get_fd(state, base._number(dirfd))
            directory = opened[0].get('path', UNKNOWN) if opened and isinstance(opened[0], dict) else UNKNOWN
        if not isinstance(directory, str):
            raise ValueError('unknown relative path')
        return os.path.normpath(os.path.join(directory, value))

    def endpoint(binding, writing):
        if not binding or not isinstance(binding[0], dict):
            return None
        resource = binding[0]
        if resource['kind'] == 'pipe':
            if resource['end'] != ('w' if writing else 'r'):
                return None
            return resource['channels'][0]
        if resource['kind'] == 'unix-stream':
            return resource['channels'][resource['end'] if writing else 1 - resource['end']]
        return None

    def access_fd(state, number, write=False):
        return (state['fds'], write, (number, number))

    for index, pid, call, finished in events:
        state = processes.get(pid)
        if state is None:
            state = fresh(pid); roots.append((pid, state['generation']))
            if len(roots) > 1:
                errors.append('unparented process or PID reuse')
        if call.startswith('+++ exited with ') or call.startswith('+++ killed by '):
            match = re.fullmatch(r'\+\+\+ exited with ([0-9]+) \+\+\+', call)
            code = int(match[1]) if match else None
            exits.append({'pid': pid, 'generation': state['generation'], 'sequence': index, 'exit_code': code})
            if state['hook'] is not None:
                hook = hooks[state['hook']]
                if (pid, state['generation']) == (hook['pid'], hook['generation']):
                    hook['exit_code'] = code; hook['exit_sequence'] = index
                    hook['exit_time'] = timestamps.get(index)
                if code is None:
                    hook['descendant_failures'].append({'pid': pid, 'generation': state['generation'],
                                                       'sequence': index, 'termination': 'signal'})
                if state['execution'] is not None:
                    state['execution']['exit_code'] = code
                    state['execution']['end_sequence'] = index
                    state['execution']['termination'] = 'exit' if code is not None else 'signal'
            del processes[pid]
            continue
        if call.startswith('--- '):
            continue
        parsed = re.match(r'^(\w+)\((.*)\)\s+=\s+(.+)$', call)
        if not parsed:
            errors.append('unrecognized syscall record'); continue
        name, body, result = parsed.groups()
        if name not in TRACE_SYSCALLS.split(','):
            errors.append('unexpected traced syscall'); continue
        try:
            args = base._arguments(body)
            if name in RAW_SYSCALLS.split(',') and not _raw(args):
                errors.append('data syscall was not raw'); continue
            # Even a failed third-party I/O attempt blocks the narrowly proved
            # close/reallocation ordering optimization. It is not byte evidence.
            if name in READS | WRITES | TRANSFERS:
                for position in TRANSFER_FDS.get(name, (0,)):
                    number = base._number(args[position])
                    guard_accesses.append((index, finished, pid, state['fds'], False, (number, number), name))
            if result.startswith('-1 '):
                if name == 'close' and not result.startswith('-1 EBADF'):
                    errors.append('failed close may have released descriptor')
                if name in READS | WRITES and endpoint(get_fd(state, base._number(args[0])), name in WRITES) is not None:
                    # Keep EAGAIN distinct from EOF; a later genuine EOF is OK.
                    if name in WRITES or not any(result.startswith('-1 ' + error) for error in ('EAGAIN', 'EINTR')):
                        binding = get_fd(state, base._number(args[0]))
                        unsupported.append((binding, 'failed channel I/O'))
                continue
            if result.startswith('? ERESTART'):
                continue
            if result.startswith('?'):
                # Only a traced native auxiliary FD can make an unfinished
                # read irrelevant to hook stdout. Retain its FD footprint over
                # the entire blocked interval for the shared-table replay.
                if name == 'read' and result == '?' and len(args) == 3 and base._number(args[2]) > 0:
                    number = base._number(args[0]); binding = get_fd(state, number)
                    accesses.append((index, finished, pid, state['fds'], False, (number, number), name))
                    if (state['host'] and state['hook'] is None and binding and isinstance(binding[0], dict)
                            and binding[0]['kind'] == 'inotify' and binding[0]['native_created']
                            and not uncertain('fds', number)):
                        auxiliary_reads.append(({'kind': 'terminated_native_inotify_read', 'pid': pid,
                                                 'generation': state['generation'], 'sequence': index,
                                                 'end_sequence': finished}, binding[0]))
                        continue
                diagnostic('unresolved_syscall', syscall=name, result_kind='unresolved_return',
                           result_sha256=_hash(result.encode('utf-8', errors='surrogatepass')))
                errors.append('unresolved syscall result'); continue
            returned = base._return_number(result)
            footprint = base._footprint('execve' if name == 'execveat' else name,
                                        args[1:] if name == 'execveat' else args, returned, body, state)
            if name in READS | WRITES | {'recvmsg', 'sendmsg', 'recvmmsg', 'sendmmsg', 'shutdown'}:
                footprint.append(access_fd(state, base._number(args[0])))
            if name in TRANSFERS:
                footprint.extend(access_fd(state, base._number(args[position]))
                                 for position in TRANSFER_FDS.get(name, (0,)))
            if name in {'pipe', 'pipe2', 'socketpair'} and returned == 0:
                for number in _pair(args[3] if name == 'socketpair' else args[0]):
                    footprint.append(access_fd(state, number, True))
            if name in {'socket', 'accept', 'accept4', 'pidfd_getfd', 'inotify_init', 'inotify_init1'} and returned >= 0:
                footprint.append(access_fd(state, returned, True))
            footprint_end = finished
            if name in {'clone', 'clone3', 'fork', 'vfork'} and returned > 0:
                child_events = process_events.get(returned, [])
                position = bisect.bisect_right(child_events, index)
                if position < len(child_events):
                    footprint_end = min(finished, child_events[position] - 1)
            for resource, write, span in footprint:
                accesses.append((index, footprint_end, pid, resource, write, span, name))

            if name in {'clone', 'clone3', 'fork', 'vfork'}:
                if returned > 0:
                    if returned in processes:
                        errors.append('child PID already active')
                    child = fresh(returned, state, body)
                    if 'CLONE_FILES' not in body:
                        child['fds'] = {n: value for n in slots(state) if (value := get_fd(state, n)) is not None}
                    if 'CLONE_FS' not in body:
                        child['cwd'] = [UNKNOWN if uncertain('cwd') else state['cwd'][0]]
            elif name in {'execve', 'execveat'} and returned == 0:
                root_execs.add((pid, state['generation']))
                state['fds'] = {n: value for n in slots(state) if (value := get_fd(state, n)) is not None and value[1] is not True}
                offset = 1 if name == 'execveat' else 0
                if name == 'execveat' and args[4] not in {'0', '0x0'}:
                    errors.append('unsupported execveat flags'); continue
                filename = absolute(base._string(args[offset]), state, args[0] if offset else None)
                state['exec_generation'] += 1
                first_root_exec = (pid, state['generation']) == roots[0] and state['exec_generation'] == 1
                if state['host']:
                    if not first_root_exec:
                        diagnostic('host_reexec', root_matches=filename == expected_host_executable,
                                   exec_path_sha256=path_hash(filename))
                        errors.append('native host process or thread executed a new image')
                        state['host'] = False
                    elif filename != expected_host_executable:
                        diagnostic('root_identity', root_matches=False, exec_path_sha256=path_hash(filename))
                        errors.append('root executable differs from caller binding')
                        state['host'] = False
                if state['execution'] is not None:
                    state['execution']['end_sequence'] = index
                    state['execution']['termination'] = 'exec-replaced'
                    errors.append('fast path execution was replaced before normal completion')
                    state['execution'] = None
                argv = ast.literal_eval(args[offset + 1])
                if not isinstance(argv, list) or not all(isinstance(a, str) for a in argv):
                    raise ValueError('incomplete exec argv')
                state['script'] = None
                if len(argv) >= 2 and Path(argv[1]).name == 'claude-hook.sh':
                    script = absolute(argv[1], state)
                    identity = {'interpreter_matches': filename in allowed_interpreters['shell'],
                                'argc': len(argv), 'argc_matches': len(argv) == 3,
                                'script_matches': script == str(Path(native_root) / REQUIRED[0]),
                                'event_known': len(argv) > 2 and argv[2] in EVENTS}
                    if not all(identity[key] for key in ('interpreter_matches', 'argc_matches', 'script_matches', 'event_known')):
                        diagnostic('dispatcher_identity', **identity, exec_path_sha256=path_hash(filename),
                                   script_path_sha256=path_hash(script))
                        errors.append('dispatcher identity or event differs'); continue
                    if state['hook'] is not None:
                        errors.append('nested or repeated dispatcher execution')
                    output = endpoint(get_fd(state, 1), True)
                    if output is None:
                        errors.append('dispatcher stdout resource is unknown')
                    hook = {'pid': pid, 'generation': state['generation'], 'exec_sequence': index,
                            'exec_time': timestamps.get(index),
                            'event': argv[2], 'dispatcher_sha256': digests[REQUIRED[0]],
                            'script_reads': [], 'fast_path_reads': [], 'fast_path_execs': [], 'output_channel': output,
                            'descendant_failures': [],
                            'exit_code': None, 'exit_sequence': None}
                    hooks.append(hook); state['hook'] = len(hooks) - 1; state['script'] = REQUIRED[0]
                    state['host'] = False
                    if len(hooks) > 64:
                        return {'errors': ['hook observation budget exceeded'], 'hooks': [],
                                'diagnostics': diagnostics, 'diagnostic_count': diagnostic_count}, accesses
                elif len(argv) >= 4 and Path(argv[3]).name == 'inject-plan.py':
                    script = absolute(argv[3], state)
                    identity = {'owner_bound': state['hook'] is not None,
                                'interpreter_matches': filename in allowed_interpreters['python'],
                                'argc': len(argv), 'argc_matches': len(argv) == 5,
                                'flags_match': argv[1:3] == ['-I', '-B'],
                                'script_matches': script == str(Path(native_root) / REQUIRED[1]),
                                'event_known': len(argv) > 4 and argv[4] in {'--claude-event=' + e for e in EVENTS},
                                'event_matches': len(argv) > 4 and state['hook'] is not None
                                and argv[4] == '--claude-event=' + hooks[state['hook']]['event']}
                    if not all(identity[key] for key in ('owner_bound', 'interpreter_matches', 'argc_matches',
                                                         'flags_match', 'script_matches', 'event_matches')):
                        diagnostic('fast_path_identity', **identity, exec_path_sha256=path_hash(filename),
                                   script_path_sha256=path_hash(script))
                        errors.append('fast path identity or event differs'); continue
                    state['script'] = REQUIRED[1]
                    execution = {'pid': pid, 'generation': state['generation'], 'exec_generation': state['exec_generation'],
                                 'exec_sequence': index, 'end_sequence': None, 'exit_code': None, 'termination': None}
                    hooks[state['hook']]['fast_path_execs'].append(execution)
                    state['execution'] = execution
            elif name in {'open', 'openat', 'openat2'} and returned >= 0:
                position = 0 if name == 'open' else 1
                path = absolute(base._string(args[position]), state, None if name == 'open' else args[0])
                if path in paths and any(flag in body for flag in ('O_WRONLY', 'O_RDWR', 'O_TRUNC', 'O_CREAT')):
                    errors.append('bound script was opened for mutation')
                if (re.search(r'^/proc/(?:self|thread-self|[0-9]+)/(?:task/(?:self|[0-9]+)/)?fd/', path)
                        or path.startswith('/dev/fd/') or path in {'/dev/stdin', '/dev/stdout', '/dev/stderr'}):
                    errors.append('unsupported descriptor import through path')
                set_fd(state, returned, ({'kind': 'file', 'path': path}, 'O_CLOEXEC' in body))
            elif name in {'pipe', 'pipe2', 'socketpair'} and returned == 0:
                numbers = _pair(args[3] if name == 'socketpair' else args[0])
                valid = name != 'socketpair' or (args[0] == 'AF_UNIX' and args[1].split('|')[0] == 'SOCK_STREAM' and args[2] in {'0', '0x0'})
                if not valid:
                    for number in numbers:
                        set_fd(state, number, UNKNOWN_FD)
                    continue
                if name == 'socketpair':
                    socketpair_events.add(index)
                count = 2 if name == 'socketpair' else 1
                allocated = list(range(len(channels), len(channels) + count))
                channels.extend({'kind': 'unix-stream' if name == 'socketpair' else 'pipe'} for _ in range(count))
                for side, number in enumerate(numbers):
                    resource = {'kind': 'unix-stream' if name == 'socketpair' else 'pipe', 'channels': allocated,
                                'end': side if name == 'socketpair' else ('r' if side == 0 else 'w')}
                    set_fd(state, number, (resource, 'CLOEXEC' in body))
            elif name in {'inotify_init', 'inotify_init1'} and returned >= 0:
                flags = set(args[0].split('|')) if name == 'inotify_init1' and len(args) == 1 else set()
                if ((name == 'inotify_init' and args not in ([], [''])) or (name == 'inotify_init1' and
                        (len(args) != 1 or not flags <= {'0', 'IN_CLOEXEC', 'IN_NONBLOCK'}))):
                    raise ValueError('unsupported inotify flags')
                set_fd(state, returned, ({'kind': 'inotify', 'native_created': state['host'] and state['hook'] is None,
                                         'stdout_alias': False}, 'IN_CLOEXEC' in flags))
            elif name in {'socket', 'accept', 'accept4', 'pidfd_getfd'} and returned >= 0:
                # Network connections are not evidence sources. Imported FDs
                # cannot later be mistaken for a fully observed stdout pipe.
                resource = None
                if name == 'socket':
                    resource = {'kind': 'opaque-socket', 'domain': args[0], 'protocol': args[2]}
                elif name in {'accept', 'accept4'}:
                    listener = get_fd(state, base._number(args[0]))
                    if listener and isinstance(listener[0], dict) and listener[0]['kind'] == 'opaque-socket':
                        resource = dict(listener[0])
                else:
                    errors.append('unmodeled cross-process descriptor import')
                set_fd(state, returned, (resource, 'CLOEXEC' in body) if resource else UNKNOWN_FD)
            elif name == 'close' and returned == 0:
                # Inspect the pre-close state after all earlier conservative
                # hazards have propagated. This close's own write hazard must
                # not be mistaken for unknown provenance of its OLD binding.
                old = get_fd(state, base._number(args[0]))
                close_bindings[index] = bool(old and isinstance(old[0], dict))
                set_fd(state, base._number(args[0]), None)
            elif name == 'close_range' and returned == 0:
                low = base._number(args[0]); high = base._number(args[1].replace('~0U', '4294967295'))
                if 'CLOSE_RANGE_UNSHARE' in body:
                    state['fds'] = {n: value for n in slots(state) if (value := get_fd(state, n)) is not None}
                for number in slots(state):
                    if low <= number <= high:
                        value = state['fds'].get(number)
                        set_fd(state, number, (value[0], True) if value and 'CLOSE_RANGE_CLOEXEC' in body else None)
            elif name in {'dup', 'dup2', 'dup3'} and returned >= 0:
                source = base._number(args[0]); value = get_fd(state, source)
                if name == 'dup2' and source == returned:
                    continue
                set_fd(state, returned, (value[0], name == 'dup3' and 'O_CLOEXEC' in body) if value else UNKNOWN_FD)
            elif name == 'fcntl' and returned >= 0:
                source = base._number(args[0]); value = get_fd(state, source)
                if args[1] in {'F_DUPFD', 'F_DUPFD_CLOEXEC'}:
                    set_fd(state, returned, (value[0], args[1] == 'F_DUPFD_CLOEXEC') if value else UNKNOWN_FD)
                elif args[1] == 'F_SETFD' and value:
                    set_fd(state, source, (value[0], 'FD_CLOEXEC' in args[2]))
            elif name == 'chdir' and returned == 0:
                state['cwd'][0] = UNKNOWN if uncertain('cwd', write=True) else absolute(base._string(args[0]), state)
            elif name == 'fchdir' and returned == 0:
                value = get_fd(state, base._number(args[0]))
                state['cwd'][0] = UNKNOWN if uncertain('cwd', write=True) or not value or not isinstance(value[0], dict) else value[0].get('path', UNKNOWN)
            elif name in READS | WRITES:
                number = base._number(args[0]); binding = get_fd(state, number); writing = name in WRITES
                if uncertain('fds', number):
                    uncertain_io.append((id(state['fds']), number))
                channel = endpoint(binding, writing)
                if name in {'read', 'write', 'recvfrom', 'sendto'} and returned > base._number(args[2]):
                    errors.append('I/O return exceeds requested byte length')
                if name == 'recvfrom' and base._number(args[3]) not in {0, 0x40}:
                    unsupported.append((binding, 'unsupported receive flags'))
                if name == 'sendto' and base._number(args[3]) & ~(0x40 | 0x4000):
                    unsupported.append((binding, 'unsupported send flags'))
                if channel is not None:
                    io.append({'channel': channel, 'write': writing, 'bytes': returned, 'sequence': index,
                               'end_sequence': finished, 'pid': pid, 'generation': state['generation'],
                               'host': state['host'], 'hook_owner': state['hook'], 'eof': not writing and name in {'read', 'recvfrom'}
                               and base._number(args[2]) > 0 and returned == 0,
                               'time': timestamps.get(index), 'end_time': timestamps.get(finished)})
                    if len(io) > 16384:
                        return {'errors': ['channel I/O observation budget exceeded'], 'hooks': [],
                                'diagnostics': diagnostics, 'diagnostic_count': diagnostic_count}, accesses
                elif state['hook'] is not None and (binding is None or binding[0] is UNKNOWN):
                    errors.append('hook I/O has ambiguous descriptor')
                if not writing and returned > 0 and state['script'] and binding and isinstance(binding[0], dict):
                    expected = str(Path(native_root) / state['script'])
                    if binding[0].get('path') == expected:
                        hook = hooks[state['hook']]
                        key = 'script_reads' if state['script'] == REQUIRED[0] else 'fast_path_reads'
                        hook[key].append({'pid': pid, 'generation': state['generation'], 'sequence': index,
                                          'exec_generation': state['exec_generation'],
                                          'bytes': returned, 'sha256': digests[state['script']]})
            elif name in TRANSFERS:
                # We do not decode iovecs, SCM_RIGHTS or transfer payloads.
                # Lengths and pointers are not FD numbers. Unix ancillary data
                # can import/export unrelated FDs even on a different socket.
                positions = TRANSFER_FDS.get(name, (0,))
                for position in positions:
                    number = base._number(args[position]); value = get_fd(state, number)
                    if uncertain('fds', number):
                        uncertain_io.append((id(state['fds']), number))
                    if value:
                        unsupported.append((value, 'unsupported channel transfer'))
                    if state['hook'] is not None and (value is None or value[0] is UNKNOWN):
                        errors.append('unsupported transfer has unknown hook descriptor')
                if name in {'recvmsg', 'sendmsg', 'recvmmsg', 'sendmmsg'}:
                    value = get_fd(state, base._number(args[0]))
                    domain = value[0].get('domain') if value and isinstance(value[0], dict) else None
                    # Linux v7.0 netlink_recvmsg zeroes scm_cookie, sets only
                    # credentials, and uses scm_recv (not scm_recv_unix). Thus
                    # no SCM_RIGHTS or SCM_PIDFD installation is possible here.
                    # https://raw.githubusercontent.com/torvalds/linux/v7.0/net/netlink/af_netlink.c
                    # https://raw.githubusercontent.com/torvalds/linux/v7.0/net/core/scm.c
                    netlink = (name == 'recvmsg' and state['host'] and state['hook'] is None
                               and domain == 'AF_NETLINK' and value[0].get('protocol') == 'NETLINK_ROUTE'
                               and base._number(args[2]) == 0)
                    if netlink:
                        if len(network_reads) < 32:
                            network_reads.append({'kind': 'native_netlink_route_recvmsg', 'pid': pid,
                                                  'generation': state['generation'], 'sequence': index,
                                                  'fd': base._number(args[0]), 'bytes': returned})
                    elif domain not in {'AF_INET', 'AF_INET6'}:
                        errors.append('unmodeled ancillary descriptor transfer')
            elif name.startswith('io_uring_'):
                errors.append('asynchronous I/O cannot prove complete channel accounting')
            elif name == 'unshare':
                errors.append('unmodeled namespace or shared-table unshare')
        except (ValueError, SyntaxError, IndexError, TypeError, KeyError, OverflowError):
            errors.append('unsupported or malformed syscall arguments')

    if not events or not roots:
        errors.append('empty process trace')
    if set(roots) - root_execs:
        errors.append('root process lacks successful exec record')
    if processes:
        errors.append('missing process exit records')
    observed_auxiliary = []
    for row, resource in auxiliary_reads:
        if resource['stdout_alias'] or not any(
                (item['pid'], item['generation']) == (row['pid'], row['generation'])
                and item['sequence'] > row['end_sequence'] for item in exits):
            errors.append('unfinished auxiliary read lacks isolated descriptor and process exit')
        else:
            observed_auxiliary.append(row)
    if not hooks:
        errors.append('no bound dispatcher executions')
    output_channels = [h['output_channel'] for h in hooks if h['output_channel'] is not None]
    if len(set(output_channels)) != len(output_channels):
        errors.append('multiple dispatcher invocations share output channel')
    if any(fd_history.get(key, set()).intersection(output_channels) for key in uncertain_io):
        errors.append('ambiguous descriptor I/O may affect hook stdout')
    for hook_id, hook in enumerate(hooks):
        channel = hook['output_channel']
        reads = [row for row in io if row['channel'] == channel and not row['write'] and row['host']]
        other_reads = [row for row in io if row['channel'] == channel and not row['write'] and not row['host']]
        writes = [row for row in io if row['channel'] == channel and row['write']]
        hook['stdout_written_bytes'] = sum(row['bytes'] for row in writes)
        hook['stdout_read_bytes'] = sum(row['bytes'] for row in reads)
        hook['stdout_eof'] = any(row['eof'] and row['end_sequence'] >= hook['exec_sequence'] for row in reads)
        hook['stdout_reads'] = reads; hook['stdout_writes'] = writes
        hook['nonhost_read_bytes'] = sum(row['bytes'] for row in other_reads)
        hook['foreign_write_bytes'] = sum(row['bytes'] for row in writes if row['hook_owner'] != hook_id)
        hook['normal_exit'] = hook['exit_code'] == 0 and hook['exit_sequence'] is not None
        hook['transport'] = channels[channel]['kind'] if channel is not None else 'unknown'
        if not hook['script_reads']:
            errors.append('dispatcher script lacks actual bound read')
        if any(execution['exit_code'] == 0 and not any(
                (row['pid'], row['generation'], row['exec_generation']) ==
                (execution['pid'], execution['generation'], execution['exec_generation'])
                and execution['exec_sequence'] < row['sequence'] < execution['end_sequence'] for row in hook['fast_path_reads'])
                for execution in hook['fast_path_execs']):
            errors.append('successful fast path lacks actual bound script read')
        if hook['descendant_failures']:
            errors.append('hook process subtree has signal termination')
        if not hook['normal_exit']:
            errors.append('dispatcher did not exit normally with zero')
        if not hook['stdout_eof']:
            errors.append('hook stdout lacks observed EOF')
        if hook['stdout_written_bytes'] != hook['stdout_read_bytes']:
            errors.append('hook stdout write/read byte totals differ')
        if hook['nonhost_read_bytes']:
            errors.append('hook stdout was consumed outside native host process or threads')
        if hook['foreign_write_bytes']:
            errors.append('hook stdout was written outside its bound dispatcher subtree')
        if channel is not None and any(endpoint(binding, side) == channel for binding, _ in unsupported for side in (False, True)):
            errors.append('hook stdout affected by unsupported or failed I/O')
        # Data on a resource before it was assigned to this invocation cannot
        # be attributed to that command merely because the FD was later reused.
        if any(row['bytes'] and row['sequence'] < hook['exec_sequence'] for row in reads + writes):
            errors.append('hook stdout contains pre-invocation data')
        hook['stdout_empty'] = hook['stdout_written_bytes'] == 0 and hook['stdout_read_bytes'] == 0
    return {'errors': sorted(set(errors)), 'hooks': hooks, 'process_count': sum(generations.values()),
            'root_pid': roots[0][0] if roots else None, 'channel_count': len(channels),
            'process_exit_count': len(exits), 'auxiliary_unfinished_reads': observed_auxiliary[:32],
            'auxiliary_unfinished_read_count': len(observed_auxiliary), 'diagnostics': diagnostics,
            'auxiliary_network_reads': network_reads, 'diagnostic_count': diagnostic_count,
            '_close_bindings': close_bindings, '_socketpair_events': socketpair_events,
            '_guard_accesses': guard_accesses}, accesses


def _close_reallocation_proofs(accesses, initial, conservative, hazards):
    """Prove only isolated Linux close -> empty-slot allocation order.

    file_close_fd_locked releases the slot before filp_close completes:
    https://raw.githubusercontent.com/torvalds/linux/v7.0/fs/file.c
    https://man7.org/linux/man-pages/man2/close.2.html
    This does NOT prove release happened before allocation syscall entry.
    Therefore any third reader, writer or table snapshot blocks shortening.
    The old binding must also remain known in the UNMODIFIED hazard replay.
    """
    proofs = []; adjusted = list(accesses)
    if initial['errors']:
        # In particular, an unmodeled import/unshare or malformed record may
        # lack a reliable footprint. It cannot support an isolation proof.
        return adjusted, proofs
    groups = {}
    for row in accesses + initial.get('_guard_accesses', []):
        groups.setdefault(id(row[3]), []).append(row)
    for position, close in enumerate(accesses):
        start, end, pid, table, write, span, operation = close
        if (operation != 'close' or not write or span[0] != span[1]
                or (start, 'fds', True) not in hazards
                or not initial.get('_close_bindings', {}).get(start)
                or not conservative.get('_close_bindings', {}).get(start)):
            continue
        fd = span[0]
        overlapping = [row for row in groups[id(table)]
                       if row[0] <= end and row[1] >= start and row[5][0] <= fd <= row[5][1]]
        allocs = [row for row in overlapping if row[6] == 'socketpair' and row[4]
                  and row[0] in initial.get('_socketpair_events', set())
                  and row[2] != pid and start < row[0] <= row[1] < end]
        if len(allocs) != 1:
            continue
        alloc = allocs[0]
        if any(row is not close and row is not alloc for row in overlapping):
            continue
        adjusted[position] = (start, alloc[0] - 1, pid, table, write, span, operation)
        proofs.append({'rule': 'linux_close_before_unique_socketpair_allocation', 'fd': fd,
                       'close_pid': pid, 'close_sequence': start, 'close_end_sequence': end,
                       'allocation_pid': alloc[2], 'allocation_sequence': alloc[0],
                       'allocation_end_sequence': alloc[1]})
        if len(proofs) == 32:
            break
    return adjusted, proofs


def analyze_trace(text, native_root, resource_sha256, *, expected_host_executable=None,
                  allowed_interpreters=None, read_script=None, max_bytes=32 * 1024**2):
    """Return bounded observations; caller separately correlates native turns.

    `resource_sha256` must contain REQUIRED relative paths. `read_script(path)`
    reads only those two absolute package files and is useful for offline tests.
    No path from the trace itself is opened. Fresh fully captured subprocess
    stdout channels are required. Unsupported inputs return incomplete facts.

    expected_host_executable is a normalized absolute path. allowed_interpreters
    is {'shell': [absolute paths], 'python': [absolute paths]}, both nonempty.
    The caller verifies their image provenance/binary hashes and may include
    verified samefile aliases. Missing bindings cannot prove native identity.
    The caller also excludes arbitrary filesystem symlinks into process FD
    paths from its isolated layout. Known Linux FD aliases fail closed here;
    offline path text alone cannot resolve arbitrary unobserved symlinks.
    """
    result = {'observation_complete': False, 'errors': [], 'hooks': [], 'diagnostics': [],
              'diagnostic_rejections_by_pass': [0, 0], 'diagnostics_truncated': False,
              'proof_scope': 'caller-bound native command identity, normal exit and stdout byte/EOF accounting; not model delivery or deduplication',
              'caller_requirements': ['verified root and interpreter binary provenance',
                                      'isolated layout excludes arbitrary unobserved filesystem aliases into process FDs',
                                      'complete collection uses exported syscall and raw-data sets']}
    if not isinstance(text, str) or type(max_bytes) is not int or not 0 < max_bytes <= 64 * 1024**2:
        result['errors'] = ['invalid trace input or byte bound']; return result
    try:
        data = text.encode('utf-8')
        if len(data) > max_bytes or any(len(line) > 16384 for line in text.splitlines()):
            result['errors'] = ['trace byte or line budget exceeded']; return result
        root = Path(native_root)
        if not root.is_absolute() or str(root) != os.path.normpath(str(root)):
            raise ValueError('invalid native root')
        def valid_executable(path):
            return isinstance(path, str) and os.path.isabs(path) and os.path.normpath(path) == path
        if (not valid_executable(expected_host_executable) or not isinstance(allowed_interpreters, dict)
                or set(allowed_interpreters) != {'shell', 'python'} or any(
                    not isinstance(paths, list) or not paths or len(paths) != len(set(paths))
                    or not all(valid_executable(path) for path in paths)
                    for paths in allowed_interpreters.values())):
            result['errors'] = ['explicit root and interpreter bindings are required']; return result
        if any(not re.fullmatch(r'[0-9a-f]{64}', resource_sha256.get(rel, '')) for rel in REQUIRED):
            raise ValueError('invalid resource digest')
        reader = read_script or (lambda path: Path(path).read_bytes())
        for rel in REQUIRED:
            if _hash(reader(str(root / rel))) != resource_sha256[rel]:
                raise ValueError('resource digest differs')
        initial, accesses = _replay(text, str(root), resource_sha256, expected_host_executable, allowed_interpreters)
        conflicts, hazards = base._conflicts(accesses)
        numbers = {n for _, _, _, resource, _, span, _ in accesses if isinstance(resource, dict) and span[0] == span[1] for n in span}
        if len(numbers) > 4096:
            result['errors'] = ['descriptor budget exceeded']; return result
        replay, _ = _replay(text, str(root), resource_sha256, expected_host_executable, allowed_interpreters,
                            hazards=hazards, fd_numbers=numbers)
        adjusted, proofs = _close_reallocation_proofs(accesses, initial, replay, hazards)
        original_conflict_count = conflicts['count']
        if proofs:
            conflicts, hazards = base._conflicts(adjusted)
            replay, _ = _replay(text, str(root), resource_sha256, expected_host_executable, allowed_interpreters,
                                hazards=hazards, fd_numbers=numbers)
        replay['errors'] = sorted(set(initial['errors'] + replay['errors']))
        if len(initial['hooks']) == len(replay['hooks']) and any(
                (first['output_channel'], first.get('stdout_written_bytes'), first.get('stdout_read_bytes')) !=
                (second['output_channel'], second.get('stdout_written_bytes'), second.get('stdout_read_bytes'))
                for first, second in zip(initial['hooks'], replay['hooks'])):
            replay['errors'].append('channel accounting changes under binding ambiguity')
        # No conflict samples: those may carry future parser implementation
        # details. Only their count and tainted proof failures are exported.
        result.update({key: value for key, value in replay.items() if not key.startswith('_')})
        # Both passes can diagnose the same rejection. Merge at most 64 bounded
        # records, preserving unique facts while exporting no more than 32.
        merged = []; keys = set()
        for row in replay.get('diagnostics', []) + initial.get('diagnostics', []):
            key = tuple(sorted(row.items()))
            if key not in keys:
                keys.add(key); merged.append(row)
        counts = [initial.get('diagnostic_count', 0), replay.get('diagnostic_count', 0)]
        result.pop('diagnostic_count', None)
        result['diagnostics'] = merged[:DIAGNOSTIC_LIMIT]
        result['diagnostic_rejections_by_pass'] = counts
        result['diagnostics_truncated'] = any(count > DIAGNOSTIC_LIMIT for count in counts) or len(merged) > DIAGNOSTIC_LIMIT
        result['binding_conflict_count'] = conflicts['count']
        result['conservative_binding_conflict_count'] = original_conflict_count
        result['close_reallocation_proofs'] = proofs
        result['trace_sha256'] = _hash(data); result['trace_bytes'] = len(data)
        result['observation_complete'] = not result['errors']
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        result['errors'] = ['invalid resource binding or trace input']
    return result
