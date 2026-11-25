import hmac
import html
import random
import uuid
import re
import threading
import streamlit as st

st.set_page_config(page_title="ليلة المواجهة", page_icon="🎡", layout="centered")

# ══════════ إعدادات يعدّلها المقدم ══════════
ROOM_LINK_TEXT = "رابط خاص في روم مزح ولعب"
ROOM_ID = "311130"
PLATFORM_TEXT = "تنسيق منصة المواجهة :"
PRESENTER_DEFAULT = ""
MAX_NAMES = 30          # أقصى عدد أسماء
MAX_NAME_LEN = 20       # أقصى طول للاسم


def _secret(key, default):
    try:
        return st.secrets[key]
    except Exception:
        return default


# المقدمين ورمز كل واحد (غيّرها هنا، أو حطها في .streamlit/secrets.toml تحت [HOSTS])
HOSTS = {
    "الوليد": "1234",
    "ＢＬＡＣＫ": "5678",
}
try:
    HOSTS = {str(k): str(v) for k, v in st.secrets["HOSTS"].items()}
except Exception:
    pass

# ══════════ الفئات والأسئلة ══════════
CATS = [
    {"name": "المواجهة والجرأة", "emoji": "🔥", "color": "#e85d75", "q": [
        "وش أكثر شي ما قد قلتيه أو قلته لشخص قدامك بس ودك تقوله الحين؟",
        "لو قالوا لك افتح جوالك وعط اللي جنبك يقلب فيه دقيقتين، توافق ولا ترتبك؟",
        "وش أكثر موقف حسّيت فيه إنك جريء وتحديت خوفك؟",
        "لو فيه شخص يغتابك من وراك وتعرفه، تواجهه ولا تسحب عليه وتنهي العلاقة؟",
        "وش الكذبة اللي تقولها كثير عشان تتهرب من المواقف؟",
        "لو عطيتك المايك وتقول رأيك بصراحة تامة في أقرب شخص لك بدون زعل، وش تقول؟",
        "وش أكثر شي سويته وكنت عارف إنه غلط بس كملت؟",
        "لو طلبوا منك ترسل “أفتقدك” لآخر شخص تواصلت معه، ترسلها ولا ترفض؟",
        "وش أكثر سؤال لو سألك إياه أحد الحين تتمنى يغيره؟",
        "هل قد جاملت شخص بقوة وبعدين ندمت على مجاملتك؟",
        "لو صار قدامك موقف ظلم، تتدخل وتتكلم ولا تفضل تبعد عن المشاكل؟",
        "وش أكثر شي تخاف الناس تعرفه عنك؟",
        "لو قالوا لك اعترف بأكبر خطأ سويته في حياتك، وش بتقول؟",
        "هل عندك الجرأة تقول “لا” لما شي ما يناسبك ولا تستحي؟",
        "وش أكثر شخص في حياتك ودك تعتذر له وتصارحه؟"]},
    {"name": "النفس والشخصية", "emoji": "🧠", "color": "#8064d8", "q": [
        "لو وصفت نفسك في ثلاث كلمات، وش بتكون؟",
        "وش أكثر صفة في شخصيتك تحبها وتفتخر فيها؟",
        "وش الصفة اللي ودك تغيرها في نفسك لو تقدر؟",
        "هل أنت شخص عملي يمشي بالعقل ولا عاطفي تمشيك مشاعرك؟",
        "كيف تتصرف لما تنحط تحت ضغط كبير وفجأة؟",
        "وش أكثر شي يطلع أسوأ نسخة منك؟",
        "هل تحب تكون وسط الناس والجمعات ولا تفضل قعدتك لحالك؟",
        "وش أكبر درس تعلمته عن نفسك خلال آخر سنة؟",
        "هل أنت شخص عنيد ولا مرن وتقتنع بسرعة؟",
        "وش الشي اللي يخليك تحس إنك فعلاً مبسوط وراضي عن يومك؟",
        "كيف تتعامل مع الانتقاد؟ تاخذه بصدر رحب ولا يزعلك؟",
        "وش أكثر فكرة تدور في بالك كثير وما تقولها لأحد؟",
        "هل تحس إنك نفس الشخص قدام الكل ولا تتغير حسب الموقف؟",
        "وش أكثر شي يخوفك على المدى الطويل؟",
        "لو جلست مع نفسك ساعة بدون جوال، وش أول شي تفكر فيه؟"]},
    {"name": "الحب والمشاعر", "emoji": "❤️", "color": "#e66b9a", "q": [
        "وش أول شي يلفت انتباهك في الشخص اللي قدامك؟",
        "هل تحس إنك تعبّر عن مشاعرك بسهولة ولا تكتمها جواك؟",
        "وش أكثر حركة بسيطة تسعدك وتفرق معك في يومك؟",
        "كيف تعرف إنك زعلان أو متضايق حتى لو قلت “عادي”؟",
        "هل يهمك الاهتمام أكثر من الكلام ولا العكس؟",
        "وش أكثر شي يكسر ثقتك في الشخص القريب منك؟",
        "لو زعلت من شخص تحبه، تعاتبه مباشرة ولا تبعد بصمت؟",
        "وش تعريفك للعلاقة المريحة اللي تخليك على طبيعتك؟",
        "هل تتعلق بسرعة بالناس ولا تاخذ وقتك لين تطمئن؟",
        "وش أكثر موقف حسّيت فيه إنك محبوب ومقدّر من اللي حولك؟",
        "هل تحس إن الغيرة دليل حب ولا أحياناً تسبب مشاكل مالها داعي؟",
        "لو خيروك بين شخص يداريك ويدلعك وشخص صريح وواضح بس جاف شوي، مين تميل له؟",
        "وش أكثر شي يهدّي نفسيتك إذا حسّيت بضغط أو حزن؟",
        "هل تسامح بسهولة ولا الموضوع يطول معك؟",
        "وش الكلمة أو الجملة اللي إذا سمعتها من شخص تحبه يروح كل تعبك؟"]},
    {"name": "الضحك والجنون", "emoji": "😂", "color": "#e8a23a", "q": [
        "وش أغرب موقف مضحك صار لك في مكان عام وحاولت تمسك ضحكتك؟",
        "لو قالوا لك البس لبس تنكري واطلع السوبرماركت، وش تختار تلبس؟",
        "وش أكثر شي يضحكك لدرجة تدمع عيونك؟",
        "لو صار عندك زر يخلي اللي قدامك يرقص غصب لمدة دقيقتين، متى تضغطه؟",
        "وش أسخف نكتة أو إفيه سمعته وما قدرت تطلع من جوّه؟",
        "لو فجأة صرت تضحك بصوت عالي في عز لحظة جدّية، وش ترقع؟",
        "وش أكثر حركة غبية سويتها وأنت تحسب إن ما فيه أحد يشوفك؟",
        "لو صرت حيوان أليف في بيتكم يوم واحد، وش تسوي عشان ترفع ضغطهم؟",
        "وش أغرب عادة أو طقس تسويه قبل تنام؟",
        "لو خيروك تصير مشهور بمقطع فشل محرج ولا تختفي من السوشيال ميديا، وش تختار؟",
        "وش أكثر مرة ضحكت فيها في وقت غلط تماماً (مثل عزاء أو اجتماع مهم)؟",
        "لو فتحت الثلاجة نص الليل ولقيت شي يتحرك، وش أول شي يطري على بالك؟",
        "وش أغرب شي أكلته بدافع الفضول أو التحدي؟",
        "لو صار بإمكانك تغير صوت كل الناس لصوت كرتوني لمدة ساعة، وش تسوي؟",
        "وش أكثر مقلب سويته أو انعمل فيك وما نسيته للحين؟"]},
    {"name": "اختيارات صعبة", "emoji": "⚡", "color": "#249eaa", "q": [
        "تعيش طول عمرك بدون جوال ولا بدون طلعات ومناسبات؟",
        "تسمع أخبار سيئة عن نفسك ولا عن شخص تحبه؟",
        "تتزوج/ترتبط عن حب كبير ولا عن توافق وعقلانية؟",
        "تشتغل شغلة راتبها عالي بس تكرهها ولا شغلة تحبها وراتبها متوسط؟",
        "ترجع بالزمن وتصلح غلطة وحدة ولا تشوف مستقبلك بعد عشر سنين؟",
        "تكون صريح لدرجة تجرح الناس ولا تجامل عشان تحافظ على علاقتك فيهم؟",
        "تعيش في مدينة زحمة وحركة طول الوقت ولا في مكان هادي ومعزول؟",
        "يضيع جوالك وفيه صور وذكريات غالية ولا يضيع محفظتك وفيها فلوسك وبطاقاتك؟",
        "تاكل نفس الأكلة طول حياتك ولا ما تقدر تاكل حلى أبداً؟",
        "تكون مشهور ومعروف عند الكل وما عندك خصوصية ولا مجهول ومرتاح في خصوصيتك؟",
        "تقرر بمشاعرك ولا بعقلك في أهم قرار في حياتك؟",
        "تسافر حول العالم لحالك ولا تسافر مكان واحد مع شلة تحبها؟",
        "تعرف متى يصير شي مهم في حياتك ولا تعيشها مفاجأة بيومها؟",
        "تضحي بشي تحبه عشان شخص عزيز ولا تتمسك باللي تحبه؟",
        "تنام ٨ ساعات متواصلة كل يوم بدون أحلام ولا تنام أقل بس تشوف أحلام ممتعة؟"]},
    {"name": "أسرار واعترافات", "emoji": "🤫", "color": "#4d9a79", "q": [
        "وش السر اللي شايله معك من زمان وما يعرفه إلا عدد ينعد على الأصابع؟",
        "هل قد خبّيت شي عن أهلك وأنت تحس إنك لو قلت لهم بتتوهق؟",
        "وش أكثر شي تسويه بالسر ولا أحد يتوقع إنك تسويه؟",
        "هل قد زعلت من شخص وبيّنت له إنك عادي وأنت من جواك شايل عليه؟",
        "وش أكثر مرة ادعيت فيها إنك مشغول أو نايم عشان تتهرب من طلعة أو مكالمة؟",
        "هل قد حسّيت بالغيرة من نجاح شخص قريب منك واعترفت لنفسك فيها؟",
        "وش الشي اللي الناس يحسبونه فيك وهو عكس الحقيقة تماماً؟",
        "هل قد كذبت كذبة صغيرة ومشت عليك وصدّقوها الكل؟",
        "وش أكثر عادة سيئة عندك وتحاول تتركها؟",
        "هل قد ندمت على قرار أخذته بسرعة بدون تفكير؟",
        "وش أكثر شي يزعلك في السوشيال ميديا بس تمشي وتعدّيه؟",
        "هل فيه شخص في حياتك للحين تفكر فيه بينك وبين نفسك؟",
        "وش أكثر مرة حسّيت إنك مظلوم وما أحد صدّقك؟",
        "هل قد أخذت شي أو سوّيت شي وأنت صغير وللحين تذكره وتضحك؟",
        "وش الاعتراف اللي لو قلته الحين يرتاح بالك؟"]},
    {"name": "ذكريات وطفولة", "emoji": "🎈", "color": "#5b8def", "q": [
        "وش أول ذكرى واضحة تذكرها وأنت صغير؟",
        "وش لعبتك المفضلة أيام الطفولة اللي ما كنت تمل منها؟",
        "وش أكثر أكلة أو حلى كنت تحبه وأنت صغير وإذا شفته الحين ترجع للذكريات؟",
        "وش أكثر موقف كنت تنضرب فيه أو تتعاقب عليه وأنت صغير؟",
        "مين كان رفيقك الدائم في الطفولة (أخ، ولد عم، صديق حارة)؟",
        "وش الكرتون أو البرنامج اللي كنت تتابعه وتتحمس معه؟",
        "وش أكثر شي كنت تخاف منه وأنت صغير (ظلام، حشرات، أصوات)؟",
        "كيف كانت إجازة الصيف عندكم زمان؟",
        "وش أكثر موقف محرج أو مضحك صار لك في المدرسة؟",
        "وش الشي اللي كنت تشتريه من البقالة وتعتبره كنز؟",
        "هل كنت طفل هادي ومؤدب ولا مشاغب وتجيب الكلام لنفسك؟",
        "وش أكثر هدية جاتك وأنت صغير وفرحت فيها من قلب؟",
        "لو تقابل نفسك وأنت عمرك ٨ سنين، وش تقوله؟",
        "وش أكثر أغنية أو نشيد إذا سمعته يذكرك بأيام زمان؟",
        "وش أكثر ذكرى عائلية تحب تحكيها وتسترجعها؟"]},
    {"name": "خيال وأحلام", "emoji": "🚀", "color": "#f0793a", "q": [
        "لو صحيت بكرة ولقيت معك قوة خارقة، وش تختار تكون؟",
        "لو تقدر تسافر عبر الزمن، تروح للماضي ولا للمستقبل، وليه؟",
        "لو فتحوا لك مشروع أحلامك بكرة وميزانيته مفتوحة، وش يكون المشروع؟",
        "لو قالوا لك عِش في مدينة خيالية أو جزيرة لحالك سنة كاملة، وش تختار؟",
        "وش حلم الطفولة اللي للحين يمر على بالك وتبتسم؟",
        "لو صار بإمكانك تتكلم مع الحيوانات يوم واحد، وش تسأل قطوة أو عصفور؟",
        "لو كتبوا فيلم عن حياتك، وش يكون اسمه وبطله مين؟",
        "وش المكان اللي لو رحت له تحس إنك في عالم ثاني؟",
        "لو عندك ثلاث أمنيات تتحقق فوراً، وش تتمنى؟",
        "لو صرت تقدر تقرأ أفكار الناس لمدة ساعة، مين أول شخص تقرأ أفكاره؟",
        "وش الشي اللي تتمنى تجربه في حياتك ولو مرة واحدة؟",
        "لو خيروك تعيش في عصر الفراعنة ولا عصر الفضاء المستقبلي، وش تختار؟",
        "وش شكل الحياة المثالية اللي ترسمها في بالك بعد خمس سنين؟",
        "لو صار في باب سري في غرفتك يوديك لأي مكان، وين تحطه يوديك؟",
        "وش أكثر حلم غريب شفته في منامك وعلق في بالك؟"]},
]

