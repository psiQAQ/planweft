"""Offline contracts for the Skill-owned document handoff and Hook reader."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'overlays/planweft/document-handoff-check.sh'


class DocumentHandoffTest(unittest.TestCase):
    def status(self, body):
        with tempfile.TemporaryDirectory(prefix='pw-document-handoff-') as directory:
            plan = Path(directory) / 'task_plan.md'
            plan.write_text(body)
            result = subprocess.run(['sh', str(HELPER), str(plan)], text=True,
                                    capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, '')
            return result.stdout.strip()

    def test_marker_requires_one_exact_section_and_value(self):
        prefix = '# Task Plan\n\n## Goal\nKeep scope.\n\n'
        marker = ('## Documentation Handoff\n\n<!-- planweft-docs-status: {} -->\n'
                  '- Documents considered: docs/README.md\n'
                  '- Rationale / evidence: source-backed result\n'
                  '- Next action: review\n')
        for value in ('pending', 'not_required', 'complete'):
            self.assertEqual(self.status(prefix + marker.format(value)), value)
        for body in (
                prefix,
                prefix + marker.format('unknown'),
                prefix + marker.format('pending') + marker.format('complete'),
                prefix + marker.format('complete') + '<!-- planweft-docs-status: unknown -->\n',
                prefix + '<!-- planweft-docs-status: complete -->\n' + marker.format('complete'),
                prefix + '<!-- planweft-docs-status: unknown -->\n' + marker.format('complete'),
                prefix + '## Documentation Handoff\n<!-- planweft-docs-status: complete -->\n',
                prefix + '<!-- planweft-docs-status: complete -->\n'):
            self.assertEqual(self.status(body), 'pending')

    def test_transformed_gate_uses_read_only_helper_only_when_supported(self):
        spec = importlib.util.spec_from_file_location('entry_builder', ROOT / 'scripts/build-plugin.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        upstream, _ = builder.read_upstream()
        tree = builder.transform(upstream)
        gates = [path for path, (data, _) in tree.items()
                 if b'HANDOFF_CHECK="${SCRIPT_DIR}/document-handoff-check.sh"' in data]
        self.assertTrue(gates)
        for path in gates:
            helper = str(Path(path).parent / 'document-handoff-check.sh')
            self.assertIn(helper, tree)
            text = tree[path][0].decode()
            self.assertIn('PWF_GATE_CAP', text)
            self.assertIn('documentation handoff pending', text)
        self.assertTrue(any(path.endswith('/scripts/check-complete.sh') and path not in gates
                            for path in tree))

    def test_all_skill_variants_explain_the_hook_contract(self):
        spec = importlib.util.spec_from_file_location('entry_builder', ROOT / 'scripts/build-plugin.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        upstream, _ = builder.read_upstream()
        tree = builder.transform(upstream)
        for path, (data, _) in tree.items():
            if not path.endswith('/SKILL.md'):
                continue
            with self.subTest(path=path):
                text = data.decode()
                self.assertIn('Documentation Handoff', text)
                self.assertIn('planweft-docs-status', text)
                self.assertIn('compatibility', text)
                self.assertIn('troubleshooting interfaces', text)
                self.assertIn('Default advisory mode', text)
                self.assertIn('blocks for document handoff', text)

    def test_existing_smart_plan_view_keeps_chinese_goal_phase_and_next_step(self):
        spec = importlib.util.spec_from_file_location('entry_builder', ROOT / 'scripts/build-plugin.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        upstream, _ = builder.read_upstream()
        tree = builder.transform(upstream)
        with tempfile.TemporaryDirectory(prefix='pw-smart-plan-') as directory:
            helper = Path(directory) / 'inject-plan.py'
            helper.write_bytes(tree['scripts/inject-plan.py'][0])
            module_spec = importlib.util.spec_from_file_location('inject_plan', helper)
            inject = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(inject)
            history = '\n'.join('- 历史记录 ' + str(index) for index in range(100))
            plan = ('# Task Plan\n\n## Goal\n中文目标和验证限制必须保留。\n\n'
                    '## Current Phase\n阶段二正在执行。\n\n## Phases\n### Phase 2: 验证\n'
                    '- **Status:** in_progress\n\n## Next Step\n完成文档交接。\n\n'
                    + history + '\n').encode()
            view = inject.smart_plan_extract(plan).decode()
            for value in ('中文目标和验证限制必须保留。', '阶段二正在执行。', '完成文档交接。'):
                self.assertIn(value, view)


if __name__ == '__main__':
    unittest.main()
