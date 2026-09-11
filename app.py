
# ===================== BAYAN PROFESSIONAL ENHANCEMENTS =====================
PLOTLY_CONFIG = {
    "responsive": True,
    "displaylogo": False,
    "scrollZoom": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"]
}

def bayan_professional_theme():
    import streamlit as st
    st.markdown("""
    <style>
    :root{
        --bayan-primary:#0B6E4F;
        --bayan-gold:#B8963E;
        --bayan-text:#111827;
        --bayan-card:#FFFFFF;
        --bayan-bg:#F6F8F7;
    }
    @media (prefers-color-scheme: dark){
        :root{
            --bayan-text:#F8FAFC;
            --bayan-card:#1E293B;
            --bayan-bg:#0F172A;
        }
    }
    .alert-critical{
        padding:12px;border-radius:10px;
        background:#FDE7EA;font-weight:bold;margin-bottom:10px;
    }
    </style>
    """, unsafe_allow_html=True)

bayan_professional_theme()

def executive_brief_widget(df):
    import streamlit as st
    try:
        critical = len(df[df["risk_score"] > 80])
        st.markdown("## Executive Brief")
        c1,c2,c3=st.columns(3)
        c1.metric("الحالات الحرجة", critical)
        c2.metric("إجمالي الحالات", len(df))
        c3.metric("جاهزة للقرار", len(df[df["priority_code"].isin(["P1","P2"])]))
    except Exception:
        pass
# ==========================================================================

# -*- coding: utf-8 -*-
"""
scoring.py
==========
محرك حساب الدرجات في منصة بَيَان | BAYAN.

كل الدرجات هنا محسوبة عبر صيغ رياضية ثابتة تعتمد على عوامل مدخلة (Reach،
Growth Rate، Service Sensitivity، Official Conflict، Time Urgency...)
وليست أرقامًا عشوائية. هذا يضمن أن النتائج قابلة للتفسير والتدقيق
(Explainable & Auditable) كما هو مطلوب في تصميم المنصة.
"""

import math

# ---------------------------------------------------------------------------
# أوزان محرك المخاطر (Risk Engine Weights) - يجب أن يكون مجموعها 100%
# ---------------------------------------------------------------------------
RISK_WEIGHTS = {
    "speed": 0.25,               # سرعة الانتشار
    "audience": 0.20,            # حجم الجمهور / الوصول
    "service_sensitivity": 0.20,  # حساسية الخدمة
    "official_conflict": 0.20,   # درجة التعارض مع المصدر الرسمي
    "time_urgency": 0.15,        # قرب الموعد المذكور بالادعاء
}

# سقف الوصول المستخدم في تطبيع محور الجمهور (Reach) على مقياس 0-100
MAX_REACH_REFERENCE = 200_000

# سقف معدل الانتشار (%/ساعة) المستخدم في تطبيع محور السرعة
MAX_GROWTH_REFERENCE = 30.0


def normalize_speed(growth_rate: float) -> float:
    """يحوّل معدل الانتشار (%/ساعة) إلى مقياس 0-100."""
    if growth_rate is None or growth_rate < 0:
        return 0.0
    return min(growth_rate / MAX_GROWTH_REFERENCE, 1.0) * 100


def normalize_audience(reach: float) -> float:
    """يحوّل حجم الوصول (Reach) إلى مقياس 0-100 باستخدام مقياس لوغاريتمي
    لأن انتشار المحتوى لا يتصرف بشكل خطي."""
    if reach is None or reach <= 0:
        return 0.0
    value = math.log10(reach + 1) / math.log10(MAX_REACH_REFERENCE + 1) * 100
    return min(value, 100.0)


def compute_risk_breakdown(claim: dict) -> dict:
    """
    يحسب تفصيل درجة الخطورة (Risk Breakdown) لكل عامل على حدة، بحيث يظهر
    للمستخدم بوضوح كيف تم احتساب الرقم النهائي (Explainable Risk Score).

    المدخلات المتوقعة في claim:
        growth_rate, reach, service_sensitivity, official_conflict, time_urgency
    """
    growth_rate = float(claim.get("growth_rate", 0))
    reach = float(claim.get("reach", 0))
    service_sensitivity = float(claim.get("service_sensitivity", 0))
    official_conflict = float(claim.get("official_conflict", 0))
    time_urgency = float(claim.get("time_urgency", 0))

    speed_norm = normalize_speed(growth_rate)
    audience_norm = normalize_audience(reach)

    speed_points = round(speed_norm * RISK_WEIGHTS["speed"], 1)
    audience_points = round(audience_norm * RISK_WEIGHTS["audience"], 1)
    sensitivity_points = round(service_sensitivity * RISK_WEIGHTS["service_sensitivity"], 1)
    conflict_points = round(official_conflict * RISK_WEIGHTS["official_conflict"], 1)
    urgency_points = round(time_urgency * RISK_WEIGHTS["time_urgency"], 1)

    total = round(
        speed_points + audience_points + sensitivity_points + conflict_points + urgency_points
    )
    total = max(0, min(100, total))

    max_points = {
        "speed": round(100 * RISK_WEIGHTS["speed"]),
        "audience": round(100 * RISK_WEIGHTS["audience"]),
        "service_sensitivity": round(100 * RISK_WEIGHTS["service_sensitivity"]),
        "official_conflict": round(100 * RISK_WEIGHTS["official_conflict"]),
        "time_urgency": round(100 * RISK_WEIGHTS["time_urgency"]),
    }

    return {
        "speed": {"label": "سرعة الانتشار", "points": speed_points, "max": max_points["speed"]},
        "audience": {"label": "حجم الجمهور", "points": audience_points, "max": max_points["audience"]},
        "service_sensitivity": {
            "label": "حساسية الخدمة",
            "points": sensitivity_points,
            "max": max_points["service_sensitivity"],
        },
        "official_conflict": {
            "label": "التعارض مع المصدر الرسمي",
            "points": conflict_points,
            "max": max_points["official_conflict"],
        },
        "time_urgency": {
            "label": "قرب الموعد المذكور",
            "points": urgency_points,
            "max": max_points["time_urgency"],
        },
        "total": total,
    }


def compute_risk_score(claim: dict) -> int:
    """يرجع درجة الخطورة الإجمالية فقط (0-100)."""
    return compute_risk_breakdown(claim)["total"]


def risk_level(score: int) -> dict:
    """يحدد مستوى الخطورة النصي ولونه بناءً على درجة الخطورة."""
    if score <= 30:
        return {"label": "منخفض", "color": "#2E7D32", "css": "success"}
    elif score <= 60:
        return {"label": "متوسط", "color": "#B8860B", "css": "warning"}
    elif score <= 80:
        return {"label": "مرتفع", "color": "#C1440E", "css": "high"}
    else:
        return {"label": "حرج", "color": "#B00020", "css": "critical"}


# ---------------------------------------------------------------------------
# Decision Priority Score - لا يعتمد فقط على Risk Score
# ---------------------------------------------------------------------------
PRIORITY_WEIGHTS = {
    "risk": 0.35,
    "growth_rate": 0.20,
    "service_sensitivity": 0.15,
    "confidence": 0.15,
    "time_urgency": 0.15,
}


def compute_decision_priority(claim: dict) -> dict:
    """
    يحسب أولوية القرار (Decision Priority) اعتمادًا على مزيج من: درجة
    الخطورة، سرعة الانتشار، حساسية الخدمة، الثقة في التصنيف، وقرب الموعد.
    يرجع الدرجة والتصنيف (P1-P4).
    """
    risk_score = compute_risk_score(claim)
    growth_norm = normalize_speed(float(claim.get("growth_rate", 0)))
    service_sensitivity = float(claim.get("service_sensitivity", 0))
    confidence = float(claim.get("confidence", 0))
    time_urgency = float(claim.get("time_urgency", 0))

    priority_score = (
        risk_score * PRIORITY_WEIGHTS["risk"]
        + growth_norm * PRIORITY_WEIGHTS["growth_rate"]
        + service_sensitivity * PRIORITY_WEIGHTS["service_sensitivity"]
        + confidence * PRIORITY_WEIGHTS["confidence"]
        + time_urgency * PRIORITY_WEIGHTS["time_urgency"]
    )
    priority_score = round(max(0, min(100, priority_score)))

    if priority_score >= 80:
        tier = {"code": "P1", "label": "تدخل فوري", "color": "#B00020"}
    elif priority_score >= 60:
        tier = {"code": "P2", "label": "تدخل عاجل", "color": "#C1440E"}
    elif priority_score >= 35:
        tier = {"code": "P3", "label": "مراقبة", "color": "#B8860B"}
    else:
        tier = {"code": "P4", "label": "منخفضة الأولوية", "color": "#2E7D32"}

    return {"score": priority_score, **tier}


# ---------------------------------------------------------------------------
# Response Effectiveness Score
# ---------------------------------------------------------------------------
def compute_response_effectiveness(growth_before: float, growth_after: float,
                                    response_minutes: float, reach_before: float,
                                    reach_after_actual: float, reach_predicted_no_action: float) -> dict:
    """
    يحسب درجة فعالية الاستجابة (0-100) بالاعتماد على:
    1. مقدار انخفاض معدل الانتشار بعد الاستجابة.
    2. مقدار انخفاض الوصول الفعلي مقارنة بالوصول المتوقع دون تدخل.
    3. سرعة الاستجابة (كلما كانت أسرع، كانت الفعالية أعلى).
    """
    growth_reduction_pct = 0.0
    if growth_before > 0:
        growth_reduction_pct = max(0.0, (growth_before - growth_after) / growth_before) * 100

    reach_reduction_pct = 0.0
    if reach_predicted_no_action > 0:
        reach_reduction_pct = max(
            0.0, (reach_predicted_no_action - reach_after_actual) / reach_predicted_no_action
        ) * 100

    # سرعة الاستجابة: كلما قلّت الدقائق زادت النقاط (سقف مرجعي 180 دقيقة = خط الأساس)
    speed_score = max(0.0, min(100.0, (1 - (response_minutes / 180)) * 100))

    effectiveness = (
        growth_reduction_pct * 0.40 + reach_reduction_pct * 0.40 + speed_score * 0.20
    )
    effectiveness = round(max(0, min(100, effectiveness)))

    return {
        "effectiveness": effectiveness,
        "growth_reduction_pct": round(growth_reduction_pct, 1),
        "reach_reduction_pct": round(reach_reduction_pct, 1),
        "speed_score": round(speed_score, 1),
    }


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


# -*- coding: utf-8 -*-
"""
decision_engine.py
===================
محرك القرار الذكي في منصة بَيَان | BAYAN.

يحوّل نتائج التحقق والمخاطر والتنبؤ إلى توصية استجابة واضحة قابلة
للتفسير (Explainable)، مع الإبقاء على القرار النهائي بيد الإنسان دائمًا
(Human-in-the-Loop) - لا يقوم الذكاء الاصطناعي بالنشر تلقائيًا أبدًا.
"""



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


# -*- coding: utf-8 -*-
"""
app.py
======
بَيَان | BAYAN - نموذج أولي (Prototype) لمنصة رصد المعلومات المضللة
المتعلقة بالخدمات الحكومية وتسريع الرد الرسمي.

⚠️ هذا نموذج أولي تجريبي (Prototype) لأغراض العرض في هاكاثون حكومي.
جميع البيانات المستخدمة بيانات محاكاة (Mock Data) ولا يوجد أي اتصال
فعلي بأي مصدر حكومي أو منصة تواصل اجتماعي حقيقية. لا يقوم الذكاء
الاصطناعي بالنشر تلقائيًا في أي مرحلة - القرار والنشر النهائي دائمًا
بيد الموظف المختص (Human-in-the-Loop).

تشغيل المشروع:
    streamlit run app.py
"""

import os
from datetime import datetime

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