NAME_COLORS = ["#e85d75", "#8064d8", "#e66b9a", "#e8a23a", "#249eaa", "#4d9a79", "#5b8def", "#f0793a"]


# ══════════ الغرفة المشتركة (يشوفها كل اللاعبين) ══════════
@st.cache_resource
def get_room():
    return {
        "lock": threading.Lock(),
        "host_tokens": {},              # اسم المقدم -> توقيع جلسته الحالية
        "phase": "register",            # register = تسجيل الأسماء | play = اللعب
        "names": [], "used_names": set(),
        "stage": None,                  # None | name | question
        "nround": 0, "nanim": False,    # عجلة الأسماء
        "player": "",
        "round": 0, "cat": None, "q": None, "anim": False,   # عجلة الأسئلة
        "hist": [], "used": set(),
        "presenter": PRESENTER_DEFAULT,
        "answers": [], "skipped": False,
    }


room = get_room()
room.setdefault("gid", 0)            # رقم اللعبة: يزيد كل ما المقدم يبدأ لعبة جديدة
ss = st.session_state
ss.setdefault("dark", False)
ss.setdefault("role", None)          # None | player | host
ss.setdefault("host_name", None)
ss.setdefault("sid", uuid.uuid4().hex)
ss.setdefault("ask_host", False)
ss.setdefault("my_names", [])
ss.setdefault("answering", None)
ss.setdefault("flash", "")
if ss.get("my_gid") != room["gid"]:   # لعبة جديدة => ينسى الجهاز أسماءه القديمة
    ss.my_names = []
    ss.answering = None
    ss.my_gid = room["gid"]

