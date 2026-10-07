from __future__ import annotations

from html import escape

import streamlit as st

ENCODING = "o200k_base"
CORPUS = [("old", 7), ("older", 3), ("finest", 9), ("lowest", 4)]
MERGES = 5
END = "</w>"
PREFERRED_MERGES = [
    ("e", "s"),
    ("es", "t"),
    ("est", END),
    ("o", "l"),
    ("ol", "d"),
]
STAGE_NAMES = ["Corpus", "Base Units", "Count Pairs", "Iteration", "Learned Vocabulary"]
ITER_STEPS = [
    "1. Highest pair",
    "2. Individual counts",
    "3. Count split",
    "4. Subtract",
    "5. New piece",
    "6. What happens next",
]
LAB_EXAMPLES = [
    "Tokenisation turns text into numbers.",
    "unpredictability",
    "ChatGPTing",
    "internationalization",
    "Hello, how are you?",
    "नमस्ते, आप कैसे हैं?",
    "Order 20250506 ships today",
    "def add(a, b): return a + b",
]
DECK = (
    '<div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span>'
    '<span class="cmx-c1"></span><span class="cmx-c2"></span></div>'
)


@st.cache_resource(show_spinner=False)
def _encoder():
    import tiktoken

    return tiktoken.get_encoding(ENCODING)


def _load():
    try:
        with st.spinner("Loading the GPT-4o tokeniser... the first time can take up to a minute."):
            return _encoder()
    except Exception as exc:
        st.error(f"The tokeniser could not be loaded – {exc}")
        return None


def _bpe_trace() -> dict:
    segs = [list(word) + [END] for word, _ in CORPUS]
    base: list[str] = []
    for seg in segs:
        for unit in seg:
            if unit != END and unit not in base:
                base.append(unit)
    base.append(END)
    stages = []
    for _ in range(MERGES):
        counts: dict[tuple[str, str], int] = {}
        found: dict[tuple[str, str], list[int]] = {}
        for w, seg in enumerate(segs):
            for a, b in zip(seg, seg[1:]):
                counts[(a, b)] = counts.get((a, b), 0) + CORPUS[w][1]
                if w not in found.setdefault((a, b), []):
                    found[(a, b)].append(w)
        best = max(counts, key=lambda p: counts[p])
        tied = [pair for pair, n in counts.items() if n == counts[best]]
        for candidate in PREFERRED_MERGES:
            if candidate in tied:
                best = candidate
                break
        else:
            best = sorted(tied)[0]
        merged = best[0] + best[1]
        new_segs = []
        for seg in segs:
            out, i = [], 0
            while i < len(seg):
                if i + 1 < len(seg) and (seg[i], seg[i + 1]) == best:
                    out.append(merged)
                    i += 2
                else:
                    out.append(seg[i])
                    i += 1
            new_segs.append(out)
        stages.append({"counts": counts, "found": found, "best": best, "merged": merged, "segs": new_segs})
        segs = new_segs
    return {"base": base, "stages": stages}


def _p(piece: str) -> str:
    return escape(piece)


def _q(piece: str) -> str:
    return f"&quot;{_p(piece)}&quot;"


def _piece(piece: str, new: str | None = None) -> str:
    cls = "bpe-token"
    if piece == END:
        cls += " end"
    if piece == new:
        cls += " new"
    return f'<span class="{cls}">{_p(piece)}</span>'


def _corpus_rows(segs: list[list[str]], new: str | None = None) -> str:
    rows = []
    for (word, n), seg in zip(CORPUS, segs):
        chips = "".join(_piece(piece, new) for piece in seg)
        rows.append(
            f'<div class="bpe-row" data-word="{escape(word)}"><span class="nm">{escape(word)}</span>'
            f'<span class="mult">&times;{n}</span><span class="ps">{chips}</span></div>'
        )
    return f'<div class="bpe-rows">{"".join(rows)}</div>'


def _vocab(pieces: list[str], new: str | None = None) -> str:
    return '<div class="bpe-rows vocab">' + "".join(_piece(piece, new) for piece in pieces) + "</div>"


