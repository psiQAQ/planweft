"""Offline adversarial contracts for stopping-counter process attribution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('pw_gate_trace',Path(__file__).with_name('gate_process_trace.py'))
trace_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(trace_module)
SCRIPT=b'#!/bin/sh\n# installed gate fixture\n'
DIGEST=hashlib.sha256(SCRIPT).hexdigest()
GATE='20<bash> execve("/bin/bash", ["bash", "/package/scripts/check-complete.sh", "--gate"], 0x1 /* 8 vars */) = 0\n'


def io(pid=20,path='/workspace/.stop_blocks',fd=3):
    return (f'{pid}<cat> openat(AT_FDCWD, "{path}", O_RDONLY) = {fd}\n'
            f'{pid}<cat> read({hex(fd)}, 0x1234, 0x100) = 0x2\n')


def ending(*pids):
    return ''.join(f'{pid}<process> +++ exited with 0 +++\n' for pid in pids)


def parse(text,**kwargs):
    return trace_module.attributed_gate_reads(text,DIGEST,read_script=lambda p:SCRIPT,**kwargs)


class GateProcessTraceTest(unittest.TestCase):
    def test_unfinished_diagnostics_are_bounded_and_do_not_resolve_exit(self):
        text=GATE+'20<bash> read(0x3, <unfinished ...>\n'+ending(20)
        result=parse(text)
        self.assertFalse(result['trace_complete'])
        self.assertIn('unfinished syscalls at EOF',result['errors'])
        self.assertEqual(result['unfinished_syscalls'],{'count':1,'samples':[
            {'pid':20,'start_event':1,'operation':'read','later_exit_event':2,'descriptor':3}]})
        text=''.join(f'{pid}<SECRET> execve("/SECRET", ["SECRET"], <unfinished ...>\n' for pid in range(100,140))
        result=parse(text)
        self.assertEqual(result['unfinished_syscalls']['count'],40)
        self.assertEqual(len(result['unfinished_syscalls']['samples']),32)
        self.assertNotIn('SECRET',json.dumps(result))
        self.assertTrue(all(s['later_exit_event'] is None for s in result['unfinished_syscalls']['samples']))

    def test_two_pass_unknown_snapshot_reaches_later_gate_exec(self):
        prefix=('10<host> execve("/bin/host", ["host"], 0x1) = 0\n'
                '10<host> clone(child_stack=NULL, flags=CLONE_FILES|SIGCHLD) = 11\n'
                '10<host> clone(child_stack=NULL, flags=SIGCHLD <unfinished ...>\n'
                '11<host> openat(AT_FDCWD, "/workspace/.stop_blocks", O_RDONLY|O_CLOEXEC) = 7\n'
                '10<host> <... clone resumed>) = 20\n')
        read='20<bash> read(0x7, 0x1234, 0x100) = 0x2\n'
        result=parse(prefix+GATE+read+ending(20,11,10))
        self.assertFalse(result['trace_complete'],result)
        self.assertIn('gate read depends on ambiguous descriptor binding',result['errors'])
        # A definite later open clears the inherited unknown binding, even
        # though the original host race remains in the reported conflicts.
        result=parse(prefix+GATE+io(fd=7)+ending(20,11,10))
        self.assertTrue(result['trace_complete'],result)
        self.assertGreater(result['conflicts']['count'],0)

    def test_unknown_bindings_propagate_through_dup_and_directory_operations(self):
        prefix=(GATE+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|SIGCHLD) = 21\n'
                '20<bash> openat(AT_FDCWD, "/workspace", <unfinished ...>\n'
                '21<host> close(7) = 0\n'
                '20<bash> <... openat resumed>O_RDONLY|O_DIRECTORY) = 7\n')
        routes=[
            '20<bash> dup2(7, 8) = 8\n20<bash> read(0x8, 0x1234, 0x100) = 0x2\n',
            '20<bash> openat(7, ".stop_blocks", O_RDONLY) = 8\n20<bash> read(0x8, 0x1234, 0x100) = 0x2\n',
            '20<bash> fchdir(7) = 0\n'+io(path='.stop_blocks'),
            '20<bash> fchdir(7) = 0\n20<bash> chdir("child") = 0\n'+io(path='.stop_blocks'),
        ]
        for route in routes:
            with self.subTest(route=route):
                self.assertFalse(parse(prefix+route+ending(21,20))['trace_complete'])
        # Absolute chdir is a definite cwd reset after the uncertainty ended.
        result=parse(prefix+'20<bash> fchdir(7) = 0\n20<bash> chdir("/workspace") = 0\n'+io(path='.stop_blocks')+ending(21,20))
        self.assertTrue(result['trace_complete'],result)

    def test_only_covering_definite_writes_clear_unknown(self):
        prefix=GATE+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|SIGCHLD) = 21\n'
        race=('20<bash> openat(AT_FDCWD, "/workspace/.stop_blocks", <unfinished ...>\n'
              '21<host> close(3) = 0\n')
        finish='20<bash> <... openat resumed>O_RDONLY) = 3\n'
        read='20<bash> read(0x3, 0x1234, 0x100) = 0x2\n'
        overwrite='21<host> openat(AT_FDCWD, "/workspace/.stop_blocks", O_RDONLY) = 3\n'
        self.assertFalse(parse(prefix+race+overwrite+finish+read+ending(21,20))['trace_complete'])
        self.assertTrue(parse(prefix+race+finish+overwrite+read+ending(21,20))['trace_complete'])
        for low,complete in [(0,True),(4,False)]:
            route=f'20<bash> close_range({low}, ~0U, CLOSE_RANGE_UNSHARE) = 0\n'
            result=parse(prefix+race+finish+route+read+ending(21,20))
            self.assertEqual(result['trace_complete'],complete,result)

    def test_unrelated_host_race_cannot_hide_relative_gate_identity(self):
        prefix=('20<host> execve("/bin/host", ["host"], 0x1) = 0\n'
                '20<host> clone(child_stack=NULL, flags=CLONE_FILES|SIGCHLD) = 21\n'
                '20<host> openat(AT_FDCWD, "/package/scripts", <unfinished ...>\n'
                '21<host> close(7) = 0\n'
                '20<host> <... openat resumed>O_RDONLY|O_DIRECTORY) = 7\n')
        result=parse(prefix+ending(21,20))
        self.assertTrue(result['trace_complete'],result)
        self.assertEqual(result['gates'],[])
        hidden='20<host> fchdir(7) = 0\n'+GATE.replace('/package/scripts/check-complete.sh','check-complete.sh')
        self.assertFalse(parse(prefix+hidden+ending(21,20))['trace_complete'])

    def test_non_ebadf_close_and_descriptor_limit_fail_closed(self):
        for error,complete in [('EIO',False),('EINTR',False),('EBADF',True)]:
            result=parse(GATE+f'20<bash> close(3) = -1 {error} (synthetic error)\n'+ending(20))
            self.assertEqual(result['trace_complete'],complete,result)
        text=GATE+''.join(f'20<bash> close({n}) = 0\n' for n in range(4097))+ending(20)
        result=parse(text)
        self.assertFalse(result['trace_complete'])
        self.assertIn('descriptor bound exceeded',result['errors'])

    def test_script_identity_is_frozen_and_first_pass_failure_survives(self):
        calls=[]
        def reader(path):
            calls.append(path)
            return b'wrong first bytes' if len(calls)==1 else SCRIPT
        result=trace_module.attributed_gate_reads(GATE+io()+ending(20),DIGEST,read_script=reader)
        self.assertFalse(result['trace_complete'],result)
        self.assertIn('gate candidate digest mismatch or unavailable',result['errors'])
        self.assertEqual(len(calls),1)

    def test_snapshot_and_async_gate_descendants_are_distinct(self):
        text=('10<claude> execve("/usr/bin/claude", ["claude", "-p"], 0x1 /* 8 vars */) = 0\n'
              +io(10)+'10<claude> clone(child_stack=NULL, flags=SIGCHLD <unfinished ...>\n'
              +GATE+'10<claude> <... clone resumed>) = 20\n'
              +'20<bash> clone3({flags=0}, 88) = 21\n'
              +'21<cat> execve("/usr/bin/cat", ["cat", ".stop_blocks"], 0x1 /* 8 vars */) = 0\n'
              +io(21,path='.stop_blocks')+'20<bash> fork() = 22\n'
              +io(22,path='.gate_last_ledger')+ending(21,22,20,10))
        result=parse(text)
        self.assertTrue(result['trace_complete'],result)
        self.assertIsNone(result['reads'][0]['gate'])
        self.assertEqual(result['attributed_files'],['.gate_last_ledger','.stop_blocks'])
        self.assertEqual(result['reads'][1]['gate']['pid'],20)

    def test_only_script_position_and_exact_digest_are_valid(self):
        for executable,argv in [('/bin/bash',['bash','/package/scripts/check-complete.sh']),
                                ('/bin/bash',['bash','/package/scripts/unrelated.sh','--gate']),
                                ('/bin/echo',['echo','/package/scripts/check-complete.sh','--gate']),
                                ('/bin/bash',['bash','-c','echo /package/scripts/check-complete.sh --gate'])]:
            with self.subTest(argv=argv):
                text=f'20<proc> execve("{executable}", {json.dumps(argv)}, 0x1 /* 8 vars */) = 0\n'+io()+ending(20)
                result=parse(text)
                self.assertTrue(result['trace_complete'],result)
                self.assertEqual(result['attributed_files'],[])
        result=trace_module.attributed_gate_reads(GATE+io()+ending(20),DIGEST,read_script=lambda p:b'wrong')
        self.assertFalse(result['trace_complete'])
        self.assertEqual(result['attributed_files'],[])
        direct='20<gate> execve("/package/scripts/check-complete.sh", ["/package/scripts/check-complete.sh", "--gate"], 0x1 /* 8 vars */) = 0\n'
        self.assertEqual(parse(direct+io()+ending(20))['attributed_files'],['.stop_blocks'])

    def test_codex_explicit_root_plan_argument_is_bound_to_this_probe(self):
        for plan in ('/workspace/task_plan.md','task_plan.md'):
            trace=GATE.replace('"--gate"]','"--gate", '+json.dumps(plan)+']')+io()+ending(20)
            result=parse(trace)
            self.assertTrue(result['trace_complete'],result)
            self.assertEqual(result['attributed_files'],['.stop_blocks'])
        for args in ['"--gate", "/other/task_plan.md"','"--gate", "--help"',
                     '"--gate", "/workspace/task_plan.md", "extra"']:
            trace=GATE.replace('"--gate"',args)+io()+ending(20)
            result=parse(trace)
            self.assertFalse(result['trace_complete'])
            self.assertEqual(result['attributed_files'],[])

    def test_exact_counter_directory_and_cwd(self):
        result=parse(GATE+io(path='/tmp/other/.stop_blocks')+ending(20))
        self.assertTrue(result['trace_complete']); self.assertEqual(result['attributed_files'],[])
        text=GATE+'20<bash> chdir("/tmp") = 0\n'+io(path='.stop_blocks')+ending(20)
        self.assertEqual(parse(text)['attributed_files'],[])
        text=GATE+'20<bash> openat(AT_FDCWD, "/workspace", O_RDONLY|O_DIRECTORY) = 7\n20<bash> openat(7, ".stop_blocks", O_RDONLY) = 3\n20<bash> read(0x3, 0x1234, 0x100) = 0x2\n'+ending(20)
        self.assertEqual(parse(text)['attributed_files'],['.stop_blocks'])

    def test_exited_pid_cannot_lend_gate_identity_to_reused_pid(self):
        text='10<claude> execve("/bin/claude", ["claude"], 0x1) = 0\n10<claude> fork() = 20\n'+GATE+ending(20)
        text+='10<claude> fork() = 20\n'+io()+ending(20,10)
        result=parse(text)
        self.assertTrue(result['trace_complete'],result)
        self.assertEqual(result['attributed_files'],[])
        self.assertEqual(result['reads'][0]['generation'],2)

    def test_parent_future_exec_does_not_retroactively_attribute_child(self):
        text='10<claude> fork() = 20\n'+GATE.replace('20<bash>','10<bash>')+io()+ending(20,10)
        result=parse(text)
        self.assertTrue(result['trace_complete'],result); self.assertEqual(result['attributed_files'],[])

    def test_close_reuse_dup_and_exec_lifecycle(self):
        opened='20<bash> openat(AT_FDCWD, "/workspace/.stop_blocks", O_RDONLY) = 3\n'
        read='20<bash> read(0x3, 0x1234, 0x100) = 0x2\n'
        for change in ['20<bash> close(3) = 0\n',
                       '20<bash> openat(AT_FDCWD, "/tmp/other", O_RDONLY) = 3\n',
                       '20<bash> dup2(9, 3) = 3\n',
                       '20<bash> close_range(3, ~0U, 0) = 0\n',
                       '20<bash> fcntl(3, F_SETFD, FD_CLOEXEC) = 0\n20<cat> execve("/bin/cat", ["cat"], 0x1) = 0\n']:
            with self.subTest(change=change):
                result=parse(GATE+opened+change+read+ending(20))
                self.assertTrue(result['trace_complete'],result); self.assertEqual(result['attributed_files'],[])
        text=GATE+opened+'20<bash> dup2(3, 4) = 4\n20<bash> close(3) = 0\n20<bash> read(0x4, 0x1234, 0x100) = 0x2\n'+ending(20)
        self.assertEqual(parse(text)['attributed_files'],['.stop_blocks'])

    def test_fork_descriptor_inheritance_and_clone_shared_descriptors(self):
        opened='20<bash> openat(AT_FDCWD, "/workspace/.stop_blocks", O_RDONLY) = 3\n'
        text=GATE+opened+'20<bash> fork() = 21\n21<cat> read(0x3, 0x1234, 0x100) = 0x2\n'+ending(21,20)
        self.assertEqual(parse(text)['attributed_files'],['.stop_blocks'])
        text=GATE+opened+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|SIGCHLD) = 21\n21<cat> close(3) = 0\n20<bash> read(0x3, 0x1234, 0x100) = 0x2\n'+ending(21,20)
        self.assertEqual(parse(text)['attributed_files'],[])

    def test_async_exec_open_read_and_incomplete_trace(self):
        text=('20<bash> execve("/bin/bash", ["bash", "/package/scripts/check-complete.sh", "--gate"], <unfinished ...>\n'
              '20<bash> <... execve resumed>0x1 /* 8 vars */) = 0\n'
              '20<bash> openat(AT_FDCWD, "/workspace/.stop_blocks", <unfinished ...>\n'
              '20<bash> <... openat resumed>O_RDONLY) = 3\n'
              '20<bash> read(0x3, <unfinished ...>\n'
              '20<bash> <... read resumed>0x1234, 0x100) = 0x2\n')
        result=parse(text+ending(20))
        self.assertTrue(result['trace_complete'],result); self.assertEqual(result['attributed_files'],['.stop_blocks'])
        for broken in ['',text,text+'20<bash> read(0x3, <unfinished ...>\n',
                       '20<bash> <... read resumed>0x1234, 0x100) = 0x2\n'+ending(20),
                       'garbage\n'+ending(20)]:
            with self.subTest(broken=broken): self.assertFalse(parse(broken)['trace_complete'])

    def test_metadata_does_not_export_arbitrary_arguments(self):
        text='10<host> execve("/bin/host", ["host", "SECRET\\nTRUNCATED"], 0x1 /* 8 vars */) = 0\n'+ending(10)
        result=parse(text)
        self.assertTrue(result['trace_complete'],result)
        self.assertNotIn('SECRET',json.dumps(result)); self.assertNotIn('argv',json.dumps(result))
        self.assertEqual(result['source_sha256'],hashlib.sha256(text.encode()).hexdigest())

    def test_decoded_clone_pid_and_shared_io_ambiguity(self):
        text=GATE+'20<bash> vfork() = 21<cat>\n'+io(21)+ending(21,20)
        result=parse(text)
        self.assertTrue(result['trace_complete'],result)
        self.assertEqual(result['attributed_files'],['.stop_blocks'])
        text=(GATE+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|SIGCHLD) = 21<cat>\n'
              +'20<bash> openat(AT_FDCWD, "/workspace/.stop_blocks", <unfinished ...>\n'
              +'21<cat> read(0x3, 0x1234, 0x100) = 0x2\n'
              +'20<bash> <... openat resumed>O_RDONLY) = 3\n'+ending(21,20))
        self.assertFalse(parse(text)['trace_complete'])

    def test_negative_control_requires_exec_and_complete_parse(self):
        for text in [io()+ending(20),
                     '20<host> execve("/bin/host", ["host", ...], 0x1) = 0\n'+ending(20),
                     GATE+'20<host> +++ superseded by execve in pid 21 +++\n'+ending(20)]:
            with self.subTest(text=text): self.assertFalse(parse(text)['trace_complete'])

    def test_real_bun_thread_comm_preserves_child_and_gate_identity(self):
        # Minimized from offline Claude 2.1.241 --help, strace --decode-pids=comm.
        # Its actual clone result and parent_tid annotation contain spaces.
        clone=('20<bash> clone(child_stack=0x7bb209d724b0, '
               'flags=CLONE_VM|CLONE_FS|CLONE_FILES|CLONE_SIGHAND|CLONE_THREAD|CLONE_SYSVSEM|CLONE_SETTLS|CLONE_PARENT_SETTID|CLONE_CHILD_CLEARTID, '
               'parent_tid=[21<Bun Pool 0>], tls=0x7bb209d796c0, '
               'child_tidptr=0x7bb209d79990) = 21<Bun Pool 0>\n')
        text=GATE+clone+io(21).replace('21<cat>','21<Bun Pool 0>')+ending(21,20)
        result=parse(text)
        self.assertTrue(result['trace_complete'],result)
        self.assertEqual(result['attributed_files'],['.stop_blocks'])
        self.assertEqual(result['reads'][0]['gate']['pid'],20)
        for token in ['21<Bun Pool 0','21<Bun Pool 0>garbage','21garbage']:
            with self.subTest(token=token):
                broken=text.replace(') = 21<Bun Pool 0>',') = '+token)
                self.assertFalse(parse(broken)['trace_complete'])

    def test_cloexec_does_not_close_other_threads_shared_table(self):
        text=(GATE+'20<bash> openat(AT_FDCWD, "/workspace/.stop_blocks", O_RDONLY|O_CLOEXEC) = 3\n'
              +'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|SIGCHLD) = 21\n'
              +'21<cat> execve("/bin/cat", ["cat"], 0x1) = 0\n'
              +'21<cat> read(0x3, 0x1234, 0x100) = 0x2\n'
              +'20<bash> read(0x3, 0x1234, 0x100) = 0x2\n'+ending(21,20))
        result=parse(text)
        self.assertTrue(result['trace_complete'],result)
        self.assertEqual([r['pid'] for r in result['reads']],[20])

    def test_unrelated_fds_and_failed_clone_are_not_conflicts(self):
        prefix=GATE+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|CLONE_FS|SIGCHLD) = 21\n'+io()
        for concurrent in [
            '21<host> clone3({flags=0}, 88) = -1 ENOSYS (Function not implemented)\n',
            '21<host> openat(AT_FDCWD, "/tmp/unrelated", O_RDONLY) = 12\n21<host> close(12) = 0\n',
            '21<host> read(0x3, 0x1234, 0x100) = 0x2\n',
        ]:
            trace=prefix+'20<bash> read(0x3, <unfinished ...>\n'+concurrent+'20<bash> <... read resumed>0x1234, 0x100) = 0x2\n'+ending(21,20)
            self.assertTrue(parse(trace)['trace_complete'],parse(trace))

    def test_relevant_shared_mutations_still_fail(self):
        prefix=GATE+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|CLONE_FS|SIGCHLD) = 21\n'+io()
        for concurrent in [
            '21<host> close(3) = 0\n',
            '21<host> dup2(12, 3) = 3\n',
            '21<host> close(3) = 0\n21<host> openat(AT_FDCWD, "/tmp/other", O_RDONLY) = 3\n',
            '21<host> close_range(0, ~0U, 0) = 0\n',
        ]:
            trace=prefix+'20<bash> read(0x3, <unfinished ...>\n'+concurrent+'20<bash> <... read resumed>0x1234, 0x100) = 0x2\n'+ending(21,20)
            self.assertFalse(parse(trace)['trace_complete'])

    def test_relative_paths_depend_on_cwd_but_absolute_paths_do_not(self):
        prefix=GATE+'20<bash> clone(child_stack=NULL, flags=CLONE_FS|SIGCHLD) = 21\n'
        for path,complete in [('/workspace/.stop_blocks',True),('.stop_blocks',False)]:
            trace=(prefix+f'20<bash> openat(AT_FDCWD, "{path}", <unfinished ...>\n'
                   +'21<host> chdir("/tmp") = 0\n'
                   +'20<bash> <... openat resumed>O_RDONLY) = 3\n20<bash> read(0x3, 0x1234, 0x100) = 0x2\n'+ending(21,20))
            self.assertEqual(parse(trace)['trace_complete'],complete,parse(trace))

    def test_clone_and_exec_snapshots_cannot_race_shared_mutations(self):
        prefix=GATE+io()+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|CLONE_FS|SIGCHLD) = 21\n'
        for change in ['21<host> chdir("/tmp") = 0\n','21<host> close(3) = 0\n']:
            trace=(prefix+'20<bash> clone(child_stack=NULL, flags=SIGCHLD <unfinished ...>\n'
                   +change+'20<bash> <... clone resumed>) = 22\n'
                   +'22<child> read(0x3, 0x1234, 0x100) = 0x2\n'+io(22,path='.stop_blocks')+ending(22,21,20))
            self.assertFalse(parse(trace)['trace_complete'])
        trace=(prefix+'20<bash> execve("/bin/cat", ["cat"], <unfinished ...>\n'
               +'21<host> close(3) = 0\n20<bash> <... execve resumed>0x1) = 0\n'
               +'20<cat> read(0x3, 0x1234, 0x100) = 0x2\n'+ending(21,20))
        self.assertFalse(parse(trace)['trace_complete'])

    def test_thread_born_inside_pending_read_is_not_missed(self):
        trace=(GATE+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|SIGCHLD) = 21\n'+io()
               +'20<bash> read(0x3, <unfinished ...>\n'
               +'21<host> clone(child_stack=NULL, flags=CLONE_FILES|SIGCHLD) = 22\n'
               +'22<host> close(3) = 0\n'
               +'20<bash> <... read resumed>0x1234, 0x100) = 0x2\n'+ending(22,21,20))
        self.assertFalse(parse(trace)['trace_complete'])

    def test_child_event_bounds_snapshot_before_delayed_parent_return(self):
        prefix=(GATE+io()+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|CLONE_FS|SIGCHLD) = 21\n')
        for mutation in ['21<host> close(3) = 0\n', '21<host> chdir("/tmp") = 0\n']:
            for before_child in (False,True):
                trace=prefix+'20<bash> clone(child_stack=NULL, flags=CLONE_VM|CLONE_VFORK|SIGCHLD <unfinished ...>\n'
                if before_child: trace+=mutation
                trace+='22<child> read(0x3, 0x1234, 0x100) = 0x2\n'
                if not before_child: trace+=mutation
                trace+='20<bash> <... clone resumed>) = 22\n'+io(22,path='.stop_blocks')+ending(22,21,20)
                result=parse(trace)
                self.assertEqual(result['trace_complete'],not before_child,result)
        # Sharing persists after the first child event: a later overlapping
        # close/read is still ambiguous even before the parent clone returns.
        trace=prefix+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|SIGCHLD <unfinished ...>\n'
        trace+='22<child> read(0x3, 0x1234, 0x100) = 0x2\n21<host> close(3 <unfinished ...>\n'
        trace+='22<child> read(0x3, 0x1234, 0x100) = 0x2\n21<host> <... close resumed>) = 0\n'
        trace+='20<bash> <... clone resumed>) = 22\n'+ending(22,21,20)
        self.assertFalse(parse(trace)['trace_complete'])

    def test_child_snapshot_bound_uses_start_and_preserves_overlapping_mutation(self):
        prefix=GATE+io()+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|CLONE_FS|SIGCHLD) = 21\n'
        clone='20<bash> clone(child_stack=NULL, flags=CLONE_VFORK|SIGCHLD <unfinished ...>\n'
        child='22<child> read(0x3, <unfinished ...>\n'
        resume='22<child> <... read resumed>0x1234, 0x100) = 0x2\n'
        tail='20<bash> <... clone resumed>) = 22\n'+ending(22,21,20)
        result=parse(prefix+clone+child+'21<host> close(3) = 0\n'+resume+tail)
        self.assertTrue(result['trace_complete'],result)
        trace=prefix+clone+'21<host> close(3 <unfinished ...>\n'+child
        trace+='21<host> <... close resumed>) = 0\n'+resume+tail
        self.assertFalse(parse(trace)['trace_complete'])
        # A PID's older generation cannot supply the new clone's bound.
        reused=prefix+'20<bash> fork() = 22\n'+ending(22)+clone
        reused+='21<host> close(3) = 0\n22<child> read(0x3, 0x1234, 0x100) = 0x2\n'+tail
        self.assertFalse(parse(reused)['trace_complete'])
        # No child events cannot prove an earlier snapshot boundary or exit.
        missing=prefix+clone+'21<host> close(3) = 0\n20<bash> <... clone resumed>) = 22\n'+ending(21,20)
        self.assertFalse(parse(missing)['trace_complete'])

    def test_exec_preserves_shared_cwd_and_unknown_exit_results_fail(self):
        trace=(GATE+'20<bash> clone(child_stack=NULL, flags=CLONE_FS|SIGCHLD) = 21\n'
               +'21<host> execve("/bin/cat", ["cat"], 0x1) = 0\n'
               +'20<bash> chdir("/tmp") = 0\n'+io(21,path='.stop_blocks')+ending(21,20))
        result=parse(trace)
        self.assertTrue(result['trace_complete'],result)
        self.assertEqual(result['attributed_files'],[])
        for unknown in ['20<bash> read(0x3, 0x1234, 0x100) = ?\n',
                        '20<bash> close(3 <unfinished ...>\n']:
            self.assertFalse(parse(GATE+unknown+ending(20))['trace_complete'])

    def test_close_range_unshare_copies_without_closing_sibling_descriptors(self):
        prefix=GATE+io()+'20<bash> clone(child_stack=NULL, flags=CLONE_FILES|SIGCHLD) = 21\n'
        trace=prefix+'20<bash> close_range(0, ~0U, CLOSE_RANGE_UNSHARE) = 0\n'
        trace+='21<cat> read(0x3, 0x1234, 0x100) = 0x2\n'+ending(21,20)
        result=parse(trace);self.assertTrue(result['trace_complete'],result)
        self.assertEqual(result['reads'][-1]['pid'],21)
        for other,complete in [('21<cat> close(3) = 0\n',False),
                               ('21<cat> read(0x3, 0x1234, 0x100) = 0x2\n',True)]:
            trace=prefix+'20<bash> close_range(4, ~0U, <unfinished ...>\n'+other
            trace+='20<bash> <... close_range resumed>CLOSE_RANGE_UNSHARE) = 0\n'
            trace+='20<bash> read(0x3, 0x1234, 0x100) = 0x2\n'+ending(21,20)
            self.assertEqual(parse(trace)['trace_complete'],complete,parse(trace))


if __name__=='__main__': unittest.main()
