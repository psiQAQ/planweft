# خطة المهمة: [وصف مختصر]

استخدم هذا الملف بوصفه خارطة الطريق المستمرة للمهمة. أنشئه قبل العمل المعقد، وحافظ على تحديثه كلما تغيرت المراحل.

## الهدف

صف النتيجة النهائية المقصودة في جملة واحدة واضحة.

[جملة واحدة تصف الحالة النهائية]

## الخطوة التالية

سجّل الإجراء الوحيد الذي يجب تنفيذه تاليًا. حدّثه كلما تغيرت المرحلة النشطة أو الإجراء الفوري.

[الإجراء التالي الوحيد. حدّثه كلما تغيرت حالة المرحلة.]

## المرحلة الحالية

اذكر المرحلة التي يجري العمل عليها الآن.

المرحلة 1

## المراحل

قسّم المهمة إلى ثلاث مراحل قابلة للتحقق أو أكثر. استخدم فقط `pending` أو `in_progress` أو `complete` للحالة، وحدّث القيمة كلما تقدم العمل.

### المرحلة 1: المتطلبات والاكتشاف

- [ ] فهم نية المستخدم
- [ ] تحديد القيود والمتطلبات
- [ ] توثيق النتائج في findings.md
- **الحالة:** in_progress

### المرحلة 2: التخطيط والهيكلة

- [ ] تحديد المنهج التقني
- [ ] إنشاء هيكل المشروع إذا لزم الأمر
- [ ] توثيق القرارات مع مبرراتها
- **الحالة:** pending

### المرحلة 3: التنفيذ

- [ ] تنفيذ الخطة خطوة بخطوة
- [ ] كتابة التعليمات البرمجية في الملفات قبل التنفيذ
- [ ] الاختبار بشكل تدريجي
- **الحالة:** pending

### المرحلة 4: الاختبار والتحقق

- [ ] التحقق من تحقيق جميع المتطلبات
- [ ] توثيق نتائج الاختبار في progress.md
- [ ] إصلاح أي مشكلات مكتشفة
- **الحالة:** pending

### المرحلة 5: التسليم

- [ ] مراجعة جميع ملفات المخرجات
- [ ] التأكد من اكتمال المخرجات
- [ ] التسليم للمستخدم
- **الحالة:** pending

## الأسئلة الرئيسية

سجّل الأسئلة المهمة، واستبدلها بالإجابات عندما تُحسم.

1. [سؤال للإجابة عنه]
2. [سؤال للإجابة عنه]

## القرارات المتخذة

سجّل القرارات المهمة وسبب كل قرار.

| القرار | المبررات |
|--------|----------|
|        |          |

## الأخطاء التي تمت مواجهتها

سجّل كل خطأ مميز ورقم المحاولة والحل. غيّر النهج قبل إعادة محاولة إجراء فاشل.

| الخطأ | المحاولة | الحل |
|-------|----------|------|
|       | 1        |      |

## ملاحظات

- حدّث حالة المرحلة مع تقدم العمل: من `pending` إلى `in_progress` ثم `complete`.
- أعد قراءة الهدف والخطوة التالية قبل القرارات المهمة.
- سجّل الأخطاء فورًا كي لا تتكرر الأساليب الفاشلة.

## Scope and acceptance evidence

Keep only fields useful to this task. Link existing approved requirements instead of copying them into a second specification. This selected plan is the single dynamic task-status source.

- Scope source: keep authorized targets, prohibited reads/writes and verification limits with their actual instruction sources in the existing Goal section within the first 30 lines; do not duplicate live boundaries here.
- Success criteria and requirement source: [observable result and exact reference]
- Verification evidence: [progress entry or reproduction record; actual Passed, Failed or Not Run]
- Stable design records: [affected specification or ADR, only if needed]
- Plan owner and worker record locations: [owner and assigned records, when using multiple agents]

## Handoff evidence

Keep the current next action in `## Next Step` above, rather than duplicating a live task list here.

- Remaining blocker or approval decision: [concrete missing input, or none]
- Independent evidence review: [record and disposition, or Not Run with reason]
- Fresh-reader check: [record and discrepancy resolution, or Not Run with reason]
- Active-plan relocation: not supported; record an in-place closure or explicitly authorized archive-index update only when applicable

Attestation records bytes, not approval. Checked phases or a gate decision do not prove that acceptance criteria passed.

## Documentation Handoff

<!-- planweft-docs-status: pending -->

- Documents considered: [affected existing documents, or none]
- Rationale / evidence: [why documentation is needed or not required]
- Next action: [authorized update, verification, or closure action]

The marker has exactly one value: `pending`, `not_required`, or `complete`. It is a
read-only Hook input and not a second task status. Missing, duplicate or malformed
markers remain pending; do not set `complete` before the actual documentation result
is recorded.