esc = html.escape



def is_host():
    """مقدم فعلي = سجّل دخول باسمه ورمزه، وجلسته هي آخر جلسة دخلت بهذا الاسم."""
    return (ss.role == "host" and ss.host_name is not None
            and room["host_tokens"].get(ss.host_name) == ss.sid)


def _norm(s):
    return " ".join(str(s).split()).casefold()


# ══════════ الدخول ══════════
def choose_player():
    ss.role = "player"
    ss.ask_host = False


def want_host():
    ss.ask_host = True


def login_host():
    name = ss.get("host_sel")
    pin = str(ss.get("pin_in", ""))
    real = HOSTS.get(name)
    if real is not None and hmac.compare_digest(pin.encode(), real.encode()):
        with room["lock"]:
            room["host_tokens"][name] = ss.sid     # آخر دخول بهذا الاسم يلغي القديم
            room["presenter"] = name
        ss.role, ss.host_name, ss.ask_host, ss.flash = "host", name, False, ""
    else:
        ss.flash = "الاسم أو الرمز غير صحيح"


def logout():
    if ss.host_name and room["host_tokens"].get(ss.host_name) == ss.sid:
        room["host_tokens"].pop(ss.host_name, None)
    ss.role, ss.host_name, ss.ask_host, ss.flash = None, None, False, ""


