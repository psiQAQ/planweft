"""Offline contracts for optional, Skill-only documentation-map guidance."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'overlays/planweft/document-handoff-check.sh'
WORKFLOW = ROOT / 'overlays/planweft/workflow.md'
REFERENCE = ROOT / 'overlays/planweft/references/documentation-map.md'


class DocumentationMapContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('entry_builder', ROOT / 'scripts/build-plugin.py')
        cls.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.builder)
        upstream, _ = cls.builder.read_upstream()
        cls.tree = cls.builder.transform(upstream)

    def test_reference_keeps_navigation_optional_and_bounded(self):
        workflow = WORKFLOW.read_text()
        guide = REFERENCE.read_text()
        for text in (workflow, guide):
            self.assertIn('Documentation Map', text)
            self.assertIn('AGENTS.md', text)
            self.assertIn('CODEX.md', text)
        self.assertIn('Do not create an index or a map unless the user explicitly authorizes', workflow)
        self.assertIn('not a schema, parser input, cache, task-state source, or', guide)
        self.assertIn('`commands/`, `.agents/skills/*/SKILL.md`, and `agents/`', guide)
        self.assertIn('does not expand read or\nwrite permission', guide)

    def test_every_generated_skill_gets_the_same_map_reference(self):
        seen = 0
        for path, (data, _) in self.tree.items():
            if not path.endswith('/SKILL.md'):
                continue
            seen += 1
            reference = str(Path(path).parent / 'references/documentation-map.md')
            with self.subTest(path=path):
                self.assertIn('(references/documentation-map.md)', data.decode())
                self.assertEqual(self.tree[reference][0], REFERENCE.read_bytes())
        self.assertGreater(seen, 1)

    def test_handoff_helper_ignores_map_and_unregistered_layout_fixture(self):
        with tempfile.TemporaryDirectory(prefix='pw-document-map-') as directory:
            project = Path(directory)
            for relative, content in {
                'docs/README.md': '## Documentation Map\n\n| Role | Canonical location |\n| --- | --- |\n| Guide | README.md |\n[CODEX](../CODEX.md)\n',
                'CODEX.md': 'supplementary guide\n',
                '.env': 'SECRET=not-read\n',
                '.codex/config.toml': 'host = "not-read"\n',
                'memory/context.json': '{"cache": true}\n',
                'commands/report.md': 'template only\n',
                '.agents/skills/sample/SKILL.md': 'template only\n',
                'agents/research.md': 'role only\n',
                'output/logs/run.log': 'unselected log\n',
            }.items():
                target = project / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            plan = project / 'task_plan.md'
            plan.write_text('## Documentation Handoff\n\n<!-- planweft-docs-status: complete -->\n'
                            '- Documents considered: docs/README.md\n'
                            '- Rationale / evidence: fixture proves helper is plan-only\n'
                            '- Next action: none\n')
            before = {path.relative_to(project): path.read_bytes() for path in project.rglob('*') if path.is_file()}
            result = subprocess.run(['sh', str(HELPER), str(plan)], cwd=project,
                                    text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), 'complete')
            after = {path.relative_to(project): path.read_bytes() for path in project.rglob('*') if path.is_file()}
            self.assertEqual(after, before)
            self.assertNotIn('Documentation Map', HELPER.read_text())


if __name__ == '__main__':
    unittest.main()
