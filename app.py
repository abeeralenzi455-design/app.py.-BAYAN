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

from scoring import (
    compute_risk_breakdown,
    compute_risk_score,
    risk_level,
    compute_decision_priority,
    compute_response_effectiveness,
)

from analysis import (
    predict_spread,
    optimal_intervention_window,
    build_spread_timeseries,
    extract_claim,
    verify_claim,
    response_time_breakdown,
    compute_reduction_vs_baseline,
)

from decision_engine import DECISION_OPTIONS, recommend_action
from response_generator import generate_response

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
    claims = pd.read_csv(os.path.join(DATA_DIR, "claims.csv"))
    sources = pd.read_csv(os.path.join(DATA_DIR, "sources.csv"))
    events = pd.read_csv(os.path.join(DATA_DIR, "events.csv"))
    agencies = pd.read_csv(os.path.join(DATA_DIR, "agencies.csv"))

    claims = claims.merge(
        agencies[["agency_id", "agency_name"]], left_on="agency", right_on="agency_id", how="left"
    )
    claims["timestamp"] = pd.to_datetime(claims["timestamp"])

    # حساب الدرجات مرة واحدة عبر محرك التسجيل الموحّد (scoring.py) لضمان الاتساق
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
