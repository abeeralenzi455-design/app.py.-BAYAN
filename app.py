import html
import random
import threading
import streamlit as st

st.set_page_config(page_title="ليلة المواجهة", page_icon="🎡", layout="centered")

# ══════════ إعدادات يعدّلها المقدم ══════════
ROOM_LINK_TEXT = "رابط خاص في روم مزح ولعب"
ROOM_ID = "31130"
PLATFORM_TEXT = "تنسيق منصة المواجهة :"
PRESENTER_DEFAULT = ""          # اسم المقدم الافتراضي (تقدر تكتبه هنا أو من لوحة المقدم)


def _secret(key, default):
    try:
        return st.secrets[key]
    except Exception:
        return default


HOST_PIN = str(_secret("HOST_PIN", "1234"))   # غيّره! أو حطه في .streamlit/secrets.toml

# ══════════ الفئات والأسئلة ══════════
CATS = [
    {"name": "المواجهة والجرأة", "emoji": "🔥", "color": "#e85d75", "q": [
        "ما الشيء الذي تخفيه خلف ابتسامتك؟",
        "هل سبق أن ندمت على ثقتك بشخص؟",
        "من آخر شخص تمنيت أن يبادر بالاعتذار؟",
        "ما الحقيقة التي تخاف مواجهتها؟",
        "هل تستطيع الاعتراف بخطئك أمام الجميع؟",
        "ما الموقف الذي تتمنى لو أنك تصرفت فيه بشكل مختلف؟",
        "ما أجرأ قرار اتخذته في حياتك، وهل كان يستحق؟",
        "لو تقدر تقول جملة واحدة لنفسك قبل خمس سنوات، ماذا تقول؟",
        "ما الأمر الذي أجّلته طويلًا وأنت تعرف أنه لا بد أن تواجهه؟",
        "متى كانت آخر مرة قلت فيها «لا» وأنت تتمنى قول «نعم»؟",
        "ما الشيء الذي يسيء الناس فهمه عنك أول ما يتعرفون عليك؟",
        "لو طُلب منك الدفاع عن رأي لا تؤمن به، أي رأي تختار؟",
        "أي كلمة أصعب عليك نطقها: «آسف» أم «شكرًا» أم «أحتاجك»؟",
        "ما الشيء الذي لو فعلته اليوم لشعرت بالفخر بنفسك غدًا؟",
        "هل دافعت يومًا عن شخص غائب؟ وكيف كان شعورك؟"]},
    {"name": "النفس والشخصية", "emoji": "🧠", "color": "#8064d8", "q": [
        "ما أكثر صفة فيك لا يفهمها الآخرون؟",
        "هل أنت قاسٍ على نفسك أكثر من اللازم؟",
        "ما الشيء الذي تغير في شخصيتك مؤخرًا؟",
        "متى تشعر أنك على طبيعتك تمامًا؟",
        "هل تهرب من مشاعرك أم تواجهها؟",
        "ما الصفة التي تحبها في نفسك؟",
        "لو كتبت عنوانًا لكتاب حياتك حتى الآن، ما هو؟",
        "ما العادة الصغيرة التي لو تغيّرت فيك لتغيّرت حياتك؟",
        "ما الشيء الذي تتقنه ولا يعرف عنه كثيرون؟",
        "في أي مرحلة من عمرك كنت أسعد نسخة من نفسك؟",
        "ما أغلى درس تعلمته من خطأ ارتكبته؟",
        "ما الذي يستنزف طاقتك دون أن يلاحظ أحد؟",
        "ما الجانب في شخصيتك الذي تقدّمه للعالم كهدية؟",
        "ما الشيء الذي تحتاج أن تسامح نفسك عليه؟",
        "ما الشيء الذي يجعلك تشعر أنك حيّ فعلًا؟"]},
    {"name": "الحب والمشاعر", "emoji": "❤️", "color": "#e66b9a", "q": [
        "هل الاشتياق سبب كافٍ للعودة؟",
        "هل يمكن أن تحب شخصًا ولا تثق به؟",
        "ما الذي يجعلك تفقد اهتمامك بشخص؟",
        "هل تفضل الاعتذار أم المبادرة؟",
        "هل سبق أن أحببت شخصًا بصمت؟",
        "أيهما أصعب: الفراق أم الخذلان؟",
        "ما أجمل تصرف بسيط من شخص جعلك تقدّره أكثر؟",
        "هل الحب يُولد من أول نظرة أم يُبنى بالأيام؟",
        "ما لغتك في التعبير عن المحبة: كلمات، وقت، هدايا، خدمة، أم حضور؟",
        "هل يمكن أن تكون الصداقة أعمق من الحب؟",
        "ما الشيء الذي لا تغفره في العلاقات مهما كان؟",
        "متى تشعر أنك محبوب بصدق؟",
        "أيهما أبقى أثرًا: كلمة جميلة سمعتها أم موقف جميل عشته؟",
        "ما أصدق شعور مررت به ولم تعرف كيف تسمّيه؟",
        "الغيرة: دليل حب أم دليل قلة ثقة؟"]},
    {"name": "الضحك والجنون", "emoji": "😂", "color": "#e8a23a", "q": [
        "قلّد لاعبًا موجودًا حتى يعرف نفسه!",
        "ما أغرب موقف محرج حصل لك؟",
        "تكلم بلهجة مختلفة لمدة دقيقة.",
        "اذكر ثلاثة أشياء لا تستطيع العيش بدونها خلال 5 ثوانٍ.",
        "اختر لاعبًا وامدحه بطريقة مضحكة.",
        "مثّل أنك مذيع أخبار يعلن نتيجة اللودو!",
        "احكِ قصة حياتك في 20 ثانية بأسلوب فيلم تشويق!",
        "لو كنت حيوانًا ليوم واحد، أي حيوان تختار وماذا تفعل؟",
        "اخترع اختراعًا غريبًا وسوّق له كأنك في إعلان تجاري!",
        "قل «ليلة المواجهة» بخمس نبرات: حزين، غاضب، مرعوب، متحمس، شاعر.",
        "ما أغرب أكلة جربتها، وهل تنصح بها؟",
        "اختر أي شيء قريب منك وسوّق له كبائع محترف خلال 20 ثانية.",
        "لو كنت شخصية كرتونية، من تكون ولماذا؟",
        "غنِّ أول جملة تخطر على بالك بصوت أوبرا!",
        "مثّل ردة فعلك لما يسقط الجوال على وجهك وأنت مستلقٍ."]},
    {"name": "اختيارات صعبة", "emoji": "⚡", "color": "#249eaa", "q": [
        "الكرامة أم الاشتياق؟ ولماذا؟",
        "أن تعرف الحقيقة المؤلمة أم تعيش مرتاحًا بوهم؟",
        "أن تُحَب أم أن تُفهَم؟",
        "النسيان أم فرصة ثانية؟",
        "الصراحة الجارحة أم المجاملة اللطيفة؟",
        "قلبك أم عقلك عندما يتعارضان؟",
        "السفر مجانًا مدى الحياة أم بيت أحلامك؟",
        "أن تكون الأذكى في الغرفة أم الأطيب فيها؟",
        "صديق واحد يفهمك تمامًا أم عشرة أصدقاء يضحّكونك؟",
        "أن تنجح وحدك أم تنجح مع فريق بنجاح أقل؟",
        "حياة هادئة بلا مفاجآت أم مغامرة مليئة بالمجهول؟",
        "مهارة واحدة بمستوى خارق أم عشر مهارات بمستوى جيد؟",
        "أن يُذكر اسمك بعد مئة سنة أم تُنسى لكنك سعيد؟",
        "أن تقول الحقيقة وتخسر موقفًا أم تصمت وتحتفظ به؟"]},
    {"name": "أسرار واعترافات", "emoji": "🤫", "color": "#4d9a79", "q": [
        "ما سر صغير لم تخبر به أحدًا؟",
        "ما أكثر شيء تتظاهر بأنه لا يهمك؟",
        "هل حكمت على شخص ثم اكتشفت أنك مخطئ؟",
        "ما الرسالة التي تمنيت إرسالها ولم تفعل؟",
        "ما الشيء الذي تتمنى أن يسألك عنه أحد؟",
        "ما مجاملة ما زلت تتذكرها؟",
        "ما أغرب عادة عندك لا يعرفها إلا أقرب الناس؟",
        "ما الشيء الذي تحب فعله وحدك ولا تخبر به أحدًا؟",
        "ما حلم تخجل أن تقوله بصوت عالٍ؟",
        "ما أكثر شيء أعجبك في أحد الجالسين ولم تقله له؟",
        "متى كانت آخر مرة بكيت فيها من الفرح؟",
        "ما الكذبة البيضاء التي تكررها دائمًا؟",
        "ما الشيء الذي تفتخر به ولا تقوله بصوت عالٍ؟",
        "من الشخص الذي تتمنى أن يعرف كم هو مهم عندك؟",
        "ما الشيء الذي تتمنى لو أخبرك به أحد قبل سنوات؟"]},
    {"name": "ذكريات وطفولة", "emoji": "🎈", "color": "#5b8def", "q": [
        "ما أجمل ذكرى من طفولتك تتمنى لو تعيشها مرة ثانية؟",
        "ما الكرتون أو اللعبة التي كانت تعني لك الدنيا وأنت صغير؟",
        "من كان بطلك في طفولتك، ولماذا؟",
        "ما أول شيء اشتريته بمصروفك وما زلت تتذكره؟",
        "ما الشيء الذي كنت تخاف منه صغيرًا وتضحك عليه الآن؟",
        "ما أغرب شيء كنت تصدّقه وأنت طفل؟",
        "ما الرائحة أو الصوت الذي يرجعك فورًا لأيام زمان؟",
        "ما المقلب الذي لا تنساه من طفولتك؟",
        "ماذا كنت تقول إنك ستصبح لما تكبر، وهل اقتربت منه؟",
        "ما أول مكان تتذكر أنك سافرت إليه؟"]},
    {"name": "خيال وأحلام", "emoji": "🚀", "color": "#f0793a", "q": [
        "لو معك مليون ريال وأسبوع واحد، ماذا تفعل بهما؟",
        "لو تتعشى مع شخصية من التاريخ، من تختار وماذا تسأله؟",
        "لو عندك قوة خارقة ليوم واحد، ماذا تختار وماذا تفعل بها؟",
        "في أي عصر من التاريخ تتمنى أن تعيش؟",
        "لو بنيت جزيرة خاصة بك، ما القوانين الثلاثة الأولى فيها؟",
        "لو تتعلم أي لغة في العالم فورًا، ماذا تختار؟",
        "لو عندك مشروع بلا حدود، ما أول مشروع تبنيه؟",
        "لو تدخل عالم فيلم أو مسلسل تحبه، أي عالم تختار؟",
        "لو تسأل سؤالًا واحدًا وتعرف جوابه بصدق، ما سؤالك؟",
        "كيف تتخيل يومك المثالي من الاستيقاظ حتى النوم؟"]},
]

