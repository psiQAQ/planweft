# سجل التقدم

استخدم هذا الملف سجلًا زمنيًا مستمرًا لما نُفّذ وما حدث. حدّثه عند اكتمال كل مرحلة، وعند ظهور خطأ، وكلما احتجت إلى حفظ دليل يساعد على استئناف العمل.

## الجلسة: [التاريخ]

استبدل الحقل بتاريخ جلسة العمل بصيغة واضحة، مثل `2026-01-15`.

### المرحلة 1: [العنوان]

سجّل إجراءات هذه المرحلة والملفات المتأثرة أثناء العمل أو فور اكتماله.

- **الحالة:** in_progress
- **بدأت في:** [الطابع الزمني]
- الإجراءات المتخذة:
  -
- الملفات التي تم إنشاؤها/تعديلها:
  -

استخدم للحالة إحدى القيم `pending` أو `in_progress` أو `complete`، وسجّل وقت البدء بصيغة قابلة للقراءة.

### المرحلة 2: [العنوان]

استخدم البنية نفسها لكل مرحلة إضافية كي يبقى السجل سهل المتابعة.

- **الحالة:** pending
- الإجراءات المتخذة:
  -
- الملفات التي تم إنشاؤها/تعديلها:
  -

## نتائج الاختبار

سجّل الاختبارات المنفذة ومدخلاتها والنتيجة المتوقعة والنتيجة الفعلية والحالة.

| الاختبار | المدخلات | المتوقع | الفعلي | الحالة |
|------|-------|----------|--------|--------|
|      |       |          |        |        |

## سجل الأخطاء

أضف كل خطأ فور حدوثه، حتى إذا أُصلح بسرعة. احتفظ برقم المحاولة والحل كي لا يتكرر النهج الفاشل.

| الطابع الزمني | الخطأ | المحاولة | الحل |
|-----------|-------|---------|------------|
|           |       | 1       |            |

## اختبار إعادة التشغيل المكون من 5 أسئلة

استخدم الأسئلة التالية للتحقق من أن سياق المهمة قابل للاستئناف. استمد الإجابات من ملفات التخطيط الحالية، وحدّثها عند تغير الحالة.

| السؤال | الإجابة |
|----------|--------|
| أين أنا؟ | المرحلة X |
| إلى أين أنا ذاهب؟ | المراحل المتبقية |
| ما الهدف؟ | [بيان الهدف] |
| ماذا تعلمت؟ | راجع findings.md |
| ماذا فعلت؟ | راجع أعلاه |

---

*حدّث هذا السجل بعد إكمال كل مرحلة أو مواجهة خطأ، وأضف الطوابع الزمنية عندما تساعد على تتبع تسلسل الأحداث.*

## Reproducible validation and document maintenance

Use this record for actual events and results. The current phase and next action remain authoritative in the selected `task_plan.md`.

| Command or scenario | Environment or revision | Expected | Observed | Passed / Failed / Not Run and reason |
| --- | --- | --- | --- | --- |

- Affected project documents and reason: [smallest necessary changes, or none]
- Evidence-review findings and owner disposition: [record, or Not Run with reason]
- Fresh-reader findings and correction: [record, or Not Run with reason]
- Remaining validation limits: [missing host, unavailable service or other concrete limit]

Keep actual host runs distinct from static checks and protocol fixtures. Preserve dated historical results; append corrections instead of rewriting past observations.
