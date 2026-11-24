import random
import streamlit as st

st.set_page_config(page_title="ليلة المواجهة", page_icon="🎡", layout="centered")

CATS = [
    {"name": "المواجهة والجرأة", "emoji": "🔥", "color": "#e85d75", "q": [
        "ما الشيء الذي تخفيه خلف ابتسامتك؟", "هل سبق أن ندمت على ثقتك بشخص؟",
        "من آخر شخص تمنيت أن يبادر بالاعتذار؟", "ما الحقيقة التي تخاف مواجهتها؟",
        "هل تستطيع الاعتراف بخطئك أمام الجميع؟",
        "ما الموقف الذي تتمنى لو أنك تصرفت فيه بشكل مختلف؟"]},
    {"name": "النفس والشخصية", "emoji": "🧠", "color": "#8064d8", "q": [
        "ما أكثر صفة فيك لا يفهمها الآخرون؟", "هل أنت قاسٍ على نفسك أكثر من اللازم؟",
        "ما الشيء الذي تغير في شخصيتك مؤخرًا؟", "متى تشعر أنك على طبيعتك تمامًا؟",
        "هل تهرب من مشاعرك أم تواجهها؟", "ما الصفة التي تحبها في نفسك؟"]},
    {"name": "الحب والمشاعر", "emoji": "❤️", "color": "#e66b9a", "q": [
        "هل الاشتياق سبب كافٍ للعودة؟", "هل يمكن أن تحب شخصًا ولا تثق به؟",
        "ما الذي يجعلك تفقد اهتمامك بشخص؟", "هل تفضل الاعتذار أم المبادرة؟",
        "هل سبق أن أحببت شخصًا بصمت؟", "أيهما أصعب: الفراق أم الخذلان؟"]},
    {"name": "الضحك والجنون", "emoji": "😂", "color": "#e8a23a", "q": [
        "قلّد لاعبًا موجودًا حتى يعرف نفسه!", "ما أغرب موقف محرج حصل لك؟",
        "تكلم بلهجة مختلفة لمدة دقيقة.",
        "اذكر ثلاثة أشياء لا تستطيع العيش بدونها خلال 5 ثوانٍ.",
        "اختر لاعبًا وامدحه بطريقة مضحكة.",
        "مثّل أنك مذيع أخبار يعلن نتيجة اللودو!"]},
    {"name": "اختيارات صعبة", "emoji": "⚡", "color": "#249eaa", "q": [
        "الكرامة أم الاشتياق؟ ولماذا؟",
        "أن تعرف الحقيقة المؤلمة أم تعيش مرتاحًا بوهم؟", "أن تُحَب أم أن تُفهَم؟",
        "النسيان أم فرصة ثانية؟", "الصراحة الجارحة أم المجاملة اللطيفة؟",
        "قلبك أم عقلك عندما يتعارضان؟"]},
    {"name": "أسرار واعترافات", "emoji": "🤫", "color": "#4d9a79", "q": [
        "ما سر صغير لم تخبر به أحدًا؟", "ما أكثر شيء تتظاهر بأنه لا يهمك؟",
        "هل حكمت على شخص ثم اكتشفت أنك مخطئ؟",
        "ما الرسالة التي تمنيت إرسالها ولم تفعل؟",
        "ما الشيء الذي تتمنى أن يسألك عنه أحد؟", "ما مجاملة ما زلت تتذكرها؟"]},
]

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], .main { direction: rtl; text-align: right; }
[data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#fff8ec,#f7f2ff);}
.hero{background:linear-gradient(135deg,#ff8da7,#a58cf4);color:#fff;border-radius:28px;
      padding:22px;text-align:center;margin-bottom:16px}
.hero h1{color:#fff;margin:4px 0;padding:0}
.result{border:2px solid #ff8da7;background:#fff;border-radius:22px;padding:22px;
        text-align:center;margin:16px 0;color:#34243f}
.tag{display:inline-block;background:#ffe0e9;color:#a53e61;padding:6px 12px;
     border-radius:30px;font-weight:700;font-size:14px}
.q{font-size:26px;font-weight:800;line-height:1.7;margin:12px 0}
.small{color:#786b83;font-size:13px}
.hist span{display:inline-block;background:#f1ecfa;color:#34243f;padding:6px 10px;
           border-radius:30px;font-size:13px;margin:3px}
.stButton>button{width:100%;border-radius:16px;font-weight:700;padding:.7rem}
</style>
<div class="hero"><div style="font-size:38px">🎡✨</div><h1>ليلة المواجهة</h1>
<div>اسأل.. واجه.. واكتشف!</div></div>
""", unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("round", 0)
ss.setdefault("hist", [])
ss.setdefault("cur", None)

def spin():
    c = random.choice(CATS)
    ss.cur = {"cat": c, "q": random.choice(c["q"])}
    ss.round += 1
    ss.hist = ([f'{c["emoji"]} {c["name"]}'] + ss.hist)[:6]

def reset():
    ss.round, ss.hist, ss.cur = 0, [], None
    ss.player = ""

player = st.text_input("🎤 اسم اللاعب (اختياري)", key="player",
                       placeholder="اكتب اسم اللاعب الحالي...")

cols = st.columns(3)
for i, c in enumerate(CATS):
    active = ss.cur and ss.cur["cat"] is c
    cols[i % 3].markdown(
        f'<div style="background:{c["color"]};color:#fff;border-radius:18px;padding:14px 6px;'
        f'text-align:center;font-weight:700;margin-bottom:10px;'
        f'{"outline:4px solid #34243f;" if active else ""}">'
        f'<div style="font-size:28px">{c["emoji"]}</div><small>{c["name"]}</small></div>',
        unsafe_allow_html=True)

st.button("🎲 أدر عجلة الحظ!", on_click=spin, type="primary")

if ss.cur:
    c, q = ss.cur["cat"], ss.cur["q"]
    who = f'<div class="small">الدور على: {player.strip()}</div>' if player.strip() else ""
    st.markdown(f'<div class="result"><span class="tag">{c["emoji"]} {c["name"]}</span>{who}'
                f'<div class="q">{q}</div>'
                f'<div class="small">الجولة رقم {ss.round} · جاوب بصراحة أو اختر تحديًا!</div></div>',
                unsafe_allow_html=True)
else:
    st.markdown('<div class="result"><div style="font-size:35px">👀</div>'
                '<div class="q">مستعدين؟</div>'
                '<div class="small">اضغطوا على العجلة لاختيار أول مواجهة!</div></div>',
                unsafe_allow_html=True)

b1, b2 = st.columns(2)
b1.button("سؤال جديد ↻", on_click=spin)
b2.button("إعادة ضبط", on_click=reset)

st.markdown("**📜 سجل الجولات**")
st.markdown('<div class="hist">' + ("".join(f"<span>{h}</span>" for h in ss.hist)
            or "<span>لم تبدأ اللعبة بعد</span>") + "</div>", unsafe_allow_html=True)
st.caption("صُممت للّمة الحلوة 💗 — العبوا بروح مرحة واحترموا حق أي لاعب في تخطي السؤال.")
