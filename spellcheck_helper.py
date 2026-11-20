"""spellcheck_helper.py — Headless Tier 1 Offline Spellcheck Engine.

Provides lightweight, pure-Python offline spellchecking designed for WordPress
publishing metadata (Title, Excerpt, Image Caption, Alt Text, Custom Notice)
and Segment Title / Metadata inputs without adding overhead to full-transcript
rendering.

Architectural invariants:
- 100% headless: zero PySide6/Qt GUI dependencies.
- Uses `pyspellchecker` (`spellchecker.SpellChecker`) when installed, with a
  compact pure-Python edit-distance fallback when running in bare headless
  environments so core diagnostics and editing workflows never crash.
- Automatically seeds its allowlist from the application's custom Glossary
  preferred terms and confirmed project/station speaker names so proper nouns
  are never falsely flagged as typos.
"""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from typing import Any, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

try:
    from spellchecker import SpellChecker as _PySpellChecker  # type: ignore
except Exception:
    _PySpellChecker = None


@dataclass(frozen=True)
class SpellIssue:
    """Represents a single misspelled word span in a text string."""

    word: str
    start: int
    end: int


# Protected spans skipped completely before word scanning
_PROTECTED_SPAN_RE = re.compile(
    r"<[^>]+>"                                                # HTML tags (e.g. <a href="...">)
    r"|\[[^\]]+\]"                                            # WordPress shortcodes (e.g. [audio ...])
    r"|https?://[^\s<>\"']+"                                  # HTTP/HTTPS URLs
    r"|www\.[^\s<>\"']+"                                      # Bare www URLs
    r"|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",       # Email addresses
    re.IGNORECASE,
)

# Candidate alphabetic tokens (including internal apostrophes and hyphens)
_WORD_TOKEN_RE = re.compile(r"[A-Za-z]+(?:['’\-][A-Za-z]+)*")

# Generic diarization labels that should not pollute the custom allowlist
_GENERIC_SPEAKER_RE = re.compile(
    r"^(?:speaker\s*\d+|speaker_\d+|spk\s*\d+|unknown(?:\s+speaker)?|unassigned|none)$",
    re.IGNORECASE,
)

# Domain-specific broadcast, journalism, and publishing words always accepted
_BROADCAST_DOMAIN_WORDS: frozenset[str] = frozenset("""
aaf alt audiogram audiograms autoplay broadcast broadcasts broadcasting broadcaster broadcasters
byline bylines caption captions castos clip clips cohost cohosts crossfade crossfades daw diarize
diarized diarizing diarization docx edl embed embedded embedding embeds episode episodes excerpt
excerpts fade fades fading ffmpeg ffprobe gutenberg headline headlines html interview interviewed
interviewee interviewees interviewer interviewers interviews intro intros journalism journalist
journalists keyframe keyframes livestream livestreamed livestreaming livestreams metadata mkv mp3
mp4 multispeaker newscast newscasts onnx outro outros parakeet pdf permalink permalinks playhead
playlist playlists plugin plugins podcast podcaster podcasters podcasting podcasts reaper rpp rss
segment segmented segmenter segmenting segments seo shortcode shortcodes show shows slug slugs
snippet snippets srt storyboard subsegment subtitle subtitles teaser teasers thumbnail thumbnails
timecode timecodes timeline timelines timestamp timestamps transcribe transcribed transcriber
transcribing transcript transcription transcripts unmute unmuted url urls voiceprint voiceprints
voicemail vtt wav waveform waveforms webinar webinars wespeaker whisper wordpress youtube
""".split())