# ══════════ التسجيل ══════════
def add_names():
    raw = str(ss.get("name_in", ""))
    parts = [p.strip() for p in re.split(r"[,\n،;؛]+", raw) if p.strip()]
    added, dup, full = 0, 0, False
    with room["lock"]:
        have = {_norm(n) for n in room["names"]}
        for p in parts:
            p = p[:MAX_NAME_LEN]
            if _norm(p) in have:
                dup += 1
            elif len(room["names"]) >= MAX_NAMES:
                full = True
                break
            else:
                room["names"].append(p)
                have.add(_norm(p))
                if not is_host():          # أسماء المقدم ما تعطيه صلاحية التجاهل
                    ss.my_names.append(p)
                added += 1
    msg = []
    if added:
        msg.append(f"✅ تمت إضافة {added}")
    if dup:
        msg.append(f"⚠️ {dup} مكرر")
    if full:
        msg.append("⚠️ وصلنا الحد الأقصى للأسماء")
    ss.flash = " · ".join(msg)


def remove_name(n):
    if not is_host():
        return
    with room["lock"]:
        if n in room["names"]:
            room["names"].remove(n)


def confirm_names():
    """التأكيد للمقدم فقط."""
    if not is_host():
        return
    with room["lock"]:
        if len(room["names"]) < 2:
            return
        room.update(phase="play", stage=None, player="", cat=None, q=None, anim=False,
                    nanim=False, answers=[], skipped=False, hist=[], round=0, nround=0)
        room["used"].clear()
        room["used_names"].clear()


def back_to_register():
    if not is_host():
        return
    with room["lock"]:
        room.update(phase="register", stage=None, player="", cat=None, q=None, anim=False,
                    nanim=False, answers=[], skipped=False)


