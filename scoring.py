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