# ══════════ الغرفة المشتركة (يشوفها كل اللاعبين) ══════════
@st.cache_resource
def get_room():
    return {
        "lock": threading.Lock(),
        "round": 0, "cat": None, "q": None, "anim": False,
        "hist": [], "used": set(),
        "player": "", "presenter": PRESENTER_DEFAULT,
        "answers": [], "skipped": False,
    }


room = get_room()
ss = st.session_state
ss.setdefault("dark", False)
ss.setdefault("is_host", False)
ss.setdefault("answering", None)

esc = html.escape


def _draw(keep_cat):
    with room["lock"]:
        had = keep_cat and room["cat"] is not None
        i = room["cat"] if had else random.randrange(len(CATS))
        c = CATS[i]
        pool = [x for x in c["q"] if x not in room["used"]]
        if not pool:
            room["used"] -= set(c["q"])
            pool = list(c["q"])
        q = random.choice(pool)
        room["used"].add(q)
        room.update(cat=i, q=q, anim=not had, answers=[], skipped=False)
        room["round"] += 1
        room["hist"] = ([f'{c["emoji"]} {c["name"]}'] + room["hist"])[:6]


def spin():
    _draw(False)


def new_q():
    _draw(True)


def reset():
    with room["lock"]:
        room.update(round=0, cat=None, q=None, anim=False, hist=[],
                    answers=[], skipped=False)
        room["used"].clear()