def new_game():
    """لعبة جديدة بالكامل: يمسح كل الأسماء والجولات ويرجع للتسجيل. للمقدم فقط."""
    if not is_host():
        return
    with room["lock"]:
        room.update(phase="register", names=[], stage=None, player="", cat=None, q=None,
                    anim=False, nanim=False, answers=[], skipped=False, hist=[],
                    round=0, nround=0)
        room["used"].clear()
        room["used_names"].clear()
        room["gid"] += 1
    ss.my_gid = room["gid"]
    ss.my_names = []
    ss.answering = None
    ss.flash = ""


# ══════════ اللعب ══════════
def spin_names():
    if not is_host():
        return
    with room["lock"]:
        names = room["names"]
        if not names:
            return
        pool = [n for n in names if n not in room["used_names"]]
        if not pool:
            room["used_names"].clear()
            pool = list(names)
        p = random.choice(pool)
        room["used_names"].add(p)
        room.update(player=p, stage="name", nanim=True, cat=None, q=None, anim=False,
                    answers=[], skipped=False)
        room["nround"] += 1


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
        room.update(cat=i, q=q, anim=not had, answers=[], skipped=False, stage="question")
        room["round"] += 1
        room["hist"] = ([f'{room["player"]} — {c["emoji"]} {c["name"]}'] + room["hist"])[:6]


def spin_q():
    if is_host() and room["player"]:
        _draw(False)


def new_q():
    if is_host() and room["player"]:
        _draw(True)


def reset():
    if not is_host():
        return
    with room["lock"]:
        room.update(stage=None, player="", cat=None, q=None, anim=False, nanim=False,
                    hist=[], answers=[], skipped=False, round=0, nround=0)
        room["used"].clear()
        room["used_names"].clear()


def _is_turn_owner():
    p = room["player"]
    return bool(p) and p in ss.my_names and not is_host()   # المقدم ما يتجاهل ولا يجاوب أبدًا


def do_skip():
    if _is_turn_owner():                 # فقط صاحب الاسم اللي طلع بالعجلة
        room["skipped"] = True


def open_answer():
    if _is_turn_owner():
        ss.answering = room["round"]


def submit_answer():
    t = str(ss.get("ans_text", "")).strip()
    if t and _is_turn_owner():
        with room["lock"]:
            room["answers"] = (room["answers"] + [{"who": room["player"], "text": t[:300]}])[-20:]
        ss.answering = None


def toggle_theme():
    ss.dark = not ss.dark


# ══════════ الثيم ══════════
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

.stApp [data-testid="stHorizontalBlock"] { flex-direction: row !important; flex-wrap: nowrap !important; gap: 12px !important; }
.stApp [data-testid="stColumn"], .stApp [data-testid="column"] { min-width: 0 !important; flex: 1 1 0 !important; width: auto !important; }

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

