# -*- coding: utf-8 -*-
"""
analysis.py
===========
وحدة التحليل التنبؤي وتحليلات زمن الاستجابة في منصة بَيَان | BAYAN.

جميع النماذج هنا نماذج رياضية بسيطة (نمو أسي/خطي) مطبّقة على بيانات
تجريبية (Mock Data)، ولا تمثل نماذج تنبؤ إنتاجية حقيقية.
"""

import pandas as pd
import numpy as np


def predict_spread(current_reach: float, growth_rate_pct_per_hour: float, hours_list=(6, 12, 24)) -> dict:
    """
    يتنبأ بحجم الانتشار خلال الساعات القادمة باستخدام نموذج نمو أسي مبسّط:
        reach(t) = current_reach * (1 + growth_rate/100) ** t
    مع تخفيف تدريجي بسيط لمعدل النمو مع الوقت (تشبّع طبيعي للانتشار).
    """
    predictions = {}
    for h in hours_list:
        # تخفيف النمو تدريجيًا كل 6 ساعات بنسبة 8% لمحاكاة التشبّع الطبيعي
        damping_periods = h / 6
        effective_rate = growth_rate_pct_per_hour * (0.92 ** damping_periods)
        predicted = current_reach * ((1 + effective_rate / 100) ** h)
        predictions[h] = int(predicted)
    return predictions


def optimal_intervention_window(growth_rate_pct_per_hour: float, risk_score: float) -> str:
    """
    يحدد نافذة التدخل المثلى المقترحة استنادًا إلى سرعة الانتشار ودرجة الخطورة.
    كلما ارتفعت السرعة والخطورة، كانت النافذة الزمنية المقترحة أضيق.
    """
    urgency_index = (growth_rate_pct_per_hour / 30 * 0.6) + (risk_score / 100 * 0.4)
    if urgency_index >= 0.75:
        return "خلال الساعة القادمة"
    elif urgency_index >= 0.55:
        return "خلال الساعتين القادمتين"
    elif urgency_index >= 0.35:
        return "خلال 6 ساعات"
    else:
        return "خلال 24 ساعة"


def build_spread_timeseries(current_reach: float, growth_rate_pct_per_hour: float,
                             total_hours: int = 24, step: int = 2) -> pd.DataFrame:
    """يبني سلسلة زمنية لمنحنى الانتشار المتوقع (Actual vs Predicted) للرسم البياني."""
    hours = list(range(0, total_hours + 1, step))
    predicted = []
    for h in hours:
        damping_periods = h / 6
        effective_rate = growth_rate_pct_per_hour * (0.92 ** damping_periods)
        predicted.append(current_reach * ((1 + effective_rate / 100) ** h))

    # "الفعلي" هنا محاكاة لأثر تدخل افتراضي مبكر يخفّض معدل النمو بعد الساعة 6
    actual = []
    for h in hours:
        if h <= 6:
            damping_periods = h / 6
            effective_rate = growth_rate_pct_per_hour * (0.92 ** damping_periods)
            actual.append(current_reach * ((1 + effective_rate / 100) ** h))
        else:
            base_at_6 = actual[hours.index(6)] if 6 in hours else current_reach
            post_response_rate = growth_rate_pct_per_hour * 0.25  # بعد الاستجابة الرسمية
            actual.append(base_at_6 * ((1 + post_response_rate / 100) ** (h - 6)))

    return pd.DataFrame({"hour": hours, "predicted": predicted, "actual": actual})


def extract_claim(claim: dict) -> dict:
    """
    طبقة محاكاة الذكاء الاصطناعي - استخراج الادعاء (Claim Extraction).
    في هذا الـ Prototype يتم استخلاص العناصر البنيوية من بيانات الحالة
    المخزّنة (Mock Data) بدلًا من نموذج NLP فعلي، مع الحفاظ على نفس شكل
    المخرجات الذي سينتجه نموذج حقيقي مستقبلًا.
    """
    return {
        "claim": claim.get("content", ""),
        "agency": claim.get("agency_name", claim.get("agency", "")),
        "service": claim.get("service", ""),
        "claim_type": claim.get("claim_type", ""),
        "mentioned_date": claim.get("mentioned_date", ""),
        "entities": [claim.get("agency_name", claim.get("agency", "")), claim.get("service", "")],
    }


def classify_claim(claim: dict) -> dict:
    """طبقة محاكاة تصنيف نوع الادعاء استنادًا إلى البيانات المخزّنة."""
    return {
        "claim_type": claim.get("claim_type", "غير متحقق"),
        "confidence": float(claim.get("confidence", 0)),
    }


