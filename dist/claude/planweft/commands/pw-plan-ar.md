---
description: "بدء تخطيط الملفات بنمط Manus. إنشاء task_plan.md و findings.md و progress.md للمهام المعقدة."
disable-model-invocation: true
---

Follow project-docs scope rules: read-only requests and host plan mode do not initialize or update project files. Resolve the task-owned plan first; never create a competing root plan.

اقرأ نص المهارة العربية من أول مسار موجود من هذين المسارين ونفّذ تعليماته بدقة:

- `$HOME/.claude/skills/project-docs-ar/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/i18n/project-docs-ar/SKILL.md`

إذا لم يكن أي من المسارين موجودًا، استدعِ مهارة planweft:project-docs وتابع العمل باللغة العربية.

إذا لم تكن ملفات التخطيط الثلاثة موجودة في مجلد المشروع الحالي، قم بإنشائها:
- task_plan.md — للمراحل والتقدم والقرارات
- findings.md — للبحث والاكتشافات
- progress.md — لسجل الجلسة

ثم ارشد المستخدم خلال سير عمل التخطيط. جميع ملفات التخطيط يجب أن تكون باللغة العربية.

تبقى علامات الحالة بالإنجليزية حرفيًا (`**Status:** in_progress` و `**Status:** complete`) لأن `check-complete.sh` يبحث عنها باستخدام `grep -F`، وترجمتها تُعطّل بوابة الإكمال.
