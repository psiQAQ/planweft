import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import claude_hook_trace as trace


ROOT = '/native/planweft'
SOURCES = {rel: ('synthetic ' + rel).encode() for rel in trace.REQUIRED}
DIGESTS = {rel: hashlib.sha256(data).hexdigest() for rel, data in SOURCES.items()}
BINDINGS = {'expected_host_executable': '/usr/bin/claude',
            'allowed_interpreters': {'shell': ['/bin/sh'], 'python': ['/usr/bin/python3']}}


class Fixture:
    def __init__(self):
        self.rows = ['100 execve("/usr/bin/claude", ["claude"], 0xeeee) = 0']
        self.pid = 200

    def add(self, event='post-tool-use', size=0, *, transport='pipe', child=False, eof=True, exit_code=0):
        pid = self.pid; self.pid += 10
        if transport == 'pipe':
            self.rows.append('100 pipe2([3, 4], O_CLOEXEC) = 0')
        else:
            self.rows.append('100 socketpair(AF_UNIX, SOCK_STREAM|SOCK_CLOEXEC, 0, [3, 4]) = 0')
        self.rows += [f'100 clone(child_stack=NULL, flags=SIGCHLD) = {pid}',
                      '100 close(4) = 0', f'{pid} close(3) = 0', f'{pid} dup2(4, 1) = 1', f'{pid} close(4) = 0',
                      f'{pid} execve("/bin/sh", ["sh", "{ROOT}/hooks/claude-hook.sh", "{event}"], 0xeeee) = 0',
                      f'{pid} openat(AT_FDCWD, "{ROOT}/hooks/claude-hook.sh", O_RDONLY) = 3',
                      f'{pid} read(0x3, 0xabcd, 0x1000) = 0x80', f'{pid} close(3) = 0']
        writer = pid
        if child:
            writer = pid + 1
            self.rows += [f'{pid} clone(child_stack=NULL, flags=SIGCHLD) = {writer}',
                          f'{writer} execve("/usr/bin/python3", ["python3", "-I", "-B", "{ROOT}/scripts/inject-plan.py", "--claude-event={event}"], 0xeeee) = 0',
                          f'{writer} openat(AT_FDCWD, "{ROOT}/scripts/inject-plan.py", O_RDONLY) = 3',
                          f'{writer} read(0x3, 0xabcd, 0x1000) = 0x100', f'{writer} close(3) = 0']
        if size:
            self.rows += [f'{writer} write(0x1, 0xabcd, {hex(size)}) = {hex(size)}',
                          f'100 read(0x3, 0xabcd, 0x1000) = {hex(size)}']
        if child:
            self.rows.append(f'{writer} +++ exited with 0 +++')
        self.rows.append(f'{pid} +++ exited with {exit_code} +++')
        if eof:
            self.rows.append('100 read(0x3, 0xabcd, 0x1000) = 0')
        self.rows.append('100 close(3) = 0')
        return pid

    def text(self):
        return '\n'.join(self.rows + ['100 +++ exited with 0 +++']) + '\n'


