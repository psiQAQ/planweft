"""Strict Codex 0.149.1 stopping observation over a complete app-server turn.

No tools, UI approval, history or project mutation is performed by this probe.
Counter/script-read attribution remains the runtime's independent gate trace.
Fixed protocol sources (not an inference from multiple assistant messages):
https://raw.githubusercontent.com/openai/codex/rust-v0.149.1/codex-rs/hooks/src/events/stop.rs
https://raw.githubusercontent.com/openai/codex/rust-v0.149.1/codex-rs/core/src/session/turn.rs
https://raw.githubusercontent.com/openai/codex/rust-v0.149.1/codex-rs/protocol/src/items.rs
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import re
from datetime import date
import xml.etree.ElementTree as ET

_spec = importlib.util.spec_from_file_location('_stop_context_transport', Path(__file__).with_name('codex_context_probe.py'))
transport = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(transport)
require = transport.require
CASES = {'stopping', 'gate-cap', 'gate-stall', 'gate-cap-disabled', 'gate-stall-disabled', 'gated-continuation'}
GATE_SYSCALLS = 'execve,clone,clone3,fork,vfork,open,openat,openat2,read,close,close_range,dup,dup2,dup3,fcntl,chdir,fchdir'


def _bootstrap(item, info, turn):
    """Recognize only this experiment's fixed native initial user context.

    Fixed sources:
    https://raw.githubusercontent.com/openai/codex/rust-v0.149.1/codex-rs/core/src/context/recommended_plugins_instructions.rs
    https://raw.githubusercontent.com/openai/codex/rust-v0.149.1/codex-rs/core/src/context/world_state/environment.rs
    https://raw.githubusercontent.com/openai/codex/rust-v0.149.1/codex-rs/core/src/context/environment_context.rs
    These render a user-role list (max 50), user-role cwd/shell/date/timezone,
    and filesystem profile. This is a restricted schema, not arbitrary user
    XML, a claim of plugin-list authenticity, or a model continuation.
    """
    transport.fresh_thread(info, Path(info.get('cwd', '')))
    require(item.get('internal_chat_message_metadata_passthrough', {}).get('turn_id') == turn,
            'Bootstrap lacks native turn binding')
    content = item.get('content')
    require(isinstance(content, list) and len(content) in {1, 2}
            and all(set(c) == {'type', 'text'} and c['type'] == 'input_text' for c in content),
            'Unsupported bootstrap contents')
    values = [c['text'] for c in content]
    require(all(isinstance(v, str) and len(v.encode()) <= 16384 and '<!' not in v and '<?' not in v
                for v in values), 'Unsafe bootstrap text')
    if len(values) == 2:
        intro = '<recommended_plugins>\nHere is a list of plugins that are available but not installed.\n\n'
        require(values[0].startswith(intro) and values[0].endswith('\n</recommended_plugins>'),
                'Unknown bootstrap recommendation frame')
        rows = values[0][len(intro):-len('\n</recommended_plugins>')].splitlines()
        require(1 <= len(rows) <= 50 and len(set(rows)) == len(rows)
                and all(re.fullmatch(r"- [A-Za-z0-9][A-Za-z0-9 .&()+:/_'’-]{0,127} \([a-z0-9][a-z0-9_-]{0,127}@[a-z0-9][a-z0-9_-]{0,63}\)", row)
                        for row in rows), 'Unknown bootstrap recommendation list')
    try: env = ET.fromstring(values[-1])
    except ET.ParseError: raise ValueError('Malformed bootstrap environment') from None
    require(env.tag == 'environment_context' and not env.attrib
            and [e.tag for e in env] == ['cwd', 'shell', 'current_date', 'timezone', 'filesystem']
            and all(not (e.tail or '').strip() for e in env) and not (env.text or '').strip(),
            'Unknown bootstrap environment schema')
    cwd, shell, day, zone, fs = env
    require(all(not e.attrib and len(e) == 0 for e in (cwd, shell, day, zone))
            and cwd.text == info['cwd'] and shell.text in {'bash', '/bin/bash'}
            and zone.text in {'UTC', 'Etc/UTC'}, 'Bootstrap environment differs from fixed experiment')
    require(isinstance(day.text, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', day.text), 'Invalid bootstrap date')
    date.fromisoformat(day.text)
    require(not fs.attrib and not (fs.text or '').strip() and [e.tag for e in fs] == ['workspace_roots', 'permission_profile'],
            'Unknown bootstrap filesystem schema')
    roots, profile = fs
    require(not roots.attrib and not (roots.text or '').strip() and len(roots) == 1
            and roots[0].tag == 'root' and not roots[0].attrib and len(roots[0]) == 0
            and roots[0].text == info['cwd'] and profile.attrib == {'type': 'disabled'}
            and len(profile) == 1 and profile[0].tag == 'file_system'
            and profile[0].attrib == {'type': 'unrestricted'} and len(profile[0]) == 0
            and all(not (e.tail or '').strip() for e in (roots, roots[0], profile, profile[0]))
            and not (profile.text or '').strip() and not (profile[0].text or '').strip(),
            'Bootstrap filesystem differs from fixed experiment')
    return ['recommended_plugins', 'environment_context'] if len(values) == 2 else ['environment_context']


def trace_prefix(private_dir, executable='/usr/bin/strace'):
    """Build the sole supported prefix, without creating files or directories."""
    return [executable, '-f', '--decode-pids=comm', '-s', '4096', '-e', 'trace=' + GATE_SYSCALLS,
            '-e', 'raw=read', '-o', str(Path(private_dir) / 'gate-private.strace'), '--']


def _validate_prefix(prefix):
    if not prefix:
        return ()
    require(isinstance(prefix, (list, tuple)) and len(prefix) == 12
            and all(isinstance(p, str) for p in prefix), 'Invalid trace prefix')
    require(prefix[0] in {'/usr/bin/strace', '/bin/strace'} and list(prefix[1:10]) ==
            ['-f', '--decode-pids=comm', '-s', '4096', '-e', 'trace=' + GATE_SYSCALLS,
             '-e', 'raw=read', '-o'] and prefix[-1] == '--', 'Unapproved trace command')
    path = Path(prefix[10]); parent = path.parent
    require(path.is_absolute() and path == path.resolve() and path.name == 'gate-private.strace'
            and parent.is_relative_to('/tmp') and parent != Path('/tmp') and parent.is_dir()
            and parent.stat().st_uid == os.getuid() and parent.stat().st_mode & 0o777 == 0o700
            and not path.exists() and not path.is_symlink(), 'Trace needs a new file in an owned private /tmp directory')
    return tuple(prefix)


def _fragment(item):
    require(item.get('role') == 'user' and len(item.get('content', [])) == 1, 'Invalid hook prompt raw role/content')
    value = transport.text_content(item)
    require('<!' not in value and '<?' not in value, 'Unsafe hook prompt XML')
    try:
        root = ET.fromstring(value)
    except ET.ParseError:
        raise ValueError('Malformed hook prompt XML') from None
    require(root.tag == 'hook_prompt' and set(root.attrib) == {'hook_run_id'} and len(root) == 0
            and root.attrib['hook_run_id'] and root.text, 'Unbound hook prompt XML')
    return {'hookRunId': root.attrib['hook_run_id'], 'text': root.text}


def assess(events, thread, turn, prompt, source, case):
    require(case in CASES, 'Unknown stopping scenario')
    disabled = case.endswith('-disabled'); continuation = case == 'gated-continuation'
    started = ended = None
    items = {}; done = {}; raw = {}; hooks = {}; completed = {}; responses = []; threads = []
    for index, event in enumerate(events):
        require(isinstance(event, dict), 'Nonobject native event')
        if 'id' in event:
            require('method' not in event and 'error' not in event, 'Native server request/error'); continue
        method = event.get('method'); p = event.get('params', {})
        require(isinstance(p, dict), 'Malformed event parameters')
        if method == 'thread/started':
            threads.append(p.get('thread', {})); continue
        require('threadId' not in p or p['threadId'] == thread, 'Foreign thread')
        require('turnId' not in p or p['turnId'] == turn, 'Foreign turn')
        if method in transport.PASSIVE:
            continue
        require(p.get('threadId') == thread, 'Missing thread binding')
        if method in {'turn/started', 'turn/completed'}:
            t = p.get('turn', {})
            require(t.get('id') == turn, 'Foreign turn boundary')
            if method == 'turn/started':
                require(started is None and ended is None and t.get('status') == 'inProgress', 'Invalid turn start')
                started = index
            else:
                require(started is not None and ended is None and t.get('status') == 'completed'
                        and t.get('error') is None, 'Invalid turn completion')
                ended = index
            continue
        require(started is not None and ended is None and p.get('turnId') == turn, 'Activity outside complete turn')
        if method in transport.DELTA:
            require(p.get('itemId') in items, 'Unbound item delta'); continue
        if method in {'item/started', 'item/completed'}:
            item = p.get('item', {}); ident = item.get('id'); kind = item.get('type')
            require(ident and kind in {'userMessage', 'agentMessage', 'reasoning', 'hookPrompt'}, 'Tool or unknown native item')
            require(kind != 'hookPrompt' or continuation, 'Unexpected hook continuation prompt')
            if method == 'item/started':
                require(ident not in items, 'Duplicate native item'); items[ident] = (index, item)
            else:
                require(ident in items and ident not in done and items[ident][1]['type'] == kind, 'Unbound item completion')
                done[ident] = (index, item)
        elif method == 'rawResponseItem/completed':
            item = p.get('item', {}); ident = item.get('id'); kind = item.get('type')
            require(ident and ident not in raw and kind in {'message', 'reasoning'}, 'Tool/duplicate/unknown raw item')
            metadata = item.get('internal_chat_message_metadata_passthrough') or {}
            require(isinstance(metadata, dict) and metadata.get('turn_id', turn) == turn, 'Foreign raw turn metadata')
            if kind == 'message':
                require(item.get('role') in {'user', 'developer', 'assistant'} and not item.get('recipient')
                        and not item.get('tool_calls'), 'Unsafe raw route')
                transport.text_content(item)
            raw[ident] = (index, item)
        elif method == 'rawResponse/completed':
            ident = p.get('responseId')
            require(isinstance(ident, str) and ident and ident not in [r[1] for r in responses], 'Duplicate/invalid response completion')
            responses.append((index, ident))
        elif method in {'hook/started', 'hook/completed'}:
            run = p.get('run', {}); ident = run.get('id'); name = run.get('eventName')
            require(ident and name in {'sessionStart', 'userPromptSubmit', 'stop'} and run.get('sourcePath') == source
                    and run.get('source') == 'plugin' and run.get('handlerType') == 'command'
                    and run.get('executionMode') == 'sync' and run.get('scope') ==
                    ('thread' if name == 'sessionStart' else 'turn'), 'Unbound/tool/unknown hook')
            if method == 'hook/started':
                require(ident not in hooks and run.get('status') == 'running' and run.get('startedAt') is not None, 'Invalid hook start')
                hooks[ident] = (index, run)
            else:
                require(ident in hooks and ident not in completed and run.get('completedAt') is not None
                        and all(run.get(k) == hooks[ident][1].get(k) for k in
                                ('id', 'eventName', 'sourcePath', 'source', 'handlerType', 'executionMode', 'scope', 'startedAt')),
                        'Incomplete/changed hook lifecycle')
                blocked = name == 'stop' and continuation and run.get('status') == 'blocked'
                require(blocked or run.get('status') == 'completed', 'Failed/stopped hook')
                entries = run.get('entries')
                allowed = {'warning', 'feedback'} if blocked else {'warning'} if name == 'stop' else {'context'}
                require(isinstance(entries, list) and all(isinstance(e, dict) and e.get('kind') in allowed
                        and isinstance(e.get('text'), str) and e['text'] for e in entries), 'Unknown hook output')
                require(not disabled or entries == [], 'Disabled hook produced output')
                if blocked:
                    require(sum(e['kind'] == 'feedback' for e in entries) == 1, 'Block lacks unique feedback')
                completed[ident] = (index, run)
        else:
            raise ValueError('Unknown native event')
    require(len(threads) == 1 and threads[0].get('id') == thread and started is not None and ended is not None, 'Incomplete thread/turn')
    require(items.keys() == done.keys() and hooks.keys() == completed.keys(), 'Unfinished item/hook')
    users = [(idx, i) for idx, i in done.values() if i['type'] == 'userMessage']
    require(len(users) == 1 and users[0][1].get('content') == [{'type': 'text', 'text': prompt, 'text_elements': []}], 'Additional or changed user input')
    messages = [(idx, i, transport.text_content(i)) for idx, i in raw.values() if i['type'] == 'message']
    original = [(idx, i) for idx, i, text in messages if i['role'] == 'user' and text == prompt]
    require(len(original) == 1, 'Original raw user prompt missing/duplicated')
    finals = sorted((idx, i) for idx, i in done.values() if i['type'] == 'agentMessage')
    wanted_count = 2 if continuation else 1
    require(len(finals) == len(responses) == wanted_count, 'Wrong number of model responses')
    raw_answers = [(idx, i) for idx, i, text in messages if i['role'] == 'assistant']
    require(len(raw_answers) == wanted_count, 'Extra/missing raw assistant output')
    for pos, (idx, item) in enumerate(finals):
        require(item.get('phase') == 'final_answer' and item.get('text') == 'STOP_PROBE', 'Unexpected stop answer')
        raw_idx, raw_item = raw.get(item['id'], (None, {}))
        item_start = items[item['id']][0]
        # Fixed 0.149.1 independently emits high-level ItemCompleted and raw
        # ResponseItem events. The real stop trace delivers high before raw;
        # bind both to this item's response interval, not an invented order.
        require(raw_item.get('role') == 'assistant' and raw_item.get('phase') == 'final_answer'
                and transport.text_content(raw_item) == 'STOP_PROBE'
                and item_start < raw_idx < responses[pos][0]
                and item_start < idx < responses[pos][0], 'Unbound raw answer')
        require(pos == 0 or responses[pos-1][0] < item_start, 'Overlapping/replayed response')
    stops = sorted((idx, r) for idx, r in completed.values() if r['eventName'] == 'stop')
    require(len(stops) == wanted_count, 'Missing/duplicate Stop executions')
    for pos, (idx, run) in enumerate(stops):
        next_boundary = items[finals[pos+1][1]['id']][0] if pos+1 < len(finals) else ended
        require(responses[pos][0] < hooks[run['id']][0] < idx < next_boundary, 'Stop is outside its response boundary')
    for name in ['sessionStart', 'userPromptSubmit']:
        runs = [(idx, r) for idx, r in completed.values() if r['eventName'] == name]
        require(len(runs) <= 1 and (disabled or len(runs) == 1), 'Missing/duplicate startup hook')
        require(all(idx < items[finals[0][1]['id']][0] for idx, _ in runs), 'Startup reset after sampling')
    injected = []; used = set()
    contexts = [(idx, run, entry['text']) for idx, run in sorted(completed.values())
                for entry in run['entries'] if entry['kind'] == 'context']
    for pos, (idx, run, text) in enumerate(contexts):
        boundary = contexts[pos+1][0] if pos+1 < len(contexts) else items[finals[0][1]['id']][0]
        matches = [(n, i) for n, i, value in messages if i['role'] == 'developer' and value == text
                   and idx < n < boundary]
        require(len(matches) == 1 and matches[0][1]['id'] not in used,
                'Hook context missing distinct ordered native developer delivery')
        n, item = matches[0]; used.add(item['id'])
        injected.append({'hook_id':run['id'], 'developer_item_id':item['id'], 'event':n})
    followups = [(idx, item) for idx, item in done.values() if item['type'] == 'hookPrompt']
    extra_users = [(idx, i) for idx, i, text in messages if i['role'] == 'user' and text != prompt]
    bootstrap = []
    startup_boundary = min([idx for idx, _ in hooks.values()] + [original[0][0]])
    sampling_boundary = min(idx for idx, i in items.values() if i['type'] in {'agentMessage', 'reasoning'})
    for idx, item in extra_users:
        if idx < original[0][0]:
            require(not bootstrap and idx < startup_boundary and idx < sampling_boundary,
                    'Duplicate/late bootstrap user context')
            tags = _bootstrap(item, threads[0], turn)
            bootstrap.append({'item_id':item['id'], 'event':idx, 'tags':tags,
                              'content_sha256':hashlib.sha256(transport.text_content(item).encode()).hexdigest()})
    extra_users = [(idx, item) for idx, item in extra_users if not any(b['item_id'] == item['id'] for b in bootstrap)]
    chain = None
    if continuation:
        first, last = stops
        require(first[1]['status'] == 'blocked' and last[1]['status'] == 'completed', 'No block then normal Stop')
        feedback = next(e['text'] for e in first[1]['entries'] if e['kind'] == 'feedback')
        require(len(followups) == len(extra_users) == 1, 'Missing/extra native feedback prompt')
        high_idx, high = followups[0]; raw_idx, raw_item = extra_users[0]
        expected = {'hookRunId':first[1]['id'], 'text':feedback}
        require(high.get('fragments') == [expected] and high['id'] == raw_item['id'] and _fragment(raw_item) == expected,
                'Feedback prompt does not bind native blocked hook')
        boundary = items[finals[1][1]['id']][0]
        require(first[0] < items[high['id']][0] < high_idx < boundary
                and first[0] < raw_idx < boundary, 'Feedback not delivered before next response')
        chain = {'blocked_hook_id':first[1]['id'], 'feedback_item_id':high['id'], 'feedback_event':raw_idx,
                 'feedback_sha256':hashlib.sha256(feedback.encode()).hexdigest(), 'response_ids':[r[1] for r in responses]}
    else:
        require(not followups and not extra_users and all(r['status'] == 'completed' for _, r in stops), 'Unexpected continuation')
    return {'status':'Passed', 'case':case, 'answer':'STOP_PROBE', 'assistant_responses':wanted_count,
            'no_model_tool_calls':True, 'thread_id':thread, 'turn_id':turn, 'actual_followup':chain is not None,
            'continuation_chain':chain, 'stop_runs':[{'hook_id':r['id'], 'status':r['status'], 'event':idx} for idx,r in stops],
            'startup_injections':injected, 'native_bootstrap_context':bootstrap,
            'turn_started_event':started, 'turn_completed_event':ended,
            'scope':'Native no-model-tools and Stop/feedback/response lifecycle only; counter reads, project preservation, trust acquisition and dedup require separate evidence.'}


def run_probe(model, work, out, package, native_root, timeout, sanitize, *, prompt, case,
              command_prefix=(), limits=None, trace_limit=32 * 1024**2):
    require(case in CASES, 'Unknown stopping scenario')
    require((os.getenv('PLANNING_DISABLED') == '1') == case.endswith('-disabled'), 'Planning-disabled environment differs from scenario')
    prefix = _validate_prefix(command_prefix)
    require(type(trace_limit) is int and 0 < trace_limit <= 32 * 1024**2, 'Invalid trace limit')
    return transport._collect_native_turn(model, work, out, package, native_root, timeout, sanitize, prompt=prompt,
        evaluator=lambda events, thread, turn, source: assess(events, thread, turn, prompt, source, case),
        evidence_prefix='stop', command_prefix=prefix, trace_limit=trace_limit, limits=limits)