.tiles { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:6px; }
.tile { color:#fff; border-radius:16px; padding:10px 2px; text-align:center; font-weight:700; }
.tile .te { font-size:24px; }
.tile small { font-size:11px; line-height:1.3; display:block; color:#fff; }
.tile.on { outline:4px solid var(--txt); }

/* العجلة */
.wheelwrap { position:relative; width:240px; height:240px; margin:14px auto 6px; }
.ptr { position:absolute; top:-14px; left:50%; margin-left:-12px; font-size:24px; z-index:3; color:var(--txt); line-height:1; }
.wheel { width:100%; height:100%; border-radius:50%; border:6px solid var(--card);
         box-shadow:0 6px 18px rgba(0,0,0,.25); position:relative; overflow:hidden; }
.wl { position:absolute; top:50%; left:50%; margin:-14px 0 0 -14px; width:28px; height:28px;
      text-align:center; font-size:21px; line-height:28px; }
.wn { position:absolute; top:50%; left:50%; width:84px; height:20px; margin-top:-10px;
      transform-origin:0 50%; direction:ltr; text-align:left; white-space:nowrap; overflow:hidden;
      text-overflow:ellipsis; font-size:13px; line-height:20px; font-weight:800; color:#fff;
      text-shadow:0 1px 3px rgba(0,0,0,.55); }
.hub { position:absolute; top:50%; left:50%; width:26px; height:26px; margin:-13px 0 0 -13px;
       border-radius:50%; background:var(--card); box-shadow:0 0 0 3px var(--bd); z-index:2; }

.st-key-resbox, .st-key-entrybox, .st-key-regbox { border:2px solid #ff8da7; background:var(--card);
                 border-radius:22px; padding:20px 16px; margin:12px 0; }
.center { text-align:center; }
.tag { display:inline-block; background:#ffe0e9; color:#a53e61 !important; padding:6px 12px;
       border-radius:30px; font-weight:700; font-size:14px; }
.presenter { margin:10px 0 2px; font-size:15px; font-weight:700; color:var(--txt); }
.q { font-size:25px; font-weight:800; line-height:1.7; margin:10px 0; color:var(--txt); }
.q.skipped { opacity:.45; text-decoration:line-through; }
.who { font-size:30px; font-weight:800; color:#d6477a; margin:6px 0; }
.small { color:var(--sub); font-size:13px; }
.ans { background:var(--chip); border-radius:14px; padding:8px 12px; margin:8px 0; text-align:right;
       color:var(--txt); font-size:15px; }
.hist span, .chips span { display:inline-block; background:var(--chip); color:var(--txt); padding:6px 12px;
             border-radius:30px; font-size:14px; margin:3px; font-weight:700; }
.st-key-hostbox { border:2px dashed var(--bd); background:var(--card); border-radius:18px; padding:14px 14px 6px;
                  margin-bottom:12px; }

.stButton>button, .stFormSubmitButton>button { width:100%; border-radius:16px; font-weight:700; padding:.7rem;
  background:var(--card); color:var(--txt); border:1.5px solid var(--bd); }
.stButton>button p, .stFormSubmitButton>button p { color:inherit !important; }
.stButton>button[kind="primary"], button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"] {
  background:linear-gradient(135deg,#ff8da7,#a58cf4) !important; color:#fff !important; border:none !important; }
button[data-testid="stBaseButton-primary"] p, button[data-testid="stBaseButton-primaryFormSubmit"] p { color:#fff !important; }
.stButton>button:disabled { opacity:.45; }

.stApp input, .stApp textarea { background:var(--inp) !important; color:var(--txt) !important;
  -webkit-text-fill-color:var(--txt) !important; }
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"], .stApp [data-baseweb="textarea"] {
  background:var(--inp) !important; border-color:var(--bd) !important; border-radius:14px !important; }
.stApp ::placeholder { color:var(--sub) !important; -webkit-text-fill-color:var(--sub) !important; opacity:1; }
[data-testid="stExpander"], [data-testid="stForm"] { background:var(--card); border:1.5px solid var(--bd) !important;
  border-radius:16px; }
</style>
""", unsafe_allow_html=True)


# ══════════ مكوّن العجلة (للأسماء وللأسئلة) ══════════
def wheel_html(items, rnd, idx, anim, pre, as_text):
    n = len(items)
    seg = 360 / n
    final = 360 * 5 - (idx * seg + seg / 2) if idx is not None else 0
    stops = ",".join(f'{it["color"]} {i * seg}deg {(i + 1) * seg}deg' for i, it in enumerate(items))
    labels = ""
    for i, it in enumerate(items):
        mid = i * seg + seg / 2
        if as_text:
            labels += (f'<span class="wn" style="transform:rotate({mid - 90}deg) translateX(24px)">'
                       f'{esc(it["label"])}</span>')
        else:
            labels += (f'<span class="wl" style="transform:rotate({mid}deg) translateY(-82px) '
                       f'rotate({-mid}deg)">{it["label"]}</span>')
    wstyle = (f"animation:{pre}{rnd} 3s cubic-bezier(.17,.67,.2,1) forwards;" if anim
              else f"transform:rotate({final}deg);")
    return (f'<style>@keyframes {pre}{rnd}{{from{{transform:rotate(0deg)}}to{{transform:rotate({final}deg)}}}}'
            f'@keyframes rv{pre}{rnd}{{from{{opacity:0}}to{{opacity:1}}}}</style>'
            f'<div class="wheelwrap"><div class="ptr">▼</div>'
            f'<div class="wheel" style="background:conic-gradient({stops});{wstyle}">{labels}</div>'
            f'<div class="hub"></div></div>')


# ══════════ أعلى الصفحة ══════════
st.markdown(
    '<div class="badges">'
    f'<span class="badge">{ROOM_LINK_TEXT} <bdi dir="ltr">mL</bdi></span>'
    f'<span class="badge"><bdi dir="ltr">ID: {ROOM_ID}</bdi></span>'
    f'<span class="badge black">{PLATFORM_TEXT} <bdi dir="ltr">BLACK mL</bdi></span>'
    '</div>', unsafe_allow_html=True)

_, theme_col = st.columns([3, 2])
theme_col.button("☀️ الوضع النهاري" if ss.dark else "🌙 الوضع الليلي", on_click=toggle_theme, key="theme_btn")


# ══════════ 1) شاشة الدخول: مقدم أم لاعب ══════════
def entry_screen():
    with st.container(key="entrybox"):
        st.markdown(
            '<div class="center"><div style="font-size:46px">🎡👋</div>'
            '<div class="q">أهلاً فيك في ليلة المواجهة</div>'
            f'<div class="small">مزح ولعب <bdi dir="ltr">mL</bdi> · <bdi dir="ltr">ID: {ROOM_ID}</bdi></div>'
            '<div class="presenter" style="margin-top:16px">هل أنت مقدم أم لاعب؟</div></div>',
            unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.button("🎮 لاعب", on_click=choose_player, key="role_player", type="primary")
        c2.button("🎤 مقدم", on_click=want_host, key="role_host")
        if ss.ask_host:
            with st.form("pin_form", border=False):
                st.selectbox("اسم المقدم", list(HOSTS.keys()), key="host_sel")
                st.text_input("رمز المقدم", type="password", key="pin_in", placeholder="اكتب الرمز...")
                st.form_submit_button("دخول", on_click=login_host)
            if ss.flash:
                st.error(ss.flash)


# ══════════ 2) صفحة تسجيل الأسماء (واجهة اللاعبين، والمقدم يشوفها ويأكد) ══════════
@st.fragment(run_every=2)
def names_live():
    if room["phase"] != "register":
        st.rerun(scope="app")
    names = list(room["names"])
    mine = set(ss.my_names)
    st.markdown(f'**👥 اللاعبين المسجلين ({len(names)})**')
    if names:
        st.markdown('<div class="chips">' + "".join(
            f'<span>{"⭐ " if n in mine else ""}{esc(n)}</span>' for n in names) + '</div>',
            unsafe_allow_html=True)
    else:
        st.markdown('<div class="small">ما أحد سجّل للحين...</div>', unsafe_allow_html=True)
    if is_host():
        if names:
            with st.expander("🗑️ حذف اسم"):
                for i, n in enumerate(names):
                    st.button(f"✖ {n}", key=f"rm_{i}", on_click=remove_name, args=(n,))
        if len(names) < 2:
            st.markdown('<div class="small">لازم اسمين على الأقل قبل التأكيد.</div>', unsafe_allow_html=True)


def register_screen():
    st.markdown(
        '<div class="hero"><div style="font-size:38px">📝</div><h1>تسجيل اللاعبين</h1>'
        '<div class="sub">اكتب اسمك (أو أكثر من اسم) وانتظر المقدم يأكد</div></div>',
        unsafe_allow_html=True)
    with st.container(key="regbox"):
        with st.form("name_form", clear_on_submit=True, border=False):
            st.text_input("✍️ اكتب اسمك", key="name_in",
                          placeholder="مثال: سارة  — أو أكثر من اسم بفاصلة: سارة، محمد")
            st.form_submit_button("➕ إضافة", on_click=add_names)
        if ss.flash:
            st.markdown(f'<div class="small">{esc(ss.flash)}</div>', unsafe_allow_html=True)
        names_live()

    if is_host():
        st.button("✅ تأكيد وبدء اللعبة", on_click=confirm_names, type="primary", key="confirm_btn")
        st.button("🆕 لعبة جديدة (مسح كل الأسماء)", on_click=new_game, key="new_game_reg_btn")
    else:
        st.markdown('<div class="center small">⏳ التأكيد وبدء اللعبة من المقدم فقط</div>',
                    unsafe_allow_html=True)


# ══════════ 3) صفحة اللعب (عجلة الأسماء ثم عجلة الأسئلة) ══════════
@st.fragment(run_every=2)
def live():
    if room["phase"] != "play":
        st.rerun(scope="app")

    stage, names, player = room["stage"], list(room["names"]), room["player"]
    rnd, idx, q = room["round"], room["cat"], room["q"]
    nrnd, nanim = room["nround"], room["nanim"]
    anim, skipped = room["anim"], room["skipped"]
    answers, hist = list(room["answers"]), list(room["hist"])
    is_me = bool(player) and player in ss.my_names and not is_host()
    presenter = esc(room["presenter"]) or "—"
    pres_html = f'<div class="presenter">اسم المقدم : {presenter}</div>'

    # ── مرحلة اختيار اللاعب ──
    if stage in (None, "name"):
        items = [{"label": n, "color": NAME_COLORS[i % len(NAME_COLORS)]} for i, n in enumerate(names)]
        pidx = names.index(player) if player in names else None
        st.markdown(wheel_html(items, nrnd, pidx, nanim and stage == "name", "nsp", True),
                    unsafe_allow_html=True)
        with st.container(key="resbox"):
            if stage is None:
                st.markdown('<div class="center"><div style="font-size:35px">👀</div>' + pres_html +
                            '<div class="q">مستعدين؟</div>'
                            '<div class="small">بانتظار المقدم ليدير عجلة الأسماء!</div></div>',
                            unsafe_allow_html=True)
            else:
                wrap = (f'<div style="animation:rvnsp{nrnd} .6s ease 3s backwards">' if nanim else "<div>")
                st.markdown(
                    f'{wrap}<div class="center">{pres_html}<div class="small">الدور على</div>'
                    f'<div class="who">🎤 {esc(player)}</div>'
                    '<div class="small">بانتظار المقدم ليدير عجلة الأسئلة</div></div></div>',
                    unsafe_allow_html=True)
    # ── مرحلة السؤال ──
    else:
        tiles = "".join(
            f'<div class="tile{" on" if i == idx else ""}" style="background:{c["color"]}">'
            f'<div class="te">{c["emoji"]}</div><small>{c["name"]}</small></div>'
            for i, c in enumerate(CATS))
        st.markdown(f'<div class="tiles">{tiles}</div>', unsafe_allow_html=True)
        items = [{"label": c["emoji"], "color": c["color"]} for c in CATS]
        st.markdown(wheel_html(items, rnd, idx, anim, "sp", False), unsafe_allow_html=True)

        with st.container(key="resbox"):
            c = CATS[idx]
            ans_html = "".join(
                f'<div class="ans">💬 <b>{esc(a["who"]) or "لاعب"}</b> : {esc(a["text"])}</div>'
                for a in answers)
            skip_html = '<div class="tag">⏭️ تم تجاهل السؤال</div>' if skipped else ""
            wrap = (f'<div style="animation:rvsp{rnd} .6s ease 3s backwards">' if anim else "<div>")
            st.markdown(
                f'{wrap}<div class="center"><span class="tag">{c["emoji"]} {c["name"]}</span>'
                f'{pres_html}<div class="small">الدور على: <b>{esc(player)}</b></div>'
                f'<div class="q{" skipped" if skipped else ""}">{esc(q)}</div>'
                f'<div class="small">الجولة رقم {rnd} · جاوب بصراحة أو اختر تحديًا!</div>'
                f'{skip_html}</div>{ans_html}</div>',
                unsafe_allow_html=True)

            if not skipped:
                if is_me:   # التخطي والإجابة لصاحب الاسم الطالع فقط
                    b1, b2 = st.columns(2)
                    b1.button("⏭️ تجاهل السؤال", key="skip_btn", on_click=do_skip)
                    b2.button("✍️ الإجابة", key="ans_btn", on_click=open_answer)
                    if ss.answering == rnd:
                        with st.form("ans_form", clear_on_submit=True, border=False):
                            st.text_input("✍️ اكتب إجابتك", key="ans_text",
                                          placeholder="اكتب إجابتك هنا...")
                            st.form_submit_button("إرسال", on_click=submit_answer)
                else:
                    st.markdown(f'<div class="center small">🔒 التجاهل والإجابة لـ «{esc(player)}» فقط</div>',
                                unsafe_allow_html=True)

    st.markdown("**📜 سجل الجولات**")
    st.markdown('<div class="hist">' + ("".join(f"<span>{esc(h)}</span>" for h in hist)
                or "<span>لم تبدأ اللعبة بعد</span>") + "</div>", unsafe_allow_html=True)


def play_screen():
    st.markdown(
        '<div class="hero"><div style="font-size:38px">🎡✨</div><h1>ليلة المواجهة</h1>'
        '<div class="sub">اسأل.. واجه.. واكتشف!</div>'
        '<div class="tagline">لمّة حلوة 💗 — العبوا بروح مرحة واحترموا حق أي لاعب في تخطي السؤال.</div></div>',
        unsafe_allow_html=True)

    if is_host():
        with st.container(key="hostbox"):
            st.markdown("**🎛️ لوحة المقدم**")
            pres = st.text_input("اسم المقدم", value=room["presenter"], key="presenter_in",
                                 placeholder="اسم المقدم...")
            room["presenter"] = pres.strip()[:40]

    live()

    if is_host():
        st.button("🎯 أدر عجلة الأسماء!", on_click=spin_names, type="primary", key="spin_names_btn")
        st.button("🎲 أدر عجلة الأسئلة!", on_click=spin_q, key="spin_btn")
        h1, h2 = st.columns(2)
        h1.button("سؤال جديد ↻", on_click=new_q, key="newq_btn")
        h2.button("إعادة ضبط", on_click=reset, key="reset_btn")
        st.button("✏️ رجوع لتسجيل الأسماء", on_click=back_to_register, key="back_reg_btn")
        st.button("🆕 لعبة جديدة (مسح كل الأسماء)", on_click=new_game, key="new_game_btn")


# ══════════ التوجيه ══════════
if ss.role == "host" and not is_host():
    ss.role, ss.host_name = None, None
    ss.flash = "تم تسجيل الدخول بهذا الاسم من جهاز آخر"
if ss.role is None:
    entry_screen()
else:
    if room["phase"] == "register":
        register_screen()
    else:
        play_screen()
    st.button("↩️ تغيير الدور", on_click=logout, key="logout_btn")
