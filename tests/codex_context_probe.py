"""Bound one fresh Codex 0.149.1 app-server turn to native context evidence.

No UI approval, session history, project writes, or trust bypass occurs here.
The claim is absence of model-initiated tools, not absence of host file I/O.
Protocol source: openai/codex rust-v0.149.1 app-server/src/bespoke_event_handling.rs.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import tempfile
import time


LIMITS = {'stdout': 16 * 1024**2, 'stderr': 8 * 1024**2,
          'line': 1024**2, 'events': 10000, 'export': 32 * 1024**2}
PASSIVE = {'configWarning', 'remoteControl/status/changed',
           'account/rateLimits/updated', 'mcpServer/startupStatus/updated',
           'thread/status/changed', 'thread/tokenUsage/updated'}
DELTA = {'item/agentMessage/delta', 'item/reasoning/summaryTextDelta',
         'item/reasoning/summaryPartAdded', 'item/reasoning/textDelta'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text_content(item):
    content = item.get('content')
    require(isinstance(content, list) and all(isinstance(c, dict) and
            c.get('type') in {'input_text', 'output_text'} and isinstance(c.get('text'), str)
            for c in content), 'Unknown/nontext raw message content')
    return '\n'.join(c['text'] for c in content)


def assess(events, thread, turn, prompt, source, expected_token, forbidden_token):
    """Assess the complete received stream, including records after turn/completed."""
    begun = ended = None
    starts = {}; ends = {}; hooks = {}; finished = {}; raw = []; final = []
    responses = []; thread_events = []; user_inputs = []
    for index, event in enumerate(events):
        require(isinstance(event, dict), 'Nonobject event')
        if 'id' in event:
            require('method' not in event and 'error' not in event, 'Server request/error')
            continue  # Request responses have already been matched by the collector.
        method = event.get('method'); p = event.get('params', {})
        require(isinstance(p, dict), 'Malformed event parameters')
        if method == 'thread/started':
            thread_events.append(p.get('thread', {})); continue
        if 'threadId' in p:
            require(p['threadId'] == thread, 'Foreign thread notification')
        if 'turnId' in p:
            require(p['turnId'] == turn, 'Foreign turn notification')
        if method in PASSIVE:
            continue
        require(p.get('threadId') == thread, 'Absent thread binding')
        if method in {'turn/started', 'turn/completed'}:
            t = p.get('turn', {})
            require(t.get('id') == turn, 'Foreign turn boundary')
            if method == 'turn/started':
                require(begun is None and ended is None and t.get('status') == 'inProgress', 'Duplicate/invalid turn start')
                begun = index
            else:
                require(begun is not None and ended is None and t.get('status') == 'completed'
                        and t.get('error') is None, 'Incomplete/duplicate turn')
                ended = index
            continue
        require(p.get('turnId') == turn and begun is not None and ended is None,
                'Activity outside the complete turn')
        if method in DELTA:
            require(p.get('itemId') in starts, 'Unbound item delta'); continue
        if method in {'item/started', 'item/completed'}:
            item = p.get('item', {}); ident = item.get('id')
            require(item.get('type') in {'userMessage', 'agentMessage', 'reasoning'} and ident,
                    'Model tool or unknown high-level item')
            if method == 'item/started':
                require(ident not in starts, 'Duplicate item start'); starts[ident] = (index, item['type'])
            else:
                require(ident in starts and ident not in ends and starts[ident][1] == item['type'], 'Unbound item completion')
                ends[ident] = index
                if item['type'] == 'agentMessage' and item.get('phase') == 'final_answer':
                    final.append((index, ident, item.get('text')))
                if item['type'] == 'userMessage':
                    user_inputs.append(item.get('content'))
        elif method == 'rawResponseItem/completed':
            item = p.get('item', {})
            require(item.get('type') in {'message', 'reasoning'}, 'Model tool or unknown raw item')
            require(item.get('id'), 'Raw item lacks identity')
            metadata = item.get('internal_chat_message_metadata_passthrough') or {}
            require(isinstance(metadata, dict) and metadata.get('turn_id', turn) == turn, 'Raw metadata turn mismatch')
            if item['type'] == 'message':
                require(item.get('role') in {'user', 'developer', 'assistant'}
                        and not item.get('recipient') and not item.get('tool_calls'), 'Unknown raw message route')
                value = text_content(item)
                raw.append((index, item, value))
        elif method == 'rawResponse/completed':
            ident = p.get('responseId')
            require(isinstance(ident, str) and ident and ident not in [r[1] for r in responses], 'Invalid raw response completion')
            responses.append((index, ident))
        elif method in {'hook/started', 'hook/completed'}:
            run = p.get('run', {}); ident = run.get('id'); name = run.get('eventName')
            require(name in {'sessionStart', 'userPromptSubmit', 'stop'}, 'Tool/reset/unknown hook')
            require(ident and run.get('sourcePath') == source and run.get('source') == 'plugin'
                    and run.get('handlerType') == 'command' and run.get('executionMode') == 'sync'
                    and run.get('scope') == ('thread' if name == 'sessionStart' else 'turn'), 'Unbound hook identity')
            if method == 'hook/started':
                require(ident not in hooks and run.get('status') == 'running' and run.get('startedAt') is not None,
                        'Invalid hook start'); hooks[ident] = (index, run)
            else:
                require(ident in hooks and ident not in finished and run.get('status') == 'completed'
                        and run.get('completedAt') is not None, 'Incomplete hook lifecycle')
                require(all(run.get(k) == hooks[ident][1].get(k) for k in
                        ('id', 'eventName', 'sourcePath', 'source', 'handlerType', 'executionMode', 'scope', 'startedAt')),
                        'Hook identity changed')
                entries = run.get('entries')
                allowed_kind = 'warning' if name == 'stop' else 'context'
                require(isinstance(entries, list) and all(isinstance(e, dict) and e.get('kind') == allowed_kind
                        and isinstance(e.get('text'), str) for e in entries), 'Hook error/control/unknown output')
                require(name != 'stop' or all('PW_RECOVERY_' not in e['text'] for e in entries),
                        'Stop warning must not introduce recovery context')
                finished[ident] = (index, run)
        else:
            raise ValueError('Unknown or unsafe native notification: ' + str(method))
    require(len(thread_events) == 1 and thread_events[0].get('id') == thread, 'Missing/duplicate thread notification')
    require(begun is not None and ended is not None and begun < ended, 'Missing turn boundaries')
    require(starts.keys() == ends.keys() and hooks.keys() == finished.keys(), 'Unfinished native item/hook')
    require(len(user_inputs) == 1 and user_inputs[0] == [{'type': 'text', 'text': prompt, 'text_elements': []}],
            'Native user input differs')
    require(any(i['role'] == 'user' and text == prompt for _, i, text in raw), 'Missing raw user input')
    require(len(final) == 1 and responses and final[0][0] < responses[-1][0] < ended,
            'Missing final model response and completion')
    wanted = expected_token if expected_token is not None else 'NO_CONTEXT'
    require(final[0][2] == wanted, 'Final response differs from expected context')
    raw_final = [(idx, item) for idx, item, value in raw if item['role'] == 'assistant'
                 and item.get('phase') == 'final_answer' and value == wanted and item['id'] == final[0][1]]
    require(len(raw_final) == 1, 'Final answer not bound to raw model response')
    if forbidden_token:
        require(forbidden_token not in json.dumps(events, ensure_ascii=False), 'Forbidden owner token present')
    contexts = [(idx, r, entry['text']) for idx, r in finished.values() for entry in r['entries']
                if entry['kind'] == 'context']
    stop_warnings = [{'hook_id': r['id'], 'hook_completed_event': idx, 'text': entry['text']}
                     for idx, r in finished.values() for entry in r['entries'] if entry['kind'] == 'warning']
    injections = []
    if expected_token is None:
        require(not hooks and not contexts and not any('PW_RECOVERY_' in value for _, _, value in raw),
                'Untrusted hook execution/context observed')
    else:
        startup = [r for _, r in finished.values() if r['eventName'] == 'sessionStart']
        submits = [r for _, r in finished.values() if r['eventName'] == 'userPromptSubmit']
        require(len(startup) == 1 and len(submits) <= 1 and len(startup[0]['entries']) == 1,
                'Startup/submit lifecycle not unique')
        require(contexts and all(expected_token in text for _, _, text in contexts), 'Unexpected context token source')
        contexts.sort(key=lambda item: item[0])
        require(contexts[0][1]['eventName'] == 'sessionStart', 'Submit context preceded startup context')
        used_ids = set()
        for pos, (idx, run, context) in enumerate(contexts):
            # Equal text is two separate injections when two native hooks emit
            # it. A distinct following developer message must bind each event;
            # neither text deduplication nor reusing one message proves this.
            boundary = contexts[pos + 1][0] if pos + 1 < len(contexts) else raw_final[0][0]
            delivered = [(n, i) for n, i, value in raw if i['role'] == 'developer' and context == value
                         and idx < n < boundary]
            require(len(delivered) == 1 and delivered[0][1]['id'] not in used_ids,
                    'Hook context lacks a distinct subsequent raw developer message')
            n, item = delivered[0]; used_ids.add(item['id'])
            injections.append({'hook_id': run['id'], 'event_name': run['eventName'], 'hook_completed_event': idx,
                               'developer_event': n, 'developer_item_id': item['id'],
                               'context_sha256': hashlib.sha256(context.encode()).hexdigest()})
        allowed_events = {entry['developer_event'] for entry in injections} | {raw_final[0][0]}
        require(all(expected_token not in value or n in allowed_events
                    for n, _, value in raw), 'Recovery token arrived through an additional message')
    return {'status': 'Passed', 'thread_id': thread, 'turn_id': turn, 'answer': wanted,
            'no_model_tool_calls': True, 'injection': injections[0] if injections else None,
            'injections': injections, 'stop_warnings': stop_warnings,
            'turn_started_event': begun, 'turn_completed_event': ended,
            'scope': 'No model-initiated tool calls in this complete native turn; host I/O is not excluded.'}


def fresh_thread(info, work):
    require(isinstance(info, dict) and info.get('id') and info.get('sessionId') == info['id']
            and info.get('ephemeral') is True and info.get('forkedFromId') is None
            and info.get('parentThreadId') is None and info.get('turns') == []
            and info.get('cwd') == str(work) and info.get('cliVersion') == '0.149.1', 'Not a fresh fixed-version native thread')


def run_probe(model, work, out, package, native_root, timeout, sanitize, *, prompt,
              expected_token, forbidden_token=None, limits=None):
    """Return CompletedProcess + observation. Use a separate out for each invocation.

    expected_token=None is the untrusted NO_CONTEXT control. Tokens are never
    sent to Codex; their only use is assessment after the stream has closed.
    Caller supplies an isolated environment, installed native root, and trust.
    """
    require(isinstance(prompt, str), 'Invalid prompt')
    for token in (expected_token, forbidden_token):
        require(token is None or isinstance(token, str) and re.fullmatch(r'PW_RECOVERY_[a-f0-9]{32}', token), 'Invalid recovery token')
        require(token is None or token not in prompt, 'Token must not be sent to model')
    require(not expected_token or expected_token != forbidden_token, 'Conflicting expected/forbidden token')
    return _collect_native_turn(model, work, out, package, native_root, timeout, sanitize,
        prompt=prompt, evaluator=lambda events, thread, turn, source:
            assess(events, thread, turn, prompt, source, expected_token, forbidden_token),
        evidence_prefix='context', limits=limits)


def _collect_native_turn(model, work, out, package, native_root, timeout, sanitize, *, prompt,
                         evaluator, evidence_prefix, limits=None, command_prefix=(), trace_limit=None):
    """Shared transport only; each probe retains its own strict final assessor.

    command_prefix is private API: the stop wrapper validates its exact strace
    shape and owned tmpfs destination before calling. It wraps the real Popen.
    """
    require(evidence_prefix in {'context', 'stop'} and callable(evaluator), 'Invalid probe assessor')
    require(os.name == 'posix' and callable(sanitize), 'POSIX and explicit sanitizer required')
    require(isinstance(timeout, (int, float)) and not isinstance(timeout, bool) and 0 < timeout <= 600,
            'Timeout must be in (0, 600]')
    require(isinstance(model, str) and model and isinstance(prompt, str) and 0 < len(prompt.encode()) <= 16384,
            'Invalid model/prompt')
    paths = [Path(p).absolute() for p in (work, out, package, native_root)]
    work, out, package, native_root = paths
    require(all(p.is_dir() for p in (work, package, native_root)) and (not out.exists() or out.is_dir()), 'Invalid resource/output directory')
    require(not out.is_symlink() and all(not out.resolve().is_relative_to(p.resolve())
            for p in (work, native_root, package)), 'Output must be separate from project/package')
    caps = dict(LIMITS)
    if limits is not None:
        require(isinstance(limits, dict) and not set(limits) - set(caps), 'Unknown limit')
        for key, value in limits.items():
            require(type(value) is int and 0 < value <= caps[key], 'Invalid output limit'); caps[key] = value
    names = [evidence_prefix + suffix for suffix in ('-protocol.jsonl', '-native.stderr', '-observation.json')]
    require(not any((out / name).exists() or (out / name).is_symlink() for name in names), 'Evidence already exists')
    expected = package / 'dist/codex/planweft'
    require(expected.is_dir(), 'Missing exact Codex distribution')
    bindings = {}
    for base in [Path('hooks'), Path('.codex/hooks'), Path('skills/project-docs/scripts')]:
        require((expected / base).is_dir(), 'Missing packaged hook dependency directory')
        for f in sorted((expected / base).rglob('*')):
            if f.is_file():
                rel = f.relative_to(expected); target = native_root / rel
                require(not f.is_symlink() and target.is_file() and not target.is_symlink(), 'Unsafe/missing hook resource')
                data = f.read_bytes()
                require(target.read_bytes() == data and (target.stat().st_mode & 0o111) == (f.stat().st_mode & 0o111), 'Installed hook resource differs')
                bindings[str(rel)] = hashlib.sha256(data).hexdigest()
    source = str(native_root / 'hooks/codex-hooks.json')
    require('hooks/codex-hooks.json' in bindings, 'Hook manifest absent')
    # Validate redaction before creating evidence or starting any process.
    redaction_check = sanitize('context-probe')
    require(isinstance(redaction_check, str) and redaction_check, 'Sanitizer must return nonempty text')
    out.mkdir(parents=True, exist_ok=True)
    command = [*command_prefix, 'codex', '--disable', 'memories', '--disable', 'multi_agent', 'app-server']
    deadline = time.monotonic() + timeout
    events = []; buffer = b''; pending = []; process = None; thread = turn = None
    raw_size = raw_stderr_size = exported = 0
    stdout_open = stderr_open = True
    evidence = {'status': 'Failed'}; stderr_text = ''; failure = None
    private = Path(tempfile.mkdtemp(prefix='planweft-codex-context-', dir='/tmp'))
    raw_error = private / 'stderr'
    journal = None; errors = None
    def safe(value):
        nonlocal exported
        result = sanitize(value)
        require(isinstance(result, str) and (not value or result), 'Sanitizer returned nontext/empty output')
        size = len(result.encode()); require(exported + size <= caps['export'], 'Sanitized export limit exceeded')
        exported += size
        return result
    try:
        errors = raw_error.open('w+b'); journal = (out / names[0]).open('x')
        def log(direction, value):
            entry = safe(json.dumps({'direction': direction, 'message': value}, ensure_ascii=False))
            require(isinstance(json.loads(entry), dict), 'Sanitizer damaged protocol JSON')
            journal.write(entry + '\n'); journal.flush()
        def send(value):
            log('sent', value)
            process.stdin.write((json.dumps(value) + '\n').encode()); process.stdin.flush()
        def pump():
            nonlocal buffer, raw_size, raw_stderr_size, stdout_open, stderr_open
            require(time.monotonic() < deadline, 'Native probe timeout')
            streams = ([process.stdout] if stdout_open else []) + ([process.stderr] if stderr_open else [])
            if not streams: return False
            ready = select.select(streams, [], [], min(0.1, max(0, deadline - time.monotonic())))[0]
            for stream in ready:
                chunk = os.read(stream.fileno(), 65536)
                if stream is process.stderr:
                    if not chunk: stderr_open = False; continue
                    available = max(0, caps['stderr'] - raw_stderr_size)
                    # Only the collector writes this private file. Native output
                    # cannot outrun a polling file-size check and fill the disk.
                    errors.write(chunk[:available]); raw_stderr_size += len(chunk)
                    require(raw_stderr_size <= caps['stderr'], 'Native stderr limit exceeded')
                    continue
                if not chunk:
                    stdout_open = False
                    require(not buffer, 'Truncated native JSON line'); continue
                raw_size += len(chunk); require(raw_size <= caps['stdout'], 'Native stdout limit exceeded')
                buffer += chunk
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    require(0 < len(line) <= caps['line'], 'Native JSON line limit/empty line')
                    value = json.loads(line)
                    require(isinstance(value, dict) and len(events) < caps['events'], 'Native event limit/type')
                    log('received', value); events.append(value); pending.append(value)
                require(len(buffer) <= caps['line'], 'Unterminated native line limit')
            return stdout_open or stderr_open
        responses = set()
        def receive():
            while not pending:
                require(pump(), 'Native EOF before completed turn')
            value = pending.pop(0)
            require(not ('id' in value and 'method' in value), 'Unexpected native server request')
            return value
        def request(ident, method, params):
            send({'id': ident, 'method': method, 'params': params})
            while True:
                value = receive()
                if 'id' in value:
                    require(value['id'] == ident and ident not in responses and 'result' in value and 'error' not in value,
                            'Mismatched/failed native response')
                    responses.add(ident); return value['result']
        spawn_options = {}
        if command_prefix:
            require(type(trace_limit) is int and 0 < trace_limit <= 32 * 1024**2, 'Invalid private trace bound')
            # Bound the actual strace writer as well as its descendants. The
            # runtime owns projection/removal; no private trace is read here.
            def limit_trace_file():
                import resource
                _, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
                limit = min(trace_limit, hard) if hard != resource.RLIM_INFINITY else trace_limit
                resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
            spawn_options['preexec_fn'] = limit_trace_file
        process = subprocess.Popen(command, cwd=work, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True, **spawn_options)
        initialized = request(1, 'initialize', {'clientInfo': {'name': 'planweft-context-probe', 'version': '1'},
                                               'capabilities': {'experimentalApi': True}})
        require('/0.149.1 ' in initialized.get('userAgent', ''), 'Unexpected native CLI version')
        send({'method': 'initialized', 'params': {}})
        result = request(2, 'thread/start', {'model': model, 'cwd': str(work), 'approvalPolicy': 'never',
                    'sandbox': 'danger-full-access', 'ephemeral': True, 'experimentalRawEvents': True})
        info = result.get('thread'); fresh_thread(info, work); thread = info['id']
        require(result.get('model') == model and result.get('cwd') == str(work)
                and result.get('approvalPolicy') == 'never' and result.get('sandbox', {}).get('type') == 'dangerFullAccess',
                'Native effective settings differ')
        result = request(3, 'turn/start', {'threadId': thread, 'input': [{'type': 'text', 'text': prompt, 'text_elements': []}]})
        turn = result.get('turn', {}).get('id'); require(turn, 'Missing native turn identity')
        while not any(e.get('method') == 'turn/completed' for e in events):
            receive()
        # Close only our input, then consume all remaining output. A completed
        # summary is not an event barrier and can hide a late tool notification.
        process.stdin.close()
        while pump():
            pending.clear()
        process.wait(timeout=max(0.01, deadline - time.monotonic()))
        require(process.returncode == 0, 'Native app-server did not exit normally')
        require([e['id'] for e in events if 'id' in e] == [1, 2, 3], 'Additional native response/request')
        for event in events:
            if event.get('method') == 'thread/started': fresh_thread(event['params']['thread'], work)
        evidence = evaluator(events, thread, turn, source)
        evidence.update(normal_eof=True, native_exit_code=0, thread_snapshot=info)
    except KeyboardInterrupt:
        failure = 'KeyboardInterrupt: native probe interrupted'
    except Exception as error:
        failure = type(error).__name__ + ': ' + str(error)
    finally:
        try:
            if process is not None:
                # A normally exited leader and closed pipes do not establish
                # that its entire group is gone: a child may use DEVNULL. Stop
                # this invocation's group on success too; preserve leader exit.
                try: os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError: pass
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired: pass
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait(timeout=2)
            if errors is not None:
                errors.seek(0); data = errors.read(caps['stderr'] + 1)
                if len(data) > caps['stderr']:
                    failure = failure or 'Native stderr limit exceeded'; data = data[:caps['stderr']]
                # A byte limit may cut through a credential. Redacting only the
                # full credential would export its unrecognized prefix. Retain
                # complete lines only and explicitly fail the incomplete export.
                if data and not data.endswith(b'\n'):
                    cut = data.rfind(b'\n') + 1
                    evidence['stderr_tail_omitted_bytes'] = len(data) - cut
                    data = data[:cut]
                    failure = failure or 'Incomplete native stderr line omitted'
                stderr_text = safe(data.decode('utf-8', errors='replace'))
                (out / names[1]).write_text(stderr_text)
        except (Exception, KeyboardInterrupt) as error:
            failure = failure or type(error).__name__ + ': safe cleanup/export failed'
        finally:
            if process is not None:
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None:
                        try: stream.close()
                        except OSError: pass
            if errors is not None: errors.close()
            if journal is not None: journal.close()
            raw_error.unlink(missing_ok=True); private.rmdir()
    if failure:
        evidence.update(status='Failed', error=failure)
    evidence.update(thread_id=thread, turn_id=turn, trust_bypass=False,
                    resource_sha256=bindings, source_path=source, raw_stdout_bytes=raw_size,
                    raw_stderr_bytes=raw_stderr_size,
                    stdout_eof=not stdout_open and not buffer, stderr_eof=not stderr_open,
                    native_exit_code=process.returncode if process is not None else None,
                    native_pid=process.pid if process is not None else None,
                    event_count=len(events), private_stderr_removed=not private.exists(),
                    no_session_history_read=True)
    try:
        report = safe(json.dumps(evidence, ensure_ascii=False, indent=2)) + '\n'
        safe_evidence = json.loads(report)
        require(isinstance(safe_evidence, dict) and safe_evidence.get('status') in {'Passed', 'Failed'},
                'Sanitizer damaged observation JSON')
    except (Exception, KeyboardInterrupt):
        # Constant-only fallback cannot disclose exception text or native data.
        evidence = {'status': 'Failed', 'error': 'Safe evidence export failed',
                    'private_stderr_removed': not private.exists()}
        report = json.dumps(evidence) + '\n'
        safe_evidence = evidence
    (out / names[2]).write_text(report)
    stdout = json.dumps({'type': evidence_prefix + '_probe_projection', 'status': safe_evidence['status'],
                         'answer': safe_evidence.get('answer', '')}) + '\n'
    return subprocess.CompletedProcess(command, 0 if safe_evidence['status'] == 'Passed' else 1,
                                       stdout, stderr_text), safe_evidence
