import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('codex_context_probe', Path(__file__).with_name('codex_context_probe.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
TOKEN = 'PW_RECOVERY_' + 'a' * 32
OLD = 'PW_RECOVERY_' + 'b' * 32
PROMPT = 'Report only the injected recovery token, or NO_CONTEXT. Use no tools.'


def fixture(work, native, token=TOKEN):
    thread = {'id': 'thread-1', 'sessionId': 'thread-1', 'ephemeral': True,
              'forkedFromId': None, 'parentThreadId': None, 'turns': [],
              'cwd': str(work), 'cliVersion': '0.149.1'}
    def event(method, **params):
        return {'method': method, 'params': {'threadId': 'thread-1', 'turnId': 'turn-1', **params}}
    def raw(ident, role, text, phase=None):
        item = {'type': 'message', 'id': ident, 'role': role,
                'content': [{'type': 'output_text' if role == 'assistant' else 'input_text', 'text': text}],
                'internal_chat_message_metadata_passthrough': {'turn_id': 'turn-1'}}
        if phase: item['phase'] = phase
        return event('rawResponseItem/completed', item=item)
    events = [
        {'method': 'thread/started', 'params': {'thread': thread}},
        event('turn/started', turn={'id': 'turn-1', 'status': 'inProgress'}),
        event('item/started', item={'type': 'userMessage', 'id': 'u'}),
        event('item/completed', item={'type': 'userMessage', 'id': 'u',
              'content': [{'type': 'text', 'text': PROMPT, 'text_elements': []}]}),
        raw('raw-u', 'user', PROMPT),
    ]
    if token:
        run = {'id': 'startup', 'eventName': 'sessionStart', 'sourcePath': str(native / 'hooks/codex-hooks.json'),
               'source': 'plugin', 'handlerType': 'command', 'executionMode': 'sync', 'scope': 'thread',
               'startedAt': 1, 'status': 'running'}
        context = '[planweft] ACTIVE PLAN\n' + token
        events += [event('hook/started', run=run), event('hook/completed', run={**run,
                   'status': 'completed', 'completedAt': 2, 'entries': [{'kind': 'context', 'text': context}]}),
                   raw('raw-d', 'developer', context)]
    answer = token or 'NO_CONTEXT'
    events += [event('item/started', item={'type': 'agentMessage', 'id': 'a', 'phase': 'final_answer'}),
               raw('a', 'assistant', answer, 'final_answer'),
               event('item/completed', item={'type': 'agentMessage', 'id': 'a', 'text': answer, 'phase': 'final_answer'}),
               event('rawResponse/completed', responseId='response-1'),
               event('turn/completed', turn={'id': 'turn-1', 'status': 'completed', 'error': None})]
    return thread, events


# The fixture process speaks only synthetic protocol. Tests never execute Codex,
# read credentials, or use Docker/network. Parent stderr intentionally simulates
# a sensitive header so all exit paths must redact and delete its private copy.
FAKE = r'''
import json,sys,time,os,signal,subprocess
cfg=json.loads(sys.argv[1]); mode=cfg['mode']
def emit(x):
 print(json.dumps(x),flush=True)
for line in sys.stdin:
 x=json.loads(line)
 if x.get('method')=='initialize':
  emit({'id':1,'result':{'userAgent':'test/0.149.1 (Linux)'}})
 elif x.get('method')=='thread/start':
  p=x['params'];emit({'id':2,'result':{'thread':cfg['thread'],'cwd':p['cwd'],'model':p['model'],
    'approvalPolicy':'never','sandbox':{'type':'dangerFullAccess'}}})
 elif x.get('method')=='turn/start':
  emit({'id':3,'result':{'turn':{'id':'turn-1'}}})
  print('header: SECRET',file=sys.stderr,flush=True)
  if mode=='timeout':
   signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)
  if mode=='child':
   child=subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)'])
   open(cfg['child_pid'],'w').write(str(child.pid));time.sleep(30)
  if mode=='devnull-child':
   child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
   open(cfg['child_pid'],'w').write(str(child.pid))
  if mode=='stdout':print('x'*cfg['limit'],flush=True);time.sleep(30)
  if mode=='stderr':print('SECRET'+'x'*cfg['limit'],file=sys.stderr,flush=True);time.sleep(30)
  if mode=='early':sys.exit(0)
  for event in cfg['events']:emit(event)
  if mode=='truncated':sys.stdout.write('{');sys.stdout.flush()
  if mode=='exit':sys.exit(2)
if mode=='late':emit({'method':'rawResponseItem/completed','params':{'threadId':'thread-1','turnId':'turn-1','item':{'type':'custom_tool_call','id':'late','name':'exec'}}})
'''


def process_finished(status):
    # A dying process can disappear after exists(), or while procfs reads it.
    try:
        return 'State:\tZ' in status.read_text()
    except (FileNotFoundError, ProcessLookupError):
        return True


class ContextProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='pw-context-test-')
        self.base = Path(self.tmp.name); self.work = self.base / 'work'; self.work.mkdir()
        self.native = self.base / 'native'; self.package = self.base / 'package'
        for root in (self.native, self.package / 'dist/codex/planweft'):
            for name in ('hooks/codex-hooks.json', '.codex/hooks/adapter.py', 'skills/project-docs/scripts/resolve.sh'):
                path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('fixture\n')
        self.count = 0

    def tearDown(self):
        self.tmp.cleanup()

    def test_high_before_raw_completion_order_is_already_supported(self):
        # Fixed Codex 0.149.1 real RC15 stopping stream emits high completion
        # before raw completion; context never required the reverse order.
        _, events = fixture(self.work, self.native)
        raw = next(e for e in events if e['method'] == 'rawResponseItem/completed'
                   and e['params']['item']['id'] == 'a')
        high = next(e for e in events if e['method'] == 'item/completed'
                    and e['params']['item']['id'] == 'a')
        events.remove(raw); events.insert(events.index(high) + 1, raw)
        self.assertEqual(self.check(events)['status'], 'Passed')

    def check(self, events, token=TOKEN):
        return probe.assess(events, 'thread-1', 'turn-1', PROMPT,
                            str(self.native / 'hooks/codex-hooks.json'), token, OLD)

    def run_fake(self, mode='normal', token=TOKEN, mutate=None, limits=None, sanitizer=None):
        self.count += 1; out = self.base / ('out' + str(self.count))
        thread, events = fixture(self.work, self.native, token)
        if mutate: mutate(events)
        cfg = {'mode': mode, 'thread': thread, 'events': events, 'limit': 8192,
               'child_pid': str(self.base / 'child.pid')}
        native_popen = subprocess.Popen; native_temp = tempfile.mkdtemp
        private = []; processes = []; commands = []
        def spawn(command, **kwargs):
            commands.append(command)
            process = native_popen([sys.executable, '-c', FAKE, json.dumps(cfg)], **kwargs)
            processes.append(process); return process
        def private_dir(**kwargs):
            path = native_temp(**kwargs); private.append(Path(path)); return path
        with mock.patch.object(probe.subprocess, 'Popen', side_effect=spawn), \
             mock.patch.object(probe.tempfile, 'mkdtemp', side_effect=private_dir):
            result, observation = probe.run_probe('synthetic-model', self.work, out, self.package,
                self.native, 0.4 if mode in {'timeout', 'child'} else 3,
                sanitizer or (lambda s: s.replace('SECRET', '[REDACTED]')), prompt=PROMPT,
                expected_token=token, forbidden_token=OLD, limits=limits)
        self.assertTrue(all(not p.exists() for p in private))
        self.assertTrue(all(p.poll() is not None for p in processes))
        self.assertTrue(all(TOKEN not in str(c) for c in commands))
        for path in out.iterdir(): self.assertNotIn('SECRET', path.read_text())
        return result, observation, out

    def test_complete_hook_raw_final_binding_and_control(self):
        for token in (TOKEN, None):
            with self.subTest(token=token):
                result, observed, out = self.run_fake(token=token)
                self.assertEqual(result.returncode, 0, observed)
                self.assertTrue(observed['normal_eof'])
                self.assertTrue(observed['no_model_tool_calls'])
                self.assertEqual(observed['answer'], token or 'NO_CONTEXT')
                journal = list(map(json.loads, (out / 'context-protocol.jsonl').read_text().splitlines()))
                sent = [x['message'] for x in journal if x['direction'] == 'sent']
                self.assertEqual([x['method'] for x in sent], ['initialize', 'initialized', 'thread/start', 'turn/start'])
                self.assertNotIn(TOKEN, json.dumps(sent))
                self.assertIn('[REDACTED]', result.stderr)
                self.assertEqual(list(self.work.iterdir()), [])

    def test_raw_tools_and_unknown_types_fail_even_when_summary_is_clean(self):
        _, original = fixture(self.work, self.native)
        for kind in ['custom_tool_call', 'custom_tool_call_output', 'function_call', 'function_call_output',
                     'local_shell_call', 'web_search_call', 'tool_search_call', 'unknown']:
            with self.subTest(kind=kind):
                events = copy.deepcopy(original)
                events.insert(5, {'method': 'rawResponseItem/completed', 'params': {'threadId': 'thread-1',
                    'turnId': 'turn-1', 'item': {'type': kind, 'id': 'hidden', 'name': 'exec',
                    'input': 'text(await tools.exec_command({"cmd":"cat task_plan.md"}));'}}})
                with self.assertRaisesRegex(ValueError, 'raw item'): self.check(events)

    def test_same_text_startup_and_submit_have_distinct_ordered_delivery(self):
        _, events = fixture(self.work, self.native)
        submit = copy.deepcopy(events[5:8])
        for e in submit[:2]:
            e['params']['run'].update(id='submit', eventName='userPromptSubmit', scope='turn', startedAt=3)
        submit[1]['params']['run']['completedAt'] = 4
        submit[2]['params']['item']['id'] = 'raw-d-submit'
        events[8:8] = submit
        result = self.check(events)
        self.assertEqual([i['event_name'] for i in result['injections']], ['sessionStart', 'userPromptSubmit'])
        self.assertEqual(len({i['developer_item_id'] for i in result['injections']}), 2)
        self.assertEqual(len({i['context_sha256'] for i in result['injections']}), 1)
        mutations = {
            'one developer only': lambda e: e.pop(10),
            'same developer id': lambda e: e[10]['params']['item'].update(id='raw-d'),
            'additional token': lambda e: e.insert(11, copy.deepcopy(e[10])),
            'developer before its hook': lambda e: e.insert(8, e.pop(10)),
            'startup developer after submit completes': lambda e: e.insert(9, e.pop(7)),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                broken = copy.deepcopy(events); mutate(broken)
                with self.assertRaises(ValueError): self.check(broken)
        result, observed, _ = self.run_fake(mutate=lambda e: e.__setitem__(slice(8, 8), copy.deepcopy(submit)))
        self.assertEqual(result.returncode, 0, observed)
        self.assertEqual(len(observed['injections']), 2)

    def test_bound_stop_warning_is_ui_only(self):
        _, events = fixture(self.work, self.native)
        warning = copy.deepcopy(events[5:7])
        for e in warning:
            e['params']['run'].update(id='stop', eventName='stop', scope='turn', startedAt=5)
        warning[1]['params']['run'].update(completedAt=6,
            entries=[{'kind': 'warning', 'text': 'Task in progress'}])
        events[-1:-1] = warning
        observed = self.check(events)
        self.assertEqual(len(observed['injections']), 1)
        self.assertEqual(observed['stop_warnings'][0]['text'], 'Task in progress')
        for key, value in [('kind', 'context'), ('kind', 'error'), ('kind', 'stop'),
                           ('text', 'Task in progress ' + TOKEN)]:
            with self.subTest(key=key, value=value):
                broken = copy.deepcopy(events)
                broken[-2]['params']['run']['entries'][0][key] = value
                with self.assertRaises(ValueError): self.check(broken)
        broken = copy.deepcopy(events); broken[-2]['params']['run']['sourcePath'] = '/foreign'
        with self.assertRaises(ValueError): self.check(broken)

    def test_protocol_gaps_and_false_context(self):
        _, original = fixture(self.work, self.native)
        mutations = {
            'missing raw final': lambda e: e.pop(9),
            'unknown notification': lambda e: e.insert(5, {'method': 'unknown', 'params': {'threadId': 'thread-1', 'turnId': 'turn-1'}}),
            'foreign turn': lambda e: e[4]['params'].update(turnId='foreign'),
            'metadata mismatch': lambda e: e[4]['params']['item']['internal_chat_message_metadata_passthrough'].update(turn_id='wrong'),
            'hook source': lambda e: e[6]['params']['run'].update(sourcePath='/foreign'),
            'hook unfinished': lambda e: e.pop(6),
            'no actual delivery': lambda e: e[7]['params']['item']['content'][0].update(text='no context'),
            'tool message route': lambda e: e[7]['params']['item'].update(recipient='tools.exec'),
            'old token': lambda e: e[7]['params']['item']['content'][0].update(text=OLD),
            'additional token source': lambda e: e.insert(5, copy.deepcopy(e[7])),
            'summary only': lambda e: e.pop(-2),
            'failed turn': lambda e: e[-1]['params']['turn'].update(status='failed'),
            'duplicate completed': lambda e: e.append(copy.deepcopy(e[-1])),
            'missing item start': lambda e: e.pop(8),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                events = copy.deepcopy(original); mutate(events)
                with self.assertRaises(ValueError): self.check(events)

    def test_complete_drain_detects_late_tool_truncation_and_exit(self):
        for mode in ['late', 'truncated', 'early', 'exit']:
            with self.subTest(mode=mode):
                result, observed, _ = self.run_fake(mode)
                self.assertEqual(result.returncode, 1, observed)
                self.assertEqual(observed['status'], 'Failed')

    def test_limits_and_redaction_failure(self):
        for mode, limits in [('stdout', {'stdout': 4096}), ('stderr', {'stderr': 4096}),
                             ('normal', {'events': 5}), ('normal', {'line': 30}),
                             ('normal', {'export': 1024})]:
            with self.subTest(mode=mode, limits=limits):
                result, observed, _ = self.run_fake(mode, limits=limits)
                self.assertEqual(result.returncode, 1, observed)
        def fail_on_native(s):
            if 'SECRET' in s: raise RuntimeError('SECRET')
            return s
        result, observed, _ = self.run_fake(sanitizer=fail_on_native)
        self.assertEqual(result.returncode, 1, observed)
        result, observed, out = self.run_fake(limits={'stderr': 11})
        self.assertEqual(result.returncode, 1)
        self.assertEqual(observed['stderr_tail_omitted_bytes'], 11)
        self.assertNotIn('header: SEC', '\n'.join(p.read_text() for p in out.iterdir()))
        self.assertEqual((out / 'context-native.stderr').read_text(), '')

    def test_procfs_exit_race_is_exit_but_other_errors_are_not(self):
        status=mock.Mock()
        for error in (FileNotFoundError(),ProcessLookupError()):
            status.read_text.side_effect=error
            self.assertTrue(process_finished(status))
        status.read_text.side_effect=PermissionError()
        with self.assertRaises(PermissionError):process_finished(status)
        status.read_text.side_effect=None
        status.read_text.return_value='State:\tS (sleeping)'
        self.assertFalse(process_finished(status))

    def test_timeout_kills_only_owned_process_group(self):
        other = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'])
        try:
            for mode in ['timeout', 'child']:
                with self.subTest(mode=mode):
                    result, observed, _ = self.run_fake(mode)
                    self.assertEqual(result.returncode, 1, observed)
                    self.assertIsNone(other.poll())
            pid = int((self.base / 'child.pid').read_text())
            status = Path('/proc') / str(pid) / 'status'
            for _ in range(20):
                if process_finished(status): break
                time.sleep(0.05)
            self.assertTrue(process_finished(status))
            result, observed, _ = self.run_fake('devnull-child')
            self.assertEqual(result.returncode, 0, observed)
            self.assertEqual(observed['native_exit_code'], 0)
            self.assertTrue(observed['normal_eof'])
            self.assertIsNone(other.poll())
            pid = int((self.base / 'child.pid').read_text())
            status = Path('/proc') / str(pid) / 'status'
            for _ in range(20):
                if process_finished(status): break
                time.sleep(0.05)
            self.assertTrue(process_finished(status))
        finally:
            other.terminate(); other.wait(timeout=3)

    def test_keyboard_interrupt_retains_failed_evidence_and_cleans_private_data(self):
        def interrupt(s):
            if '"direction": "received"' in s:
                raise KeyboardInterrupt('SECRET interruption details')
            return s.replace('SECRET', '[REDACTED]')
        result, observed, out = self.run_fake(sanitizer=interrupt)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(observed['status'], 'Failed')
        self.assertEqual(observed['error'], 'KeyboardInterrupt: native probe interrupted')
        self.assertTrue(observed['private_stderr_removed'])
        self.assertTrue((out / 'context-observation.json').is_file())
        self.assertNotIn('interruption details', (out / 'context-observation.json').read_text())

    def test_invalid_arguments_and_resource_mismatch_have_no_side_effects(self):
        out = self.base / 'invalid-output'
        cases = [{'timeout': 601}, {'timeout': float('nan')}, {'prompt': PROMPT + TOKEN},
                 {'expected_token': 'bad'}, {'limits': {'stdout': 0}}, {'out': self.work / 'output'},
                 {'sanitize': None}, {'sanitize': lambda s: ''}]
        for change in cases:
            with self.subTest(change=change), mock.patch.object(probe.subprocess, 'Popen') as spawn:
                args = dict(model='fake', work=self.work, out=out, package=self.package,
                            native_root=self.native, timeout=1, sanitize=lambda s: s,
                            prompt=PROMPT, expected_token=TOKEN)
                args.update(change)
                with self.assertRaises(ValueError): probe.run_probe(**args)
                spawn.assert_not_called(); self.assertFalse(out.exists())
        alias = self.base / 'project-link'; alias.symlink_to(self.work, target_is_directory=True)
        with mock.patch.object(probe.subprocess, 'Popen') as spawn:
            with self.assertRaisesRegex(ValueError, 'separate'):
                probe.run_probe('fake', self.work, alias / 'new-output', self.package, self.native, 1,
                                lambda s: s, prompt=PROMPT, expected_token=TOKEN)
            spawn.assert_not_called(); self.assertFalse((self.work / 'new-output').exists())
        (self.native / '.codex/hooks/adapter.py').write_text('different')
        with mock.patch.object(probe.subprocess, 'Popen') as spawn:
            with self.assertRaisesRegex(ValueError, 'differs'):
                probe.run_probe('fake', self.work, out, self.package, self.native, 1,
                                lambda s: s, prompt=PROMPT, expected_token=TOKEN)
            spawn.assert_not_called(); self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main()