class ClaudeHookTraceTests(unittest.TestCase):
    def analyze(self, value, **kwargs):
        value = value.text() if isinstance(value, Fixture) else value
        return trace.analyze_trace(value, ROOT, DIGESTS,
                                   read_script=lambda path: SOURCES[str(Path(path).relative_to(ROOT))], **BINDINGS, **kwargs)

    def test_serial_four_hooks_real_eof_and_inherited_python(self):
        for transport in ['pipe', 'unix']:
            with self.subTest(transport=transport):
                fixture = Fixture()
                for size in [200, 0, 200, 0]:
                    fixture.add(size=size, transport=transport, child=True)
                result = self.analyze(fixture)
                self.assertTrue(result['observation_complete'], result['errors'])
                self.assertEqual([200, 0, 200, 0], [h['stdout_written_bytes'] for h in result['hooks']])
                self.assertEqual([False, True, False, True], [h['stdout_empty'] for h in result['hooks']])
                self.assertTrue(all(h['normal_exit'] and h['stdout_eof'] and h['fast_path_reads'] for h in result['hooks']))
                self.assertNotIn('Passed', json.dumps(result))

    def test_unix_duplex_input_not_counted_as_stdout(self):
        fixture = Fixture(); pid = fixture.add(size=5, transport='unix')
        pos = fixture.rows.index(f'{pid} execve("/bin/sh", ["sh", "{ROOT}/hooks/claude-hook.sh", "post-tool-use"], 0xeeee) = 0')
        fixture.rows[pos:pos] = ['100 write(0x3, 0xaaaa, 0x8) = 0x8', f'{pid} read(0x1, 0xaaaa, 0x8) = 0x8']
        result = self.analyze(fixture)
        self.assertTrue(result['observation_complete'], result['errors'])
        self.assertEqual(5, result['hooks'][0]['stdout_read_bytes'])

    def test_empty_needs_eof_and_normal_exit(self):
        for eof, exit_code in [(False, 0), (True, 2)]:
            with self.subTest(eof=eof, exit_code=exit_code):
                fixture = Fixture(); fixture.add(eof=eof, exit_code=exit_code)
                self.assertFalse(self.analyze(fixture)['observation_complete'])
        fixture = Fixture(); pid = fixture.add()
        for text in [fixture.text().replace('100 read(0x3, 0xabcd, 0x1000) = 0', '100 read(0x3, 0xabcd, 0x1000) = -1 EAGAIN (Resource temporarily unavailable)'),
                     fixture.text().replace(f'{pid} +++ exited with 0 +++', f'{pid} +++ killed by SIGKILL +++'),
                     fixture.text().replace(f'{pid} +++ exited with 0 +++\n', '')]:
            self.assertFalse(self.analyze(text)['observation_complete'])

    def test_zero_length_read_and_raw_readv_zero_are_not_eof(self):
        fixture = Fixture(); fixture.add()
        for replacement in ['100 read(0x3, 0xabcd, 0x0) = 0',
                            '100 readv(0x3, 0xabcd, 0x2) = 0',
                            '100 recvfrom(0x3, 0xabcd, 0x0, 0x0, 0x0, 0x0) = 0']:
            with self.subTest(replacement=replacement):
                result = self.analyze(fixture.text().replace('100 read(0x3, 0xabcd, 0x1000) = 0', replacement))
                self.assertFalse(result['observation_complete'])
                self.assertFalse(result['hooks'][0]['stdout_eof'])

    def test_unix_recv_flags_and_native_thread_receiver(self):
        fixture = Fixture(); fixture.add(size=8, transport='unix')
        for flags, complete in [(0, True), (0x40, True), (2, False), (0x20, False)]:
            with self.subTest(flags=flags):
                text = fixture.text().replace('100 read(0x3, 0xabcd, 0x1000)',
                                              f'100 recvfrom(0x3, 0xabcd, 0x1000, {hex(flags)}, 0x0, 0x0)')
                result = self.analyze(text)
                self.assertEqual(complete, result['observation_complete'], result['errors'])
        fixture.rows.insert(1, '100 clone(child_stack=NULL, flags=CLONE_VM|CLONE_FILES|CLONE_FS|CLONE_SIGHAND|CLONE_THREAD) = 101')
        fixture.rows.append('101 +++ exited with 0 +++')
        result = self.analyze(fixture.text().replace('100 read(', '101 read('))
        self.assertTrue(result['observation_complete'], result['errors'])
        self.assertTrue(all(row['host'] and row['pid'] == 101 for row in result['hooks'][0]['stdout_reads']))

    def test_descendant_self_read_is_not_host_consumption(self):
        fixture = Fixture(); pid = fixture.add(size=8)
        text = fixture.text().replace('pipe2([3, 4], O_CLOEXEC)', 'pipe2([3, 4], 0)')
        text = text.replace(f'{pid} close(3) = 0\n', '', 1)
        text = text.replace(f'{pid} openat(AT_FDCWD, "{ROOT}/hooks/claude-hook.sh", O_RDONLY) = 3',
                            f'{pid} openat(AT_FDCWD, "{ROOT}/hooks/claude-hook.sh", O_RDONLY) = 5')
        text = text.replace(f'{pid} read(0x3, 0xabcd, 0x1000) = 0x80', f'{pid} read(0x5, 0xabcd, 0x1000) = 0x80')
        text = text.replace(f'{pid} close(3) = 0', f'{pid} close(5) = 0')
        text = text.replace('100 read(0x3, 0xabcd, 0x1000) = 0x8', f'{pid} read(0x3, 0xabcd, 0x1000) = 0x8')
        result = self.analyze(text)
        self.assertFalse(result['observation_complete'])
        self.assertEqual(0, result['hooks'][0]['stdout_read_bytes'])
        self.assertEqual(8, result['hooks'][0]['nonhost_read_bytes'])

    def test_truncated_and_unfinished_fail_closed(self):
        fixture = Fixture(); fixture.add(size=4)
        for text in [fixture.text().rsplit('100 +++', 1)[0], fixture.text() + '100 read(0x3, 0xaaaa, 0x1000 <unfinished ...>\n',
                     fixture.text().replace('["sh",', '["sh", ...,'), fixture.text() + 'not a trace line\n']:
            self.assertFalse(self.analyze(text)['observation_complete'])

    def test_identity_requires_exact_argv_script_and_actual_read(self):
        fixture = Fixture(); fixture.add()
        for text in [fixture.text().replace(ROOT + '/hooks/claude-hook.sh', '/foreign/claude-hook.sh'),
                     fixture.text().replace('"post-tool-use"],', '"post-tool-use", "extra"],'),
                     fixture.text().replace('"/bin/sh"', '"/usr/bin/cat"'),
                     fixture.text().replace('read(0x3, 0xabcd, 0x1000) = 0x80', 'read(0x3, 0xabcd, 0x1000) = 0')]:
            self.assertFalse(self.analyze(text)['observation_complete'])
        changed = dict(DIGESTS); changed[trace.REQUIRED[0]] = '0' * 64
        result = trace.analyze_trace(fixture.text(), ROOT, changed, **BINDINGS, read_script=lambda path: SOURCES[str(Path(path).relative_to(ROOT))])
        self.assertFalse(result['observation_complete'])
        fixture = Fixture(); fixture.add(child=True)
        result = self.analyze(fixture.text().replace('read(0x3, 0xabcd, 0x1000) = 0x100', 'read(0x3, 0xabcd, 0x1000) = 0'))
        self.assertFalse(result['observation_complete'])
        self.assertIn('successful fast path lacks actual bound script read', result['errors'])

    def test_explicit_executable_bindings_refuse_basename_lookalikes(self):
        fixture = Fixture(); fixture.add(child=True)
        for old, new in [('execve("/usr/bin/claude", ["claude"]', 'execve("/usr/bin/cat", ["cat"]'),
                         ('execve("/bin/sh"', 'execve("/untrusted/sh"'),
                         ('execve("/usr/bin/python3"', 'execve("/untrusted/python3"')]:
            with self.subTest(new=new):
                self.assertFalse(self.analyze(fixture.text().replace(old, new))['observation_complete'])
        calls = []
        result = trace.analyze_trace(fixture.text(), ROOT, DIGESTS, read_script=lambda path: calls.append(path))
        self.assertFalse(result['observation_complete']); self.assertEqual([], calls)

    def test_native_receiver_identity_does_not_survive_reexec(self):
        fixture = Fixture(); fixture.add(size=8)
        for pid in [100, 101]:
            with self.subTest(pid=pid):
                text = fixture.text()
                if pid == 101:
                    text = text.replace('100 pipe2(', '100 clone(child_stack=NULL, flags=CLONE_VM|CLONE_FILES|CLONE_FS|CLONE_SIGHAND|CLONE_THREAD) = 101\n100 pipe2(', 1)
                    text = text.replace('100 +++ exited with 0 +++', '101 +++ exited with 0 +++\n100 +++ exited with 0 +++')
                text = text.replace('100 read(0x3, 0xabcd, 0x1000) = 0x8',
                                    f'{pid} execve("/usr/bin/cat", ["cat"], 0xeeee) = 0\n'
                                    f'{pid} read(0x3, 0xabcd, 0x1000) = 0x8')
                result = self.analyze(text)
                self.assertFalse(result['observation_complete'])
                self.assertIn('native host process or thread executed a new image', result['errors'])

    def test_descendant_signal_cannot_hide_behind_successful_dispatcher(self):
        fixture = Fixture(); pid = fixture.add(child=True)
        text = fixture.text().replace(f'{pid + 1} +++ exited with 0 +++', f'{pid + 1} +++ killed by SIGKILL +++')
        result = self.analyze(text)
        self.assertFalse(result['observation_complete'])
        self.assertEqual('signal', result['hooks'][0]['descendant_failures'][0]['termination'])

    def test_source_read_is_bound_to_one_exec_generation(self):
        fixture = Fixture(); pid = fixture.add(child=True)
        second = (f'{pid + 1} execve("/usr/bin/python3", ["python3", "-I", "-B", '
                  f'"{ROOT}/scripts/inject-plan.py", "--claude-event=post-tool-use"], 0xeeee) = 0')
        text = fixture.text().replace(f'{pid + 1} openat', second + '\n' + f'{pid + 1} openat', 1)
        result = self.analyze(text)
        self.assertFalse(result['observation_complete'])
        first, last = result['hooks'][0]['fast_path_execs']
        self.assertEqual('exec-replaced', first['termination']); self.assertIsNone(first['exit_code'])
        self.assertEqual(0, last['exit_code'])
        self.assertGreaterEqual(first['end_sequence'], first['exec_sequence'])
        self.assertTrue(all(row['exec_generation'] == last['exec_generation']
                            for row in result['hooks'][0]['fast_path_reads']))

    def test_known_regular_file_pread_is_unrelated_to_hook_stdout(self):
        fixture = Fixture(); pid = fixture.add(child=True)
        text = fixture.text().replace(f'{pid + 1} openat',
                                     f'{pid + 1} openat(AT_FDCWD, "/usr/lib/synthetic-libc.so", O_RDONLY|O_CLOEXEC) = 7\n'
                                     f'{pid + 1} pread64(0x7, 0xabcd, 0x8, 0x0) = 0x8\n'
                                     f'{pid + 1} close(7) = 0\n{pid + 1} openat', 1)
        result = self.analyze(text)
        self.assertTrue(result['observation_complete'], result['errors'])
        self.assertFalse(self.analyze(text.replace('pread64(0x7', 'pread64(0x1'))['observation_complete'])
        self.assertFalse(self.analyze(text.replace('pread64(0x7', 'pread64(0x63'))['observation_complete'])

    def test_fd_reuse_and_internal_pipe_do_not_pollute_stdout(self):
        fixture = Fixture(); pid = fixture.add()
        position = fixture.rows.index(f'{pid} +++ exited with 0 +++')
        fixture.rows[position:position] = [f'{pid} pipe2([5, 6], O_CLOEXEC) = 0',
                                         f'{pid} write(0x6, 0xaaaa, 0x8) = 0x8',
                                         f'{pid} read(0x5, 0xaaaa, 0x8) = 0x8',
                                         f'{pid} close(6) = 0', f'{pid} close(5) = 0']
        fixture.add(size=7)
        result = self.analyze(fixture)
        self.assertTrue(result['observation_complete'], result['errors'])
        self.assertEqual([0, 7], [h['stdout_written_bytes'] for h in result['hooks']])

    def test_successful_write_and_read_totals_must_match(self):
        fixture = Fixture(); fixture.add(size=8)
        text = fixture.text().replace('100 read(0x3, 0xabcd, 0x1000) = 0x8', '100 read(0x3, 0xabcd, 0x1000) = 0x7')
        self.assertFalse(self.analyze(text)['observation_complete'])
        text = fixture.text().replace('write(0x1, 0xabcd, 0x8) = 0x8', 'write(0x1, 0xabcd, 0x8) = -1 EPIPE (Broken pipe)')
        self.assertFalse(self.analyze(text)['observation_complete'])
        fixture = Fixture(); pid = fixture.add()
        for error in ['EPIPE', 'EAGAIN', 'EINTR']:
            text = fixture.text().replace(f'{pid} +++ exited with 0 +++',
                                         f'{pid} write(0x1, 0xabcd, 0x8) = -1 {error} (synthetic)\n{pid} +++ exited with 0 +++')
            self.assertFalse(self.analyze(text)['observation_complete'])

    def test_host_cannot_forge_hook_stdout_by_writing_its_pipe(self):
        fixture = Fixture(); pid = fixture.add(size=8)
        text = fixture.text().replace('100 close(4) = 0\n', '', 1)
        text = text.replace(f'{pid} write(0x1, 0xabcd, 0x8) = 0x8',
                            '100 write(0x4, 0xabcd, 0x8) = 0x8\n100 close(4) = 0')
        result = self.analyze(text)
        self.assertFalse(result['observation_complete'])
        self.assertEqual(8, result['hooks'][0]['foreign_write_bytes'])

    def test_writev_raw_is_counted_without_iovec_capture(self):
        fixture = Fixture(); fixture.add(size=8)
        result = self.analyze(fixture.text().replace('write(0x1, 0xabcd, 0x8)', 'writev(0x1, 0xabcd, 0x2)'))
        self.assertTrue(result['observation_complete'], result['errors'])
        self.assertEqual(8, result['hooks'][0]['stdout_written_bytes'])

    def test_descendant_late_write_after_dispatcher_exit(self):
        fixture = Fixture(); pid = fixture.add(size=8, child=True)
        text = fixture.text()
        root_exit = f'{pid} +++ exited with 0 +++\n'
        text = text.replace(root_exit, '').replace(f'{pid + 1} write(', root_exit + f'{pid + 1} write(')
        result = self.analyze(text)
        self.assertTrue(result['observation_complete'], result['errors'])
        self.assertEqual(8, result['hooks'][0]['stdout_written_bytes'])

    def test_shared_output_and_nested_dispatcher_refuse_attribution(self):
        fixture = Fixture(); pid = fixture.add()
        position = fixture.rows.index(f'{pid} +++ exited with 0 +++')
        fixture.rows[position:position] = [f'{pid} clone(child_stack=NULL, flags=SIGCHLD) = 999',
                                         f'999 execve("/bin/sh", ["sh", "{ROOT}/hooks/claude-hook.sh", "post-tool-use"], 0xaaaa) = 0',
                                         f'999 openat(AT_FDCWD, "{ROOT}/hooks/claude-hook.sh", O_RDONLY) = 3',
                                         '999 read(0x3, 0xabcd, 0x1000) = 0x80', '999 +++ exited with 0 +++']
        result = self.analyze(fixture)
        self.assertFalse(result['observation_complete'])
        self.assertIn('multiple dispatcher invocations share output channel', result['errors'])

    def test_unsupported_transfer_and_async_io_cannot_hide_output(self):
        fixture = Fixture(); pid = fixture.add()
        for line in [f'{pid} sendmsg(0x1, 0xabcd, 0x0) = 0x8',
                     f'{pid} splice(0x5, 0x0, 0x1, 0x0, 0x8, 0x0) = 0x8',
                     '100 io_uring_setup(0x8, 0xaaaa) = 0x8']:
            text = fixture.text().replace(f'{pid} +++ exited with 0 +++', line + '\n' + f'{pid} +++ exited with 0 +++')
            self.assertFalse(self.analyze(text)['observation_complete'])
        fixture = Fixture(); fixture.add(transport='unix')
        self.assertFalse(self.analyze(fixture.text().replace('SOCK_STREAM', 'SOCK_DGRAM'))['observation_complete'])
        for domain, complete in [('AF_UNIX', False), ('AF_INET', True)]:
            with self.subTest(domain=domain):
                text = fixture.text().replace('100 socketpair(',
                                             f'100 socket({domain}, SOCK_STREAM|SOCK_CLOEXEC, 0) = 9\n'
                                             '100 sendmsg(0x9, 0xabcd, 0x0) = 0x8\n100 close(9) = 0\n100 socketpair(', 1)
                result = self.analyze(text)
                self.assertEqual(complete, result['observation_complete'], result['errors'])

    def test_shared_fd_race_rejects_relevant_but_not_unrelated_read(self):
        fixture = Fixture(); fixture.add(size=8)
        fixture.rows.insert(1, '100 clone(child_stack=NULL, flags=CLONE_VM|CLONE_FILES|CLONE_FS|CLONE_SIGHAND|CLONE_THREAD) = 101')
        fixture.rows.append('101 +++ exited with 0 +++')
        text = fixture.text().replace('100 read(0x3, 0xabcd, 0x1000) = 0x8',
                                     '101 read(0x3, 0xabcd, 0x1000 <unfinished ...>\n100 dup2(3, 7) = 7\n100 close(3) = 0\n101 <... read resumed>) = 0x8')
        text = text.replace('100 read(0x3, 0xabcd, 0x1000) = 0\n', '100 read(0x7, 0xabcd, 0x1000) = 0\n')
        result = self.analyze(text)
        self.assertFalse(result['observation_complete'])
        self.assertGreater(result['binding_conflict_count'], 0)
        text = fixture.text().replace('100 pipe2([3, 4], O_CLOEXEC) = 0',
                                     '100 openat(AT_FDCWD, "/synthetic/unrelated", O_RDONLY) = 9\n'
                                     '101 read(0x9, 0xabcd, 0x8 <unfinished ...>\n100 close(9) = 0\n'
                                     '101 <... read resumed>) = 0x8\n100 pipe2([3, 4], O_CLOEXEC) = 0')
        result = self.analyze(text)
        self.assertTrue(result['observation_complete'], result['errors'])
        self.assertGreater(result['binding_conflict_count'], 0)

    def test_transfer_fd_race_is_not_silently_unrelated(self):
        fixture = Fixture(); pid = fixture.add(size=8)
        fixture.rows[1:1] = ['100 clone(child_stack=NULL, flags=CLONE_VM|CLONE_FILES|CLONE_FS|CLONE_SIGHAND|CLONE_THREAD) = 101',
                            '100 pipe2([9, 10], O_CLOEXEC) = 0', '100 pipe2([11, 12], O_CLOEXEC) = 0']
        fixture.rows.append('101 +++ exited with 0 +++')
        text = fixture.text().replace('100 read(0x3, 0xabcd, 0x1000) = 0x8',
                                     '100 tee(0x9, 0xc, 0x8, 0x0 <unfinished ...>\n101 dup2(3, 9) = 9\n'
                                     '100 <... tee resumed>) = 0x8\n100 read(0x3, 0xabcd, 0x1000) = 0x8')
        result = self.analyze(text)
        self.assertFalse(result['observation_complete'])
        self.assertIn('ambiguous descriptor I/O may affect hook stdout', result['errors'])
        self.assertGreater(result['binding_conflict_count'], 0)

    def test_descriptor_alias_paths_and_unshare_fail_closed(self):
        fixture = Fixture(); pid = fixture.add()
        for path in ['/dev/stdout', '/dev/stdin', '/dev/stderr', '/dev/fd/1',
                     '/proc/self/task/100/fd/3', '/proc/100/task/101/fd/3', '/proc/thread-self/fd/3']:
            with self.subTest(path=path):
                text = fixture.text().replace(f'{pid} +++ exited with 0 +++',
                                             f'{pid} openat(AT_FDCWD, "{path}", O_WRONLY) = 5\n'
                                             f'{pid} write(0x5, 0xabcd, 0x8) = 0x8\n{pid} +++ exited with 0 +++')
                self.assertFalse(self.analyze(text)['observation_complete'])
        text = fixture.text().replace('100 pipe2(', '100 unshare(CLONE_FILES) = 0\n100 pipe2(', 1)
        self.assertFalse(self.analyze(text)['observation_complete'])
        self.assertIn('unshare', trace.TRACE_SYSCALLS.split(','))

    def test_optional_native_timestamps_keep_event_order(self):
        fixture = Fixture(); fixture.add()
        text = '\n'.join(line.split(' ', 1)[0] + f' 1788971400.{index:06d} ' + line.split(' ', 1)[1]
                         for index, line in enumerate(fixture.text().splitlines())) + '\n'
        result = self.analyze(text)
        self.assertTrue(result['observation_complete'], result['errors'])
        self.assertRegex(result['hooks'][0]['exec_time'], r'^1788971400\.[0-9]{6}$')

    def test_data_buffers_never_exported_and_budget_precedes_resource_reads(self):
        fixture = Fixture(); pid = fixture.add(size=8)
        text = fixture.text().replace('write(0x1, 0xabcd, 0x8)', 'write(1, "SECRET", 8)')
        result = self.analyze(text)
        self.assertFalse(result['observation_complete'])
        self.assertNotIn('SECRET', json.dumps(result)); self.assertNotIn('0xeeee', json.dumps(result))
        calls = []
        result = trace.analyze_trace(fixture.text(), ROOT, DIGESTS, max_bytes=1, read_script=lambda path: calls.append(path))
        self.assertFalse(result['observation_complete']); self.assertEqual([], calls)


if __name__ == '__main__':
    unittest.main()