# Compact pure-Python English fallback vocabulary (used only when `pyspellchecker`
# is not installed in a headless or bare Python environment).
_FALLBACK_CORE_WORDS: frozenset[str] = frozenset("""
a about above access accessibility account across action active actual actually add added adding
additional address after again against age agency ago agree ahead air all allow almost alone along
already also although always am america american among amount an analysis anchor and announce
announcement another answer any anyone anything appear apply approach april are area around art
article artist as ask at attach attachment attack attention audience audio august author auto
automatic available avoid award away back background bad balance band bank bar base based basic
basis be beat beautiful because become been before begin behind being believe below benefit best
better between beyond big bill billion bit black block blog blue board body book born both bottom
box boy break breaking brief bring budget build building business but buy by call camera campaign
can cancel candidate cannot capital capture car card care career carry case cat catch category
cause center central century certain chair challenge chance change channel chapter character charge
check chief child children choice choose church city civic claim class clean clear clearly climate
close closed cloud club coach coast code cold collect collection college color column come comment
commercial commission committee common community company compare complete computer concern
condition conference confirm congress connect consider contact contain content context continue
contract control conversation copy core corner correct cost could council count country county
couple course court cover coverage create credit crime crisis critic crop cross crowd cultural
culture cup current currently custom customer cut daily damage dance danger dark data date daughter
day dead deal death debate decade december decide decision deep default defense define degree delay
delete deliver demand democracy department depend describe description design desk desktop detail
detect detection determine develop development device dialog dialogue did die difference different
difficult digital direct direction director discover discuss discussion disease display distance
district do doctor document does dog dollar domestic done door double down download draft drama
draw dream drive driver drop drug during each early earth east easy eat economic economy edge edit
edition editor editorial education effect effective effort eight either election electric element
else email emergency employee empty enable end energy engine english enjoy enough enter entire
entry environment equal error especially essential establish estate estimate even evening event
ever every everyone everything evidence exact exactly example exchange executive exist existing
expand expect experience expert explain export express extend extra eye face fact factor fail fair
faith fall false family famous fan far farm fast father fault favor favorite fear feature featured
february federal feed feedback feel feeling feet fellow female festival few field fifteen fifth
fifty fight figure file fill film filter final finally finance financial find fine finger finish
fire firm first fiscal fish fit five fix flag flat flight floor flow flower fly focus folder follow
following food foot football for force foreign forest forget form formal format former formula
forth forty forum forward found foundation four fourth frame framework free freedom french
frequency fresh friday friend from front fruit fuel full fully fun function fund funding further
future gain gallery game gap garden gas gate gather gave general generally generate generation
gentle get girl give given glad glass global glossary go goal god gold golden gone good got govern
government governor grade grand grant graphic grass great green grid ground group grow growth guard
guess guest guide guideline guilty gun guy habit had hair half hall hand handle hang happen happy
hard hardware harm has hat hate have he head header health healthy hear hearing heart heat heavy
height held hello help helpful her here hero herself hesitate hey hi hidden hide high highlight
highly highway hill him himself hint hire his historic historical history hit hold holder hole
holiday home honest honor hope horse hospital host hot hotel hour house housing how however huge
human hundred hunt hurry hurt husband i ice icon idea ideal identify identity if ignore ill illegal
illness image imagine immediate immediately impact implement imply import important impose
impossible improve improvement in inaccuracy inaccuracies inch incident include including income
increase indeed independent index indicate individual industrial industry info inform information
initial initiative injury inline inner input inquiry inside insight inspect install instance
instant instead institute institution instruction instrument insurance integer integrate
intelligence intend interest interesting interface internal international internet interpret into
introduce invest investigate investigation investment invite involve iron is island issue it item
its itself january jazz job join joint joke journal journey joy judge judgment july jump june
junior jury just justice keep key keyboard kick kid kill kind king kitchen knee knew knife knock
know knowledge known lab label labor lack lady lake land landscape language large largely last late
later latest latin latter laugh launch law lawyer lay layer layout lead leader leadership leading
leaf league lean learn learning least leather leave lecture left leg legacy legal legend
legislation length lens less lesson let letter level liberal library license lie life lift light
like likely limit line linear link list listen listener literal literature little live living load
loan local locate location lock log logic login logo long look loop loose lord lose loss lost lot
loud loudness love low lower luck lucky lunch machine mad made magazine magic mail main mainly
maintain major majority make maker male mall man manage management manager manner manual many map
march margin mark marker market marketing marriage marry mask mass massive master match material
math matter may maybe mayor me meal mean meaning meanwhile measure meat media medical medicine
medium meet meeting member membership memory men mental mention menu mere merge merit message metal
meter method metro mexico mic microphone middle midnight might migration mile military milk mill
million mind mine minimum minister minor minority minute mirror miss mission mistake mix mixed
mixer mobile mode model moderate modern modify module mom moment monday money monitor month monthly
mood moon moral more moreover morning most mostly mother motion motor mount mountain mouse mouth
move movement movie much multi multiple municipal murder muscle museum music musical musician must
mute mutual my myself mystery myth name narrative narrow nation national native natural nature near
nearby nearly necessary neck need negative negotiate neighbor neighborhood neither nerve net
network neutral never new newly news newsletter newspaper newsroom next nice night nine no nobody
nod noise noisy nominate none nonprofit noon nor norm normal normally north northern nose not note
notebook nothing notice notion noun novel november now nowhere nuclear number numerous nurse nut
object objective observe obtain obvious occasion occupy occur ocean october odd odds of off offense
offer office officer official offline often oh oil ok okay old olympic on once one ongoing online
only onto open opening opera operate operation operator opinion opponent opportunity oppose
opposite option optional or oral orange order ordinary organ organic organization organize origin
original other otherwise ought our ourselves out outcome outdoor outer outlet outline output
outside over overall overcome overlap overseas overview own owner pace pack package pad padding
page paid pain paint pair palace pale palm pan panel panelist panic paper paragraph parent park
parking part partial participant participate particular partly partner party pass passage passenger
passion password past patch path patient pattern pause pay payment peace peak peer pen penalty
pending people pepper per perceive percent percentage perception perfect perform performance
perhaps period permanent permission permit person personal personality personally personnel
perspective persuade pet phase phenomenon philosophy phone photo photograph photographer phrase
physical physician piano pick picture pie piece pig pile pilot pin pine pink pipe pitch place
placement plain plan plane planet planning plant plastic plate platform play playback player please
pleasure plenty plot plus pocket poem poet poetry point pole police policy political politician
politics poll pollution pool poor pop popular population porch port portion portrait portray pose
position positive possess possibility possible possibly post poster pot potato potential pound pour
poverty powder power powerful practical practice praise pray prayer preach precisely predict prefer
preference pregnant premier premise premium prepare presence present presentation preserve
president presidential press pressure pretend pretty prevent preview previous previously price
pride priest primarily primary prime prince principal principle print prior priority prison
prisoner privacy private privilege prize pro probably problem procedure proceed process processing
produce producer product production profession professional professor profile profit program
progress project prominent promise promote prompt proof proper properly property proportion
proposal propose prose prosecutor prospect protect protection protein protest protocol proud prove
provide provider province provision public publication publicly publish publisher publishing pull
pulse pump punch punish purchase pure purple purpose pursue push put qualify quality quantity
quarter queen query quest question queue quick quickly quiet quietly quit quite quote race racial
rack radar radiation radical radio rail rain raise rally ran range rank rapid rapidly rare rarely
rate rather rating ratio raw reach react reaction read reader reading ready real reality realize
really realm rear reason reasonable rebel rebuild recall receive recent recently recipe recognition
recognize recommend record recorder recording recover recovery recruit red reduce reduction refer
reference reflect reflection reform refresh refugee refuse regard regarding regardless regime region
regional register regret regular regularly regulate regulation reinforce reject relate related
relation relationship relative relatively relax release relevant reliable relief religion religious
rely remain remaining remark remarkable remember remind remote removal remove rename render renew
rent repair repeat replace reply report reporter reporting represent representative republic
republican reputation request require requirement rescue research researcher resemble reservation
reserve reset resident resist resistance resolution resolve resort resource respect respond
respondent response responsibility responsible rest restaurant restore restrict result resume
retail retain retire retirement retreat return reveal revenue reverse review revise revision
revolution reward rhythm rice rich rid ride rider ridge rifle right ring riot rise risk ritual
rival river road roast rob robot rock rocket rod role roll roman romance romantic roof room root
rope rose rough roughly round route routine row royal rub rubber rude rug ruin rule ruler rumor run
runner running runtime rural rush russian sacred sad safe safely safety said sail sake salad salary
sale sales salmon salon salt same sample sanction sand sandwich satellite satisfaction satisfy
saturday sauce save saving saw say scale scan scandal scare scared scatter scenario scene schedule
schema scheme scholar scholarship school science scientific scientist scope score scout scramble
scrap scratch scream screen script scroll scrub sculpture sea seal search season seat second
secondary secret secretary section sector secure security see seed seek seem seen seize seldom
select selection self sell seller senate senator send senior sense sensitive sensitivity sensor
sentence separate september sequence series serious seriously servant serve server service session
set setting settle settlement seven several severe sex sexual shade shadow shake shall shallow
shame shape share sharp she shed sheep sheer sheet shelf shell shelter shift shine ship shirt shock
shoe shoot shooting shop shopping shore short shortly shot should shoulder shout shower shrink
shrug shut shy sibling sick side sidewalk sigh sight sign signal signature significance significant
significantly silence silent silk silly silver similar similarly simple simply sin since sing
singer single sink sir sister sit site situation six sixth sixty size ski skill skin skip skirt sky
slam slap slave sleep sleeve slice slide slider slight slightly slim slip slope slot slow slowly
small smart smell smile smoke smooth snap snow so soap soar soccer social society sock sodium sofa
soft software soil solar sold soldier sole solid solo solution solve some somebody someday somehow
someone something sometimes somewhat somewhere son song soon sophisticated sorry sort soul sound
soup source south southern soviet space spanish spare spark speak speaker special specialist
species specific specifically specify spectacular spectrum speculate speech speed spell spellcheck
spelling spend spending sphere spice spider spill spin spine spirit spiritual spite split spokesman
spokesperson sponsor spoon sport spot spouse spray spread spring sprint spy squad square squeeze
stability stable stack stadium staff stage stain stair stake stale stall stamp stance stand
standard standing star stare start startup state statement station statistical statistics statue
status statute stay steady steak steal steam steel steep steer stem step stereo stick stiff still
stimulate stimulus stir stitch stock stomach stone stood stool stop storage store storm story stove
straight strain strand strange stranger strategic strategy straw streak stream streaming street
strength strengthen stress stretch strict strictly stride strike string strip strive stroke strong
strongly structural structure struggle stub stuck student studio study stuff stumble stun style
subject submit subsequent subsidy substance substantial substitute subtle suburb suburban succeed
success successful successfully such suck sudden suddenly sue suffer sufficient sugar suggest
suggestion suicide suit suitable suite sum summarize summary summer summit sun sunday sunlight
sunny sunrise sunset super superior supermarket supervise supervisor supper supplement supplier
supply support supporter suppose supposed supreme sure surely surface surge surgeon surgery surplus
surprise surprised surprising surrender surround survey survival survive survivor suspect suspend
suspicion sustain sustainable swallow swap swear sweat sweater sweep sweet swell swift swim swing
switch sword symbol sympathy symphony symptom sync synchronize syndrome syntax system tab table
tablespoon tablet tackle tactic tag tail take tale talent talk tall tank tap tape target tariff
task taste tax taxpayer tea teach teacher teaching team tear teaspoon tech technical technique
technology teen teenage teenager teeth telephone telescope television tell temp temper temperature
template temple temporary ten tenant tend tendency tender tennis tense tension tent tenth tenure
term terminal terminate terms terrace terrain terrible terrific territory terror terrorism
terrorist test testify testimony testing text textbook texture than thank thanks that the theater
theatre theft their them theme themselves then theology theoretical theory therapist therapy there
thereby therefore thermal these thesis they thick thief thigh thin thing think thinking third
thirsty thirteen thirty this thorough thoroughly those though thought thousand thread threat
threaten three threshold threw thrill thrive throat throne through throughout throw thrust thumb
thunder thursday thus ticket tide tidy tie tier tiger tight tighten tile till timber time timely
timer timing tin tiny tip tire tired tissue title to toast tobacco today toe together toggle toilet
token told tolerance tolerate toll tomato tomb tomorrow ton tone tongue tonight too took tool
toolbar toolkit tooltip tooth top topic torch tornado torture toss total totally touch tough tour
tourism tourist tournament toward towards towel tower town toxic toy trace track tractor trade
trader trading tradition traditional traffic tragedy tragic trail trailer train trainer training
trait tram transaction transfer transform transformation transit transition translate translation
translator transmission transmit transparent transport transportation trap trash trauma travel
traveler tray tread treasure treasury treat treatment treaty tree trek tremendous trend trial
triangle tribal tribe tribute trick trigger trillion trim trio trip triple triumph troop tropical
trouble trousers truck true truly trumpet trunk trust trustee truth try tub tube tuck tuesday
tuition tumble tumor tuna tune tunnel turbine turf turkey turmoil turn turnout turnover turtle
tutor tv twelve twenty twice twig twilight twin twist two type typical typically typo ugly
ultimate ultimately ultra umbrella unable unanimous unaware uncertain uncertainty uncle
uncomfortable uncover under undergo undergraduate underground underline underlying undermine
understand understanding undertake undo undoubtedly uneasy unemployment unexpected unfair unfold
unfortunate unfortunately unhappy uniform unify union unique unit unite united unity universal
universe university unknown unless unlike unlikely unlimited unload unlock unnecessary unpack
unpleasant unprecedented unrest unsafe unsaved unsure until unusual unveil unwilling up upcoming
update upgrade uphold upload upon upper upright uprising upset upstairs upstream uptown upward
urban urge urgent us usable usage use used useful user usual usually utility utilize utter vacancy
vacant vacation vaccine vacuum vague vain valid validate validity valley valuable value valve van
vanish vanity vapor variable variant variation varied variety various vary vase vast vat vault
vector vegetable vehicle veil vein velocity velvet vendor vengeance venom vent venture venue verb
verbal verdict verge verification verify versatile verse version versus vertical very vessel vest
veteran veto via viable vibrant vibrate vibration vice vicinity vicious victim victor victory video
view viewer viewpoint vigor vigorous vile villa village villager villain vine vinegar vintage
violate violation violence violent violet violin viral virgin virtual virtually virtue virus visa
viscous visible visibly vision visit visitor visual visualize vital vitamin vivid vocal vocation
voice void volatile volcano volleyball volt voltage volume voluntary volunteer vomit vote voter
voting vouch voucher vow vowel voyage vulgar vulnerable wade wafer wage wagon waist wait waiter
waitress waive wake walk walker walking wall wallet wallpaper walnut wander want war ward wardrobe
warehouse warfare warm warmth warn warning warp warrant warranty warrior wary was wash washer
washing wasp waste watch water waterfall waterfront watt wave wax way we weak weaken weakness
wealth wealthy weapon wear weary weather weave web webcam website wed wedding wedge wednesday
weed week weekday weekend weekly weep weigh weight weird welcome weld welfare well went were west
western wet whale wharf what whatever wheat wheel wheelchair when whenever where whereas whereby
wherever whether which whichever whiff while whim whine whip whirl whisk whisker whiskey whisper
whistle white who whoever whole wholesale wholesome wholly whom whoop whose why wick wicked wide
widely widen widespread widget widow widower width wield wife wig wiggle wild wilderness wildlife
wildly will willing willingness willow wilt win wince winch wind window windshield windy wine wing
wink winner winning winter wipe wire wireless wiring wisdom wise wisely wish wisp wit witch with
withdraw withdrawal wither withhold within without witness witty wizard wobble woe woke wolf woman
womb women won wonder wonderful wood wooden woodland woody wool word wording wore work workaround
workbook worker workflow workforce working workload workout workplace workshop workspace world
worldwide worm worn worried worry worse worsen worship worst worth worthless worthwhile worthy
would wound wove woven wow wrap wrapper wrath wreak wreath wreck wreckage wren wrench wrestle
wrestler wretch wretched wriggle wring wrinkle wrist write writer writhe writing written wrong
wrongful wrongly wrote wrought wrung wry x yacht yam yank yap yard yarn yawn yeah year yearly yearn
yeast yell yellow yelp yep yes yesterday yet yield yoga yogurt yoke yolk yonder you young younger
youngest youngster your yours yourself yourselves youth youthful yowl yule zap zeal zealot zealous
zebra zen zenith zero zest zigzag zinc zing zip zipper zodiac zombie zone zoo zoology zoom
""".split()) | _BROADCAST_DOMAIN_WORDS