import streamlit as st

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"]{
    color:#111827 !important;
}
p, span, label, li, div, h1, h2, h3, h4, h5, h6{
    color:#111827 !important;
}
[data-testid="stSidebar"] *{
    color:white !important;
}
</style>
""", unsafe_allow_html=True)








# =============================================================================
# إعدادات الصفحة العامة
# =============================================================================
st.set_page_config(
    page_title="بَيَان | BAYAN",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ألوان الهوية البصرية للمنصة
COLORS = {
    "primary": "#0B6E4F",        # أخضر سعودي عميق
    "primary_dark": "#08543C",
    "secondary": "#1F2937",      # Charcoal / Near Black
    "bg": "#FFFFFF",
    "bg_light": "#F6F8F7",
    "accent": "#B8963E",         # ذهبي سعودي هادئ
    "ai_purple": "#5B3E96",      # Deep Purple - استخدام محدود لعناصر الذكاء الاصطناعي
    "success": "#2E7D32",
    "warning": "#B8860B",
    "high": "#C1440E",
    "critical": "#B00020",
    "muted": "#6B7280",
    "border": "#E5E7EB",
}

# =============================================================================
# حقن CSS لدعم RTL والهوية البصرية المؤسسية
# =============================================================================
def inject_css():
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{
            direction: rtl;
            text-align: right;
            font-family: 'Tahoma', 'Segoe UI', 'Arial', sans-serif;
        }}
        .stApp {{
            background-color: {COLORS['bg_light']};
        }}
        section[data-testid="stSidebar"] {{
            background-color: {COLORS['secondary']};
            direction: rtl;
        }}
        section[data-testid="stSidebar"] * {{
            color: #F3F4F6 !important;
        }}
        section[data-testid="stSidebar"] .stButton button {{
            width: 100%;
            text-align: right;
            background-color: transparent;
            border: none;
            color: #E5E7EB !important;
            padding: 0.45rem 0.6rem;
            font-size: 0.92rem;
            border-radius: 6px;
        }}
        section[data-testid="stSidebar"] .stButton button:hover {{
            background-color: rgba(255,255,255,0.08);
            color: #FFFFFF !important;
        }}
        div[data-testid="stMetricValue"] {{
            color: {COLORS['primary_dark']};
        }}
        .bayan-hero {{
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['primary_dark']} 100%);
            padding: 3rem 2.5rem;
            border-radius: 14px;
            color: white;
            text-align: center;
            margin-bottom: 1.5rem;
        }}
        .bayan-hero h1 {{
            font-size: 2.6rem;
            margin-bottom: 0.2rem;
            letter-spacing: 1px;
        }}
        .bayan-hero .tagline {{
            font-size: 1.15rem;
            opacity: 0.95;
            margin-bottom: 0.9rem;
        }}
        .bayan-hero .badge {{
            display: inline-block;
            background: rgba(255,255,255,0.15);
            padding: 0.3rem 0.9rem;
            border-radius: 20px;
            font-size: 0.85rem;
            margin-bottom: 1rem;
        }}
        .bayan-card {{
            background: white;
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.8rem;
        }}
        .bayan-card-title {{
            font-weight: 700;
            font-size: 1.02rem;
            color: {COLORS['secondary']};
            margin-bottom: 0.3rem;
        }}
        .pill {{
            display: inline-block;
            padding: 0.15rem 0.65rem;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 600;
            margin-left: 0.3rem;
        }}
        .pill-critical {{ background:#FDE7EA; color:{COLORS['critical']}; }}
        .pill-high {{ background:#FDEEE6; color:{COLORS['high']}; }}
        .pill-warning {{ background:#FBF3DE; color:{COLORS['warning']}; }}
        .pill-success {{ background:#E6F4EA; color:{COLORS['success']}; }}
        .pill-ai {{ background:#EFE9F8; color:{COLORS['ai_purple']}; }}
        .pill-neutral {{ background:#F1F2F4; color:{COLORS['secondary']}; }}
        .bayan-banner {{
            background: #F1EAFB;
            border-right: 5px solid {COLORS['ai_purple']};
            padding: 0.8rem 1.1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-weight: 600;
            color: {COLORS['secondary']};
        }}
        .demo-banner {{
            background: #FBF3DE;
            border-right: 5px solid {COLORS['warning']};
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            margin-bottom: 1rem;
        }}
        .footer-note {{
            text-align: center;
            color: {COLORS['muted']};
            font-size: 0.8rem;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid {COLORS['border']};
        }}
        .step-flow span {{
            display: inline-block;
            background: {COLORS['bg_light']};
            border: 1px solid {COLORS['border']};
            border-radius: 20px;
            padding: 0.35rem 0.9rem;
            margin: 0.15rem;
            font-size: 0.85rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# تحميل البيانات (Mock Data)
# =============================================================================
@st.cache_data
def load_data():
    claims = pd.DataFrame([{"id": "CLM001", "content": "تداول واسع لمنشور يزعم إيقاف خدمة تجديد الهوية الوطنية عبر أبشر نهائيًا ابتداءً من الأسبوع القادم", "source": "مواقع تواصل - Demo", "timestamp": "2026-09-11 08:12:00", "agency": "AG02", "service": "تجديد الهوية الوطنية", "claim_type": "معلومات مضللة", "status": "معلومات مضللة", "reach": 95000, "growth_rate": 28, "confidence": 91, "service_sensitivity": 95, "official_conflict": 90, "time_urgency": 80, "response_status": "قيد المراجعة البشرية", "mentioned_date": "2026-09-18"}, {"id": "CLM002", "content": "حساب يحاكي شعار وتصميم منصة أبشر وينشر رابطًا لتحديث بيانات الجوال بشكل عاجل", "source": "منتدى عام - Demo", "timestamp": "2026-09-11 06:40:00", "agency": "AG02", "service": "تحديث بيانات الجوال", "claim_type": "محتوى منتحل", "status": "محتوى منتحل", "reach": 90000, "growth_rate": 27, "confidence": 89, "service_sensitivity": 92, "official_conflict": 97, "time_urgency": 65, "response_status": "قيد المراجعة البشرية", "mentioned_date": "2026-09-11"}, {"id": "CLM003", "content": "إعادة تداول منشور قديم من عام سابق عن تعليق إصدار رخص القيادة للنساء في بعض المناطق", "source": "تطبيقات مراسلة - Demo", "timestamp": "2026-09-10 21:15:00", "agency": "AG04", "service": "إصدار رخصة القيادة", "claim_type": "معلومة قديمة", "status": "معلومة قديمة", "reach": 60000, "growth_rate": 18, "confidence": 74, "service_sensitivity": 70, "official_conflict": 65, "time_urgency": 60, "response_status": "قيد التحقيق", "mentioned_date": "2026-09-01"}, {"id": "CLM004", "content": "اقتباس صحيح لتعميم قديم عن رسوم الخدمات الصحية يُعاد نشره وكأنه قرار جديد هذا الأسبوع", "source": "مواقع تواصل - Demo", "timestamp": "2026-09-10 14:05:00", "agency": "AG03", "service": "رسوم الخدمات العلاجية", "claim_type": "خارج السياق", "status": "خارج السياق", "reach": 45000, "growth_rate": 15, "confidence": 68, "service_sensitivity": 62, "official_conflict": 55, "time_urgency": 60, "response_status": "قيد التحقيق", "mentioned_date": "2026-09-05"}, {"id": "CLM005", "content": "منشور فردي محدود الانتشار يشكك في مواعيد عمل أحد مكاتب الجوازات دون أدلة", "source": "منتدى عام - Demo", "timestamp": "2026-09-09 11:20:00", "agency": "AG05", "service": "مواعيد خدمة الجوازات", "claim_type": "غير متحقق", "status": "غير متحقق", "reach": 2000, "growth_rate": 3, "confidence": 52, "service_sensitivity": 20, "official_conflict": 15, "time_urgency": 20, "response_status": "مراقبة", "mentioned_date": "2026-09-09"}, {"id": "CLM006", "content": "انتشار سريع جدًا لادعاء بفرض رسوم مفاجئة على تجديد الإقامة اعتبارًا من الغد", "source": "مواقع تواصل - Demo", "timestamp": "2026-09-11 09:50:00", "agency": "AG01", "service": "تجديد الإقامة", "claim_type": "معلومات مضللة", "status": "معلومات مضللة", "reach": 180000, "growth_rate": 32, "confidence": 93, "service_sensitivity": 90, "official_conflict": 90, "time_urgency": 85, "response_status": "قيد المراجعة البشرية", "mentioned_date": "2026-09-12"}, {"id": "CLM007", "content": "تساؤلات متفرقة حول تغيير مزعوم في آلية صرف معاش التقاعد دون مصدر واضح", "source": "تطبيقات مراسلة - Demo", "timestamp": "2026-09-08 17:30:00", "agency": "AG07", "service": "صرف المعاش التقاعدي", "claim_type": "غير متحقق", "status": "غير متحقق", "reach": 15000, "growth_rate": 8, "confidence": 58, "service_sensitivity": 45, "official_conflict": 35, "time_urgency": 35, "response_status": "مراقبة", "mentioned_date": "2026-09-15"}, {"id": "CLM008", "content": "ادعاء بتعليق خدمة التأشيرات الإلكترونية تم إصدار توضيح رسمي بشأنه سابقًا", "source": "مواقع تواصل - Demo", "timestamp": "2026-09-07 10:00:00", "agency": "AG05", "service": "التأشيرة الإلكترونية", "claim_type": "معلومات مضللة", "status": "معلومات مضللة", "reach": 85000, "growth_rate": 22, "confidence": 88, "service_sensitivity": 85, "official_conflict": 80, "time_urgency": 70, "response_status": "معتمد ومنشور", "mentioned_date": "2026-09-08"}, {"id": "CLM009", "content": "منشور يشير إلى تعديل مزعوم في نسب التأمينات الاجتماعية للمنشآت الصغيرة دون توثيق", "source": "منتدى عام - Demo", "timestamp": "2026-09-09 19:45:00", "agency": "AG07", "service": "اشتراكات المنشآت", "claim_type": "غير متحقق", "status": "غير متحقق", "reach": 20000, "growth_rate": 10, "confidence": 60, "service_sensitivity": 50, "official_conflict": 30, "time_urgency": 45, "response_status": "قيد التحقيق", "mentioned_date": "2026-09-20"}, {"id": "CLM010", "content": "صورة معدّلة بصريًا تحاكي إعلانًا رسميًا لوزارة الداخلية بشأن تمديد صلاحية الإقامة", "source": "مواقع تواصل - Demo", "timestamp": "2026-09-11 07:05:00", "agency": "AG01", "service": "صلاحية الإقامة", "claim_type": "محتوى منتحل", "status": "محتوى منتحل", "reach": 100000, "growth_rate": 26, "confidence": 90, "service_sensitivity": 90, "official_conflict": 95, "time_urgency": 75, "response_status": "قيد المراجعة البشرية", "mentioned_date": "2026-09-11"}, {"id": "CLM011", "content": "ادعاء غير دقيق عن فرض رسوم جديدة على رخص البناء في بعض الأمانات", "source": "تطبيقات مراسلة - Demo", "timestamp": "2026-09-10 12:30:00", "agency": "AG09", "service": "رخصة البناء", "claim_type": "معلومات غير صحيحة", "status": "معلومات غير صحيحة", "reach": 52000, "growth_rate": 19, "confidence": 72, "service_sensitivity": 65, "official_conflict": 70, "time_urgency": 55, "response_status": "قيد التحقيق", "mentioned_date": "2026-09-14"}, {"id": "CLM012", "content": "تأكيد صحيح لقرار رسمي منشور مسبقًا بشأن جدول العام الدراسي يعاد تداوله بدقة", "source": "مواقع تواصل - Demo", "timestamp": "2026-09-06 09:00:00", "agency": "AG10", "service": "التقويم الدراسي", "claim_type": "صحيح", "status": "صحيح", "reach": 8000, "growth_rate": 6, "confidence": 95, "service_sensitivity": 40, "official_conflict": 5, "time_urgency": 20, "response_status": "مغلق", "mentioned_date": "2026-09-01"}])
    sources = pd.DataFrame([{"source_id": "SRC001", "source_name": "تحديث صفحة خدمة أبشر - مصدر تجريبي", "source_type": "مصدر رسمي - Demo Data", "date": "2026-09-11", "verified": "صحيح", "related_claim": "CLM001", "description": "تحديث توضيحي يؤكد استمرار خدمة تجديد الهوية الوطنية دون أي إيقاف مزمع"}, {"source_id": "SRC002", "source_name": "تعميم داخلي سابق - مصدر تجريبي", "source_type": "تعميم داخلي - Demo Data", "date": "2026-08-20", "verified": "صحيح", "related_claim": "CLM001", "description": "لا يوجد أي تعميم رسمي يشير إلى إيقاف الخدمة المذكورة"}, {"source_id": "SRC003", "source_name": "دليل الهوية البصرية الرسمية - مصدر تجريبي", "source_type": "مرجع تصميم - Demo Data", "date": "2026-01-15", "verified": "صحيح", "related_claim": "CLM002", "description": "الحساب المنتحل يستخدم شعارًا وألوانًا مقاربة لكنه غير مرتبط بأي نطاق رسمي معتمد"}, {"source_id": "SRC004", "source_name": "صفحة التحقق من الحسابات الرسمية - مصدر تجريبي", "source_type": "مصدر رسمي - Demo Data", "date": "2026-09-10", "verified": "صحيح", "related_claim": "CLM002", "description": "القائمة الرسمية للحسابات المعتمدة لا تتضمن الحساب المصدر لهذا المحتوى"}, {"source_id": "SRC005", "source_name": "أرشيف بيانات سابقة - مصدر تجريبي", "source_type": "أرشيف رسمي - Demo Data", "date": "2025-11-02", "verified": "صحيح", "related_claim": "CLM003", "description": "البيان الأصلي الذي استند إليه المنشور يعود لعام سابق ولا ينطبق على الفترة الحالية"}, {"source_id": "SRC006", "source_name": "تحديث موقع خدمة رخص القيادة - مصدر تجريبي", "source_type": "مصدر رسمي - Demo Data", "date": "2026-09-01", "verified": "صحيح", "related_claim": "CLM003", "description": "تأكيد استمرار إصدار رخص القيادة دون أي تعليق أو تعديل"}, {"source_id": "SRC007", "source_name": "تعميم رسوم الخدمات العلاجية الأصلي - مصدر تجريبي", "source_type": "وثيقة رسمية - Demo Data", "date": "2025-06-10", "verified": "صحيح", "related_claim": "CLM004", "description": "التعميم المقتبس صحيح في نصه لكنه يخص فترة سابقة ولا يعكس القرار الحالي"}, {"source_id": "SRC008", "source_name": "تحديث موقع خدمة تجديد الإقامة - مصدر تجريبي", "source_type": "مصدر رسمي - Demo Data", "date": "2026-09-11", "verified": "صحيح", "related_claim": "CLM006", "description": "لا توجد أي رسوم إضافية مقررة على تجديد الإقامة في التاريخ المذكور"}, {"source_id": "SRC009", "source_name": "بيان توضيحي سابق مشابه - مصدر تجريبي", "source_type": "بيان صحفي - Demo Data", "date": "2026-03-05", "verified": "صحيح", "related_claim": "CLM006", "description": "سبق وأن تم تفنيد ادعاء مشابه بنفس النمط خلال فترة سابقة"}, {"source_id": "SRC010", "source_name": "صفحة خدمة صرف المعاش التقاعدي - مصدر تجريبي", "source_type": "مصدر رسمي - Demo Data", "date": "2026-09-08", "verified": "صحيح", "related_claim": "CLM007", "description": "آلية الصرف الحالية مطابقة للمعتمد دون أي تغيير معلن"}, {"source_id": "SRC011", "source_name": "بيان رسمي منشور سابقًا بشأن التأشيرة الإلكترونية - مصدر تجريبي", "source_type": "بيان صحفي - Demo Data", "date": "2026-09-08", "verified": "صحيح", "related_claim": "CLM008", "description": "تم نشر توضيح رسمي مسبق يؤكد استمرار خدمة التأشيرة الإلكترونية دون تعليق"}, {"source_id": "SRC012", "source_name": "تحديث سياسة اشتراكات المنشآت - مصدر تجريبي", "source_type": "مصدر رسمي - Demo Data", "date": "2026-08-25", "verified": "صحيح", "related_claim": "CLM009", "description": "لا يوجد تعديل معلن على نسب الاشتراكات للمنشآت الصغيرة حتى تاريخه"}, {"source_id": "SRC013", "source_name": "صفحة التحقق من الإعلانات الرسمية - مصدر تجريبي", "source_type": "مصدر رسمي - Demo Data", "date": "2026-09-11", "verified": "صحيح", "related_claim": "CLM010", "description": "التصميم المتداول لا يطابق قوالب الإعلانات الرسمية المعتمدة لوزارة الداخلية"}, {"source_id": "SRC014", "source_name": "أرشيف الإعلانات الرسمية السابقة - مصدر تجريبي", "source_type": "أرشيف رسمي - Demo Data", "date": "2026-07-01", "verified": "صحيح", "related_claim": "CLM010", "description": "لا يوجد إعلان رسمي مطابق للمحتوى المتداول في الأرشيف الرسمي"}, {"source_id": "SRC015", "source_name": "تحديث موقع خدمة رخصة البناء - مصدر تجريبي", "source_type": "مصدر رسمي - Demo Data", "date": "2026-09-10", "verified": "صحيح", "related_claim": "CLM011", "description": "جدول الرسوم المعتمد الحالي لا يتضمن أي رسوم جديدة كما هو مزعوم"}, {"source_id": "SRC016", "source_name": "التقويم الدراسي الرسمي المعتمد - مصدر تجريبي", "source_type": "مصدر رسمي - Demo Data", "date": "2026-06-01", "verified": "صحيح", "related_claim": "CLM012", "description": "المحتوى المتداول مطابق تمامًا للتقويم الدراسي الرسمي المعتمد والمنشور مسبقًا"}])
    events = pd.DataFrame([{"claim_id": "CLM001", "event": "تم الرصد", "timestamp": "2026-09-11 08:12:00", "actor": "محرك الرصد", "details": "رصد المحتوى ضمن مواقع التواصل - Demo"}, {"claim_id": "CLM001", "event": "استخراج الادعاء", "timestamp": "2026-09-11 08:12:18", "actor": "محرك الاستخراج", "details": "تحديد الجهة والخدمة المعنية بالادعاء"}, {"claim_id": "CLM001", "event": "اكتمال التحقق", "timestamp": "2026-09-11 08:13:00", "actor": "محرك التحقق", "details": "تصنيف الحالة كمعلومات مضللة بثقة 91%"}, {"claim_id": "CLM001", "event": "حساب Risk Score", "timestamp": "2026-09-11 08:13:20", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 91/100"}, {"claim_id": "CLM001", "event": "توصية القرار", "timestamp": "2026-09-11 08:13:35", "actor": "محرك القرار", "details": "التوصية بإصدار توضيح رسمي مختصر"}, {"claim_id": "CLM001", "event": "توليد المسودة", "timestamp": "2026-09-11 08:14:10", "actor": "مولد الردود", "details": "إنشاء مسودة توضيح أولية"}, {"claim_id": "CLM001", "event": "مراجعة بشرية", "timestamp": "2026-09-11 08:20:00", "actor": "فريق التواصل المؤسسي", "details": "المسودة قيد المراجعة حاليًا"}, {"claim_id": "CLM002", "event": "تم الرصد", "timestamp": "2026-09-11 06:40:00", "actor": "محرك الرصد", "details": "رصد حساب منتحل ضمن منتدى عام - Demo"}, {"claim_id": "CLM002", "event": "استخراج الادعاء", "timestamp": "2026-09-11 06:40:22", "actor": "محرك الاستخراج", "details": "تحديد الجهة المنتحلة والخدمة المرتبطة"}, {"claim_id": "CLM002", "event": "اكتمال التحقق", "timestamp": "2026-09-11 06:41:05", "actor": "محرك التحقق", "details": "تصنيف الحالة كمحتوى منتحل بثقة 89%"}, {"claim_id": "CLM002", "event": "حساب Risk Score", "timestamp": "2026-09-11 06:41:30", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 89/100"}, {"claim_id": "CLM002", "event": "توصية القرار", "timestamp": "2026-09-11 06:41:50", "actor": "محرك القرار", "details": "التوصية بتصعيد داخلي وإصدار تنبيه توعوي"}, {"claim_id": "CLM002", "event": "توليد المسودة", "timestamp": "2026-09-11 06:42:40", "actor": "مولد الردود", "details": "إنشاء مسودة تنبيه توعوي"}, {"claim_id": "CLM002", "event": "مراجعة بشرية", "timestamp": "2026-09-11 06:50:00", "actor": "فريق أمن المعلومات", "details": "المسودة قيد المراجعة حاليًا"}, {"claim_id": "CLM003", "event": "تم الرصد", "timestamp": "2026-09-10 21:15:00", "actor": "محرك الرصد", "details": "رصد المحتوى ضمن تطبيقات مراسلة - Demo"}, {"claim_id": "CLM003", "event": "استخراج الادعاء", "timestamp": "2026-09-10 21:15:19", "actor": "محرك الاستخراج", "details": "تحديد الجهة والخدمة المعنية بالادعاء"}, {"claim_id": "CLM003", "event": "اكتمال التحقق", "timestamp": "2026-09-10 21:16:10", "actor": "محرك التحقق", "details": "تصنيف الحالة كمعلومة قديمة بثقة 74%"}, {"claim_id": "CLM003", "event": "حساب Risk Score", "timestamp": "2026-09-10 21:16:30", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 69/100"}, {"claim_id": "CLM004", "event": "تم الرصد", "timestamp": "2026-09-10 14:05:00", "actor": "محرك الرصد", "details": "رصد المحتوى ضمن مواقع التواصل - Demo"}, {"claim_id": "CLM004", "event": "استخراج الادعاء", "timestamp": "2026-09-10 14:05:15", "actor": "محرك الاستخراج", "details": "تحديد الجهة والخدمة المعنية بالادعاء"}, {"claim_id": "CLM004", "event": "اكتمال التحقق", "timestamp": "2026-09-10 14:06:00", "actor": "محرك التحقق", "details": "تصنيف الحالة كمحتوى خارج السياق بثقة 68%"}, {"claim_id": "CLM004", "event": "حساب Risk Score", "timestamp": "2026-09-10 14:06:25", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 62/100"}, {"claim_id": "CLM005", "event": "تم الرصد", "timestamp": "2026-09-09 11:20:00", "actor": "محرك الرصد", "details": "رصد منشور محدود الانتشار"}, {"claim_id": "CLM005", "event": "استخراج الادعاء", "timestamp": "2026-09-09 11:20:12", "actor": "محرك الاستخراج", "details": "تحديد الجهة والخدمة المعنية بالادعاء"}, {"claim_id": "CLM005", "event": "اكتمال التحقق", "timestamp": "2026-09-09 11:21:00", "actor": "محرك التحقق", "details": "تصنيف الحالة كغير متحقق بثقة 52%"}, {"claim_id": "CLM005", "event": "حساب Risk Score", "timestamp": "2026-09-09 11:21:20", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 25/100"}, {"claim_id": "CLM006", "event": "تم الرصد", "timestamp": "2026-09-11 09:50:00", "actor": "محرك الرصد", "details": "رصد انتشار سريع ضمن مواقع التواصل - Demo"}, {"claim_id": "CLM006", "event": "استخراج الادعاء", "timestamp": "2026-09-11 09:50:20", "actor": "محرك الاستخراج", "details": "تحديد الجهة والخدمة المعنية بالادعاء"}, {"claim_id": "CLM006", "event": "اكتمال التحقق", "timestamp": "2026-09-11 09:51:05", "actor": "محرك التحقق", "details": "تصنيف الحالة كمعلومات مضللة بثقة 93%"}, {"claim_id": "CLM006", "event": "حساب Risk Score", "timestamp": "2026-09-11 09:51:25", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 94/100"}, {"claim_id": "CLM006", "event": "توصية القرار", "timestamp": "2026-09-11 09:51:40", "actor": "محرك القرار", "details": "التوصية بإصدار بيان رسمي عاجل"}, {"claim_id": "CLM006", "event": "توليد المسودة", "timestamp": "2026-09-11 09:52:20", "actor": "مولد الردود", "details": "إنشاء مسودة بيان رسمي عاجل"}, {"claim_id": "CLM006", "event": "مراجعة بشرية", "timestamp": "2026-09-11 09:58:00", "actor": "فريق التواصل المؤسسي", "details": "المسودة قيد المراجعة العاجلة"}, {"claim_id": "CLM007", "event": "تم الرصد", "timestamp": "2026-09-08 17:30:00", "actor": "محرك الرصد", "details": "رصد تساؤلات متفرقة"}, {"claim_id": "CLM007", "event": "استخراج الادعاء", "timestamp": "2026-09-08 17:30:14", "actor": "محرك الاستخراج", "details": "تحديد الجهة والخدمة المعنية بالادعاء"}, {"claim_id": "CLM007", "event": "اكتمال التحقق", "timestamp": "2026-09-08 17:31:00", "actor": "محرك التحقق", "details": "تصنيف الحالة كغير متحقق بثقة 58%"}, {"claim_id": "CLM007", "event": "حساب Risk Score", "timestamp": "2026-09-08 17:31:20", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 44/100"}, {"claim_id": "CLM008", "event": "تم الرصد", "timestamp": "2026-09-07 10:00:00", "actor": "محرك الرصد", "details": "رصد المحتوى ضمن مواقع التواصل - Demo"}, {"claim_id": "CLM008", "event": "استخراج الادعاء", "timestamp": "2026-09-07 10:00:18", "actor": "محرك الاستخراج", "details": "تحديد الجهة والخدمة المعنية بالادعاء"}, {"claim_id": "CLM008", "event": "اكتمال التحقق", "timestamp": "2026-09-07 10:01:00", "actor": "محرك التحقق", "details": "تصنيف الحالة كمعلومات مضللة بثقة 88%"}, {"claim_id": "CLM008", "event": "حساب Risk Score", "timestamp": "2026-09-07 10:01:20", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 80/100"}, {"claim_id": "CLM008", "event": "توصية القرار", "timestamp": "2026-09-07 10:01:35", "actor": "محرك القرار", "details": "التوصية بإصدار توضيح رسمي وتحديث صفحة الخدمة"}, {"claim_id": "CLM008", "event": "توليد المسودة", "timestamp": "2026-09-07 10:02:10", "actor": "مولد الردود", "details": "إنشاء مسودة توضيح رسمي"}, {"claim_id": "CLM008", "event": "مراجعة بشرية", "timestamp": "2026-09-07 10:06:00", "actor": "فريق التواصل المؤسسي", "details": "مراجعة وتعديل نص المسودة"}, {"claim_id": "CLM008", "event": "اعتماد بشري", "timestamp": "2026-09-07 10:07:40", "actor": "م. سارة القحطاني", "details": "اعتماد المسودة بعد المراجعة"}, {"claim_id": "CLM008", "event": "نشر رسمي", "timestamp": "2026-09-07 10:08:10", "actor": "فريق التواصل المؤسسي", "details": "نشر التوضيح الرسمي عبر القناة المعتمدة"}, {"claim_id": "CLM009", "event": "تم الرصد", "timestamp": "2026-09-09 19:45:00", "actor": "محرك الرصد", "details": "رصد المحتوى ضمن منتدى عام - Demo"}, {"claim_id": "CLM009", "event": "استخراج الادعاء", "timestamp": "2026-09-09 19:45:16", "actor": "محرك الاستخراج", "details": "تحديد الجهة والخدمة المعنية بالادعاء"}, {"claim_id": "CLM009", "event": "اكتمال التحقق", "timestamp": "2026-09-09 19:46:00", "actor": "محرك التحقق", "details": "تصنيف الحالة كغير متحقق بثقة 60%"}, {"claim_id": "CLM009", "event": "حساب Risk Score", "timestamp": "2026-09-09 19:46:25", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 47/100"}, {"claim_id": "CLM010", "event": "تم الرصد", "timestamp": "2026-09-11 07:05:00", "actor": "محرك الرصد", "details": "رصد صورة معدّلة بصريًا"}, {"claim_id": "CLM010", "event": "استخراج الادعاء", "timestamp": "2026-09-11 07:05:20", "actor": "محرك الاستخراج", "details": "تحديد الجهة المنتحلة والخدمة المرتبطة"}, {"claim_id": "CLM010", "event": "اكتمال التحقق", "timestamp": "2026-09-11 07:06:05", "actor": "محرك التحقق", "details": "تصنيف الحالة كمحتوى منتحل بثقة 90%"}, {"claim_id": "CLM010", "event": "حساب Risk Score", "timestamp": "2026-09-11 07:06:25", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 89/100"}, {"claim_id": "CLM010", "event": "توصية القرار", "timestamp": "2026-09-11 07:06:45", "actor": "محرك القرار", "details": "التوصية بإصدار بيان رسمي وتصعيد داخلي"}, {"claim_id": "CLM010", "event": "توليد المسودة", "timestamp": "2026-09-11 07:07:30", "actor": "مولد الردود", "details": "إنشاء مسودة بيان توضيحي"}, {"claim_id": "CLM010", "event": "مراجعة بشرية", "timestamp": "2026-09-11 07:15:00", "actor": "فريق أمن المعلومات", "details": "المسودة قيد المراجعة حاليًا"}, {"claim_id": "CLM011", "event": "تم الرصد", "timestamp": "2026-09-10 12:30:00", "actor": "محرك الرصد", "details": "رصد المحتوى ضمن تطبيقات مراسلة - Demo"}, {"claim_id": "CLM011", "event": "استخراج الادعاء", "timestamp": "2026-09-10 12:30:15", "actor": "محرك الاستخراج", "details": "تحديد الجهة والخدمة المعنية بالادعاء"}, {"claim_id": "CLM011", "event": "اكتمال التحقق", "timestamp": "2026-09-10 12:31:00", "actor": "محرك التحقق", "details": "تصنيف الحالة كمعلومات غير صحيحة بثقة 72%"}, {"claim_id": "CLM011", "event": "حساب Risk Score", "timestamp": "2026-09-10 12:31:25", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 69/100"}, {"claim_id": "CLM012", "event": "تم الرصد", "timestamp": "2026-09-06 09:00:00", "actor": "محرك الرصد", "details": "رصد إعادة تداول تعميم رسمي"}, {"claim_id": "CLM012", "event": "استخراج الادعاء", "timestamp": "2026-09-06 09:00:10", "actor": "محرك الاستخراج", "details": "تحديد الجهة والخدمة المعنية بالادعاء"}, {"claim_id": "CLM012", "event": "اكتمال التحقق", "timestamp": "2026-09-06 09:00:45", "actor": "محرك التحقق", "details": "تصنيف الحالة كمعلومة صحيحة بثقة 95%"}, {"claim_id": "CLM012", "event": "حساب Risk Score", "timestamp": "2026-09-06 09:01:00", "actor": "محرك المخاطر", "details": "احتساب درجة الخطورة 32/100"}, {"claim_id": "CLM012", "event": "توصية القرار", "timestamp": "2026-09-06 09:01:10", "actor": "محرك القرار", "details": "التوصية بعدم التدخل ومراقبة اعتيادية"}, {"claim_id": "CLM012", "event": "إغلاق الحالة", "timestamp": "2026-09-06 09:02:00", "actor": "فريق التواصل المؤسسي", "details": "إغلاق الحالة دون الحاجة لاستجابة رسمية"}])
    agencies = pd.DataFrame([{"agency_id": "AG01", "agency_name": "وزارة الداخلية", "category": "أمن وخدمات مدنية", "sensitivity_level": 90}, {"agency_id": "AG02", "agency_name": "منصة أبشر", "category": "خدمات رقمية حكومية", "sensitivity_level": 85}, {"agency_id": "AG03", "agency_name": "وزارة الصحة", "category": "صحة عامة", "sensitivity_level": 95}, {"agency_id": "AG04", "agency_name": "الإدارة العامة للمرور", "category": "مرور وسلامة", "sensitivity_level": 75}, {"agency_id": "AG05", "agency_name": "الجوازات", "category": "هوية وسفر", "sensitivity_level": 88}, {"agency_id": "AG06", "agency_name": "وزارة الموارد البشرية والتنمية الاجتماعية", "category": "عمل وتنمية اجتماعية", "sensitivity_level": 70}, {"agency_id": "AG07", "agency_name": "المؤسسة العامة للتأمينات الاجتماعية", "category": "تقاعد وتأمينات", "sensitivity_level": 80}, {"agency_id": "AG08", "agency_name": "هيئة الزكاة والضريبة والجمارك", "category": "مالية وضرائب", "sensitivity_level": 72}, {"agency_id": "AG09", "agency_name": "وزارة الشؤون البلدية والقروية والإسكان", "category": "خدمات بلدية", "sensitivity_level": 60}, {"agency_id": "AG10", "agency_name": "وزارة التعليم", "category": "تعليم", "sensitivity_level": 78}])

    claims = claims.merge(
        agencies[["agency_id", "agency_name"]], left_on="agency", right_on="agency_id", how="left"
    )
    claims["timestamp"] = pd.to_datetime(claims["timestamp"])

    risk_scores, priority_scores, priority_codes, priority_labels = [], [], [], []
    for _, row in claims.iterrows():
        c = row.to_dict()
        risk_scores.append(compute_risk_score(c))
        pr = compute_decision_priority(c)
        priority_scores.append(pr["score"])
        priority_codes.append(pr["code"])
        priority_labels.append(pr["label"])

    claims["risk_score"] = risk_scores
    claims["priority_score"] = priority_scores
    claims["priority_code"] = priority_codes
    claims["priority_label"] = priority_labels
    claims["risk_label"] = claims["risk_score"].apply(lambda s: risk_level(s)["label"])

    return claims, sources, events, agencies

claims_df_raw, sources_df, events_df, agencies_df = load_data()

# =============================================================================
# تهيئة حالة الجلسة (Session State)
# =============================================================================
def init_session_state():
    if "page" not in st.session_state:
        st.session_state.page = "الرئيسية"
    if "selected_claim" not in st.session_state:
        st.session_state.selected_claim = claims_df_raw.iloc[0]["id"]
    if "claims_runtime" not in st.session_state:
        # نسخة قابلة للتعديل أثناء الجلسة (اعتماد/رفض/تحديث الحالة) دون المساس بملفات CSV الأصلية
        st.session_state.claims_runtime = claims_df_raw.copy().set_index("id").to_dict(orient="index")
    if "drafts" not in st.session_state:
        st.session_state.drafts = {}
    if "approvals" not in st.session_state:
        st.session_state.approvals = {}
    if "demo_step" not in st.session_state:
        st.session_state.demo_step = 0
    if "demo_running" not in st.session_state:
        st.session_state.demo_running = False


init_session_state()
inject_css()


def get_claims_df():
    """يرجع نسخة DataFrame محدثة من الحالة التشغيلية الحالية (بعد أي اعتماد/رفض)."""
    df = pd.DataFrame.from_dict(st.session_state.claims_runtime, orient="index")
    df.index.name = "id"
    df = df.reset_index()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def go_to(page_name, claim_id=None):
    st.session_state.page = page_name
    if claim_id is not None:
        st.session_state.selected_claim = claim_id
    st.rerun()


REVIEWER_NAME = "م. سارة القحطاني"
REVIEWER_ROLE = "مختص التواصل المؤسسي"

# =============================================================================
# مكوّنات واجهة قابلة لإعادة الاستخدام
# =============================================================================
def risk_pill(score):
    lvl = risk_level(score)
    css_class = {"critical": "pill-critical", "high": "pill-high", "warning": "pill-warning", "success": "pill-success"}[lvl["css"]]
    return f'<span class="pill {css_class}">خطورة {lvl["label"]} · {score}</span>'


def priority_pill(code, label):
    css_map = {"P1": "pill-critical", "P2": "pill-high", "P3": "pill-warning", "P4": "pill-success"}
    return f'<span class="pill {css_map.get(code,"pill-neutral")}">{code} · {label}</span>'


def status_pill(status):
    css = "pill-neutral"
    if status in ["معتمد ومنشور"]:
        css = "pill-success"
    elif status in ["قيد المراجعة البشرية"]:
        css = "pill-ai"
    elif status in ["قيد التحقيق", "مراقبة"]:
        css = "pill-warning"
    elif status in ["مرفوض"]:
        css = "pill-critical"
    return f'<span class="pill {css}">{status}</span>'


def kpi_card(label, value, sublabel=""):
    st.markdown(
        f"""
        <div class="bayan-card" style="text-align:center;">
            <div style="color:{COLORS['muted']}; font-size:0.8rem;">{label}</div>
            <div style="font-size:1.7rem; font-weight:800; color:{COLORS['primary_dark']};">{value}</div>
            <div style="color:{COLORS['muted']}; font-size:0.75rem;">{sublabel}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def claim_card(row, show_button=True, key_suffix=""):
    st.markdown(
        f"""
        <div class="bayan-card">
            <div class="bayan-card-title">{row['content'][:90]}{'...' if len(row['content'])>90 else ''}</div>
            <div style="margin:0.3rem 0;">
                {risk_pill(row['risk_score'])}
                {priority_pill(row['priority_code'], row['priority_label'])}
                {status_pill(row['response_status'])}
            </div>
            <div style="font-size:0.85rem; color:{COLORS['muted']};">
                الجهة: {row['agency_name']} &nbsp;|&nbsp; الخدمة: {row['service']} &nbsp;|&nbsp;
                معدل الانتشار: {row['growth_rate']}%/ساعة &nbsp;|&nbsp; الثقة: {row['confidence']}%
                &nbsp;|&nbsp; نافذة التدخل: {optimal_intervention_window(row['growth_rate'], row['risk_score'])}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if show_button:
        if st.button(f"فتح التحقيق · {row['id']}", key=f"open_{row['id']}{key_suffix}"):
            go_to("التحقيق الذكي", row["id"])


def render_risk_breakdown_chart(breakdown):
    factors = ["speed", "audience", "service_sensitivity", "official_conflict", "time_urgency"]
    labels = [breakdown[f]["label"] for f in factors]
    points = [breakdown[f]["points"] for f in factors]
    maxpts = [breakdown[f]["max"] for f in factors]

    fig = go.Figure()
    fig.add_trace(go.Bar(y=labels, x=maxpts, orientation="h", marker_color="#E5E7EB", name="الحد الأقصى", showlegend=False))
    fig.add_trace(go.Bar(y=labels, x=points, orientation="h", marker_color=COLORS["primary"], name="النقاط المحققة", showlegend=False))
    fig.update_layout(
        barmode="overlay", height=280, margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="النقاط", plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Tahoma"),
    )
    return fig


def render_timeline(claim_id):
    ev = events_df[events_df["claim_id"] == claim_id].sort_values("timestamp")
    if ev.empty:
        st.info("لا تتوفر أحداث مسجّلة لهذه الحالة بعد.")
        return
    for _, e in ev.iterrows():
        ts = pd.to_datetime(e["timestamp"]).strftime("%H:%M:%S")
        st.markdown(
            f"""
            <div style="display:flex; gap:0.8rem; margin-bottom:0.5rem;">
                <div style="min-width:70px; color:{COLORS['primary_dark']}; font-weight:700; font-size:0.85rem;">{ts}</div>
                <div style="border-right:2px solid {COLORS['primary']}; padding-right:0.8rem;">
                    <div style="font-weight:700; font-size:0.9rem;">{e['event']}</div>
                    <div style="color:{COLORS['muted']}; font-size:0.8rem;">{e['details']} — <i>{e['actor']}</i></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    rt = response_time_breakdown(ev)
    return rt


# =============================================================================
# الشريط الجانبي (Sidebar)
# =============================================================================
def sidebar_nav():
    st.sidebar.markdown(
        f"""
        <div style="text-align:center; padding:0.6rem 0 0.3rem 0;">
            <div style="font-size:1.5rem; font-weight:800; color:white;">بَيَان</div>
            <div style="font-size:0.8rem; color:#B8963E; letter-spacing:2px;">BAYAN</div>
            <div style="font-size:0.72rem; color:#9CA3AF; margin-top:0.3rem;">
                من الرصد المبكر إلى البيان الرسمي
            </div>
        </div>
        <hr style="border-color:rgba(255,255,255,0.15);">
        """,
        unsafe_allow_html=True,
    )

    def nav_button(label, icon=""):
        active = st.session_state.page == label
        prefix = "▸ " if active else "‎ ‎ "
        if st.sidebar.button(f"{prefix}{icon} {label}", key=f"nav_{label}"):
            st.session_state.page = label
            st.rerun()

    nav_button("الرئيسية", "🏠")

    st.sidebar.markdown('<div style="font-size:0.75rem; color:#9CA3AF; margin:0.8rem 0 0.2rem;">الرصد والتحليل</div>', unsafe_allow_html=True)
    nav_button("لوحة القيادة", "📊")
    nav_button("مركز الرصد", "🛰️")
    nav_button("التحقيق الذكي", "🔍")

    st.sidebar.markdown('<div style="font-size:0.75rem; color:#9CA3AF; margin:0.8rem 0 0.2rem;">القرار والاستجابة</div>', unsafe_allow_html=True)
    nav_button("محرك المخاطر", "⚠️")
    nav_button("محرك القرار", "🧭")
    nav_button("الردود الرسمية", "📝")
    nav_button("دورة الاستجابة", "🔄")

    st.sidebar.markdown('<div style="font-size:0.75rem; color:#9CA3AF; margin:0.8rem 0 0.2rem;">القياس</div>', unsafe_allow_html=True)
    nav_button("أثر الاستجابة", "📈")
    nav_button("سجل الحالات", "🗂️")

    st.sidebar.markdown("<hr style='border-color:rgba(255,255,255,0.15); margin-top:1.2rem;'>", unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div style="font-size:0.72rem; color:#9CA3AF; text-align:center; line-height:1.6;">
        🧪 بيئة تجريبية Prototype<br>
        جميع البيانات المعروضة بيانات محاكاة (Demo Data)<br>
        لأغراض العرض فقط
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# صفحة: الرئيسية (Hero)
# =============================================================================
def page_home():
    st.markdown(
        f"""
        <div class="bayan-hero">
            <div class="badge">AI-Assisted • Human-Approved</div>
            <h1>بَيَان | BAYAN</h1>
            <div class="tagline">من الرصد المبكر إلى البيان الرسمي.</div>
            <div style="font-size:0.95rem; opacity:0.9;">
                الرصد المبكر للمعلومات المضللة المتعلقة بالخدمات الحكومية وتسريع الرد الرسمي
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 ابدأ العرض التجريبي", use_container_width=True):
            st.session_state.demo_step = 0
            st.session_state.demo_running = True
            go_to("العرض التجريبي")
    with col2:
        if st.button("📊 استكشف لوحة القيادة", use_container_width=True):
            go_to("لوحة القيادة")

    st.markdown(
        f"""
        <div style="text-align:center; margin:1.2rem 0 2rem 0; color:{COLORS['secondary']}; font-size:1.05rem; font-weight:600;">
            "من المعلومة المتداولة إلى الرد الرسمي، بقرار أسرع وأوضح."
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### المشكلة والحل")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""
            <div class="bayan-card">
                <div class="bayan-card-title">المشكلة</div>
                <div style="color:{COLORS['muted']}; font-size:0.92rem;">
                المعلومة المضللة تنتشر أسرع من قدرة الجهة الحكومية على اكتشافها والتحقق منها والرد عليها رسميًا.
                </div>
            </div>
            """, unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="bayan-card">
                <div class="bayan-card-title">الحل</div>
                <div style="color:{COLORS['muted']}; font-size:0.92rem;">
                بَيَان يختصر دورة الاستجابة من الرصد إلى التحقق إلى تقييم الخطورة إلى التنبؤ
                إلى القرار إلى المسودة إلى الاعتماد البشري إلى النشر إلى قياس الأثر — مع إبقاء
                القرار والنشر الرسمي دائمًا بيد الإنسان.
                </div>
            </div>
            """, unsafe_allow_html=True,
        )

    st.markdown("#### دورة العمل")
    st.markdown(
        """
        <div class="step-flow" style="text-align:center;">
        <span>رصد</span> → <span>فهم</span> → <span>تحقق</span> → <span>تقييم</span> →
        <span>توقع</span> → <span>قرار</span> → <span>مسودة</span> → <span>مراجعة بشرية</span> →
        <span>اعتماد</span> → <span>نشر</span> → <span>قياس الأثر</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="footer-note">
        بَيَان لا يكتفي باكتشاف التضليل؛ بل يحوّل المعلومة المتداولة إلى قرار قابل للتنفيذ،
        ويختصر الطريق من الرصد إلى البيان الرسمي.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# صفحة: لوحة القيادة (Executive Dashboard)
# =============================================================================
def page_dashboard():
    df = get_claims_df()
    st.title("لوحة القيادة")
    st.caption("صورة لحظية عن المعلومات المضللة المتعلقة بالخدمات الحكومية")

    total = len(df)
    critical = len(df[df["risk_score"] > 80])
    high = len(df[(df["risk_score"] > 60) & (df["risk_score"] <= 80)])
    needs_action = len(df[df["priority_code"].isin(["P1", "P2"])])
    avg_response = 6.2
    avg_draft = 2.1
    effectiveness_avg = 78

    c = st.columns(7)
    with c[0]: kpi_card("إجمالي الادعاءات", total, "حالة مرصودة")
    with c[1]: kpi_card("حالات حرجة", critical, "خطورة > 80")
    with c[2]: kpi_card("عالية الخطورة", high, "61-80")
    with c[3]: kpi_card("تحتاج تدخل", needs_action, "P1 + P2")
    with c[4]: kpi_card("متوسط زمن الاستجابة", f"{avg_response} د", "من الرصد للنشر")
    with c[5]: kpi_card("متوسط زمن المسودة", f"{avg_draft} د", "من القرار للمسودة")
    with c[6]: kpi_card("فعالية الاستجابة", f"{effectiveness_avg}%", "متوسط تجريبي")

    st.markdown("### 🚨 يحتاج تدخلك الآن")
    urgent = df.sort_values("priority_score", ascending=False).head(4)
    cols = st.columns(2)
    for i, (_, row) in enumerate(urgent.iterrows()):
        with cols[i % 2]:
            claim_card(row, key_suffix="_dash")

    st.markdown("---")
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown("#### انتشار الادعاءات عبر الزمن")
        window = st.radio("المدى الزمني", ["آخر 6 ساعات", "12 ساعة", "24 ساعة", "7 أيام"], horizontal=True, index=2)
        hours_map = {"آخر 6 ساعات": 6, "12 ساعة": 12, "24 ساعة": 24, "7 أيام": 168}
        cutoff = df["timestamp"].max() - pd.Timedelta(hours=hours_map[window])
        window_df = df[df["timestamp"] >= cutoff].sort_values("timestamp")
        if window_df.empty:
            window_df = df.sort_values("timestamp")
        fig = px.line(
            window_df, x="timestamp", y="reach", markers=True,
            color_discrete_sequence=[COLORS["primary"]],
        )
        fig.update_layout(height=340, plot_bgcolor="white", paper_bgcolor="white",
                           xaxis_title="الوقت", yaxis_title="حجم الوصول (Reach)", font=dict(family="Tahoma"))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("#### توزيع الحالات حسب الجهات")
        by_agency = df.groupby("agency_name")["id"].count().reset_index().rename(columns={"id": "عدد الحالات"})
        fig2 = px.bar(
            by_agency.sort_values("عدد الحالات", ascending=True),
            x="عدد الحالات", y="agency_name", orientation="h",
            color_discrete_sequence=[COLORS["accent"]],
        )
        fig2.update_layout(height=340, plot_bgcolor="white", paper_bgcolor="white",
                            yaxis_title="", xaxis_title="عدد الحالات", font=dict(family="Tahoma"))
        st.plotly_chart(fig2, use_container_width=True)


# =============================================================================
# صفحة: مركز الرصد (Monitoring Center)
# =============================================================================
def page_monitoring():
    df = get_claims_df()
    st.title("مركز الرصد")
    st.caption("تدفّق المحتوى العام المرصود حول الخدمات والإجراءات الحكومية")

    with st.expander("🔎 الفلاتر والبحث", expanded=True):
        f1, f2, f3, f4 = st.columns(4)
        agency_filter = f1.multiselect("الجهة", sorted(df["agency_name"].unique()))
        service_filter = f2.multiselect("الخدمة", sorted(df["service"].unique()))
        type_filter = f3.multiselect("نوع الادعاء", sorted(df["claim_type"].unique()))
        status_filter = f4.multiselect("الحالة", sorted(df["response_status"].unique()))
        f5, f6 = st.columns(2)
        risk_filter = f5.select_slider("مستوى الخطورة (حد أدنى)", options=[0, 30, 60, 80], value=0)
        search = f6.text_input("🔍 بحث عن كلمات / خدمات / جهات / ادعاءات")

    filtered = df.copy()
    if agency_filter:
        filtered = filtered[filtered["agency_name"].isin(agency_filter)]
    if service_filter:
        filtered = filtered[filtered["service"].isin(service_filter)]
    if type_filter:
        filtered = filtered[filtered["claim_type"].isin(type_filter)]
    if status_filter:
        filtered = filtered[filtered["response_status"].isin(status_filter)]
    filtered = filtered[filtered["risk_score"] >= risk_filter]
    if search:
        s = search.strip()
        filtered = filtered[
            filtered["content"].str.contains(s, case=False, na=False)
            | filtered["service"].str.contains(s, case=False, na=False)
            | filtered["agency_name"].str.contains(s, case=False, na=False)
        ]

    st.caption(f"عدد النتائج: {len(filtered)} من أصل {len(df)}")

    for _, row in filtered.sort_values("timestamp", ascending=False).iterrows():
        with st.container():
            st.markdown(
                f"""
                <div class="bayan-card">
                    <div style="display:flex; justify-content:space-between; flex-wrap:wrap;">
                        <div class="bayan-card-title">{row['id']} — {row['content']}</div>
                        <div style="color:{COLORS['muted']}; font-size:0.8rem; white-space:nowrap;">
                            {row['timestamp'].strftime('%Y-%m-%d %H:%M')}
                        </div>
                    </div>
                    <div style="margin:0.4rem 0;">
                        {risk_pill(row['risk_score'])}
                        <span class="pill pill-neutral">{row['claim_type']}</span>
                        {status_pill(row['response_status'])}
                    </div>
                    <div style="font-size:0.85rem; color:{COLORS['muted']};">
                        المصدر: {row['source']} &nbsp;|&nbsp; الجهة: {row['agency_name']} &nbsp;|&nbsp;
                        الخدمة: {row['service']} &nbsp;|&nbsp; الوصول: {row['reach']:,} &nbsp;|&nbsp;
                        النمو: {row['growth_rate']}%/ساعة &nbsp;|&nbsp; الثقة: {row['confidence']}%
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"فتح التحقيق · {row['id']}", key=f"mon_{row['id']}"):
                go_to("التحقيق الذكي", row["id"])


# =============================================================================
# صفحة: التحقيق الذكي (AI Investigation) — أهم صفحة في المنصة
# =============================================================================
def page_investigation():
    df = get_claims_df()
    st.title("التحقيق الذكي")
    st.caption("من الادعاء المتداول إلى القرار القابل للتنفيذ")

    claim_id = st.selectbox(
        "اختر حالة للتحقيق",
        df["id"].tolist(),
        index=df["id"].tolist().index(st.session_state.selected_claim)
        if st.session_state.selected_claim in df["id"].tolist() else 0,
        format_func=lambda x: f"{x} — {df[df['id']==x]['content'].values[0][:60]}",
    )
    st.session_state.selected_claim = claim_id
    row = df[df["id"] == claim_id].iloc[0].to_dict()

    # 1) الادعاء الأصلي
    st.markdown("### 1️⃣ الادعاء الأصلي")
    st.markdown(
        f"""<div class="bayan-card">{row['content']}
        <div style="margin-top:0.5rem; font-size:0.8rem; color:{COLORS['muted']};">
        المصدر: {row['source']} &nbsp;|&nbsp; وقت الرصد: {row['timestamp']}</div></div>""",
        unsafe_allow_html=True,
    )

    # 2) استخراج الادعاء
    st.markdown("### 2️⃣ استخراج الادعاء")
    ext = extract_claim({**row, "agency_name": row["agency_name"]})
    e1, e2, e3 = st.columns(3)
    e1.markdown(f"**الجهة:** {ext['agency']}")
    e1.markdown(f"**الخدمة:** {ext['service']}")
    e2.markdown(f"**نوع الادعاء:** {ext['claim_type']}")
    e2.markdown(f"**التاريخ المذكور:** {ext['mentioned_date']}")
    e3.markdown(f"**العناصر المرتبطة:** {' ، '.join(ext['entities'])}")

    # 3) التحقق الذكي
    st.markdown("### 3️⃣ هل هو مضلل؟ — التحقق الذكي")
    v = verify_claim(row)
    vc1, vc2 = st.columns([1, 2])
    with vc1:
        st.markdown(status_pill(v["status"]), unsafe_allow_html=True)
        st.metric("درجة الثقة (Confidence)", f"{v['confidence']:.0f}%")
    with vc2:
        st.markdown("**لماذا صنف النظام الحالة بهذه الطريقة؟**")
        for r in v["reasons"]:
            st.markdown(f"- {r}")

    # 4) الأدلة
    st.markdown("### 4️⃣ الأدلة — Evidence Engine")
    evidence = sources_df[sources_df["related_claim"] == claim_id]
    if evidence.empty:
        st.info("لا تتوفر أدلة مرتبطة بعد — الحالة قيد جمع الأدلة.")
    else:
        ev_cols = st.columns(min(3, len(evidence)))
        for i, (_, ev) in enumerate(evidence.iterrows()):
            with ev_cols[i % len(ev_cols)]:
                st.markdown(
                    f"""
                    <div class="bayan-card">
                        <div class="bayan-card-title">{ev['source_name']}</div>
                        <div style="font-size:0.8rem; color:{COLORS['muted']};">{ev['source_type']} · {ev['date']}</div>
                        <div style="margin:0.4rem 0;"><span class="pill pill-success">{ev['verified']}</span></div>
                        <div style="font-size:0.85rem;">{ev['description']}</div>
                        <div style="font-size:0.7rem; color:{COLORS['ai_purple']}; margin-top:0.4rem;">مصدر تجريبي — Demo Data</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # 5) Risk Engine
    st.markdown("### 5️⃣ Risk — درجة الخطورة")
    breakdown = compute_risk_breakdown(row)
    rc1, rc2 = st.columns([1, 2])
    with rc1:
        lvl = risk_level(breakdown["total"])
        st.markdown(
            f"""<div class="bayan-card" style="text-align:center;">
                <div style="font-size:2.4rem; font-weight:800; color:{lvl['color']};">{breakdown['total']}</div>
                <div>{risk_pill(breakdown['total'])}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with rc2:
        st.plotly_chart(render_risk_breakdown_chart(breakdown), use_container_width=True)

    # 6) التنبؤ بالانتشار
    st.markdown("### 6️⃣ ماذا لو لم نتدخل؟ — التنبؤ بالانتشار")
    preds = predict_spread(row["reach"], row["growth_rate"])
    pc1, pc2, pc3, pc4 = st.columns(4)
    pc1.metric("الوصول الحالي", f"{row['reach']:,}")
    pc2.metric("معدل النمو", f"{row['growth_rate']}%/ساعة")
    pc3.metric("توقع خلال 12 ساعة", f"{preds[12]:,}")
    pc4.metric("توقع خلال 24 ساعة", f"{preds[24]:,}")
    window = optimal_intervention_window(row["growth_rate"], breakdown["total"])
    st.markdown(f'<div class="bayan-banner">⏱️ نافذة التدخل المثلى: {window}</div>', unsafe_allow_html=True)

    ts = build_spread_timeseries(row["reach"], row["growth_rate"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts["hour"], y=ts["predicted"], name="بدون تدخل (Predicted)", line=dict(color=COLORS["critical"], dash="dash")))
    fig.add_trace(go.Scatter(x=ts["hour"], y=ts["actual"], name="مع تدخل مبكر (Actual محاكاة)", line=dict(color=COLORS["primary"])))
    fig.update_layout(height=300, xaxis_title="الساعات", yaxis_title="الوصول المتوقع", plot_bgcolor="white",
                       paper_bgcolor="white", font=dict(family="Tahoma"), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("⚠️ نموذج رياضي مبسّط مبني على بيانات تجريبية — ليس نموذج تنبؤ إنتاجي حقيقي.")

    # 7) محرك القرار
    st.markdown("### 7️⃣ ماذا يجب أن تفعل الجهة الآن؟")
    rec = recommend_action(row)
    dc1, dc2 = st.columns([1, 2])
    with dc1:
        st.markdown(
            f"""<div class="bayan-card" style="background:{COLORS['bg_light']};">
                <div style="font-size:0.8rem; color:{COLORS['muted']};">التوصية</div>
                <div style="font-size:1.25rem; font-weight:800; color:{COLORS['primary_dark']};">{rec['option']['title']}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with dc2:
        st.markdown("**لماذا هذه التوصية؟**")
        for r in rec["reasons"]:
            st.markdown(f"- {r}")
        st.markdown(f"<div style='font-size:0.82rem; color:{COLORS['muted']};'><b>ما الذي قد يغيّر التوصية؟</b> {rec['what_could_change']}</div>", unsafe_allow_html=True)

    # 8) مولّد المسودة
    st.markdown("### 8️⃣ مولّد المسودة الرسمية")
    if st.button("✍️ إنشاء مسودة توضيح رسمي", key=f"gen_{claim_id}"):
        evidence_list = evidence.to_dict(orient="records")
        draft = generate_response(row, row["agency_name"], evidence_list)
        st.session_state.drafts[claim_id] = draft
        st.session_state.approvals.setdefault(claim_id, {"status": "قيد المراجعة البشرية"})
        st.session_state.claims_runtime[claim_id]["response_status"] = "قيد المراجعة البشرية"
        st.success("تم إنشاء المسودة. يمكنك مراجعتها من صفحة «الردود الرسمية».")

    if claim_id in st.session_state.drafts:
        d = st.session_state.drafts[claim_id]
        st.markdown(
            f"""<div class="bayan-card">
                <div class="bayan-card-title">{d['title']}</div>
                <div style="margin:0.4rem 0;">{d['statement']}</div>
                <div style="font-size:0.85rem; color:{COLORS['muted']};">القناة المقترحة: {d['recommended_channel']}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button("➡️ الانتقال لمراجعة المسودة", key=f"goto_review_{claim_id}"):
            go_to("الردود الرسمية", claim_id)


# =============================================================================
# صفحة: محرك المخاطر (Risk Engine)
# =============================================================================
def page_risk_engine():
    df = get_claims_df()
    st.title("محرك المخاطر")
    st.caption("درجة خطورة قابلة للتفسير (Explainable Risk Score) — محسوبة وليست عشوائية")

    st.markdown("#### منهجية الاحتساب")
    weights_df = pd.DataFrame({
        "العامل": ["سرعة الانتشار", "حجم الجمهور", "حساسية الخدمة", "التعارض مع المصدر الرسمي", "قرب الموعد المذكور"],
        "الوزن": ["25%", "20%", "20%", "20%", "15%"],
    })
    st.table(weights_df)

    st.markdown("#### مستويات الخطورة")
    lc = st.columns(4)
    levels = [("0–30", "منخفض", COLORS["success"]), ("31–60", "متوسط", COLORS["warning"]),
              ("61–80", "مرتفع", COLORS["high"]), ("81–100", "حرج", COLORS["critical"])]
    for col, (rng, label, color) in zip(lc, levels):
        col.markdown(f"""<div class="bayan-card" style="text-align:center; border-top:4px solid {color};">
            <div style="font-weight:700;">{label}</div><div style="color:{COLORS['muted']};">{rng}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    claim_id = st.selectbox("اختر حالة لعرض تفصيل الخطورة", df["id"].tolist(),
                             format_func=lambda x: f"{x} — {df[df['id']==x]['content'].values[0][:60]}")
    row = df[df["id"] == claim_id].iloc[0].to_dict()
    breakdown = compute_risk_breakdown(row)

    b1, b2 = st.columns([1, 2])
    with b1:
        lvl = risk_level(breakdown["total"])
        st.markdown(f"""<div class="bayan-card" style="text-align:center;">
            <div style="font-size:2.6rem; font-weight:800; color:{lvl['color']};">{breakdown['total']}/100</div>
            <div>{risk_pill(breakdown['total'])}</div></div>""", unsafe_allow_html=True)
        for f in ["speed", "audience", "service_sensitivity", "official_conflict", "time_urgency"]:
            item = breakdown[f]
            st.markdown(f"**{item['label']}:** {item['points']}/{item['max']}")
    with b2:
        st.plotly_chart(render_risk_breakdown_chart(breakdown), use_container_width=True)

    st.markdown("---")
    st.markdown("#### توزيع الحالات حسب مستوى الخطورة")
    dist = df["risk_label"].value_counts().reindex(["منخفض", "متوسط", "مرتفع", "حرج"]).fillna(0).reset_index()
    dist.columns = ["المستوى", "عدد الحالات"]
    color_map = {"منخفض": COLORS["success"], "متوسط": COLORS["warning"], "مرتفع": COLORS["high"], "حرج": COLORS["critical"]}
    fig = px.bar(dist, x="المستوى", y="عدد الحالات", color="المستوى", color_discrete_map=color_map)
    fig.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white", showlegend=False, font=dict(family="Tahoma"))
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# صفحة: محرك القرار (Decision Engine)
# =============================================================================
def page_decision_engine():
    df = get_claims_df()
    st.title("محرك القرار الذكي")
    st.caption('"ماذا يجب أن تفعل الجهة الآن؟" — قرار قابل للتفسير والتدقيق (Explainable · Auditable · Traceable)')

    st.markdown("#### خيارات الاستجابة المتاحة")
    opt_df = pd.DataFrame(DECISION_OPTIONS)[["title", "impact", "speed", "risk_of_inaction"]]
    opt_df.columns = ["الخيار", "الأثر المتوقع", "سرعة الاستجابة", "مخاطر عدم التدخل"]
    st.table(opt_df)

    st.markdown("---")
    claim_id = st.selectbox("اختر حالة لعرض توصية محرك القرار", df["id"].tolist(),
                             format_func=lambda x: f"{x} — {df[df['id']==x]['content'].values[0][:60]}")
    row = df[df["id"] == claim_id].iloc[0].to_dict()
    rec = recommend_action(row)
    priority = compute_decision_priority(row)

    p1, p2 = st.columns([1, 2])
    with p1:
        st.markdown(f"""<div class="bayan-card" style="text-align:center; background:{COLORS['bg_light']};">
            <div style="font-size:0.8rem; color:{COLORS['muted']};">التوصية</div>
            <div style="font-size:1.3rem; font-weight:800; color:{COLORS['primary_dark']};">{rec['option']['title']}</div>
            <div style="margin-top:0.5rem;">{priority_pill(priority['code'], priority['label'])}</div>
            <div style="font-size:0.75rem; color:{COLORS['muted']}; margin-top:0.3rem;">Decision Priority: {priority['score']}/100</div>
        </div>""", unsafe_allow_html=True)
    with p2:
        st.markdown("**Why this recommendation؟**")
        for r in rec["reasons"]:
            st.markdown(f"- {r}")
        st.markdown("**Evidence supporting it:**")
        ev = sources_df[sources_df["related_claim"] == claim_id]
        if not ev.empty:
            for _, e in ev.head(3).iterrows():
                st.markdown(f"- {e['source_name']} ({e['source_type']})")
        else:
            st.markdown("- لا تتوفر أدلة إضافية بعد.")
        st.markdown(f"**What could change the recommendation?** {rec['what_could_change']}")

    st.markdown("---")
    st.markdown("#### توزيع أولويات القرار عبر الحالات")
    pdist = df["priority_code"].value_counts().reindex(["P1", "P2", "P3", "P4"]).fillna(0).reset_index()
    pdist.columns = ["الأولوية", "عدد الحالات"]
    color_map = {"P1": COLORS["critical"], "P2": COLORS["high"], "P3": COLORS["warning"], "P4": COLORS["success"]}
    fig = px.bar(pdist, x="الأولوية", y="عدد الحالات", color="الأولوية", color_discrete_map=color_map)
    fig.update_layout(height=280, plot_bgcolor="white", paper_bgcolor="white", showlegend=False, font=dict(family="Tahoma"))
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# صفحة: الردود الرسمية (مراجعة واعتماد المسودات)
# =============================================================================
def page_responses():
    df = get_claims_df()
    st.title("الردود الرسمية")
    st.markdown(
        '<div class="bayan-banner">🤖 الذكاء الاصطناعي يقترح — والقرار النهائي للجهة المختصة.</div>',
        unsafe_allow_html=True,
    )

    with_drafts = [cid for cid in st.session_state.drafts.keys()]
    if not with_drafts:
        st.info("لا توجد مسودات حتى الآن. توجّه إلى «التحقيق الذكي» واضغط «إنشاء مسودة توضيح رسمي» لأي حالة.")
        return

    claim_id = st.selectbox("اختر مسودة لمراجعتها", with_drafts,
                             index=with_drafts.index(st.session_state.selected_claim) if st.session_state.selected_claim in with_drafts else 0,
                             format_func=lambda x: f"{x} — {df[df['id']==x]['content'].values[0][:60]}")
    st.session_state.selected_claim = claim_id
    row = df[df["id"] == claim_id].iloc[0].to_dict()
    draft = st.session_state.drafts[claim_id]
    approval = st.session_state.approvals.get(claim_id, {"status": "قيد المراجعة البشرية"})

    st.markdown(f"**الحالة الحالية:** {status_pill(approval['status'])}", unsafe_allow_html=True)

    edited_title = st.text_input("عنوان المسودة", draft["title"], key=f"title_{claim_id}")
    edited_statement = st.text_area("نص التوضيح الرسمي", draft["statement"], height=140, key=f"stmt_{claim_id}")

    with st.expander("📌 الحقائق الأساسية / مراجعة الأدلة"):
        for kf in draft["key_facts"]:
            st.markdown(f"- {kf}")
        st.markdown(f"**الأدلة المستخدمة:** {', '.join(draft['evidence_used']) or 'لا يوجد'}")
        st.markdown(f"**القناة المقترحة للنشر:** {draft['recommended_channel']}")

    b1, b2, b3, b4, b5 = st.columns(5)
    if b1.button("💾 حفظ التعديل", key=f"save_{claim_id}"):
        draft["title"] = edited_title
        draft["statement"] = edited_statement
        st.session_state.drafts[claim_id] = draft
        st.success("تم حفظ التعديلات على المسودة.")

    if b2.button("🔁 إعادة توليد", key=f"regen_{claim_id}"):
        evidence_list = sources_df[sources_df["related_claim"] == claim_id].to_dict(orient="records")
        st.session_state.drafts[claim_id] = generate_response(row, row["agency_name"], evidence_list)
        st.rerun()

    if b3.button("✅ اعتماد", key=f"approve_{claim_id}"):
        st.session_state.approvals[claim_id] = {
            "status": "معتمد ومنشور",
            "reviewer": REVIEWER_NAME,
            "approval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "decision": "اعتماد",
        }
        st.session_state.claims_runtime[claim_id]["response_status"] = "معتمد ومنشور"
        st.rerun()

    if b4.button("❌ رفض", key=f"reject_{claim_id}"):
        st.session_state.approvals[claim_id] = {
            "status": "مرفوض",
            "reviewer": REVIEWER_NAME,
            "approval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "decision": "رفض",
        }
        st.session_state.claims_runtime[claim_id]["response_status"] = "مرفوض"
        st.rerun()

    if b5.button("✏️ طلب تعديل", key=f"revise_{claim_id}"):
        st.session_state.approvals[claim_id] = {"status": "قيد المراجعة البشرية"}
        st.session_state.claims_runtime[claim_id]["response_status"] = "قيد المراجعة البشرية"
        st.info("تم تحويل المسودة لطلب تعديل إضافي.")

    if approval["status"] == "معتمد ومنشور" and "reviewer" in approval:
        st.success(
            f"✅ معتمد بشريًا بواسطة {approval['reviewer']} ({REVIEWER_ROLE}) — "
            f"بتاريخ {approval['approval_time']}"
        )
        st.caption("🔒 لا يمكن الوصول لمرحلة النشر الرسمي إلا بعد اعتماد بشري صريح — لا يوجد نشر تلقائي بواسطة الذكاء الاصطناعي.")


# =============================================================================
# صفحة: دورة الاستجابة (Response Cycle)
# =============================================================================
def page_response_cycle():
    df = get_claims_df()
    st.title("دورة الاستجابة")

    st.markdown('<div class="bayan-banner">🤖 الذكاء الاصطناعي يقترح — والقرار النهائي للجهة المختصة.</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align:center; margin-bottom:1.2rem;">
        <span class="pill pill-ai">توصية الذكاء الاصطناعي</span> ↓
        <span class="pill pill-ai">إنشاء المسودة</span> ↓
        <span class="pill pill-warning">مراجعة بشرية</span> ↓
        <span class="pill pill-warning">اعتماد بشري</span> ↓
        <span class="pill pill-success">نشر رسمي</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("🚫 لا يمكن الوصول إلى مرحلة النشر الرسمي إلا بعد اعتماد بشري صريح.")

    st.markdown("---")
    claim_id = st.selectbox("اختر حالة لعرض دورة الاستجابة الكاملة", df["id"].tolist(),
                             format_func=lambda x: f"{x} — {df[df['id']==x]['content'].values[0][:60]}")

    st.markdown("#### الخط الزمني للاستجابة (Response Timeline)")
    rt = render_timeline(claim_id)

    if rt:
        st.markdown("#### أزمنة كل مرحلة (بالدقائق)")
        cols = st.columns(4)
        labels = {
            "detection_to_verification": "الرصد ← التحقق",
            "verification_to_draft": "التحقق ← المسودة",
            "draft_to_approval": "المسودة ← الاعتماد",
            "approval_to_publication": "الاعتماد ← النشر",
        }
        for i, key in enumerate(labels):
            val = rt.get(key)
            cols[i].metric(labels[key], f"{val} د" if val is not None else "—")
        if rt.get("total"):
            st.metric("إجمالي زمن الاستجابة (Total Response Time)", f"{rt['total']} دقيقة")

    st.markdown("---")
    st.markdown("#### تحليلات زمن الاستجابة — تسريع الرد الرسمي")
    st.caption("Simulation / Prototype Scenario — مقارنة توضيحية وليست نتيجة تشغيل حقيقية.")

    bayan_minutes = rt.get("total") if rt and rt.get("total") else 6.5
    comp = compute_reduction_vs_baseline(bayan_minutes)

    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Baseline (تقليدي)", f"{comp['baseline_minutes']} دقيقة")
    cc2.metric("BAYAN-assisted", f"{comp['bayan_minutes']} دقيقة")
    cc3.metric("نسبة التسريع", f"{comp['reduction_pct']}%")

    fig = go.Figure(go.Bar(
        x=["Baseline (تقليدي)", "BAYAN-assisted"],
        y=[comp["baseline_minutes"], comp["bayan_minutes"]],
        marker_color=[COLORS["muted"], COLORS["primary"]],
        text=[f"{comp['baseline_minutes']} د", f"{comp['bayan_minutes']} د"],
        textposition="outside",
    ))
    fig.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white", yaxis_title="الدقائق", font=dict(family="Tahoma"))
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# صفحة: أثر الاستجابة (Response Impact)
# =============================================================================
def page_impact():
    df = get_claims_df()
    st.title("أثر الاستجابة")
    st.caption("قياس الأثر الفعلي للاستجابة الرسمية على معدل الانتشار (بيانات محاكاة)")

    published = df[df["response_status"] == "معتمد ومنشور"]
    options = published["id"].tolist() if not published.empty else df["id"].tolist()
    claim_id = st.selectbox("اختر حالة لعرض أثر الاستجابة", options,
                             format_func=lambda x: f"{x} — {df[df['id']==x]['content'].values[0][:60]}")
    row = df[df["id"] == claim_id].iloc[0].to_dict()

    growth_before = row["growth_rate"]
    growth_after = round(growth_before * 0.32, 1)  # محاكاة أثر الاستجابة على معدل النمو
    reach_before = row["reach"]
    preds = predict_spread(reach_before, growth_before, hours_list=(12,))
    predicted_no_action = preds[12]
    reach_after_actual = int(reach_before * ((1 + growth_after / 100) ** 12))

    eff = compute_response_effectiveness(
        growth_before, growth_after, response_minutes=6.5,
        reach_before=reach_before, reach_after_actual=reach_after_actual,
        reach_predicted_no_action=predicted_no_action,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("معدل النمو قبل الاستجابة", f"{growth_before}%/ساعة")
    c2.metric("معدل النمو بعد الاستجابة", f"{growth_after}%/ساعة")
    c3.metric("نسبة تراجع الانتشار", f"{eff['reach_reduction_pct']}%")
    c4.metric("Response Effectiveness", f"{eff['effectiveness']}/100")

    st.markdown("---")
    hours = list(range(0, 13, 1))
    before_curve = [reach_before * ((1 + growth_before / 100) ** h) for h in hours if h <= 3]
    response_point = len(before_curve) - 1
    after_curve = [before_curve[-1] * ((1 + growth_after / 100) ** (h - response_point)) for h in hours[response_point:]]
    full_hours = hours[:response_point] + hours[response_point:]
    full_values = before_curve[:-1] + after_curve

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours[:response_point + 1], y=before_curve, name="قبل الاستجابة", line=dict(color=COLORS["critical"])))
    fig.add_trace(go.Scatter(x=hours[response_point:], y=after_curve, name="بعد الاستجابة", line=dict(color=COLORS["primary"])))
    fig.add_vline(x=response_point, line_dash="dash", line_color=COLORS["accent"],
                  annotation_text="نشر الرد الرسمي", annotation_position="top")
    fig.update_layout(height=340, xaxis_title="الساعات", yaxis_title="الوصول (Reach)",
                       plot_bgcolor="white", paper_bgcolor="white", font=dict(family="Tahoma"))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"""
        <div class="bayan-card">
            <b>ملخص الأثر:</b> بعد نشر الرد الرسمي، انخفض معدل نمو انتشار الادعاء من
            <b>{growth_before}%</b> إلى <b>{growth_after}%</b> في الساعة، بما يعادل تراجعًا في الوصول
            المتوقع بنسبة <b>{eff['reach_reduction_pct']}%</b> مقارنة بسيناريو عدم التدخل.
            درجة فعالية الاستجابة الإجمالية: <b>{eff['effectiveness']}/100</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# صفحة: سجل الحالات (Case History)
# =============================================================================
def page_case_history():
    df = get_claims_df()
    st.title("سجل الحالات")
    st.caption("سجل تدقيق كامل لجميع الحالات المرصودة والقرارات المتخذة بشأنها")

    table = df[["id", "content", "agency_name", "risk_score", "priority_label", "response_status"]].copy()
    table.columns = ["رقم الحالة", "الادعاء", "الجهة", "الخطورة", "القرار/الأولوية", "حالة الاستجابة"]
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.markdown("---")
    claim_id = st.selectbox("افتح حالة لعرض دورة القرار الكاملة", df["id"].tolist(),
                             format_func=lambda x: f"{x} — {df[df['id']==x]['content'].values[0][:60]}")
    row = df[df["id"] == claim_id].iloc[0]
    approval = st.session_state.approvals.get(claim_id)

    st.markdown(f"### {row['content']}")
    st.markdown(
        f"{risk_pill(row['risk_score'])} {priority_pill(row['priority_code'], row['priority_label'])} {status_pill(row['response_status'])}",
        unsafe_allow_html=True,
    )
    if approval and approval.get("reviewer"):
        st.caption(f"المراجع: {approval['reviewer']} ({REVIEWER_ROLE}) — القرار: {approval.get('decision','-')} — بتاريخ {approval.get('approval_time','-')}")

    st.markdown("#### الخط الزمني الكامل للقرار")
    render_timeline(claim_id)


# =============================================================================
# صفحة: العرض التجريبي (Demo Mode)
# =============================================================================
DEMO_STEPS = [
    "الرصد", "استخراج الادعاء", "تحديد الجهة", "التحقق", "الأدلة", "Risk Score",
    "توقع الانتشار", "Decision Recommendation", "Generate Draft", "Human Review",
    "Human Approval", "Publication", "Impact",
]
DEMO_CLAIM_ID = "CLM006"  # حالة حرجة جاهزة للعرض


def page_demo():
    df = get_claims_df()
    row = df[df["id"] == DEMO_CLAIM_ID].iloc[0].to_dict()

    st.title("🚀 العرض التجريبي")
    st.markdown('<div class="demo-banner">يعرض هذا المسار حالة حرجة جاهزة عبر دورة الاستجابة الكاملة لبَيَان.</div>', unsafe_allow_html=True)

    step = st.session_state.demo_step
    progress = (step + 1) / len(DEMO_STEPS)
    st.progress(progress, text=f"الخطوة {step+1} من {len(DEMO_STEPS)}: {DEMO_STEPS[step]}")

    st.markdown(f"### {DEMO_STEPS[step]}")

    if step == 0:
        st.markdown(f"""<div class="bayan-card">تم رصد محتوى متداول:<br><b>{row['content']}</b><br>
        المصدر: {row['source']}</div>""", unsafe_allow_html=True)
    elif step == 1:
        ext = extract_claim({**row, "agency_name": row["agency_name"]})
        st.json(ext)
    elif step == 2:
        st.markdown(f"**الجهة المحتملة:** {row['agency_name']}  \n**الخدمة:** {row['service']}")
    elif step == 3:
        v = verify_claim(row)
        st.markdown(status_pill(v["status"]), unsafe_allow_html=True)
        for r in v["reasons"]:
            st.markdown(f"- {r}")
    elif step == 4:
        evidence = sources_df[sources_df["related_claim"] == DEMO_CLAIM_ID]
        for _, e in evidence.iterrows():
            st.markdown(f"- **{e['source_name']}** ({e['source_type']}) — {e['description']}")
    elif step == 5:
        breakdown = compute_risk_breakdown(row)
        st.plotly_chart(render_risk_breakdown_chart(breakdown), use_container_width=True)
        st.metric("Risk Score", f"{breakdown['total']}/100")
    elif step == 6:
        preds = predict_spread(row["reach"], row["growth_rate"])
        c1, c2, c3 = st.columns(3)
        c1.metric("خلال 6 ساعات", f"{preds[6]:,}")
        c2.metric("خلال 12 ساعة", f"{preds[12]:,}")
        c3.metric("خلال 24 ساعة", f"{preds[24]:,}")
    elif step == 7:
        rec = recommend_action(row)
        st.markdown(f"**التوصية:** {rec['option']['title']}")
        for r in rec["reasons"]:
            st.markdown(f"- {r}")
    elif step == 8:
        evidence_list = sources_df[sources_df["related_claim"] == DEMO_CLAIM_ID].to_dict(orient="records")
        draft = generate_response(row, row["agency_name"], evidence_list)
        st.session_state.drafts[DEMO_CLAIM_ID] = draft
        st.markdown(f"""<div class="bayan-card"><b>{draft['title']}</b><br>{draft['statement']}</div>""", unsafe_allow_html=True)
    elif step == 9:
        st.markdown('<div class="bayan-banner">🤖 الذكاء الاصطناعي يقترح — والقرار النهائي للجهة المختصة.</div>', unsafe_allow_html=True)
        st.markdown(f"المسودة الآن قيد مراجعة **{REVIEWER_NAME}** ({REVIEWER_ROLE}).")
    elif step == 10:
        st.session_state.approvals[DEMO_CLAIM_ID] = {
            "status": "معتمد ومنشور", "reviewer": REVIEWER_NAME,
            "approval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "decision": "اعتماد",
        }
        st.session_state.claims_runtime[DEMO_CLAIM_ID]["response_status"] = "معتمد ومنشور"
        st.success(f"✅ تم الاعتماد البشري بواسطة {REVIEWER_NAME}")
    elif step == 11:
        st.success("📢 تم نشر التوضيح الرسمي عبر القناة المعتمدة.")
    elif step == 12:
        eff = compute_response_effectiveness(
            row["growth_rate"], round(row["growth_rate"] * 0.3, 1), 6.5,
            row["reach"], int(row["reach"] * 1.4), predict_spread(row["reach"], row["growth_rate"], (12,))[12],
        )
        st.metric("Response Effectiveness", f"{eff['effectiveness']}/100")
        st.markdown(f"**تراجع الوصول المتوقع:** {eff['reach_reduction_pct']}%")

    st.markdown("---")
    nav1, nav2, nav3 = st.columns([1, 1, 2])
    with nav1:
        if step > 0 and st.button("⬅️ السابق"):
            st.session_state.demo_step -= 1
            st.rerun()
    with nav2:
        if step < len(DEMO_STEPS) - 1 and st.button("التالي ➡️"):
            st.session_state.demo_step += 1
            st.rerun()

    if step == len(DEMO_STEPS) - 1:
        st.markdown("---")
        st.markdown("## ✅ تم تحويل حالة تضليل حرجة إلى استجابة رسمية معتمدة")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Response Time", "6.5 دقيقة")
        m2.metric("Risk Before Intervention", f"{compute_risk_score(row)}/100")
        m3.metric("Predicted Reach (No Action)", f"{predict_spread(row['reach'], row['growth_rate'], (12,))[12]:,}")
        m4.metric("Actual Simulated Reach", f"{int(row['reach']*1.4):,}")
        if st.button("🔄 إعادة تشغيل العرض التجريبي"):
            st.session_state.demo_step = 0
            st.rerun()


# =============================================================================
# التوجيه (Router)
# =============================================================================
sidebar_nav()

PAGES = {
    "الرئيسية": page_home,
    "لوحة القيادة": page_dashboard,
    "مركز الرصد": page_monitoring,
    "التحقيق الذكي": page_investigation,
    "محرك المخاطر": page_risk_engine,
    "محرك القرار": page_decision_engine,
    "الردود الرسمية": page_responses,
    "دورة الاستجابة": page_response_cycle,
    "أثر الاستجابة": page_impact,
    "سجل الحالات": page_case_history,
    "العرض التجريبي": page_demo,
}

page_fn = PAGES.get(st.session_state.page, page_home)
page_fn()

st.markdown(
    """
    <div class="footer-note">
    BAYAN | Prototype — نموذج أولي تجريبي — البيانات محاكاة لأغراض العرض.
    </div>
    """,
    unsafe_allow_html=True,
)

