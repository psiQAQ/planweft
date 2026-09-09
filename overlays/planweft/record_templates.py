"""Build-time record patches; never rewrite an existing project's documents.

The pinned upstream has both Markdown templates and initializer here-docs.
Patch both surfaces, preserving their language, timestamps and test/error logs.
Only task_plan.md owns live phase state; findings are observations with a time.
"""
import json
from pathlib import PurePosixPath
import re


LOCALES = {
    'en': {
        'phase': 'Phase', 'current': 'Current Status', 'session': 'Session record',
        'work': 'Recorded work', 'reboot': '5-Question Reboot Check',
        'findings': 'Findings & Decisions',
        'live': 'Record dated actions and results here. Read the goal, current phase and next action only in [task_plan.md](task_plan.md); do not maintain a second live status.',
        'observations': 'Give each implementation observation its source and observation time or revision (before a change or after verification). Preserve earlier findings; append a dated correction or superseding evidence when behavior changes. Do not present a pre-change observation as the current implementation.',
    },
    'zh': {
        'phase': '阶段', 'current': '当前状态', 'session': '会话记录',
        'work': '已记录的工作', 'reboot': '五问重启检查', 'findings': '发现与决策',
        'live': '在此记录带日期的操作与结果。目标、当前阶段和下一步只以 [task_plan.md](task_plan.md) 为准，不维护第二份动态状态。',
        'observations': '每项实现观察注明来源及观察时点或修订（修改前或验证后）。保留早期发现；行为变化后追加带日期的更正或替代证据，不把修改前的观察称为当前实现。',
    },
    'zht': {
        'phase': '階段', 'current': '目前狀態', 'session': '會話記錄',
        'work': '已記錄的工作', 'reboot': '五問重啟檢查', 'findings': '發現與決策',
        'live': '在此記錄附日期的操作與結果。目標、目前階段及下一步僅以 [task_plan.md](task_plan.md) 為準，不維護第二份動態狀態。',
        'observations': '每項實作觀察註明來源及觀察時間或修訂（修改前或驗證後）。保留早期發現；行為改變後追加附日期的更正或替代證據，不將修改前的觀察稱為目前實作。',
    },
    'de': {
        'phase': 'Phase', 'current': 'Aktueller Status', 'session': 'Sitzungsprotokoll',
        'work': 'Protokollierte Arbeit', 'reboot': '5-Fragen-Neustartprüfung',
        'findings': 'Erkenntnisse & Entscheidungen', 'template_findings': 'Ergebnisse & Entscheidungen',
        'live': 'Hier stehen datierte Aktionen und Ergebnisse. Ziel, aktuelle Phase und nächsten Schritt nur in [task_plan.md](task_plan.md) nachlesen; keinen zweiten laufenden Status pflegen.',
        'observations': 'Für jede Beobachtung zur Implementierung Quelle und Zeitpunkt oder Revision angeben (vor einer Änderung oder nach der Prüfung). Frühere Erkenntnisse erhalten und bei Änderungen eine datierte Korrektur oder neue Evidenz ergänzen. Frühere Beobachtungen nicht als aktuelle Implementierung darstellen.',
    },
    'es': {
        'phase': 'Fase', 'current': 'Estado Actual', 'session': 'Registro de sesión',
        'work': 'Trabajo registrado', 'reboot': 'Prueba de Reinicio de 5 Preguntas',
        'findings': 'Hallazgos y Decisiones',
        'live': 'Registra aquí acciones y resultados con fecha. Consulta el objetivo, la fase actual y el siguiente paso solo en [task_plan.md](task_plan.md); no mantengas otro estado dinámico.',
        'observations': 'Indica la fuente y la fecha o revisión de cada observación de implementación (antes del cambio o después de verificarlo). Conserva los hallazgos anteriores y añade correcciones o evidencia posterior con fecha cuando cambie el comportamiento. No presentes una observación anterior al cambio como implementación actual.',
    },
    'ar': {
        'phase': 'المرحلة', 'current': 'الحالة الحالية', 'session': 'سجل الجلسة',
        'work': 'العمل المسجل', 'reboot': 'اختبار إعادة التشغيل المكون من 5 أسئلة',
        'findings': 'الاكتشافات والقرارات', 'template_findings': 'النتائج والقرارات',
        'live': 'سجّل هنا الإجراءات والنتائج مع تواريخها. اقرأ الهدف والمرحلة الحالية والخطوة التالية فقط من [task_plan.md](task_plan.md)، ولا تحتفظ بحالة حالية ثانية.',
        'observations': 'اذكر مصدر كل ملاحظة عن التنفيذ ووقتها أو مراجعتها (قبل التغيير أو بعد التحقق). احتفظ بالنتائج السابقة وأضف تصحيحًا مؤرخًا أو دليلًا أحدث عند تغير السلوك. لا تعرض ملاحظة سابقة للتغيير على أنها التنفيذ الحالي.',
    },
}