_FALLBACK_CONTRACTIONS: frozenset[str] = frozenset("""
ain't aren't can't couldn't didn't doesn't don't hadn't hasn't haven't he'd he'll he's here's how's
i'd i'll i'm i've isn't it'd it'll it's let's mightn't mustn't needn't shan't she'd she'll she's
shouldn't that's there's they'd they'll they're they've wasn't we'd we'll we're we've weren't
what's where's who's won't wouldn't you'd you'll you're you've
""".split())

_BASE_PYSPELL_LOCK = threading.Lock()
_BASE_PYSPELL_INSTANCE: Any = None
_SESSION_IGNORED_LOCK = threading.Lock()
_SESSION_IGNORED_WORDS: Set[str] = set()


def is_pyspellchecker_available() -> bool:
    """Return True if the `pyspellchecker` library is importable."""
    return _PySpellChecker is not None


def _get_base_pyspellchecker() -> Any:
    """Return a cached read-only `pyspellchecker.SpellChecker` instance if available."""
    global _BASE_PYSPELL_INSTANCE
    if _PySpellChecker is None:
        return None
    if _BASE_PYSPELL_INSTANCE is None:
        with _BASE_PYSPELL_LOCK:
            if _BASE_PYSPELL_INSTANCE is None:
                sp = _PySpellChecker(language="en", distance=2)
                sp.word_frequency.load_words(_BROADCAST_DOMAIN_WORDS)
                _BASE_PYSPELL_INSTANCE = sp
    return _BASE_PYSPELL_INSTANCE