def do_skip():
    room["skipped"] = True


def open_answer():
    ss.answering = room["round"]


def submit_answer():
    t = str(ss.get("ans_text", "")).strip()
    if t:
        with room["lock"]:
            room["answers"] = (room["answers"] + [{"who": room["player"], "text": t[:300]}])[-20:]
        ss.answering = None


def toggle_theme():
    ss.dark = not ss.dark


# ══════════ الثيم (مستقل عن وضع الجوال) ══════════
LIGHT = dict(bg="linear-gradient(135deg,#fff8ec,#f7f2ff)", card="#ffffff", txt="#34243f",
             sub="#786b83", chip="#f1ecfa", inp="#ffffff", bd="#e4d9f5", scheme="light")
DARK = dict(bg="linear-gradient(135deg,#171021,#261a3a)", card="#2c2142", txt="#f4edff",
            sub="#b9aacb", chip="#3b2d55", inp="#221838", bd="#5d4a85", scheme="dark")
T = DARK if ss.dark else LIGHT

st.markdown(
    "<style>:root{"
    f"--bg:{T['bg']};--card:{T['card']};--txt:{T['txt']};--sub:{T['sub']};"
    f"--chip:{T['chip']};--inp:{T['inp']};--bd:{T['bd']};color-scheme:{T['scheme']};"
    "}</style>", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
html, body, .stApp, .stMarkdown, button, input, textarea, label, p {
  font-family:'Cairo',sans-serif;}
html, body, [data-testid="stAppViewContainer"], .main { direction: rtl; text-align: right; }
.stApp, [data-testid="stAppViewContainer"] { background: var(--bg) !important; }
[data-testid="stHeader"] { background: transparent !important; }
.stApp p, .stApp label, .stApp li, .stApp .stMarkdown { color: var(--txt); }

/* الأعمدة تبقى جنب بعض حتى على الجوال */
.stApp [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 12px !important; }
.stApp [data-testid="stColumn"], .stApp [data-testid="column"] { min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; }

/* المربعات العلوية */
.badges { display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-start; margin-bottom:10px; }
.badge { background:linear-gradient(135deg,#ff8da7,#a58cf4); color:#fff !important; padding:8px 14px;
         border-radius:14px; font-weight:800; font-size:14px; box-shadow:0 3px 10px rgba(165,140,244,.35); }
.badge.black { background:#1b1b1f; color:#fff !important; box-shadow:0 3px 10px rgba(0,0,0,.35); }

.hero { background:linear-gradient(135deg,#ff8da7,#a58cf4); color:#fff; border-radius:28px;
        padding:22px 18px; text-align:center; margin-bottom:16px; }
.hero h1 { color:#fff !important; margin:4px 0; padding:0; font-weight:800; }
.hero .sub { font-size:17px; font-weight:600; }
.tagline { margin-top:12px; background:rgba(255,255,255,.22); border-radius:16px; padding:9px 14px;
           font-size:15px; font-weight:600; line-height:1.8; }

/* الفئات */
.tiles { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:6px; }
.tile { color:#fff; border-radius:16px; padding:10px 2px; text-align:center; font-weight:700; }
.tile .te { font-size:24px; }
.tile small { font-size:11px; line-height:1.3; display:block; color:#fff; }
.tile.on { outline:4px solid var(--txt); }

/* العجلة */
.wheelwrap { position:relative; width:190px; height:190px; margin:14px auto 6px; }
.ptr { position:absolute; top:-14px; left:50%; margin-left:-12px; font-size:24px; z-index:3; color:var(--txt); line-height:1; }
.wheel { width:100%; height:100%; border-radius:50%; border:6px solid var(--card);
         box-shadow:0 6px 18px rgba(0,0,0,.25); position:relative; }
.wl { position:absolute; top:50%; left:50%; margin:-14px 0 0 -14px; width:28px; height:28px;
      text-align:center; font-size:21px; line-height:28px; }
.hub { position:absolute; top:50%; left:50%; width:26px; height:26px; margin:-13px 0 0 -13px;
       border-radius:50%; background:var(--card); box-shadow:0 0 0 3px var(--bd); z-index:2; }

/* مربع السؤال */
.st-key-resbox { border:2px solid #ff8da7; background:var(--card); border-radius:22px; padding:20px 16px;
                 margin:12px 0; }
.center { text-align:center; }
.tag { display:inline-block; background:#ffe0e9; color:#a53e61 !important; padding:6px 12px;
       border-radius:30px; font-weight:700; font-size:14px; }
.presenter { margin:10px 0 2px; font-size:15px; font-weight:700; color:var(--txt); }
.q { font-size:25px; font-weight:800; line-height:1.7; margin:10px 0; color:var(--txt); }
.q.skipped { opacity:.45; text-decoration:line-through; }
.small { color:var(--sub); font-size:13px; }
.ans { background:var(--chip); border-radius:14px; padding:8px 12px; margin:8px 0; text-align:right;
       color:var(--txt); font-size:15px; }
.hist span { display:inline-block; background:var(--chip); color:var(--txt); padding:6px 10px;
             border-radius:30px; font-size:13px; margin:3px; }
.st-key-hostbox { border:2px dashed var(--bd); background:var(--card); border-radius:18px; padding:14px 14px 6px;
                  margin-bottom:12px; }

/* الأزرار */
.stButton>button, .stFormSubmitButton>button { width:100%; border-radius:16px; font-weight:700; padding:.7rem;
  background:var(--card); color:var(--txt); border:1.5px solid var(--bd); }
.stButton>button p, .stFormSubmitButton>button p { color:inherit !important; }
.stButton>button[kind="primary"], button[data-testid="stBaseButton-primary"] {
  background:linear-gradient(135deg,#ff8da7,#a58cf4) !important; color:#fff !important; border:none !important; }
button[data-testid="stBaseButton-primary"] p { color:#fff !important; }

/* الحقول */
.stApp input, .stApp textarea { background:var(--inp) !important; color:var(--txt) !important;
  -webkit-text-fill-color:var(--txt) !important; }
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"], .stApp [data-baseweb="textarea"] {
  background:var(--inp) !important; border-color:var(--bd) !important; border-radius:14px !important; }
.stApp ::placeholder { color:var(--sub) !important; -webkit-text-fill-color:var(--sub) !important; opacity:1; }
[data-testid="stExpander"], [data-testid="stForm"] { background:var(--card); border:1.5px solid var(--bd) !important;
  border-radius:16px; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary p { color:var(--txt) !important; }
</style>
""", unsafe_allow_html=True)

# ══════════ أعلى الصفحة ══════════
st.markdown(
    '<div class="badges">'
    f'<span class="badge">{ROOM_LINK_TEXT} <bdi dir="ltr">mL</bdi></span>'
    f'<span class="badge"><bdi dir="ltr">ID: {ROOM_ID}</bdi></span>'
    f'<span class="badge black">{PLATFORM_TEXT} <bdi dir="ltr">BLACK mL</bdi></span>'
    '</div>', unsafe_allow_html=True)

_, theme_col = st.columns([3, 2])
theme_col.button("☀️ الوضع النهاري" if ss.dark else "🌙 الوضع الليلي", on_click=toggle_theme, key="theme_btn")

st.markdown(
    '<div class="hero"><div style="font-size:38px">🎡✨</div><h1>ليلة المواجهة</h1>'
    '<div class="sub">اسأل.. واجه.. واكتشف!</div>'
    '<div class="tagline">لمّة حلوة 💗 — العبوا بروح مرحة واحترموا حق أي لاعب في تخطي السؤال.</div></div>',
    unsafe_allow_html=True)

# ══════════ لوحة المقدم (الأسماء عند المقدم فقط) ══════════
if ss.is_host:
    with st.container(key="hostbox"):
        st.markdown("**🎛️ لوحة المقدم**")
        c1, c2 = st.columns(2)
        pres = c1.text_input("اسم المقدم", value=room["presenter"], key="presenter_in",
                             placeholder="اسم المقدم...")
        play = c2.text_input("🎤 اللاعب الحالي", value=room["player"], key="player_in",
                             placeholder="اسم اللاعب...")
        room["presenter"], room["player"] = pres.strip()[:40], play.strip()[:40]


# ══════════ الجزء الحي: يتحدث عند الكل كل ثانيتين ══════════
@st.fragment(run_every=2)
def live():
    rnd, idx, q = room["round"], room["cat"], room["q"]
    anim, skipped = room["anim"], room["skipped"]
    answers = list(room["answers"])
    hist = list(room["hist"])
    n = len(CATS)
    seg = 360 / n

    # الفئات
    tiles = "".join(
        f'<div class="tile{" on" if i == idx else ""}" style="background:{c["color"]}">'
        f'<div class="te">{c["emoji"]}</div><small>{c["name"]}</small></div>'
        for i, c in enumerate(CATS))
    st.markdown(f'<div class="tiles">{tiles}</div>', unsafe_allow_html=True)

    # العجلة (تدور عند الكل مع كل دورة جديدة)
    final = 360 * 5 - (idx * seg + seg / 2) if idx is not None else 0
    stops = ",".join(f'{c["color"]} {i * seg}deg {(i + 1) * seg}deg' for i, c in enumerate(CATS))
    labels = "".join(
        f'<span class="wl" style="transform:rotate({i * seg + seg / 2}deg) translateY(-64px) '
        f'rotate({-(i * seg + seg / 2)}deg)">{c["emoji"]}</span>' for i, c in enumerate(CATS))
    wstyle = (f"animation:sp{rnd} 3s cubic-bezier(.17,.67,.2,1) forwards;" if anim
              else f"transform:rotate({final}deg);")
    st.markdown(
        f'<style>@keyframes sp{rnd}{{from{{transform:rotate(0deg)}}to{{transform:rotate({final}deg)}}}}'
        f'@keyframes rv{rnd}{{from{{opacity:0}}to{{opacity:1}}}}</style>'
        f'<div class="wheelwrap"><div class="ptr">▼</div>'
        f'<div class="wheel" style="background:conic-gradient({stops});{wstyle}">{labels}</div>'
        f'<div class="hub"></div></div>', unsafe_allow_html=True)

    presenter = esc(room["presenter"]) or "—"
    player = esc(room["player"])
    who = f'<div class="small">الدور على: <b>{player}</b></div>' if player else ""
    pres_html = f'<div class="presenter">اسم المقدم : {presenter}</div>'

    with st.container(key="resbox"):
        if idx is None:
            st.markdown(
                '<div class="center"><div style="font-size:35px">👀</div>' + pres_html +
                '<div class="q">مستعدين؟</div>'
                '<div class="small">بانتظار المقدم ليدير العجلة!</div></div>',
                unsafe_allow_html=True)
        else:
            c = CATS[idx]
            ans_html = "".join(
                f'<div class="ans">💬 <b>{esc(a["who"]) or "لاعب"}</b> : {esc(a["text"])}</div>'
                for a in answers)
            skip_html = '<div class="tag">⏭️ تم تجاهل السؤال</div>' if skipped else ""
            wrap = (f'<div style="animation:rv{rnd} .6s ease 3s backwards">' if anim else "<div>")
            st.markdown(
                f'{wrap}<div class="center"><span class="tag">{c["emoji"]} {c["name"]}</span>'
                f'{pres_html}{who}'
                f'<div class="q{" skipped" if skipped else ""}">{esc(q)}</div>'
                f'<div class="small">الجولة رقم {rnd} · جاوب بصراحة أو اختر تحديًا!</div>'
                f'{skip_html}</div>{ans_html}</div>',
                unsafe_allow_html=True)

            if not skipped:
                b1, b2 = st.columns(2)
                b1.button("⏭️ تجاهل السؤال", key="skip_btn", on_click=do_skip)
                b2.button("✍️ الإجابة", key="ans_btn", on_click=open_answer)
                if ss.answering == rnd:
                    with st.form("ans_form", clear_on_submit=True, border=False):
                        st.text_input("✍️ اكتب إجابتك", key="ans_text",
                                      placeholder="اكتب إجابتك هنا...")
                        st.form_submit_button("إرسال", on_click=submit_answer)

    st.markdown("**📜 سجل الجولات**")
    st.markdown('<div class="hist">' + ("".join(f"<span>{esc(h)}</span>" for h in hist)
                or "<span>لم تبدأ اللعبة بعد</span>") + "</div>", unsafe_allow_html=True)


live()

# ══════════ أزرار المقدم ══════════
if ss.is_host:
    st.button("🎲 أدر عجلة الحظ!", on_click=spin, type="primary", key="spin_btn")
    h1, h2 = st.columns(2)
    h1.button("سؤال جديد ↻", on_click=new_q, key="newq_btn")
    h2.button("إعادة ضبط", on_click=reset, key="reset_btn")
else:
    with st.expander("🔐 دخول المقدم"):
        pin = st.text_input("رمز المقدم", type="password", key="pin_in", placeholder="اكتب الرمز...")
        if st.button("دخول", key="login_btn"):
            if pin == HOST_PIN:
                ss.is_host = True
                st.rerun()
            else:
                st.error("الرمز غير صحيح")
