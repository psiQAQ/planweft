"""DSH native bundle contracts; runtime probes remain separate evidence."""
import json
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
DSH = ROOT / 'dist/dsh/planweft'

class DshDistributionTest(unittest.TestCase):
    def test_single_npm_and_standalone_native_bundle_select_same_adapter(self):
        package = json.loads((ROOT / 'package.json').read_text())
        native = json.loads((DSH / 'package.json').read_text())
        self.assertEqual((ROOT / package['exports']['./dsh']).read_bytes(), (DSH / native['exports']['./dsh']).read_bytes())
        self.assertEqual((ROOT / package['dsh']['bundle']['patch']).read_bytes(), (DSH / native['dsh']['bundle']['patch']).read_bytes())
        patch=(DSH / native['dsh']['bundle']['patch'])
        entry=next(line.split('name:',1)[1].strip() for line in patch.read_text().splitlines() if 'name:' in line)
        self.assertTrue(entry.startswith('./'), 'DSH must anchor the module to the bundle patch')
        self.assertEqual((patch.parent / entry).resolve(), (DSH / native['exports']['./dsh']).resolve())
        for name in ['@deepseek-ai/dsh-hooks-claude-code', '@deepseek-ai/dsh-skill-filesystem']:
            self.assertEqual(package['dependencies'][name], '0.1.2-rc.1')
            self.assertEqual(native['dependencies'][name], package['dependencies'][name])
        self.assertEqual(package['exports']['.']['import'], './dist/opencode/planweft/dist/index.js')

    def test_only_supported_bridge_events_and_one_skill_are_distributed(self):
        config = json.loads((DSH / 'hooks/hooks.json').read_text())
        self.assertEqual(set(config['hooks']), {'SessionStart', 'UserPromptSubmit', 'PostToolUse', 'Stop'})
        for groups in config['hooks'].values():
            for group in groups:
                for hook in group['hooks']:
                    self.assertIn('/hooks/dsh-hook.sh', hook['command'])
                    self.assertNotIn('permissionDecision', hook)
        self.assertEqual([p.relative_to(DSH).as_posix() for p in DSH.rglob('SKILL.md')], ['skills/project-docs/SKILL.md'])
        self.assertIn('export CLAUDE_PLUGIN_ROOT', (DSH / 'hooks/dsh-hook.sh').read_text())
        self.assertNotIn('hooks:', (DSH / 'skills/project-docs/SKILL.md').read_text().split('---')[1])

if __name__ == '__main__': unittest.main()