def _normalize_apostrophe(word: str) -> str:
    return word.replace("’", "'").strip()


def _extract_word_tokens(text: str) -> Set[str]:
    """Extract lowercase alphabetic tokens (plus full hyphenated form) from a phrase."""
    if not text:
        return set()
    tokens: Set[str] = set()
    cleaned = _normalize_apostrophe(str(text))
    for match in _WORD_TOKEN_RE.finditer(cleaned):
        raw = match.group(0).lower()
        if len(raw) > 1:
            tokens.add(raw)
        if "-" in raw:
            for part in raw.split("-"):
                if len(part) > 1:
                    tokens.add(part)
        if raw.endswith("'s") and len(raw) > 3:
            tokens.add(raw[:-2])
    return tokens


def match_case(source_word: str, suggestion: str) -> str:
    """Apply the capitalization pattern of `source_word` onto `suggestion`."""
    if not source_word or not suggestion:
        return suggestion
    if source_word.isupper() and len(source_word) > 1:
        return suggestion.upper()
    if source_word[0].isupper() and source_word[1:].islower():
        return suggestion[0].upper() + suggestion[1:]
    return suggestion


def ignore_word_for_session(word: str) -> None:
    """Add `word` to the process-wide session ignore list."""
    tokens = _extract_word_tokens(word)
    if not tokens:
        return
    with _SESSION_IGNORED_LOCK:
        _SESSION_IGNORED_WORDS.update(tokens)


