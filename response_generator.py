# -*- coding: utf-8 -*-
"""
response_generator.py
======================
مولّد المسودة الرسمية في منصة بَيَان | BAYAN.

يبني مسودة توضيح اعتمادًا فقط على معلومات الحالة والأدلة التجريبية
المتوفرة محليًا - دون أي اتصال فعلي بأي مصدر خارجي أو نموذج لغوي حقيقي.
المسودة الناتجة تبقى دائمًا "مقترحة" ولا يمكن نشرها إلا بعد اعتماد بشري
صريح (Human-in-the-Loop).
"""

CHANNEL_MAP = {
    "محتوى منتحل": "بيان توعوي + تنبيه عبر القناة الرسمية المعتمدة",
    "معلومات مضللة": "توضيح رسمي عبر الحساب الرسمي المعتمد وصفحة الخدمة",
    "معلومات غير صحيحة": "تحديث صفحة الخدمة مع منشور توضيحي مختصر",
    "معلومة قديمة": "منشور تذكيري يوضّح تاريخ آخر تحديث رسمي",
    "خارج السياق": "منشور توضيحي يوضّح السياق الكامل للمعلومة",
    "غير متحقق": "رصد ومتابعة دون نشر حتى اكتمال التحقق",
    "صحيح": "لا حاجة لرد رسمي إضافي",
}

NEGATIVE_TYPES = {"معلومات مضللة", "معلومات غير صحيحة", "محتوى منتحل"}


def generate_response(claim: dict, agency_name: str, evidence_list: list) -> dict:
    """
    يولّد مسودة توضيح رسمي (Generate Response) بالاعتماد فقط على معلومات
    الحالة والأدلة التجريبية المتوفرة.

    المخرجات: Title, Official Statement, Key Facts, Claim Addressed,
    Evidence Used, Recommended Publication Channel.
    """
    service = claim.get("service", "الخدمة المعنية")
    claim_type = claim.get("claim_type", "")
    content = claim.get("content", "")

    title = f"توضيح رسمي بشأن {service}"

    evidence_names = [e.get("source_name", "") for e in evidence_list]
    evidence_summary = "، ".join(evidence_names[:2]) or "التحديثات الرسمية المعتمدة"

    is_negative = claim_type in NEGATIVE_TYPES

    key_facts = [
        f"لا يوجد أي قرار أو تعميم رسمي جديد يؤكد ما تم تداوله بشأن {service}."
        if is_negative
        else f"المعلومة المتداولة عن {service} صحيحة في أصلها وتحتاج لتوضيح السياق الكامل فقط.",
        "البيانات الرسمية المحدثة تؤكد استمرار الوضع الحالي للخدمة دون أي تغيير غير معلن.",
        "يُرجى الاعتماد على القنوات الرسمية المعتمدة فقط للحصول على المعلومات الدقيقة والمحدثة.",
    ]

    statement = (
        f"بالإشارة إلى ما يتم تداوله بشأن {service} لدى {agency_name}، توضّح الجهة المختصة أن "
        f"المعلومة المتداولة {'غير دقيقة ولا تستند إلى أي مصدر رسمي' if is_negative else 'تحتاج إلى توضيح السياق الكامل لها'}، "
        f"استنادًا إلى تحديث رسمي حديث ({evidence_summary}). وتدعو الجهة الجمهور إلى التحقق من "
        f"أي معلومة تخص إجراءاتها وخدماتها عبر القنوات الرسمية المعتمدة حصرًا، وعدم الاعتماد على "
        f"المصادر غير الموثقة."
    )

    return {
        "title": title,
        "statement": statement,
        "key_facts": key_facts,
        "claim_addressed": content,
        "evidence_used": evidence_names,
        "recommended_channel": CHANNEL_MAP.get(claim_type, "القناة الرسمية المعتمدة"),
    }