def _active(segs: list[list[str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for (_, n), seg in zip(CORPUS, segs):
        for piece in seg:
            counts[piece] = counts.get(piece, 0) + n
    return counts


def _usage(order: list[str], counts: dict[str, int], new: str | None = None) -> str:
    rows = []
    for piece in order:
        n = counts.get(piece, 0)
        cls = "bpe-row"
        if piece == new:
            cls += " is-new"
        if n == 0:
            cls += " is-zero"
        rows.append(
            f'<div class="{cls}"><span class="ps">{_piece(piece, new)}</span>'
            f'<span class="bpe-use">{n}</span></div>'
        )
    return f'<div class="bpe-rows">{"".join(rows)}</div>'


def _usage_shift(order: list[str], before: dict[str, int], after: dict[str, int], new: str | None = None) -> str:
    rows = [
        '<div class="bpe-shift-head"><span>Token / unit</span><span>Before</span><span>After</span></div>'
    ]
    for piece in order:
        old = before.get(piece, 0)
        now = after.get(piece, 0)
        cls = "bpe-shift-row"
        if piece == new:
            cls += " is-new"
        elif now != old:
            cls += " is-drop"
            if now == 0:
                cls += " is-zero"
        old_cell = "&mdash;" if piece == new else str(old)
        rows.append(
            f'<div class="{cls}"><span class="ps">{_piece(piece, new)}</span>'
            f'<span class="bpe-use was">{old_cell}</span>'
            f'<span class="bpe-use now">{now}</span></div>'
        )
    return f'<div class="bpe-shift">{"".join(rows)}</div>'


def _venn(
    left: str,
    right: str,
    merged: str,
    left_before: int,
    right_before: int,
    freq: int,
    left_only: int,
    right_only: int,
    stages: list[dict],
    phase: str,
) -> str:
    left_strike = " can-strike" if left_only == 0 else ""
    right_strike = " can-strike" if right_only == 0 else ""
    right_zero = " is-zero-only" if right_only == 0 else ""
    absorbed = " is-absorbed" if phase in ("strike", "result") else ""
    if phase == "strike":
        overlap_label = f"subtract this {freq} from both"
        equations = (
            f'<div class="bpe-venn-eq">{_q(left)} <span class="bpe-venn-eq-op">{left_before} &minus; {freq} =</span> '
            f"<strong>{left_only} kept</strong></div>"
            f'<div class="bpe-venn-eq{right_zero}">{_q(right)} <span class="bpe-venn-eq-op">{right_before} &minus; {freq} =</span> '
            f'<strong>{right_only} {"used up" if right_only == 0 else "kept"}</strong></div>'
            f'<div class="bpe-venn-eq">{_q(merged)} <span class="bpe-venn-eq-op">receives the pair</span> '
            f'<span class="bpe-venn-eq-pair">{freq}</span></div>'
        )
    else:
        overlap_label = "where they occur in pair"
        equations = (
            f'<div class="bpe-venn-eq">{_q(left)} is <strong>{left_before}</strong> '
            f'<span class="bpe-venn-eq-op">=</span> <span class="bpe-venn-eq-pair">{freq} in the pair</span> '
            f'<span class="bpe-venn-eq-op">+</span> <span class="bpe-venn-eq-only">{left_only} only {_q(left)}</span></div>'
            f'<div class="bpe-venn-eq{right_zero}">{_q(right)} is <strong>{right_before}</strong> '
            f'<span class="bpe-venn-eq-op">=</span> <span class="bpe-venn-eq-pair">{freq} in the pair</span> '
            f'<span class="bpe-venn-eq-op">+</span> <span class="bpe-venn-eq-only">{right_only} only {_q(right)}</span></div>'
        )
    later = "".join(
        f'<div class="bpe-remaining-row"><span class="bpe-remaining-number">{i}</span>'
        f'<span class="bpe-remaining-formula">{_q(s["best"][0])} + {_q(s["best"][1])}'
        f' <span aria-hidden="true">&rarr;</span> {_q(s["merged"])}</span></div>'
        for i, s in enumerate(stages[1:], start=2)
    )
    return (
        f'<div class="bpe-venn" data-venn-phase="{phase}">'
        f'<div class="bpe-venn-headline">Highest pair &ndash; {_q(left)} + {_q(right)}</div>'
        '<div class="bpe-venn-facts">'
        f'<div class="bpe-venn-fact" data-fact="left"><span>Individual {_q(left)}</span><strong>{left_before}</strong></div>'
        f'<div class="bpe-venn-fact" data-fact="right"><span>Individual {_q(right)}</span><strong>{right_before}</strong></div>'
        f'<div class="bpe-venn-fact" data-fact="pair"><span>Where they occur in pair</span><strong>{freq}</strong></div>'
        "</div>"
        '<div class="bpe-venn-diagram">'
        '<div class="bpe-venn-callout bpe-venn-callout--overlap">'
        f'<span class="bpe-venn-callout-text">{overlap_label}<strong>{freq}</strong></span>'
        '<span class="bpe-venn-callout-arrow" aria-hidden="true">&darr;</span></div>'
        '<div class="bpe-venn-stage">'
        '<div class="bpe-venn-callout bpe-venn-callout--left">'
        '<span class="bpe-venn-callout-arrow" aria-hidden="true">&rarr;</span>'
        f'<span class="bpe-venn-callout-text">only {_q(left)}<strong>{left_only}</strong></span></div>'
        '<div class="bpe-venn-circles">'
        f'<div class="bpe-venn-circle bpe-venn-circle--left{left_strike}">'
        f'<span class="bpe-venn-circle-label">{_q(left)}</span>'
        f'<span class="bpe-venn-region bpe-venn-region--only"><small>only</small>{left_only}</span></div>'
        f'<div class="bpe-venn-circle bpe-venn-circle--right{right_strike}">'
        f'<span class="bpe-venn-circle-label">{_q(right)}</span>'
        f'<span class="bpe-venn-region bpe-venn-region--only"><small>only</small>{right_only}</span></div>'
        f'<div class="bpe-venn-overlap{absorbed}"><strong>{freq}</strong></div>'
        "</div>"
        '<div class="bpe-venn-callout bpe-venn-callout--right">'
        f'<span class="bpe-venn-callout-text">only {_q(right)}<strong>{right_only}</strong></span>'
        '<span class="bpe-venn-callout-arrow" aria-hidden="true">&larr;</span></div>'
        "</div></div>"
        f'<div class="bpe-venn-equations">{equations}</div>'
        '<div class="bpe-venn-result">'
        f'<span class="bpe-venn-result-chip">{_q(merged)}<strong>+{freq}</strong></span>'
        f"<span>The new piece receives the shared pair count ({freq}).</span></div>"
        '<div class="bpe-venn-continue">'
        '<p class="bpe-continue-kicker">The first merge is complete</p>'
        '<h4 class="bpe-continue-title">The same process now repeats</h4>'
        '<p class="bpe-continue-body">After every merge, the old pair counts are thrown away and the updated corpus is scanned again. '
        "The new highest pair is merged everywhere, active usage is updated, and the new piece is added to the vocabulary.</p>"
        '<div class="bpe-continue-cycle" aria-label="Repeating BPE learning loop">'
        "<span>Recount pairs</span><span aria-hidden=\"true\">&rarr;</span>"
        "<span>Select highest pair</span><span aria-hidden=\"true\">&rarr;</span>"
        "<span>Merge globally</span><span aria-hidden=\"true\">&rarr;</span>"
        "<span>Update vocabulary</span></div>"
        f'<div class="bpe-remaining-merges"><span class="bpe-remaining-label">Remaining merges in this demonstration</span>{later}</div>'
        f'<p class="bpe-continue-stop"><strong>Stopping condition</strong> &ndash; this illustration stops after {len(stages)} merges. '
        "A real tokeniser may instead stop when the chosen vocabulary size is reached.</p>"
        "</div></div>"
    )


def _iteration(stage: dict, letters: list[list[str]], stages: list[dict], which: int) -> str:
    left, right = stage["best"]
    freq = stage["counts"][stage["best"]]
    before = _active(letters)
    after = _active(stage["segs"])
    left_before = before.get(left, 0)
    right_before = before.get(right, 0)
    left_only = left_before - freq
    right_only = right_before - freq
    merged = stage["merged"]
    head = f'<div class="tok-h">Iteration &ndash; {escape(ITER_STEPS[which])}</div>'
    phase = ("intro", "individuals", "together", "strike", "result", "continue")[which]
    venn = _venn(left, right, merged, left_before, right_before, freq, left_only, right_only, stages, phase)
    if which == 0:
        tied = [pair for pair, n in stage["counts"].items() if n == freq and pair != stage["best"]]
        tie = ""
        if tied:
            others = ", ".join(f"{_q(pair[0])} + {_q(pair[1])}" for pair in tied)
            tie = (
                f" {_q(left)} + {_q(right)} and {others} are tied at {freq}. "
                f"This walkthrough selects <b>{_q(left)} + {_q(right)}</b>."
            )
        body = (
            f"{venn}"
            f'<div class="tok-k">Highest pair &ndash; {_q(left)} + {_q(right)}</div>{_pair_table(stage, mark=True)}'
            f'<p class="tok-say">Highest adjacent pair is <b>{_q(left)} + {_q(right)}</b> with count <b>{freq}</b>.'
            f"{tie} Next, count each letter on its own.</p>"
        )
    elif which == 1:
        body = (
            f"{venn}"
            f'<div class="tok-k">Active unit usage, before the merge</div>{_usage(list(before), before)}'
            f'<p class="tok-say"><b>{_q(left)}</b> = {left_before} and <b>{_q(right)}</b> = {right_before}. '
            f"Of those, {freq} uses come from the pair itself.</p>"
        )
    elif which == 2:
        body = (
            f"{venn}"
            f"<p class=\"tok-say\">Nothing is removed yet. <b>{_q(left)}</b> is {left_before} because {freq} of those "
            f"sit beside <b>{_q(right)}</b> and {left_only} do not. <b>{_q(right)}</b> is {right_before} because "
            f"every one sits beside <b>{_q(left)}</b>, so {right_only} are left on their own.</p>"
        )
    elif which == 3:
        order = list(before) + [merged]
        body = (
            f"{venn}"
            f'<div class="tok-k">Active unit usage</div>'
            f"{_usage_shift(order, before, after, merged)}"
            f"<p class=\"tok-say\">Subtract the shared {freq} from each letter. <b>{_q(left)}</b> keeps {left_only}. "
            f"<b>{_q(right)}</b> falls to {right_only}, so it is used up. Those {freq} uses become the new piece "
            f"<b>{_q(merged)}</b>.</p>"
        )
    elif which == 4:
        order = list(before) + [merged]
        body = (
            f"{venn}"
            f'<div class="tok-grid"><div><div class="tok-k">The pair is now one piece</div>'
            f'{_corpus_rows(stage["segs"], merged)}</div>'
            f'<div><div class="tok-k">Active unit usage</div>{_usage(order, after, merged)}</div></div>'
        )
    else:
        body = venn
    return f'<div class="tok-stage">{head}{body}</div>'


def _pair_table(stage: dict, mark: bool = False) -> str:
    counts, found, best = stage["counts"], stage["found"], stage["best"]
    order = sorted(counts, key=lambda p: (-counts[p], p[0], p[1]))
    rows = []
    for pair in order:
        words = ", ".join(f"{_q(CORPUS[w][0])} &times;{CORPUS[w][1]}" for w in found[pair])
        keys = ",".join(CORPUS[w][0] for w in found[pair])
        cls = "bpe-pair"
        if mark and pair == best:
            cls += " win"
        rows.append(
            f'<div class="{cls}" data-words="{escape(keys)}">'
            f'<span class="bits">{_piece(pair[0])} + {_piece(pair[1])}</span>'
            f'<span class="ct">{counts[pair]}</span><span class="src">{words}</span></div>'
        )
    return f'<div class="bpe-pairs">{"".join(rows)}</div>'


_OVERVIEW = """
<figure class="tok-overview" id="lecTokOverview" data-phase="0" aria-labelledby="lec-tok-cap">
  <figcaption class="tok-overview-caption" id="lec-tok-cap">Segment the text, then look each token up in the Token &#8596; ID table</figcaption>
  <div class="tok-overview-build">
    <div class="tok-overview-break" aria-label="Prepared fragment broken into pieces">
      <span class="tok-overview-eyebrow">Prepared fragment</span>
      <strong class="tok-overview-break-title">1 &middot; Segment into tokens</strong>
      <div class="tok-overview-break-board" id="lecTokBoard">
        <span class="tok-overview-plain" aria-hidden="true">In the Harappan civilisation around five thousand BC, people built planned cities beside the Indus with baked-brick houses, covered drains and shared wells. Streets followed careful layouts, storehouses held surplus grain, and workshops produced tools, ornaments and inscribed seals used in trade. Traders moved goods across long distances by river and land, craft workers shaped pottery and metal objects, and farmers grew crops on the fertile river plains through changing seasons . . . and this short account of that early urban world, its people and its patterns of settlement, ends here.</span>
        <span class="tok-overview-piece" data-token="In" style="--i:0">In</span>
        <span class="tok-overview-sep" style="--i:0" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="the" style="--i:1">the</span>
        <span class="tok-overview-sep" style="--i:1" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="Harappan" style="--i:2">Harappan</span>
        <span class="tok-overview-sep" style="--i:2" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="civilisation" style="--i:3">civilisation</span>
        <span class="tok-overview-sep" style="--i:3" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="around" style="--i:4">around</span>
        <span class="tok-overview-sep" style="--i:4" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="five" style="--i:5">five</span>
        <span class="tok-overview-sep" style="--i:5" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="thousand" style="--i:6">thousand</span>
        <span class="tok-overview-sep" style="--i:6" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="BC" style="--i:7">BC</span>
        <span class="tok-overview-sep" style="--i:7" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="," style="--i:8">,</span>
        <span class="tok-overview-sep" style="--i:8" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="people" style="--i:9">people</span>
        <span class="tok-overview-sep" style="--i:9" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="built" style="--i:10">built</span>
        <span class="tok-overview-sep" style="--i:10" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="planned" style="--i:11">planned</span>
        <span class="tok-overview-sep" style="--i:11" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="cities" style="--i:12">cities</span>
        <span class="tok-overview-sep" style="--i:12" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="beside" style="--i:13">beside</span>
        <span class="tok-overview-sep" style="--i:13" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="the" style="--i:14">the</span>
        <span class="tok-overview-sep" style="--i:14" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="Indus" style="--i:15">Indus</span>
        <span class="tok-overview-sep" style="--i:15" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="with" style="--i:16">with</span>
        <span class="tok-overview-sep" style="--i:16" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="baked-brick" style="--i:17">baked-brick</span>
        <span class="tok-overview-sep" style="--i:17" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="houses" style="--i:18">houses</span>
        <span class="tok-overview-sep" style="--i:18" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="," style="--i:19">,</span>
        <span class="tok-overview-sep" style="--i:19" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="covered" style="--i:20">covered</span>
        <span class="tok-overview-sep" style="--i:20" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="drains" style="--i:21">drains</span>
        <span class="tok-overview-sep" style="--i:21" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="and" style="--i:22">and</span>
        <span class="tok-overview-sep" style="--i:22" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="shared" style="--i:23">shared</span>
        <span class="tok-overview-sep" style="--i:23" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="wells" style="--i:24">wells</span>
        <span class="tok-overview-sep" style="--i:24" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="." style="--i:25">.</span>
        <span class="tok-overview-sep" style="--i:25" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="Streets" style="--i:26">Streets</span>
        <span class="tok-overview-sep" style="--i:26" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="followed" style="--i:27">followed</span>
        <span class="tok-overview-sep" style="--i:27" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="careful" style="--i:28">careful</span>
        <span class="tok-overview-sep" style="--i:28" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="layouts" style="--i:29">layouts</span>
        <span class="tok-overview-sep" style="--i:29" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="," style="--i:30">,</span>
        <span class="tok-overview-sep" style="--i:30" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="storehouses" style="--i:31">storehouses</span>
        <span class="tok-overview-sep" style="--i:31" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="held" style="--i:32">held</span>
        <span class="tok-overview-sep" style="--i:32" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="surplus" style="--i:33">surplus</span>
        <span class="tok-overview-sep" style="--i:33" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="grain" style="--i:34">grain</span>
        <span class="tok-overview-sep" style="--i:34" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="," style="--i:35">,</span>
        <span class="tok-overview-sep" style="--i:35" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="and" style="--i:36">and</span>
        <span class="tok-overview-sep" style="--i:36" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="workshops" style="--i:37">workshops</span>
        <span class="tok-overview-sep" style="--i:37" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="produced" style="--i:38">produced</span>
        <span class="tok-overview-sep" style="--i:38" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="tools" style="--i:39">tools</span>
        <span class="tok-overview-sep" style="--i:39" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="," style="--i:40">,</span>
        <span class="tok-overview-sep" style="--i:40" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="ornaments" style="--i:41">ornaments</span>
        <span class="tok-overview-sep" style="--i:41" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="and" style="--i:42">and</span>
        <span class="tok-overview-sep" style="--i:42" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="inscribed" style="--i:43">inscribed</span>
        <span class="tok-overview-sep" style="--i:43" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="seals" style="--i:44">seals</span>
        <span class="tok-overview-sep" style="--i:44" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="used" style="--i:45">used</span>
        <span class="tok-overview-sep" style="--i:45" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="in" style="--i:46">in</span>
        <span class="tok-overview-sep" style="--i:46" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="trade" style="--i:47">trade</span>
        <span class="tok-overview-sep" style="--i:47" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="." style="--i:48">.</span>
        <span class="tok-overview-sep" style="--i:48" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="Traders" style="--i:49">Traders</span>
        <span class="tok-overview-sep" style="--i:49" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="moved" style="--i:50">moved</span>
        <span class="tok-overview-sep" style="--i:50" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="goods" style="--i:51">goods</span>
        <span class="tok-overview-sep" style="--i:51" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="across" style="--i:52">across</span>
        <span class="tok-overview-sep" style="--i:52" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="long" style="--i:53">long</span>
        <span class="tok-overview-sep" style="--i:53" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="distances" style="--i:54">distances</span>
        <span class="tok-overview-sep" style="--i:54" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="by" style="--i:55">by</span>
        <span class="tok-overview-sep" style="--i:55" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="river" style="--i:56">river</span>
        <span class="tok-overview-sep" style="--i:56" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="and" style="--i:57">and</span>
        <span class="tok-overview-sep" style="--i:57" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="land" style="--i:58">land</span>
        <span class="tok-overview-sep" style="--i:58" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="," style="--i:59">,</span>
        <span class="tok-overview-sep" style="--i:59" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="craft" style="--i:60">craft</span>
        <span class="tok-overview-sep" style="--i:60" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="workers" style="--i:61">workers</span>
        <span class="tok-overview-sep" style="--i:61" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="shaped" style="--i:62">shaped</span>
        <span class="tok-overview-sep" style="--i:62" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="pottery" style="--i:63">pottery</span>
        <span class="tok-overview-sep" style="--i:63" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="and" style="--i:64">and</span>
        <span class="tok-overview-sep" style="--i:64" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="metal" style="--i:65">metal</span>
        <span class="tok-overview-sep" style="--i:65" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="objects" style="--i:66">objects</span>
        <span class="tok-overview-sep" style="--i:66" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="," style="--i:67">,</span>
        <span class="tok-overview-sep" style="--i:67" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="and" style="--i:68">and</span>
        <span class="tok-overview-sep" style="--i:68" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="farmers" style="--i:69">farmers</span>
        <span class="tok-overview-sep" style="--i:69" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="grew" style="--i:70">grew</span>
        <span class="tok-overview-sep" style="--i:70" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="crops" style="--i:71">crops</span>
        <span class="tok-overview-sep" style="--i:71" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="on" style="--i:72">on</span>
        <span class="tok-overview-sep" style="--i:72" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="the" style="--i:73">the</span>
        <span class="tok-overview-sep" style="--i:73" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="fertile" style="--i:74">fertile</span>
        <span class="tok-overview-sep" style="--i:74" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="river" style="--i:75">river</span>
        <span class="tok-overview-sep" style="--i:75" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="plains" style="--i:76">plains</span>
        <span class="tok-overview-sep" style="--i:76" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="through" style="--i:77">through</span>
        <span class="tok-overview-sep" style="--i:77" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="changing" style="--i:78">changing</span>
        <span class="tok-overview-sep" style="--i:78" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="seasons" style="--i:79">seasons</span>
        <span class="tok-overview-sep" style="--i:79" aria-hidden="true"></span>
        <span class="tok-overview-ellipsis" aria-label="Ellipsis in the passage">. . .</span>
        <span class="tok-overview-sep" style="--i:80" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="and" style="--i:80">and</span>
        <span class="tok-overview-sep" style="--i:80" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="this" style="--i:81">this</span>
        <span class="tok-overview-sep" style="--i:81" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="short" style="--i:82">short</span>
        <span class="tok-overview-sep" style="--i:82" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="account" style="--i:83">account</span>
        <span class="tok-overview-sep" style="--i:83" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="of" style="--i:84">of</span>
        <span class="tok-overview-sep" style="--i:84" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="that" style="--i:85">that</span>
        <span class="tok-overview-sep" style="--i:85" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="early" style="--i:86">early</span>
        <span class="tok-overview-sep" style="--i:86" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="urban" style="--i:87">urban</span>
        <span class="tok-overview-sep" style="--i:87" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="world" style="--i:88">world</span>
        <span class="tok-overview-sep" style="--i:88" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="," style="--i:89">,</span>
        <span class="tok-overview-sep" style="--i:89" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="its" style="--i:90">its</span>
        <span class="tok-overview-sep" style="--i:90" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="people" style="--i:91">people</span>
        <span class="tok-overview-sep" style="--i:91" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="and" style="--i:92">and</span>
        <span class="tok-overview-sep" style="--i:92" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="its" style="--i:93">its</span>
        <span class="tok-overview-sep" style="--i:93" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="patterns" style="--i:94">patterns</span>
        <span class="tok-overview-sep" style="--i:94" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="of" style="--i:95">of</span>
        <span class="tok-overview-sep" style="--i:95" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="settlement" style="--i:96">settlement</span>
        <span class="tok-overview-sep" style="--i:96" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="," style="--i:97">,</span>
        <span class="tok-overview-sep" style="--i:97" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="ends" style="--i:98">ends</span>
        <span class="tok-overview-sep" style="--i:98" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="here" style="--i:99">here</span>
        <span class="tok-overview-sep" style="--i:99" aria-hidden="true"></span>
        <span class="tok-overview-piece" data-token="." style="--i:100">.</span>
      </div>
    </div>
    <div class="tok-overview-arrow tok-overview-arrow--build" aria-hidden="true"><span></span></div>
    <div class="tok-overview-node tok-overview-node--vocabulary">
      <span class="tok-overview-eyebrow">2 &middot; Look up each token</span>
      <strong>Token &#8596; ID vocabulary table</strong>
      <div class="tok-overview-vocab" id="lecTokVocab" role="table" aria-label="Illustrative token vocabulary">
        <div class="tok-overview-vocab-head" role="row"><span role="columnheader">Token</span><span role="columnheader">ID</span></div>
        <div class="tok-overview-vocab-row" role="row" data-token="In"><span role="cell" class="tok-overview-vocab-token">In</span><span role="cell" class="tok-overview-vocab-id">4821</span></div>
        <div class="tok-overview-vocab-row" role="row" data-token="the"><span role="cell" class="tok-overview-vocab-token">the</span><span role="cell" class="tok-overview-vocab-id">262</span></div>
        <div class="tok-overview-vocab-row" role="row" data-token="Harappan"><span role="cell" class="tok-overview-vocab-token">Harappan</span><span role="cell" class="tok-overview-vocab-id">917</span></div>
        <div class="tok-overview-vocab-row" role="row" data-token="civilisation"><span role="cell" class="tok-overview-vocab-token">civilisation</span><span role="cell" class="tok-overview-vocab-id">422</span></div>
        <div class="tok-overview-vocab-row tok-overview-vocab-row--more" role="row"><span role="cell">. . .</span><span role="cell">. . .</span></div>
        <div class="tok-overview-vocab-row" role="row" data-token="of"><span role="cell" class="tok-overview-vocab-token">of</span><span role="cell" class="tok-overview-vocab-id">316</span></div>
        <div class="tok-overview-vocab-row" role="row" data-token="settlement"><span role="cell" class="tok-overview-vocab-token">settlement</span><span role="cell" class="tok-overview-vocab-id">2104</span></div>
        <div class="tok-overview-vocab-row" role="row" data-token="ends"><span role="cell" class="tok-overview-vocab-token">ends</span><span role="cell" class="tok-overview-vocab-id">1337</span></div>
        <div class="tok-overview-vocab-row" role="row" data-token="here"><span role="cell" class="tok-overview-vocab-token">here</span><span role="cell" class="tok-overview-vocab-id">990</span></div>
        <div class="tok-overview-vocab-row" role="row" data-token="."><span role="cell" class="tok-overview-vocab-token">.</span><span role="cell" class="tok-overview-vocab-id">13</span></div>
      </div>
      <span class="tok-overview-frozen" id="lecTokFrozen">Vocabulary and mapping are then frozen</span>
    </div>
  </div>
</figure>
<script>
(function () {
  if (window.__lecTokStop) window.__lecTokStop();
  var root = document.getElementById("lecTokOverview");
  var board = document.getElementById("lecTokBoard");
  var vocab = document.getElementById("lecTokVocab");
  if (!root || !board || !vocab) return;
  var pieces = Array.prototype.slice.call(board.querySelectorAll(".tok-overview-piece"));
  var rows = Array.prototype.slice.call(vocab.querySelectorAll(".tok-overview-vocab-row:not(.tok-overview-vocab-row--more)"));
  var moreRows = Array.prototype.slice.call(vocab.querySelectorAll(".tok-overview-vocab-row--more"));
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var timers = [];
  var flights = [];
  var started = false;
  var runToken = 0;
  var observer = null;
  function clearTimers() {
    timers.forEach(function (id) { window.clearTimeout(id); });
    timers = [];
  }
  function clearFlights() {
    flights.forEach(function (item) {
      if (item.animation && item.animation.cancel) item.animation.cancel();
      if (item.element && item.element.parentNode) item.element.parentNode.removeChild(item.element);
    });
    flights = [];
  }
  window.__lecTokStop = function () {
    clearTimers();
    clearFlights();
    if (observer) observer.disconnect();
  };
  function setPhase(phase) { root.setAttribute("data-phase", String(phase)); }
  function lockHeight() {
    if (board.dataset.heightLocked === "1") return;
    var prev = root.getAttribute("data-phase");
    root.classList.add("tok-overview--measure");
    root.setAttribute("data-phase", "2");
    var height = board.getBoundingClientRect().height;
    if (height > 0) {
      board.style.minHeight = Math.ceil(height) + "px";
      board.dataset.heightLocked = "1";
    }
    root.setAttribute("data-phase", prev || "0");
    root.classList.remove("tok-overview--measure");
  }
  function resetTable() {
    rows.forEach(function (row) { row.classList.remove("is-filled"); });
    moreRows.forEach(function (row) { row.classList.remove("is-shown"); });
    pieces.forEach(function (piece) { piece.classList.remove("is-seated"); });
  }
  function fillRow(row) {
    if (!row || row.classList.contains("is-filled")) return;
    row.classList.add("is-filled");
    var filled = rows.filter(function (item) { return item.classList.contains("is-filled"); }).length;
    if (filled >= 4 && moreRows[0]) moreRows[0].classList.add("is-shown");
  }
  function fly(piece, row, done) {
    var from = piece.getBoundingClientRect();
    var cell = row.querySelector(".tok-overview-vocab-token");
    var to = (cell || row).getBoundingClientRect();
    var flight = document.createElement("span");
    flight.className = "tok-overview-flight";
    flight.textContent = piece.textContent || "";
    flight.setAttribute("aria-hidden", "true");
    flight.style.left = from.left + "px";
    flight.style.top = from.top + "px";
    document.body.appendChild(flight);
    function finish() {
      if (flight.parentNode) flight.parentNode.removeChild(flight);
      piece.classList.add("is-seated");
      fillRow(row);
      if (done) done();
    }
    if (flight.animate) {
      var animation = flight.animate([
        { transform: "translate(0, 0) scale(1)", opacity: 1 },
        { transform: "translate(" + (to.left - from.left) + "px, " + (to.top - from.top) + "px) scale(0.92)", opacity: 0.95 }
      ], { duration: 480, easing: "cubic-bezier(0.22, 1, 0.36, 1)", fill: "forwards" });
      flights.push({ element: flight, animation: animation });
      animation.onfinish = finish;
    } else {
      finish();
    }
  }
  function pickIndex(name, used) {
    var matches = [];
    for (var i = 0; i < pieces.length; i += 1) {
      if (pieces[i].getAttribute("data-token") === name && !used[i]) matches.push(i);
    }
    if (!matches.length) return -1;
    var chosen = (name === "." || name === "of") ? matches[matches.length - 1] : matches[0];
    used[chosen] = true;
    return chosen;
  }
  function seatBetween(fromIndex, toIndex, used) {
    var start = fromIndex < 0 ? -1 : fromIndex;
    var end = toIndex < 0 ? pieces.length : toIndex;
    for (var i = start + 1; i < end; i += 1) {
      if (!used[i]) pieces[i].classList.add("is-seated");
    }
  }
  function seat(token) {
    if (token !== runToken) return;
    var used = [];
    var plan = [];
    for (var r = 0; r < rows.length; r += 1) {
      plan.push({ row: rows[r], index: pickIndex(rows[r].getAttribute("data-token") || "", used) });
    }
    function step(n) {
      if (token !== runToken) return;
      if (n >= plan.length) {
        seatBetween(plan.length ? plan[plan.length - 1].index : -1, -1, used);
        timers.push(window.setTimeout(function () {
          if (token !== runToken) return;
          setPhase(4);
        }, 280));
        timers.push(window.setTimeout(function () {
          if (token !== runToken) return;
          play();
        }, 3200));
        return;
      }
      var cur = plan[n];
      var nextIndex = n + 1 < plan.length ? plan[n + 1].index : -1;
      if (cur.index < 0) {
        fillRow(cur.row);
        seatBetween(n > 0 ? plan[n - 1].index : -1, nextIndex, used);
        timers.push(window.setTimeout(function () { step(n + 1); }, 40));
        return;
      }
      fly(pieces[cur.index], cur.row, function () {
        seatBetween(cur.index, nextIndex, used);
        timers.push(window.setTimeout(function () { step(n + 1); }, 100));
      });
    }
    step(0);
  }
  function play() {
    clearTimers();
    clearFlights();
    runToken += 1;
    var token = runToken;
    resetTable();
    lockHeight();
    setPhase(0);
    if (reduced) {
      setPhase(4);
      pieces.forEach(function (piece) { piece.classList.add("is-seated"); });
      rows.forEach(fillRow);
      moreRows.forEach(function (row) { row.classList.add("is-shown"); });
      return;
    }
    timers.push(window.setTimeout(function () { if (token === runToken) setPhase(1); }, 900));
    timers.push(window.setTimeout(function () { if (token === runToken) setPhase(2); }, 2400));
    timers.push(window.setTimeout(function () {
      if (token !== runToken) return;
      setPhase(3);
      seat(token);
    }, 3400));
  }
  if ("IntersectionObserver" in window) {
    observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting && !started) {
          started = true;
          play();
        }
      });
    }, { threshold: 0.35 });
    observer.observe(root);
  } else {
    play();
  }
  window.setTimeout(function () {
    if (started) return;
    if (root.getClientRects().length) {
      started = true;
      play();
    }
  }, 500);
})();
</script>
"""


def _loop() -> str:
    return """
    <div class="bpe-mech tok-bpe-start-sink" aria-label="BPE Mechanism">
      <strong class="bpe-mech-title tok-bpe-start-sink-title">BPE Mechanism</strong>
      <p class="bpe-mech-note tok-bpe-start-sink-note">The same count &rarr; select &rarr; merge &rarr; recount cycle repeats over the updated corpus.</p>
      <div class="tok-bpe-loop bpe-loop-fig bpe-loop-animated" role="img" aria-label="BPE loop. 1 Count adjacent-pair frequencies of the current pieces. 2 Select the highest-frequency pair. 3 Merge the selected pair wherever it occurs. The return path is the updated vocabulary.">
        <span class="bpe-loop-runner bpe-loop-runner--1" aria-hidden="true"></span>
        <span class="bpe-loop-runner bpe-loop-runner--2" aria-hidden="true"></span>
        <span class="bpe-loop-runner bpe-loop-runner--3" aria-hidden="true"></span>
        <svg class="tok-bpe-loop-svg" viewBox="0 0 520 292" xmlns="http://www.w3.org/2000/svg" focusable="false" aria-hidden="true" hidden>
          <defs>
            <marker id="lecBpeLoopArrN" markerWidth="8.5" markerHeight="8.5" refX="8.25" refY="3.1" orient="auto">
              <path d="M0,0 L8.25,3.1 L0,6.2 Z" fill="#0B1F3A"></path>
            </marker>
            <marker id="lecBpeLoopArrG" markerWidth="8.5" markerHeight="8.5" refX="8.25" refY="3.1" orient="auto">
              <path d="M0,0 L8.25,3.1 L0,6.2 Z" fill="#C9973A"></path>
            </marker>
            <marker id="lecBpeLoopArrD" markerWidth="8.5" markerHeight="8.5" refX="8.25" refY="3.1" orient="auto">
              <path d="M0,0 L8.25,3.1 L0,6.2 Z" fill="#8A6A2C"></path>
            </marker>
          </defs>

          <path d="M 260 74 L 400 232" fill="none" stroke="#0B1F3A" stroke-width="2.5" stroke-opacity="0.22" stroke-linecap="round" marker-end="url(#lecBpeLoopArrN)"></path>
          <path d="M 300 258 L 220 258" fill="none" stroke="#C9973A" stroke-width="2.5" stroke-opacity="0.22" stroke-linecap="round" marker-end="url(#lecBpeLoopArrG)"></path>
          <path d="M 120 232 L 260 74" fill="none" stroke="#8A6A2C" stroke-width="2.5" stroke-opacity="0.22" stroke-linecap="round" marker-end="url(#lecBpeLoopArrD)"></path>

          <path data-bpe-loop-path="0" d="M 260 74 L 400 232" class="tok-bpe-loop-flow" fill="none" stroke="#0B1F3A" stroke-width="2.7" stroke-linecap="round"></path>
          <path data-bpe-loop-path="1" d="M 300 258 L 220 258" class="tok-bpe-loop-flow" fill="none" stroke="#C9973A" stroke-width="2.7" stroke-linecap="round" style="animation-delay:0.35s"></path>
          <path data-bpe-loop-path="2" d="M 120 232 L 260 74" class="tok-bpe-loop-flow" fill="none" stroke="#8A6A2C" stroke-width="2.7" stroke-linecap="round" style="animation-delay:0.7s"></path>

          <circle data-bpe-loop-dot="0" class="tok-bpe-loop-dot" cx="260" cy="74" r="4.8" fill="#0B1F3A"></circle>
          <circle data-bpe-loop-dot="1" class="tok-bpe-loop-dot" cx="300" cy="258" r="4.8" fill="#C9973A"></circle>
          <circle data-bpe-loop-dot="2" class="tok-bpe-loop-dot" cx="120" cy="232" r="4.8" fill="#8A6A2C"></circle>

          <g transform="translate(172, 138) rotate(-49.5)">
            <rect x="-54.5" y="-12.5" width="109" height="25" rx="12.5" fill="#fff" stroke="#8A6A2C" stroke-width="1.6" stroke-opacity="0.85"></rect>
            <text x="0" y="4.2" text-anchor="middle" fill="#8A6A2C" font-size="12.5" font-weight="800">updated vocab</text>
          </g>

          <circle cx="260" cy="178" r="36" fill="#fff" stroke="#0B1F3A" stroke-width="2.1"></circle>
          <text x="260" y="173.5" text-anchor="middle" fill="#0B1F3A" font-size="13.75" font-weight="800">BPE</text>
          <text x="260" y="190.5" text-anchor="middle" fill="#5A6880" font-size="10.5" font-weight="650">loop</text>

          <g class="tok-bpe-loop-step tok-bpe-loop-step--1" transform="translate(260, 48)">
            <rect x="-154.5" y="-27" width="309" height="54" rx="27" fill="#0B1F3A"></rect>
            <circle cx="-126" cy="0" r="12.5" fill="#fff"></circle>
            <text x="-126" y="5" text-anchor="middle" fill="#0B1F3A" font-size="13.5" font-weight="800">1</text>
            <text x="-101.5" y="-5.2" fill="#fff" font-size="13" font-weight="750">Count adjacent-pair frequencies of</text>
            <text x="-101.5" y="13.2" fill="#fff" font-size="13" font-weight="750">the current pieces</text>
          </g>

          <g class="tok-bpe-loop-step tok-bpe-loop-step--2" transform="translate(400, 258)">
            <rect x="-103" y="-27" width="206" height="54" rx="27" fill="#C9973A"></rect>
            <circle cx="-76.5" cy="0" r="12.5" fill="#fff"></circle>
            <text x="-76.5" y="5" text-anchor="middle" fill="#C9973A" font-size="13.5" font-weight="800">2</text>
            <text x="-53.5" y="-5.2" fill="#fff" font-size="13.5" font-weight="750">Select the highest-</text>
            <text x="-53.5" y="13.2" fill="#fff" font-size="13.5" font-weight="750">frequency pair</text>
          </g>

          <g class="tok-bpe-loop-step tok-bpe-loop-step--3" transform="translate(120, 258)">
            <rect x="-103" y="-27" width="206" height="54" rx="27" fill="#8A6A2C"></rect>
            <circle cx="-76.5" cy="0" r="12.5" fill="#fff"></circle>
            <text x="-76.5" y="5" text-anchor="middle" fill="#8A6A2C" font-size="13.5" font-weight="800">3</text>
            <text x="-53.5" y="-5.2" fill="#fff" font-size="13.5" font-weight="750">Merge selected pair</text>
            <text x="-53.5" y="13.2" fill="#fff" font-size="13.5" font-weight="750">wherever it occurs</text>
          </g>
        </svg>
      </div>
    </div>
    """


def _bpe_explain(operation: str, evidence: str, insight: str) -> str:
    return (
        '<aside class="bpe-explain" aria-label="Stage explanation">'
        '<div class="bpe-explain-block"><span class="bpe-explain-label">Operation</span>'
        f'<div class="bpe-explain-text">{operation}</div></div>'
        '<div class="bpe-explain-block"><span class="bpe-explain-label">Evidence from this corpus</span>'
        f'<div class="bpe-explain-text">{evidence}</div></div>'
        '<div class="bpe-explain-block"><span class="bpe-explain-label">What to understand</span>'
        f'<div class="bpe-explain-text">{insight}</div></div>'
        '</aside>'
    )


def _bpe_stage_panel(
    index: int,
    stage_id: str,
    title: str,
    body: str,
    operation: str,
    evidence: str,
    insight: str,
) -> str:
    hidden = "" if index == 0 else " hidden"
    return (
        f'<section class="bpe-stage-panel" id="lec-bpe-stage-panel-{index}" data-bpe-stage-panel="{index}" data-stage="{stage_id}" '
        f'role="tabpanel" aria-labelledby="lec-bpe-stage-{index}"{hidden}>'
        '<div class="bpe-layout">'
        '<div class="bpe-board">'
        '<div class="bpe-step-banner"><span class="bpe-merge-kicker">Stage</span>'
        f'<span class="bpe-step-title">{title}</span></div>{body}</div>'
        f'{_bpe_explain(operation, evidence, insight)}'
        '</div></section>'
    )


_BPE_WALKTHROUGH_SCRIPT = r"""
<script>
(function () {
  var root = document.getElementById("lecBpeWalkthrough");
  if (!root || root.dataset.ready === "true") return;
  root.dataset.ready = "true";

  var stageButtons = Array.prototype.slice.call(root.querySelectorAll("[data-bpe-stage-button]"));
  var stagePanels = Array.prototype.slice.call(root.querySelectorAll("[data-bpe-stage-panel]"));
  var progress = root.querySelector("[data-bpe-stage-progress]");
  var iterPanels = Array.prototype.slice.call(root.querySelectorAll("[data-bpe-iteration-panel]"));
  var iterPrev = root.querySelector("[data-bpe-iter-prev]");
  var iterNext = root.querySelector("[data-bpe-iter-next]");
  var iterLabel = root.querySelector("[data-bpe-iter-label]");
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var loopPaths = Array.prototype.slice.call(root.querySelectorAll("[data-bpe-loop-path]"));
  var loopDots = Array.prototype.slice.call(root.querySelectorAll("[data-bpe-loop-dot]"));
  var currentStage = 0;
  var currentIteration = 0;

  function placeLoopDots(now) {
    var duration = 2200;
    var offsets = [0, 700, 1400];
    loopDots.forEach(function (dot, index) {
      var path = loopPaths[index];
      if (!path || !path.getTotalLength || !path.getPointAtLength) return;
      var elapsed = ((now - offsets[index]) % duration + duration) % duration;
      var point = path.getPointAtLength(path.getTotalLength() * (elapsed / duration));
      dot.setAttribute("cx", point.x.toFixed(2));
      dot.setAttribute("cy", point.y.toFixed(2));
    });
  }

  function animateLoop(now) {
    if (!document.documentElement.contains(root)) return;
    placeLoopDots(now);
    window.requestAnimationFrame(animateLoop);
  }

  if (reduced) placeLoopDots(1100);
  else window.requestAnimationFrame(animateLoop);

  function animatePanel(panel, forward) {
    if (!panel || reduced || !panel.animate) return;
    panel.animate([
      { opacity: 0, transform: "translateX(" + (forward ? "32px" : "-32px") + ")" },
      { opacity: 1, transform: "translateX(0)" }
    ], { duration: 340, easing: "cubic-bezier(0.22, 1, 0.36, 1)" });
  }

  function syncIteration() {
    iterPanels.forEach(function (panel, index) {
      panel.hidden = index !== currentIteration;
      panel.setAttribute("aria-hidden", index === currentIteration ? "false" : "true");
    });
    if (iterPrev) iterPrev.disabled = currentIteration === 0;
    if (iterNext) iterNext.disabled = currentIteration === iterPanels.length - 1;
    if (iterLabel) iterLabel.textContent = (currentIteration + 1) + " / " + iterPanels.length;
  }

  function showStage(index) {
    index = Math.max(0, Math.min(stagePanels.length - 1, index));
    var forward = index >= currentStage;
    currentStage = index;
    stagePanels.forEach(function (panel, panelIndex) {
      panel.hidden = panelIndex !== index;
      panel.setAttribute("aria-hidden", panelIndex === index ? "false" : "true");
    });
    stageButtons.forEach(function (button, buttonIndex) {
      var active = buttonIndex === index;
      button.classList.toggle("is-active", active);
      button.classList.toggle("is-done", buttonIndex < index);
      button.setAttribute("aria-selected", active ? "true" : "false");
      button.tabIndex = active ? 0 : -1;
    });
    root.setAttribute("data-stage", stagePanels[index].getAttribute("data-stage"));
    if (progress) progress.textContent = stageButtons[index].getAttribute("data-stage-label");
    animatePanel(stagePanels[index], forward);
    if (index === 3) syncIteration();
  }

  stageButtons.forEach(function (button, index) {
    button.addEventListener("click", function () { showStage(index); });
    button.addEventListener("keydown", function (event) {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      event.preventDefault();
      var next = event.key === "ArrowRight"
        ? (index + 1) % stageButtons.length
        : (index - 1 + stageButtons.length) % stageButtons.length;
      stageButtons[next].focus();
      showStage(next);
    });
  });

  if (iterPrev) iterPrev.addEventListener("click", function () {
    if (currentIteration === 0) return;
    currentIteration -= 1;
    syncIteration();
    animatePanel(iterPanels[currentIteration], false);
  });
  if (iterNext) iterNext.addEventListener("click", function () {
    if (currentIteration >= iterPanels.length - 1) return;
    currentIteration += 1;
    syncIteration();
    animatePanel(iterPanels[currentIteration], true);
  });

  var countBoard = root.querySelector("[data-bpe-count-board]");
  if (countBoard) {
    var countPairs = Array.prototype.slice.call(countBoard.querySelectorAll(".bpe-pair"));
    var countWords = Array.prototype.slice.call(countBoard.querySelectorAll(".bpe-row[data-word]"));
    function clearCountHot() {
      countPairs.forEach(function (el) { el.classList.remove("is-hot"); });
      countWords.forEach(function (el) { el.classList.remove("is-hot"); });
    }
    countWords.forEach(function (row) {
      row.addEventListener("mouseenter", function () {
        var word = row.getAttribute("data-word");
        clearCountHot();
        row.classList.add("is-hot");
        countPairs.forEach(function (pair) {
          var list = (pair.getAttribute("data-words") || "").split(",");
          if (list.indexOf(word) !== -1) pair.classList.add("is-hot");
        });
      });
      row.addEventListener("mouseleave", clearCountHot);
    });
  }

  syncIteration();
  showStage(0);
})();
</script>
"""


def _bpe_walkthrough(trace: dict) -> str:
    base, stages = trace["base"], trace["stages"]
    letters = [list(word) + [END] for word, _ in CORPUS]
    first = stages[0]
    vocab = base + [stage["merged"] for stage in stages]
    rules = "".join(
        f"<li>{_q(stage['best'][0])} + {_q(stage['best'][1])} &rarr; <b>{_q(stage['merged'])}</b></li>"
        for stage in stages
    )

    corpus_cards = "".join(
        f'<div class="bpe-count" style="--i:{index}"><span class="bpe-count-word">{escape(word)}</span>'
        f'<span class="bpe-count-times">&times;{count}</span></div>'
        for index, (word, count) in enumerate(CORPUS)
    )
    corpus_body = (
        '<div class="bpe-viz-corpus"><span class="bpe-viz-corpus-label">Tokenizer-training corpus</span>'
        f'<div class="bpe-viz-counts">{corpus_cards}</div></div>'
        '<p class="tok-say">A pair inside <i>old</i> is counted 7 times, because the word itself appears 7 times. '
        'Nothing has been split yet.</p>'
    )
    base_body = (
        '<div class="tok-grid"><div><div class="tok-k">1 &middot; Append the word boundary and separate the units</div>'
        f'{_corpus_rows(letters)}</div><div><div class="tok-k">2 &middot; Initial base-unit vocabulary &ndash; {len(base)} entries</div>'
        f'<div class="tok-vocab">{_vocab(base)}</div>'
        '<p class="tok-say">11 letters plus the end marker. These are the base units. Nothing has been learned yet.</p>'
        '</div></div>'
    )
    count_body = (
        '<div class="bpe-count-board" data-bpe-count-board>'
        '<div><div class="tok-k">Adjacent pair counts</div>'
        f'{_pair_table(first)}'
        '<p class="tok-say">Hover a word on the right to see which neighbouring pairs it contributes to. '
        "Every neighbouring pair is listed, sorted by count. "
        "<b>&quot;e&quot; + &quot;s&quot;</b>, <b>&quot;s&quot; + &quot;t&quot;</b>, and <b>&quot;t&quot; + &quot;&lt;/w&gt;&quot;</b> "
        "are tied at 13. This walkthrough selects <b>&quot;e&quot; + &quot;s&quot;</b>.</p>"
        '</div><div><div class="tok-k">Corpus still in base units</div>'
        f'{_corpus_rows(letters)}</div></div>'
    )
    iteration_panels = "".join(
        f'<div class="bpe-iteration-panel" data-bpe-iteration-panel="{index}"'
        f'{"" if index == 0 else " hidden"}>{_iteration(first, letters, stages, index)}</div>'
        for index in range(len(ITER_STEPS))
    )
    iteration_body = (
        '<p class="bpe-loop-banner">Count current pairs &rarr; select the highest-frequency pair &rarr; merge &rarr; '
        'update active unit usage &rarr; recount.</p>'
        '<div class="bpe-merge-update-head"><span class="bpe-pair-label">First merge, step by step</span>'
        '<div class="bpe-venn-stepper" role="group" aria-label="Merge explanation steps">'
        '<button type="button" class="bpe-venn-step-btn" data-bpe-iter-prev aria-label="Previous merge step">&lt;</button>'
        '<span class="bpe-venn-step-label" data-bpe-iter-label aria-live="polite">1 / 6</span>'
        '<button type="button" class="bpe-venn-step-btn" data-bpe-iter-next aria-label="Next merge step">&gt;</button>'
        '</div></div>'
        f'<div class="bpe-iteration-track">{iteration_panels}</div>'
    )
    vocab_body = (
        '<div class="tok-grid"><div><div class="tok-k">Final split of the corpus</div>'
        f'{_corpus_rows(stages[-1]["segs"])}'
        '<p class="tok-say"><i>finest</i> and <i>lowest</i> now share <b>&quot;est&lt;/w&gt;&quot;</b>, and '
        '<i>old</i> and <i>older</i> share <b>&quot;old&quot;</b>.</p></div>'
        f'<div><div class="tok-k">Complete learned vocabulary &ndash; {len(vocab)} entries</div>'
        f'<div class="tok-vocab">{_vocab(vocab)}</div>'
        f'<div class="tok-k tok-gap">Ordered merge rules</div><ol class="tok-rules">{rules}</ol>'
        '<p class="tok-say">12 base units plus 5 merge-created pieces. A piece can stay in the vocabulary even when '
        'its active usage is zero; later rules and new text may still need it.</p></div></div>'
    )

    panels = "".join([
        _bpe_stage_panel(
            0,
            "corpus",
            "Corpus",
            corpus_body,
            "Start with the tokenizer-training corpus and preserve how often each supplied word occurs.",
            "<b>old &times; 7</b>, <b>older &times; 3</b>, <b>finest &times; 9</b>, and <b>lowest &times; 4</b>.",
            "The frequencies are weights. A neighbouring pair found once in a word contributes that word's full corpus count.",
        ),
        _bpe_stage_panel(
            1,
            "base",
            "Base Units",
            base_body,
            "Append the teaching example's word-boundary marker, split every word, and keep one copy of each unique starting unit.",
            "The four words produce 11 distinct letters plus <b>&lt;/w&gt;</b>, giving 12 starting vocabulary entries.",
            "These pieces are available before BPE learns anything. Every accepted merge will add exactly one new entry.",
        ),
        _bpe_stage_panel(
            2,
            "count",
            "Count Pairs",
            count_body,
            "Scan only adjacent pieces, add their corpus-weighted occurrences, and rank the resulting pair counts.",
            "<b>&quot;e&quot; + &quot;s&quot;</b>, <b>&quot;s&quot; + &quot;t&quot;</b>, and <b>&quot;t&quot; + &quot;&lt;/w&gt;&quot;</b> each reach 13. The fixed tie rule selects <b>&quot;e&quot; + &quot;s&quot;</b>.",
            "BPE does not inspect meaning or grammar. It chooses from the counts produced by the current segmentation.",
        ),
        _bpe_stage_panel(
            3,
            "iteration",
            "Iteration",
            iteration_body,
            "Select the winning pair, merge it everywhere, update active unit usage, add the new piece, and repeat.",
            "The first merge replaces every adjacent <b>&quot;e&quot; + &quot;s&quot;</b> with <b>&quot;es&quot;</b>, so the new piece enters with active usage 13.",
            "Use the arrows to walk through the first merge. The remaining merges repeat this same count &rarr; select &rarr; merge &rarr; recount loop.",
        ),
        _bpe_stage_panel(
            4,
            "vocab",
            "Learned Vocabulary",
            vocab_body,
            "Freeze the base units and every merge-created piece after the configured five-merge budget is exhausted.",
            "The learned rules create <b>&quot;es&quot;</b>, <b>&quot;est&quot;</b>, <b>&quot;est&lt;/w&gt;&quot;</b>, <b>&quot;ol&quot;</b>, and <b>&quot;old&quot;</b> in that order.",
            "A piece remains in the vocabulary even if its active usage in this final toy-corpus segmentation falls to zero.",
        ),
    ])
    buttons = "".join(
        f'<button type="button" class="bpe-stage-capsule{" is-active" if index == 0 else ""}" '
        f'id="lec-bpe-stage-{index}" data-bpe-stage-button="{index}" data-stage-label="{escape(label)}" '
        f'role="tab" aria-controls="lec-bpe-stage-panel-{index}" aria-selected="{"true" if index == 0 else "false"}" '
        f'tabindex="{0 if index == 0 else -1}"><span class="bpe-stage-capsule-num">{index + 1}</span>'
        f'<span class="bpe-stage-capsule-label">{escape(label)}</span></button>'
        for index, label in enumerate(STAGE_NAMES)
    )
    return (
        '<section class="bpe-walkthrough-v2" id="lecBpeWalkthrough" data-stage="corpus" aria-labelledby="lec-bpe-walk-title">'
        '<div class="att-head" id="lec-bpe-walk-title"><span class="att-tag">Walkthrough</span>'
        'Five clickable stages. Iteration opens six more steps</div>'
        '<p class="se-hint">Corpus, Base Units, Count Pairs, Iteration, and Learned Vocabulary. '
        'Open Iteration and use the arrows to walk through the first merge. Later merges repeat the same loop.</p>'
        '<div class="bpe-stage-nav" aria-label="BPE stages"><div class="bpe-stage-capsules" role="tablist" '
        f'aria-label="BPE walkthrough stages">{buttons}</div>'
        '<div class="bpe-stage-status"><span class="bpe-stage-progress" data-bpe-stage-progress '
        'aria-live="polite">Corpus</span></div></div>'
        f'<div class="bpe-viz">{panels}</div>{_loop()}</section>{_BPE_WALKTHROUGH_SCRIPT}'
    )


def _set_text(text: str) -> None:
    st.session_state.tok_text = text


_UNIT_PLAY = """
<script>
(function () {
  if (window.__lecUnitStop) window.__lecUnitStop();
  var units = Array.prototype.slice.call(document.querySelectorAll(".tok-unit-viz"));
  if (!units.length) return;
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var timers = [];
  var playing = false;
  var visible = 0;
  var observer = null;
  function clearTimers() {
    timers.forEach(function (id) { window.clearTimeout(id); });
    timers = [];
  }
  function setPhase(phase) {
    units.forEach(function (root) { root.setAttribute("data-phase", String(phase)); });
  }
  window.__lecUnitStop = function () {
    clearTimers();
    playing = false;
    if (observer) observer.disconnect();
  };
  function play() {
    clearTimers();
    setPhase(0);
    if (reduced) {
      setPhase(2);
      return;
    }
    timers.push(window.setTimeout(function () { setPhase(1); }, 700));
    timers.push(window.setTimeout(function () { setPhase(2); }, 1600));
    timers.push(window.setTimeout(play, 3800));
  }
  function start() {
    if (playing || !visible) return;
    playing = true;
    play();
  }
  function stop() {
    if (visible > 0) return;
    playing = false;
    clearTimers();
    setPhase(0);
  }
  if ("IntersectionObserver" in window) {
    observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          if (!entry.target._tokUnitOn) {
            entry.target._tokUnitOn = true;
            visible += 1;
          }
          start();
        } else if (entry.target._tokUnitOn) {
          entry.target._tokUnitOn = false;
          visible = Math.max(0, visible - 1);
          stop();
        }
      });
    }, { threshold: 0.2 });
    units.forEach(function (unit) { observer.observe(unit); });
  } else {
    visible = units.length;
    start();
  }
  window.setTimeout(function () {
    if (playing) return;
    var shown = units.some(function (unit) { return unit.getClientRects().length; });
    if (!shown) return;
    visible = Math.max(visible, 1);
    start();
  }, 400);
})();
</script>
"""


def render_idea() -> None:
    st.html(
        f"""
        <section class="cmx-card dtx-card w2x" aria-labelledby="tok-idea-title">
          {DECK}
          <div class="cmx-kicker">Tokenisation</div>
          <h2 id="tok-idea-title">From text to token IDs</h2>
          <p class="dtx-lead">A language model does not read letters or words. It reads <b>numbers</b>. Before any text
          reaches the model, a <b>tokeniser</b> cuts it into pieces called <b>tokens</b> and replaces every token with its
          <b>token ID</b> &ndash; a whole number.</p>
          <p class="dtx-lead">The heart of the tokeniser is a finite <b>Token &harr; ID table</b>, also called the
          <b>vocabulary</b>. Each row pairs one token with one unique ID. It is the master record of which token has which
          ID.</p>

          <h3>Two steps, every time</h3>
          <ol class="w2x-steps">
            <li><b class="t">Cut the text into tokens</b>
            The Harappan passage starts as one block. Gold cuts open between the words, then each word becomes a capsule.
            This preview uses one token per word, so the break is easy to see.</li>
            <li><b class="t">Look up each token in the table</b>
            A few of those words fly to the table and receive an ID. The words in between stand for the many other rows a
            real table holds. Then the mapping is frozen.</li>
          </ol>
          """ + _OVERVIEW + """
          <div class="w2x-note"><b>A simplified picture</b> &ndash; the passage is cut on whole words, and the IDs in the table are
          illustrative, so the two steps are easy to follow. A real tokeniser may cut inside a word. The GPT-4o table has
          about <b>200,000</b> rows. The last tab runs that tokeniser on text you type.</div>

          <h3>Built once, then frozen</h3>
          <p class="dtx-lead">The table is <b>built once</b>, from a large sample of text, and then <b>frozen</b>. From then
          on the same text always gives the same tokens and the same IDs &ndash; during training and every time you chat.
          The hard design question is not handing out the numbers. It is deciding <b>what should count as a token</b> in the
          first place &ndash; the next tab.</p>
        </section>
        """,
        unsafe_allow_javascript=True,
    )


def render_units() -> None:
    st.html(
        f"""
        <section class="cmx-card dtx-card w2x" aria-labelledby="tok-units-title">
          {DECK}
          <div class="cmx-kicker">What counts as a token</div>
          <h2 id="tok-units-title">Words, characters, bytes or subwords</h2>
          <p class="dtx-lead">The choice of unit decides how long a piece of text becomes in tokens &ndash; and so how much
          memory and compute it costs, and how much text fits in the model&rsquo;s fixed input limit, called its
          <b>context window</b>. There are four main families.</p>
          <div class="att-gaps">
            <div class="gc"><span class="att-tag">A &middot; Word</span><b>One token per word</b>
              <div class="tok-unit-viz" data-phase="0" aria-label="Word-level tokenisation">
                <span class="tok-unit-viz-source">&ldquo;Models learn from data&rdquo;</span>
                <span class="tok-unit-viz-arrow" aria-hidden="true">&rarr;</span>
                <div class="tok-unit-viz-board">
                  <span class="tok-unit-viz-piece" style="--i:0">Models</span><span class="tok-unit-viz-sep" style="--i:0" aria-hidden="true"></span>
                  <span class="tok-unit-viz-piece" style="--i:1">learn</span><span class="tok-unit-viz-sep" style="--i:1" aria-hidden="true"></span>
                  <span class="tok-unit-viz-piece" style="--i:2">from</span><span class="tok-unit-viz-sep" style="--i:2" aria-hidden="true"></span>
                  <span class="tok-unit-viz-piece" style="--i:3">data</span>
                </div>
              </div>
              <small><b class="up">Good</b> &ndash; short, readable sequences.<br>
              <b class="down">Problem</b> &ndash; a huge table that still misses new words, names, code and numbers.</small></div>
            <div class="gc"><span class="att-tag">B &middot; Character</span><b>One token per letter</b>
              <div class="tok-unit-viz" data-phase="0" aria-label="Character-level tokenisation">
                <span class="tok-unit-viz-source">&ldquo;model&rdquo;</span>
                <span class="tok-unit-viz-arrow" aria-hidden="true">&rarr;</span>
                <div class="tok-unit-viz-board">
                  <span class="tok-unit-viz-piece" style="--i:0">m</span><span class="tok-unit-viz-sep" style="--i:0" aria-hidden="true"></span>
                  <span class="tok-unit-viz-piece" style="--i:1">o</span><span class="tok-unit-viz-sep" style="--i:1" aria-hidden="true"></span>
                  <span class="tok-unit-viz-piece" style="--i:2">d</span><span class="tok-unit-viz-sep" style="--i:2" aria-hidden="true"></span>
                  <span class="tok-unit-viz-piece" style="--i:3">e</span><span class="tok-unit-viz-sep" style="--i:3" aria-hidden="true"></span>
                  <span class="tok-unit-viz-piece" style="--i:4">l</span>
                </div>
              </div>
              <small><b class="up">Good</b> &ndash; a tiny table and no unknown words.<br>
              <b class="down">Problem</b> &ndash; very long sequences, and the model must learn how letters make words.</small></div>
            <div class="gc"><span class="att-tag">C &middot; Byte</span><b>One token per byte</b>
              <div class="tok-unit-viz" data-phase="0" aria-label="Byte-level tokenisation">
                <span class="tok-unit-viz-source">&ldquo;&#2344;&rdquo;</span>
                <span class="tok-unit-viz-arrow" aria-hidden="true">&rarr;</span>
                <div class="tok-unit-viz-board">
                  <span class="tok-unit-viz-piece" style="--i:0">E0</span><span class="tok-unit-viz-sep" style="--i:0" aria-hidden="true"></span>
                  <span class="tok-unit-viz-piece" style="--i:1">A4</span><span class="tok-unit-viz-sep" style="--i:1" aria-hidden="true"></span>
                  <span class="tok-unit-viz-piece" style="--i:2">A8</span>
                </div>
              </div>
              <small>Text is stored in computers as bytes, and there are only <b>256</b> possible byte values. One Hindi letter needs three of them.<br>
              <b class="up">Good</b> &ndash; any script, emoji or symbol can be written.<br>
              <b class="down">Problem</b> &ndash; even longer sequences.</small></div>
            <div class="gc"><span class="att-tag">D &middot; Subword</span><b>Common words whole, rare words in pieces</b>
              <div class="tok-unit-viz" data-phase="0" aria-label="Subword tokenisation">
                <span class="tok-unit-viz-source">&ldquo;unpredictability&rdquo;</span>
                <span class="tok-unit-viz-arrow" aria-hidden="true">&rarr;</span>
                <div class="tok-unit-viz-board">
                  <span class="tok-unit-viz-piece" style="--i:0">un</span><span class="tok-unit-viz-sep" style="--i:0" aria-hidden="true"></span>
                  <span class="tok-unit-viz-piece" style="--i:1">predict</span><span class="tok-unit-viz-sep" style="--i:1" aria-hidden="true"></span>
                  <span class="tok-unit-viz-piece" style="--i:2">ability</span>
                </div>
              </div>
              <small><b class="up">Good</b> &ndash; a manageable table, short sequences, and unseen words built from known parts.<br>
              <b class="up">Today</b> &ndash; the mainstream choice in modern language models.</small></div>
          </div>

          <h3>Why subwords win</h3>
          <p class="dtx-lead">A tokeniser has to satisfy three demands at once &ndash; keep the <b>table</b> a manageable size,
          keep <b>sequences short</b>, and still handle <b>text it has never seen</b>. Take a word no dictionary has &ndash;
          <i>ChatGPTing</i>.</p>
          <table class="w2x-set se-check tok-cmp">
            <thead><tr><th>Unit</th><th>ChatGPTing becomes</th><th>Length</th><th>Handles the new word?</th></tr></thead>
            <tbody>
              <tr><td>Word</td><td><span class="tok-p unk">[UNK]</span> &ndash; unknown</td><td class="yes">1 &ndash; short</td><td class="no">No</td></tr>
              <tr><td>Subword</td><td><span class="tok-p">Chat</span><span class="tok-p">GPT</span><span class="tok-p">ing</span></td><td class="yes">3 &ndash; short</td><td class="yes">Yes &ndash; from known pieces</td></tr>
              <tr><td>Character</td><td><span class="tok-p">C</span><span class="tok-p">h</span><span class="tok-p">a</span><span class="tok-p">t</span><span class="tok-p">G</span><span class="tok-p">P</span><span class="tok-p">T</span><span class="tok-p">i</span><span class="tok-p">n</span><span class="tok-p">g</span></td><td class="no">10 &ndash; long</td><td class="yes">Yes</td></tr>
            </tbody>
          </table>
          <p class="dtx-lead">Each extreme wins on one demand and fails on another. Subwords sit in between &ndash; the subword
          row is the real split made by the GPT-4o tokeniser.</p>
          <div class="w2x-note"><b>The families can be combined</b> &ndash; GPT-style tokenisers start from the 256
          <b>bytes</b>, so nothing is ever unknown, and then learn to join frequent byte sequences into larger
          <b>subword</b> pieces. The most influential way to learn those pieces is <b>Byte Pair Encoding (BPE)</b> &ndash; the
          next tab.</div>
        </section>
        """ + _UNIT_PLAY,
        unsafe_allow_javascript=True,
    )


def render_bpe() -> None:
    trace = _bpe_trace()
    base, stages = trace["base"], trace["stages"]
    st.html(
        f"""
        <section class="cmx-card dtx-card w2x" aria-labelledby="tok-bpe-title">
          {DECK}
          <div class="cmx-kicker">How the pieces are learned</div>
          <h2 id="tok-bpe-title">Byte Pair Encoding (BPE)</h2>
          <p class="dtx-lead">BPE builds the vocabulary from the bottom up. It starts from the smallest units and keeps
          repeating one simple loop &ndash; <b>count every neighbouring pair, select the most frequent pair, merge it
          everywhere, and count again</b>. Every merge adds one entry to the table.</p>
          <p class="dtx-lead">To watch it, we use a tiny toy corpus &ndash; <i>old</i> appears 7 times, <i>older</i> 3,
          <i>finest</i> 9 and <i>lowest</i> 4. A pair found once inside <i>old</i> therefore counts 7 times. We also add a
          marker <span class="tok-p end">&lt;/w&gt;</span> at the end of each word, so the tokeniser can tell a piece that ends
          a word from the same letters in the middle of one.</p>
          <div class="w2x-note"><b>Source</b> &ndash; this toy corpus and the merge walkthrough follow
          <a href="https://youtu.be/fKd8s29e-l4" target="_blank" rel="noopener">Vizuara, Lecture 8 &ndash; The GPT Tokenizer:
          Byte Pair Encoding</a>.</div>
          <div class="w2x-note"><b>This is not training the model</b> &ndash; BPE only decides the vocabulary. It happens
          once, before the language model itself starts learning.</div>
        </section>
        """
    )
    st.html(_bpe_walkthrough(trace), unsafe_allow_javascript=True)
    st.html(
        f"""
        <section class="cmx-card dtx-card w2x tok-after" aria-labelledby="tok-stop-title">
          <h3 id="tok-stop-title">When does the loop stop?</h3>
          <p class="dtx-lead">BPE has no natural end &ndash; it would keep merging until whole words, and then whole phrases,
          became single tokens. So it is given a <b>finish line</b> before it starts. It can be told how many merges to learn,
          or how large the vocabulary should grow. These are the same finish line &ndash; each merge adds exactly one entry,
          so <b>{len(base)} starting entries + {MERGES} merges = {len(base) + MERGES} entries</b>.</p>
          <div class="w2x-note"><b>BPE knows no grammar</b> &ndash; <i>&quot;old&quot;</i> and <i>&quot;est&quot;</i> look like a stem and an
          ending only because this toy corpus was built that way. BPE just counts which neighbours appear together most
          often.</div>

          <h3>How big should the vocabulary be?</h3>
          <p class="dtx-lead">A larger target means more merges, so longer pieces can be reused. Take
          <i>internationalization</i>.</p>
          <div class="att-gaps">
            <div class="gc"><span class="att-tag">Smaller vocabulary</span><b>More, shorter pieces</b>
              <small><span class="tok-p">inter</span><span class="tok-p">nation</span><span class="tok-p">al</span><span class="tok-p">ization</span> &ndash; 4 tokens (illustrative)<br>
              <b class="up">Good</b> &ndash; small pieces are reused across many words, so the model sees each one often.<br>
              <b class="down">Cost</b> &ndash; longer sequences, more compute, less text fits in the context window.</small></div>
            <div class="gc"><span class="att-tag">Larger vocabulary</span><b>Fewer, longer pieces</b>
              <small><span class="tok-p">international</span><span class="tok-p">ization</span> &ndash; 2 tokens (the real GPT-4o split)<br>
              <b class="up">Good</b> &ndash; shorter sequences, more text fits in the context window.<br>
              <b class="down">Cost</b> &ndash; a bigger table, and very specific pieces appear rarely, so the model gets few
              examples to learn them from.</small></div>
          </div>
          <p class="dtx-lead">There is <b>no single best size</b> &ndash; it is a design choice. BERT, from the Attention tab,
          uses about <b>30,000</b> entries. The GPT-4o tokeniser uses about <b>200,000</b>, partly to cover many languages
          and code well.</p>
        </section>
        """
    )


def render_ids() -> None:
    trace = _bpe_trace()
    vocab = trace["base"] + [s["merged"] for s in trace["stages"]]
    rows = [
        f'<tr><td><span class="tok-p{" end" if piece == END else ""}{" new" if i >= len(trace["base"]) else ""}">'
        f'{_p(piece)}</span></td><td class="n">{i}</td></tr>'
        for i, piece in enumerate(vocab)
    ]
    half = (len(rows) + 1) // 2
    left, right = "".join(rows[:half]), "".join(rows[half:])
    head = "<thead><tr><th>Token</th><th>ID</th></tr></thead>"
    st.html(
        f"""
        <section class="cmx-card dtx-card w2x" aria-labelledby="tok-ids-title">
          {DECK}
          <div class="cmx-kicker">Token IDs and special tokens</div>
          <h2 id="tok-ids-title">Giving every token a number</h2>
          <p class="dtx-lead">Once BPE stops, the vocabulary is known. Each entry is now given one <b>unique whole
          number</b> &ndash; its <b>token ID</b>. Here is the toy vocabulary from the BPE tab, numbered in the order the
          entries were created. The gold pieces came from merges.</p>
          <div class="tok-idtab">
            <table class="w2x-set tok-ids">{head}<tbody>{left}</tbody></table>
            <table class="w2x-set tok-ids">{head}<tbody>{right}</tbody></table>
          </div>
          <div class="w2x-note"><b>The numbers carry no meaning</b> &ndash; <i>old</i> being 16 says nothing about old.
          Only the mapping matters. The <b>token</b> is the text piece; the <b>token ID</b> is its fixed label in the
          table.</div>

          <h3>Small differences, different tokens</h3>
          <p class="dtx-lead">In the real GPT-4o table, a space or a capital letter gives a different token with a different
          ID &ndash; the model has to learn that they are related.</p>
          <div class="tok-chips">
            <span class="tc c0"><b>bank</b><small>17289</small></span><span class="tc c1"><b><i class="tok-sp">_</i>bank</b><small>6922</small></span><span class="tc c2"><b>Bank</b><small>22057</small></span><span class="tc c3"><b><i class="tok-sp">_</i>Bank</b><small>9950</small></span><span class="tc c4"><b><i class="tok-sp">_</i>BANK</b><small>100886</small></span>
          </div>

          <h3>Special tokens</h3>
          <p class="dtx-lead">A few entries are <b>not learned by BPE</b> at all. They are reserved on purpose, to mark
          something about the <b>structure</b> of the text rather than the text itself. They are called <b>special
          tokens</b>.</p>
          <p class="dtx-lead">Why would a model need an <b>end-of-text</b> token when text already has full stops? Look at
          <i>Dr. Rao arrived. He sat down.</i> &ndash; the full stop appears <b>three times</b>, and only the last one ends the
          text. A full stop is ordinary punctuation. An end marker is a clear signal that the text is over.</p>
          <table class="w2x-set tok-special">
            <thead><tr><th>Role</th><th>What it marks</th><th>Example</th></tr></thead>
            <tbody>
              <tr><td>Beginning</td><td>The start of a sequence</td><td><span class="tok-p">&lt;s&gt;</span> <span class="tok-p">&lt;|begin_of_text|&gt;</span> in Llama</td></tr>
              <tr><td>End of text</td><td>The text is over &ndash; also how a model signals it has finished its answer</td><td><span class="tok-p">&lt;|endoftext|&gt;</span> in GPT tokenisers</td></tr>
              <tr><td>Padding</td><td>Fills empty slots so texts of different lengths can be processed together</td><td><span class="tok-p">[PAD]</span> in BERT</td></tr>
              <tr><td>Unknown</td><td>A fallback for text the table cannot write &ndash; byte-based tokenisers rarely need it</td><td><span class="tok-p">[UNK]</span> in BERT</td></tr>
              <tr><td>Separator</td><td>The border between two pieces of input</td><td><span class="tok-p">[SEP]</span> in BERT</td></tr>
            </tbody>
          </table>
          <p class="dtx-lead">Chat models use the same idea to mark turns. Llama, which you use in Post Training, wraps every
          message in markers such as <span class="tok-p">&lt;|start_header_id|&gt;</span> and ends each turn with
          <span class="tok-p">&lt;|eot_id|&gt;</span>.</p>

          <h3>What comes out of tokenisation</h3>
          <ol class="w2x-steps">
            <li><b class="t">For training</b>
            The frozen tokeniser turns the huge training text into long lists of token IDs. These lists are what the
            language model learns from.</li>
            <li><b class="t">Every time you chat</b>
            Your prompt is cut into tokens the same way. The model predicts the <b>next token ID</b>, which is looked up in
            the same table and turned back into text &ndash; one token at a time, until it produces an end token or hits a
            limit.</li>
          </ol>
          <div class="w2x-note w2x-next"><b>Why this matters next</b> &ndash; everything a model counts, it counts in
          tokens. The context window, the <b>Output length</b> control in Post Training and the price of every request are
          all measured in tokens, not words. The last tab lets you tokenise your own text.</div>
        </section>
        """
    )


def _chip(enc, token_id: int, n: int) -> str:
    raw = enc.decode_single_token_bytes(token_id)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        hexed = " ".join(f"{b:02x}" for b in raw)
        return (
            f'<span class="tc c{n % 5} part" title="Part of a character &ndash; bytes {hexed}">'
            f"<b>{hexed}</b><small>{token_id}</small></span>"
        )
    lead = ""
    if text.startswith(" "):
        lead = '<i class="tok-sp">_</i>'
        text = text[1:]
    shown = escape(text).replace(" ", '<i class="tok-sp">_</i>').replace("\n", '<i class="tok-sp">&crarr;</i>')
    return f'<span class="tc c{n % 5}"><b>{lead}{shown}</b><small>{token_id}</small></span>'


def render_lab() -> None:
    state = st.session_state
    state.setdefault("tok_text", LAB_EXAMPLES[0])
    with st.container(key="tok_lab"):
        st.html(
            '<div class="att-head"><span class="att-tag">Lab</span>Tokenise your own text</div>'
            '<p class="se-hint">This tab runs the <b>real GPT-4o tokeniser</b> (<span class="tok-p">o200k_base</span> in tiktoken), '
            "not the toy BPE walkthrough. Type anything and press Enter. You will see the actual tokens and IDs GPT-4o uses. "
            "An underscore (<i class='tok-sp'>_</i>) marks a space that belongs to the token.</p>"
        )
        text = st.text_input(
            "Text to tokenise",
            key="tok_text",
            placeholder="Type some text and press Enter",
            label_visibility="collapsed",
        )
        with st.container(key="tok_examples", horizontal=True, gap="small", vertical_alignment="center"):
            st.html('<span class="att-exlabel">Try an example</span>', width="content")
            for example in LAB_EXAMPLES:
                st.button(example, key=f"tok_ex_{example}", width="content", on_click=_set_text, args=(example,))
        if not text.strip():
            return
        enc = _load()
        if enc is None:
            return
        ids = enc.encode(text, disallowed_special=())
        chips = "".join(_chip(enc, token_id, n) for n, token_id in enumerate(ids))
        words = len(text.split())
        id_list = ", ".join(str(i) for i in ids)
        st.html(
            '<div class="tok-stats">'
            f'<div class="sc"><span class="gk">Characters</span><b>{len(text):,}</b></div>'
            f'<div class="sc"><span class="gk">Words</span><b>{words:,}</b></div>'
            f'<div class="sc end"><span class="gk">Tokens</span><b>{len(ids):,}</b></div>'
            "</div>"
            f'<div class="tok-live"><div class="tok-chips">{chips}</div></div>'
            f'<div class="tok-k tok-gap">What the model receives</div><div class="tok-idlist">[{id_list}]</div>'
        )
    st.html(
        """
        <section class="cmx-card dtx-card w2x tok-after" aria-labelledby="tok-look-title">
          <h3 id="tok-look-title">What to look for</h3>
          <ul class="w2x-list">
            <li><b>Common words stay whole</b> &ndash; <i>turns</i>, <i>text</i> and <i>numbers</i> are one token each.</li>
            <li><b>Rare or new words split</b> &ndash; <i>unpredictability</i> becomes un / predict / ability, and
            <i>ChatGPTing</i> becomes Chat / GPT / ing.</li>
            <li><b>Other languages cost more</b> &ndash; <i>Hello, how are you?</i> takes 6 tokens, while the same greeting
            in Hindi takes 9. The same message can cost more and fill the context window faster.</li>
            <li><b>Numbers and code split their own way</b> &ndash; <i>20250506</i> becomes 202 / 505 / 06, and in code
            symbols such as <i>(a</i> and <i>):</i> join into tokens of their own.</li>
          </ul>
          <div class="w2x-note"><b>Every model has its own tokeniser</b> &ndash; this is the one used by OpenAI&rsquo;s
          GPT-4o models. Llama or BERT would split the same text differently and give different IDs.</div>
        </section>
        """
    )


def render() -> None:
    tab_idea, tab_units, tab_bpe, tab_ids, tab_lab = st.tabs(
        ["From text to tokens", "What counts as a token", "How BPE learns", "Token IDs and special tokens", "Tokenise your text"]
    )
    with tab_idea:
        render_idea()
    with tab_units:
        render_units()
    with tab_bpe:
        render_bpe()
    with tab_ids:
        render_ids()
    with tab_lab:
        render_lab()