def get_session_ignored_words() -> Set[str]:
    """Return a copy of the session-ignored lowercase words."""
    with _SESSION_IGNORED_LOCK:
        return set(_SESSION_IGNORED_WORDS)


def clear_session_ignored_words() -> None:
    """Clear the process-wide session ignore list (primarily for tests)."""
    with _SESSION_IGNORED_LOCK:
        _SESSION_IGNORED_WORDS.clear()


def collect_allowlist_words(
    main_window: Any = None,
    glossary: Any = None,
    speaker_names: Optional[Iterable[str]] = None,
    extra_words: Optional[Iterable[str]] = None,
) -> Set[str]:
    """Build a lowercase word allowlist from custom Glossary preferred terms
    and confirmed project/station speaker names.

    Deliberately excludes misspelled glossary `source` variants so ASR typos
    remain flagged if entered manually in metadata fields.
    """
    allow: Set[str] = set(_BROADCAST_DOMAIN_WORDS)

    # 1. Glossary preferred / canonical target terms
    raw_glossary_sources: List[Any] = []
    if glossary is not None:
        raw_glossary_sources.append(glossary)
    if main_window is not None:
        win_glossary = getattr(main_window, "glossary", None)
        if win_glossary:
            raw_glossary_sources.append(win_glossary)
        settings_store = getattr(main_window, "settings_store", None)
        if settings_store is not None and not win_glossary:
            try:
                from terminology import load_glossary
                loaded = load_glossary(settings_store)
                if loaded:
                    raw_glossary_sources.append(loaded)
            except Exception:
                pass

    if raw_glossary_sources:
        try:
            from terminology import parse_glossary
        except Exception:
            parse_glossary = None

        for src in raw_glossary_sources:
            entries = parse_glossary(src) if parse_glossary is not None else (src if isinstance(src, list) else [])
            for entry in entries:
                if isinstance(entry, dict):
                    preferred = entry.get("preferred") or entry.get("target") or ""
                    if preferred:
                        allow.update(_extract_word_tokens(str(preferred)))
                elif isinstance(entry, str):
                    allow.update(_extract_word_tokens(entry))

    # 2. Confirmed speaker names (explicit arg + main_window sources)
    candidate_speakers: List[str] = []
    if speaker_names:
        candidate_speakers.extend(str(s) for s in speaker_names if s)

    if main_window is not None:
        spk_map = getattr(main_window, "speaker_names", None)
        if isinstance(spk_map, dict):
            candidate_speakers.extend(str(v) for v in spk_map.values() if v)
        custom_spk = getattr(main_window, "custom_speakers_glossary", None)
        if isinstance(custom_spk, (list, set, tuple)):
            candidate_speakers.extend(str(v) for v in custom_spk if v)

        diar_segs = getattr(main_window, "diarization_segments", None)
        if isinstance(diar_segs, list):
            for seg in diar_segs:
                if isinstance(seg, dict) and seg.get("speaker"):
                    candidate_speakers.append(str(seg["speaker"]))

        transcript = getattr(main_window, "transcript", None)
        t_segs = transcript.get("segments", []) if isinstance(transcript, dict) else (transcript if isinstance(transcript, list) else [])
        for seg in t_segs:
            if isinstance(seg, dict) and seg.get("speaker"):
                candidate_speakers.append(str(seg["speaker"]))

        vp_store = getattr(main_window, "voice_profile_store", None)
        if vp_store is not None and hasattr(vp_store, "list_profiles"):
            try:
                for prof in vp_store.list_profiles():
                    pname = getattr(prof, "name", None) or (prof.get("name") if isinstance(prof, dict) else None)
                    if pname:
                        candidate_speakers.append(str(pname))
            except Exception:
                pass

    for raw_name in candidate_speakers:
        cleaned = str(raw_name or "").strip()
        if not cleaned or _GENERIC_SPEAKER_RE.match(cleaned):
            continue
        allow.update(_extract_word_tokens(cleaned))

    # 3. Caller-supplied extra allowlist words
    if extra_words:
        for w in extra_words:
            allow.update(_extract_word_tokens(str(w)))

    return allow


