"""Native trust UI automation only reacts to observed review states."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock,patch
import subprocess
import tempfile

spec=importlib.util.spec_from_file_location('pw_trust',Path(__file__).with_name('codex_trust_probe.py'))
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)


class CodexTrustProbeTest(unittest.TestCase):
    def test_closed_terminal_and_exited_process_do_not_skip_wait(self):
        process=Mock(pid=123)
        process.poll.return_value=None
        process.wait.side_effect=[subprocess.TimeoutExpired('owned-ui',5),0]
        with patch.object(probe.os,'write',side_effect=OSError('EIO')), \
             patch.object(probe.os,'killpg',side_effect=ProcessLookupError):
            probe.stop_ui(process,9)
        self.assertEqual(process.wait.call_count,2)

    def test_trace_uses_runtime_redaction_and_counts_the_leak(self):
        runtime_spec=importlib.util.spec_from_file_location('pw_trust_redaction',Path(__file__).with_name('five_agent_runtime.py'))
        runtime=importlib.util.module_from_spec(runtime_spec);runtime_spec.loader.exec_module(runtime)
        secret='synthetic-secret-do-not-export'
        runtime.SECRETS=[secret];runtime.REDACTIONS=0
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'ui.log'
            probe.save_trace(output,['prefix '+secret],[],'failed',runtime.safe_text)
            self.assertNotIn(secret,output.read_text())
            self.assertIn('[REDACTED_CREDENTIAL]',output.read_text())
            self.assertEqual(runtime.REDACTIONS,1)

    def test_requires_observed_native_review_and_active_transition(self):
        self.assertEqual(probe.review_action('unrelated startup text','start'),(None,'start'))
        self.assertEqual(probe.review_action('Do you trust the contents of this directory? Press enter to continue','start'),(b'\r','directory-approved'))
        self.assertEqual(probe.review_action('Hooks need review Press enter to confirm','directory-approved'),(b'\r','review-opened'))
        self.assertEqual(probe.review_action('Hooks need review','start'),(None,'start'))
        self.assertEqual(probe.review_action('Press t to trust all','review-opened'),(b't','hooks-approved'))
        self.assertEqual(probe.review_action('Active\nPress enter to view hooks','hooks-approved'),(None,'verified-active'))
        self.assertEqual(probe.review_action('Active\nPress enter to view hooks','start'),(None,'start'))
        self.assertEqual(probe.review_action('Press t to trust all','hooks-approved'),(None,'hooks-approved'))

    def test_ansi_and_wrapped_text_are_normalized_without_reading_files(self):
        screen='\x1b[31mHooks\n need review\x1b[0m Press enter to confirm'
        self.assertEqual(probe.review_action(screen,'start'),(b'\r','review-opened'))
        self.assertEqual(probe.review_action('No hooks installed','start'),(None,'start'))


if __name__=='__main__': unittest.main()