VERIFICATION_REASONS = {
    "معلومات مضللة": [
        "لا يوجد إعلان أو تعميم رسمي يدعم الادعاء المتداول.",
        "يوجد مصدر رسمي حديث يتعارض بشكل مباشر مع مضمون الادعاء.",
        "نمط صياغة المحتوى يحاكي التعميمات الرسمية دون أن يكون صادرًا عنها.",
    ],
    "محتوى منتحل": [
        "الحساب أو المصدر الناشر غير مدرج ضمن القائمة الرسمية المعتمدة.",
        "الهوية البصرية المستخدمة لا تطابق دليل الهوية الرسمي بدقة.",
        "لا يوجد أي إعلان مطابق في الأرشيف الرسمي للجهة.",
    ],
    "معلومة قديمة": [
        "تاريخ المحتوى الأصلي لا يتوافق مع آخر تحديث رسمي.",
        "المصدر الذي استند إليه المنشور يعود لفترة سابقة منتهية الصلاحية.",
    ],
    "خارج السياق": [
        "المحتوى صحيح في أصله لكنه يُعرض دون السياق الزمني أو الشرطي الكامل.",
        "يوجد تعميم رسمي أحدث يوضّح النطاق الفعلي للمعلومة.",
    ],
    "غير متحقق": [
        "لم يتم العثور على مصدر رسمي كافٍ لتأكيد أو نفي الادعاء حتى الآن.",
        "الانتشار الحالي محدود، وتستمر عملية جمع الأدلة.",
    ],
    "معلومات غير صحيحة": [
        "البيانات الرسمية المحدثة تناقض تفاصيل الادعاء المتداول.",
        "لا يوجد أي أساس رسمي للأرقام أو التفاصيل المذكورة في المحتوى.",
    ],
    "صحيح": [
        "المحتوى مطابق تمامًا لما هو منشور رسميًا.",
        "لا يوجد أي تعارض مع المصادر الرسمية المعتمدة.",
    ],
}


def verify_claim(claim: dict) -> dict:
    """
    طبقة محاكاة التحقق (Verification Engine) - ترجع حالة التحقق ودرجة
    الثقة وأسباب التصنيف (Explainable Reasons) بناءً على نوع الادعاء
    المخزّن في البيانات التجريبية.
    """
    claim_type = claim.get("claim_type", "غير متحقق")
    reasons = VERIFICATION_REASONS.get(claim_type, VERIFICATION_REASONS["غير متحقق"])
    return {
        "status": claim_type,
        "confidence": float(claim.get("confidence", 0)),
        "reasons": reasons,
    }


def response_time_breakdown(events_df: pd.DataFrame) -> dict:
    """
    يحسب زمن كل مرحلة من مراحل دورة الاستجابة بالدقائق، بناءً على الفروقات
    الزمنية بين الأحداث المسجّلة في events.csv لحالة معينة.
    """
    if events_df.empty:
        return {}

    events_df = events_df.copy()
    events_df["timestamp"] = pd.to_datetime(events_df["timestamp"])
    events_df = events_df.sort_values("timestamp").reset_index(drop=True)

    def find_time(event_name):
        row = events_df[events_df["event"] == event_name]
        return row.iloc[0]["timestamp"] if not row.empty else None

    detection = find_time("تم الرصد")
    verification = find_time("اكتمال التحقق")
    risk = find_time("حساب Risk Score")
    draft = find_time("توليد المسودة")
    approval = find_time("اعتماد بشري")
    publication = find_time("نشر رسمي")

    def diff_minutes(t1, t2):
        if t1 is None or t2 is None:
            return None
        return round((t2 - t1).total_seconds() / 60, 1)

    return {
        "detection_to_verification": diff_minutes(detection, verification),
        "verification_to_draft": diff_minutes(verification, draft),
        "draft_to_approval": diff_minutes(draft, approval),
        "approval_to_publication": diff_minutes(approval, publication),
        "total": diff_minutes(detection, publication) or diff_minutes(detection, events_df["timestamp"].max()),
    }


BASELINE_RESPONSE_MINUTES = 180  # سيناريو محاكاة: المتوسط التقليدي دون منصة بَيَان


def compute_reduction_vs_baseline(bayan_minutes: float) -> dict:
    """يقارن زمن الاستجابة بمساعدة بَيَان بسيناريو أساس محاكى (Baseline)."""
    if bayan_minutes is None or bayan_minutes <= 0:
        bayan_minutes = BASELINE_RESPONSE_MINUTES * 0.05
    reduction_pct = round((1 - (bayan_minutes / BASELINE_RESPONSE_MINUTES)) * 100, 1)
    return {
        "baseline_minutes": BASELINE_RESPONSE_MINUTES,
        "bayan_minutes": round(bayan_minutes, 1),
        "reduction_pct": max(0, reduction_pct),
    }