def _edits1(word: str) -> Set[str]:
    """All strings one Levenshtein edit away from `word`."""
    letters = "abcdefghijklmnopqrstuvwxyz"
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
    inserts = [L + c + R for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)


def _fallback_stem_matches(word: str, vocab: Set[str]) -> bool:
    """Check regular English inflections against the fallback vocabulary."""
    if word in vocab or word in _FALLBACK_CONTRACTIONS:
        return True
    if word.endswith("'s") and word[:-2] in vocab:
        return True
    for suffix, replacements in (
        ("ies", ("y",)),
        ("ied", ("y",)),
        ("es", ("", "e")),
        ("s", ("",)),
        ("ed", ("", "e")),
        ("ing", ("", "e")),
        ("er", ("", "e")),
        ("est", ("", "e")),
        ("ly", ("", "e")),
        ("ness", ("",)),
        ("ment", ("",)),
        ("ful", ("",)),
        ("less", ("",)),
    ):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            stem = word[: -len(suffix)]
            for rep in replacements:
                cand = stem + rep
                if cand in vocab:
                    return True
                # Doubled final consonant (e.g. running -> run, stopped -> stop)
                if suffix in ("ed", "ing", "er", "est") and len(stem) >= 3 and stem[-1] == stem[-2]:
                    if stem[:-1] in vocab:
                        return True
    return False