def replace(text, old, new, count, label):
    if text.count(old) != count:
        raise ValueError('Upstream record shape changed: ' + label)
    return text.replace(old, new)


def progress_template(text, words):
    phases = list(re.finditer(r'^### ' + re.escape(words['phase']) + r' [12][:：][^\n]*\n', text, re.M))
    if len(phases) != 2:
        raise ValueError('Upstream progress phase placeholders changed')
    following = re.search(r'^## ', text[phases[1].end():], re.M)
    if not following:
        raise ValueError('Upstream progress test section missing')
    stop = phases[1].end() + following.start()
    states = re.findall(r'^- \*\*[^\n]+\*\* (in_progress|pending)\s*$',
                        text[phases[0].start():stop], re.M)
    if states != ['in_progress', 'pending']:
        raise ValueError('Upstream progress status placeholders changed')
    body = text[phases[0].end():phases[1].start()]
    # Keep the first event's actions, timestamp and files, not live phase flags
    # or instructions to maintain them. Drop the unstarted second placeholder.
    body = '\n'.join(line for line in body.splitlines()
                     if not any(token in line for token in ('in_progress', '`pending`', '`complete`'))).strip()
    text = text[:phases[0].start()] + '### ' + words['work'] + '\n\n' + body + '\n\n' + text[stop:]
    heading = '## ' + words['reboot'] + '\n'
    if text.count(heading) != 1:
        raise ValueError('Upstream progress reboot section changed')
    before, tail = text.split(heading)
    table_start = tail.find('|')
    if table_start < 0:
        raise ValueError('Upstream progress reboot table missing')
    rows = tail[table_start:].splitlines()
    table = [i for i, line in enumerate(rows) if line.startswith('|')]
    if len(table) != 7:
        raise ValueError('Upstream progress reboot questions changed')
    for i in table[2:5]:
        cells = rows[i].split('|')
        if len(cells) != 4:
            raise ValueError('Upstream progress reboot answer shape changed')
        cells[2] = ' [task_plan.md](task_plan.md) '
        rows[i] = '|'.join(cells)
    return before + heading + '\n' + words['live'] + '\n\n' + '\n'.join(rows) + '\n'


def transform(path, text):
    """Apply guarded patches after identity mapping and before append overlays."""
    if path == 'tests/test_template_transparency.py':
        # Preserve the raw upstream regression separately. Only these two
        # progress placeholders intentionally differ in the local contract.
        for old, new in [('"### Phase 1: [Title]"', '"### Recorded work"'),
                         ('"### Phase 2: [Title]"', '"[task_plan.md](task_plan.md)"')]:
            text=replace(text,old,new,1,'progress transparency contract')
        return text
    matched = re.search(r'/i18n/project-docs-([^/]+)/', '/' + path)
    locale = matched[1] if matched else 'en'
    words = LOCALES[locale]
    name = PurePosixPath(path).name
    if '/templates/' in '/' + path:
        if name == 'progress.md':
            text = progress_template(text, words)
        elif name in {'findings.md', 'analytics_findings.md'}:
            title = '# ' + words.get('template_findings', words['findings']) + '\n'
            text = replace(text, title, title + '\n' + words['observations'] + '\n', 1, path)
    if name in {'init-session.sh', 'init-session.ps1'}:
        # No backticks/$ in inserted prose: both Bash unquoted here-docs and
        # PowerShell expandable here-strings must emit literal Markdown.
        # These two pinned adapters and localized helpers have default-only
        # initializers. Other English helpers also carry the analytics branch.
        default_only = locale != 'en' or path.startswith(('.mastracode/', '.opencode/'))
        expected = 1 if default_only else 2
        pattern = r'^### ' + re.escape(words['current']) + r'\n- \*\*[^\n]+\*\* 1 - [^\n]+\n'
        text, count = re.subn(pattern, '### ' + words['session'] + '\n' + words['live'] + '\n', text, flags=re.M)
        if count != expected:
            raise ValueError('Upstream initializer progress blocks changed: ' + path)
        title = '# ' + words['findings'] + '\n'
        text = replace(text, title, title + '\n' + words['observations'] + '\n', 1, path)
    if path == '.opencode/packages/opencode-planweft/src/core.ts':
        for title, guidance in [('Findings & Decisions', words['observations']), ('Progress Log', words['live'])]:
            old = '    ' + json.dumps('# ' + title) + ',\n    "",\n'
            new = old + '    ' + json.dumps(guidance) + ',\n    "",\n'
            text = replace(text, old, new, 1, 'OpenCode fallback ' + title)
    return text
