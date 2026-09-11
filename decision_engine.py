# -*- coding: utf-8 -*-
"""
decision_engine.py
===================
محرك القرار الذكي في منصة بَيَان | BAYAN.

يحوّل نتائج التحقق والمخاطر والتنبؤ إلى توصية استجابة واضحة قابلة
للتفسير (Explainable)، مع الإبقاء على القرار النهائي بيد الإنسان دائمًا
(Human-in-the-Loop) - لا يقوم الذكاء الاصطناعي بالنشر تلقائيًا أبدًا.
"""

from utils.scoring import compute_risk_score, compute_risk_breakdown

DECISION_OPTIONS = [
    {
        "key": "no_action",
        "title": "لا تدخل",
        "impact": "منخفض",
        "speed": "غير منطبق",
        "risk_of_inaction": "منخفض",
    },
    {
        "key": "monitor",
        "title": "مراقبة",
        "impact": "منخفض إلى متوسط",
        "speed": "غير عاجل",
        "risk_of_inaction": "منخفض إلى متوسط",
    },
    {
        "key": "short_clarification",
        "title": "توضيح رسمي مختصر",
        "impact": "متوسط إلى مرتفع",
        "speed": "سريع (دقائق)",
        "risk_of_inaction": "متوسط",
    },
    {
        "key": "official_statement",
        "title": "بيان رسمي",
        "impact": "مرتفع",
        "speed": "متوسط",
        "risk_of_inaction": "مرتفع",
    },
    {
        "key": "update_and_clarify",
        "title": "تحديث صفحة الخدمة + توضيح",
        "impact": "مرتفع جدًا",
        "speed": "متوسط",
        "risk_of_inaction": "مرتفع",
    },
    {
        "key": "internal_escalation",
        "title": "تصعيد داخلي",
        "impact": "يعتمد على المتابعة",
        "speed": "فوري داخليًا",
        "risk_of_inaction": "مرتفع (لحالات الانتحال والأمن)",
    },
]


def recommend_action(claim: dict) -> dict:
    """
    يحدد التوصية الأنسب استنادًا إلى: درجة الخطورة، نوع الادعاء، ومعدل
    الانتشار. المنطق قائم على قواعد واضحة (Rule-Based) وليس عشوائيًا.
    """
    risk_score = compute_risk_score(claim)
    claim_type = claim.get("claim_type", "")
    growth_rate = float(claim.get("growth_rate", 0))

    reasons = []

    if claim_type == "محتوى منتحل":
        key = "internal_escalation"
        reasons.append("المحتوى ينتحل صفة جهة رسمية، ما يستدعي تصعيدًا داخليًا فوريًا.")
        if risk_score >= 70:
            reasons.append("درجة الخطورة المرتفعة تستدعي أيضًا إصدار بيان توعوي مصاحب.")
    elif risk_score >= 85:
        key = "official_statement" if growth_rate >= 20 else "update_and_clarify"
        reasons.append("درجة الخطورة في المستوى الحرج، ما يستدعي استجابة رسمية موسّعة.")
    elif risk_score >= 60:
        key = "short_clarification"
        reasons.append("درجة الخطورة مرتفعة مع انتشار متصاعد، ويُكتفى بتوضيح رسمي مختصر وسريع.")
    elif risk_score >= 31:
        key = "monitor"
        reasons.append("درجة الخطورة متوسطة؛ يُكتفى بالمراقبة الحالية مع الاستعداد للتصعيد.")
    else:
        key = "no_action"
        reasons.append("درجة الخطورة منخفضة ولا تستدعي تدخلًا حاليًا.")

    if growth_rate >= 20:
        reasons.append("معدل الانتشار مرتفع، ما يقلّص نافذة التدخل الآمنة.")
    breakdown = compute_risk_breakdown(claim)
    if breakdown["official_conflict"]["points"] >= 15:
        reasons.append("يوجد تعارض واضح بين الادعاء المتداول والمصدر الرسمي.")
    if breakdown["service_sensitivity"]["points"] >= 15:
        reasons.append("حساسية الخدمة المعنية مرتفعة لدى الجمهور المستهدف.")

    option = next((o for o in DECISION_OPTIONS if o["key"] == key), DECISION_OPTIONS[0])

    what_could_change = (
        "قد تتغير التوصية إذا ظهر مصدر رسمي جديد يوثّق الادعاء، أو انخفض معدل "
        "الانتشار بشكل ملحوظ، أو تراجعت درجة الثقة في التصنيف الحالي."
    )

    return {
        "option": option,
        "reasons": reasons,
        "what_could_change": what_could_change,
        "risk_score": risk_score,
    }