def _is_camel_or_mixed_brand(token: str) -> bool:
    """Skip internal-capital identifiers like WordPress, YouTube, iPhone, PySide."""
    if len(token) < 2:
        return False
    has_internal_upper = any(ch.isupper() for ch in token[1:])
    has_lower = any(ch.islower() for ch in token)
    return has_internal_upper and has_lower


def iter_checkable_words(text: str) -> Iterator[Tuple[str, int, int]]:
    """Yield `(word, start, end)` spans in `text` that should be spellchecked.

    Skips HTML tags, WordPress shortcodes, URLs, emails, digits/alphanumeric
    codes (e.g. `128kbps`, `MP3`), single letters, ALL-CAPS acronyms, and
    mixed-case brand identifiers (e.g. `WordPress`, `YouTube`).
    """
    if not text:
        return

    protected_ranges: List[Tuple[int, int]] = [
        (m.start(), m.end()) for m in _PROTECTED_SPAN_RE.finditer(text)
    ]

    def _in_protected(start: int, end: int) -> bool:
        for p_start, p_end in protected_ranges:
            if start < p_end and end > p_start:
                return True
        return False

    text_len = len(text)
    for match in _WORD_TOKEN_RE.finditer(text):
        start, end = match.start(), match.end()
        if _in_protected(start, end):
            continue
        # Skip alphanumeric codes adjacent to digits (e.g. 48kHz, MP3, 3rd, v3)
        if (start > 0 and text[start - 1].isdigit()) or (end < text_len and text[end].isdigit()):
            continue

        raw = match.group(0)
        if len(raw) <= 1:
            continue
        # Skip ALL-CAPS acronyms (e.g. NPR, PBS, SEO, URL, RSS)
        if raw.isupper() and len(raw) >= 2:
            continue
        if _is_camel_or_mixed_brand(raw):
            continue

        yield raw, start, end


class OfflineSpellChecker:
    """Lightweight offline spellchecker seeded with Glossary + Speaker allowlists."""

    def __init__(
        self,
        custom_words: Optional[Iterable[str]] = None,
        main_window: Any = None,
        use_pyspellchecker: bool = True,
    ):
        self._main_window = main_window
        self._use_pyspellchecker = bool(use_pyspellchecker)
        self._base_sp = _get_base_pyspellchecker() if self._use_pyspellchecker else None
        self._explicit_words: Set[str] = set()
        if custom_words:
            for w in custom_words:
                self._explicit_words.update(_extract_word_tokens(str(w)))
        self._window_words: Set[str] = (
            collect_allowlist_words(main_window=main_window)
            if main_window is not None
            else set(_BROADCAST_DOMAIN_WORDS)
        )
        self._custom_words: Set[str] = set(_BROADCAST_DOMAIN_WORDS) | self._explicit_words | self._window_words

    @property
    def backend_name(self) -> str:
        """Return active backend name: `'pyspellchecker'` or `'fallback'`."""
        return "pyspellchecker" if self._base_sp is not None else "fallback"

    def refresh_from_window(self, main_window: Any = None) -> None:
        """Reload Glossary terms and confirmed speaker names from `main_window`."""
        win = main_window if main_window is not None else self._main_window
        if win is None:
            return
        self._main_window = win
        self._window_words = collect_allowlist_words(main_window=win)
        self._custom_words = set(_BROADCAST_DOMAIN_WORDS) | self._explicit_words | self._window_words

    def add_words(self, words: Iterable[str]) -> None:
        """Add one or more words/phrases to this instance's explicit allowlist."""
        for w in words:
            tokens = _extract_word_tokens(str(w))
            self._explicit_words.update(tokens)
            self._custom_words.update(tokens)

    def is_word_known(self, word: str) -> bool:
        """Return True if `word` is valid English or present in allowlist / session ignores."""
        if not word:
            return True
        norm = _normalize_apostrophe(word)
        if len(norm) <= 1:
            return True
        if norm.isupper() and len(norm) >= 2:
            return True
        if _is_camel_or_mixed_brand(norm):
            return True

        lower = norm.lower()
        if lower in self._custom_words:
            return True
        with _SESSION_IGNORED_LOCK:
            if lower in _SESSION_IGNORED_WORDS:
                return True

        # Strip possessive 's and test root
        if lower.endswith("'s") and len(lower) > 3:
            root = lower[:-2]
            if self.is_word_known(root):
                return True

        if lower in _FALLBACK_CONTRACTIONS:
            return True

        if self._base_sp is not None:
            if lower in self._base_sp:
                return True
            return False

        # Pure-Python fallback dictionary
        vocab = _FALLBACK_CORE_WORDS | self._custom_words
        return _fallback_stem_matches(lower, vocab)

    def find_misspelled_spans(self, text: str) -> List[SpellIssue]:
        """Return all misspelled word spans in `text` in left-to-right order."""
        if not text:
            return []
        issues: List[SpellIssue] = []
        for raw, start, end in iter_checkable_words(text):
            if self.is_word_known(raw):
                continue
            # For hyphenated compounds (e.g. "well-knwon"), inspect parts individually
            if "-" in raw:
                offset = start
                for part in raw.split("-"):
                    part_len = len(part)
                    if part_len > 1 and not self.is_word_known(part):
                        issues.append(SpellIssue(word=part, start=offset, end=offset + part_len))
                    offset += part_len + 1
                continue
            issues.append(SpellIssue(word=raw, start=start, end=end))
        return issues

    def find_issue_at(self, text: str, char_index: int) -> Optional[SpellIssue]:
        """Return the `SpellIssue` covering `char_index` (inclusive of boundaries), if any."""
        if char_index < 0 or not text:
            return None
        for issue in self.find_misspelled_spans(text):
            if issue.start <= char_index <= issue.end:
                return issue
        return None

    def get_suggestions(self, word: str, max_suggestions: int = 5) -> List[str]:
        """Return up to `max_suggestions` spelling suggestions preserving input case."""
        if not word or max_suggestions <= 0:
            return []
        norm = _normalize_apostrophe(word)
        lower = norm.lower()
        possessive = False
        query = lower
        if lower.endswith("'s") and len(lower) > 3:
            query = lower[:-2]
            possessive = True

        ranked: List[str] = []
        seen: Set[str] = set()

        def _push(cand: str) -> None:
            c = cand.strip()
            if not c or c.lower() == query or c.lower() in seen:
                return
            seen.add(c.lower())
            final = f"{c}'s" if possessive else c
            ranked.append(match_case(word, final))

        # 1. Check custom allowlist (Glossary + speaker names) within edit distance 1 first
        edits1 = _edits1(query)
        custom_hits = sorted(
            (w for w in edits1 if w in self._custom_words),
            key=lambda w: (abs(len(w) - len(query)), w),
        )
        for hit in custom_hits:
            _push(hit)
            if len(ranked) >= max_suggestions:
                return ranked

        # 2. Primary backend: pyspellchecker
        if self._base_sp is not None:
            try:
                best = self._base_sp.correction(query)
                if best:
                    _push(best)
                cands = self._base_sp.candidates(query) or set()
                ordered = sorted(
                    cands,
                    key=lambda w: (-int(self._base_sp.word_frequency[w]), w),
                )
                for cand in ordered:
                    _push(cand)
                    if len(ranked) >= max_suggestions:
                        return ranked
            except Exception:
                pass
            return ranked[:max_suggestions]

        # 3. Pure-Python fallback: distance 1 then distance 2 against core vocabulary
        vocab = _FALLBACK_CORE_WORDS | self._custom_words
        d1_hits = sorted(
            (w for w in edits1 if w in vocab),
            key=lambda w: (abs(len(w) - len(query)), w),
        )
        for hit in d1_hits:
            _push(hit)
            if len(ranked) >= max_suggestions:
                return ranked

        if len(query) <= 14:
            d2_hits_set: Set[str] = set()
            for e1 in edits1:
                for e2 in _edits1(e1):
                    if e2 in vocab:
                        d2_hits_set.add(e2)
            for hit in sorted(d2_hits_set, key=lambda w: (abs(len(w) - len(query)), w)):
                _push(hit)
                if len(ranked) >= max_suggestions:
                    return ranked

        return ranked[:max_suggestions]


__all__ = [
    "SpellIssue",
    "OfflineSpellChecker",
    "is_pyspellchecker_available",
    "collect_allowlist_words",
    "iter_checkable_words",
    "match_case",
    "ignore_word_for_session",
    "get_session_ignored_words",
    "clear_session_ignored_words",
]
