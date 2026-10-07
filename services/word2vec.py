from __future__ import annotations

import base64
import math
import random
from pathlib import Path

import streamlit as st

_NAVY = "#0b1f3a"
_CTX = "#2f6fd6"
_TGT = "#c9973a"
_POS = "#1b7a47"
_NEG = "#c0392b"
_MUTED = "#9aa3b2"
_ROYAL = "#7a4fc0"


_FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
_FONT_FILES = (
    ("inter-latin-700", 700, "U+0020-007E,U+00B7,U+2013,U+2192,U+2212,U+2248"),
    ("inter-latin-800", 800, "U+0020-007E,U+00B7,U+2013,U+2192,U+2212,U+2248"),
    ("inter-greek-800", 800, "U+03B8"),
)


def _font_faces() -> str:
    faces = []
    for name, weight, rng in _FONT_FILES:
        path = _FONT_DIR / f"{name}.woff2"
        if path.exists():
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            faces.append(
                f"@font-face{{font-family:Inter;font-weight:{weight};unicode-range:{rng};"
                f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
            )
    return "".join(faces)


_SVG_STYLE = (
    "<style>"
    + _font_faces()
    + "text{font-family:Inter,sans-serif}"
    ".sv-l{fill:#1f2a44;font-size:13px;font-weight:700}"
    ".sv-c{font-size:14px;font-weight:700}"
    ".sv-b{font-size:15px;font-weight:800}"
    ".sv-t{fill:#9b7229;font-size:15px;font-weight:800}"
    ".sv-s{fill:#9aa3b2;font-size:11px;font-weight:700}"
    ".sv-r{fill:#7a4fc0;font-size:13px;font-weight:800}"
    ".sv-g{fill:#9b7229;font-size:11px;font-weight:700}"
    ".flow{stroke-dasharray:8 7;animation:d 1.1s linear infinite}"
    ".flow.gold{stroke-dasharray:10 6}"
    ".pulse{animation:p 1.8s ease-in-out infinite}"
    "@keyframes d{to{stroke-dashoffset:-30}}"
    "@keyframes p{0%,100%{opacity:.45}50%{opacity:1}}"
    "@media (prefers-reduced-motion:reduce){.flow,.pulse{animation:none}}"
    "</style>"
)


def _img(svg: str) -> str:
    svg = svg.replace('<svg class="w2v-svg"', '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    head_end = svg.index(">") + 1
    svg = svg[:head_end] + _SVG_STYLE + svg[head_end:]
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<img class="w2v-svg" src="data:image/svg+xml;base64,{data}" alt="">'


def _chip(word: str, kind: str = "") -> str:
    return f'<span class="wk {kind}">{word}</span>'


_HEAT = ("hn3", "hn2", "hn1", "h0", "hp1", "hp2", "hp3")


def _bucket(v: float) -> str:
    return _HEAT[max(0, min(6, round(v * 3) + 3))]


def _cell(v: float) -> str:
    return f'<span class="n {_bucket(v)}">{_num(v)}</span>'


def _num(v: float) -> str:
    return f"{v:.2f}".replace("-", "&minus;")


def _nv(values: list[float], label: str = "", more: bool = True) -> str:
    cells = "".join(_cell(v) for v in values)
    dots = '<span class="dots">&hellip;</span>' if more else ""
    box = f'<span class="w2v-nv"><b class="br">[</b>{cells}{dots}<b class="br">]</b></span>'
    return f'<span class="w2v-nvw"><em>{label}</em>{box}</span>' if label else box


def _points(word: str, kind: str, values: list[float]) -> str:
    return (
        f'<div class="w2v-vrow pv">{_chip(word, kind)}<span class="w2v-conn sm"><i></i></span>'
        f'{_nv(values, f"vector of <b>&ldquo;{word}&rdquo;</b>")}</div>'
    )


def _rand_vec(seed: int, n: int = 8) -> list[float]:
    rng = random.Random(seed)
    return [rng.uniform(-1, 1) for _ in range(n)]


def _arrow(x1: float, y1: float, x2: float, y2: float, color: str, width: float = 2.5, dash: bool = False, cls: str = "") -> str:
    ang = math.atan2(y2 - y1, x2 - x1)
    c, s = math.cos(ang), math.sin(ang)
    bx, by = x2 - 11 * c, y2 - 11 * s
    p1 = (bx + 5.5 * s, by - 5.5 * c)
    p2 = (bx - 5.5 * s, by + 5.5 * c)
    d = ' stroke-dasharray="6 5"' if dash else ""
    if cls:
        d += f' class="{cls}"'
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round"{d}/>'
        f'<polygon points="{x2:.1f},{y2:.1f} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" fill="{color}"/>'
    )


def _dot(x: float, y: float, label: str, color: str, dx: float = 9, dy: float = 4, anchor: str = "start") -> str:
    return (
        f'<circle cx="{x}" cy="{y}" r="6" fill="{color}"/>'
        f'<text x="{x + dx}" y="{y + dy}" text-anchor="{anchor}" class="sv-l">{label}</text>'
    )


def _fit_x(x: float, label: str, width: float = 260) -> float:
    half = len(label) * 4.8 + 4
    return min(max(x, half), width - half)


def _cosine_panel(a_deg: float, b_deg: float, la: str, lb: str, ca: str, cb: str) -> str:
    ox, oy, r, ar = 130, 150, 104, 34
    a, b = math.radians(a_deg), math.radians(b_deg)
    ax, ay = ox + r * math.cos(a), oy - r * math.sin(a)
    bx, by = ox + r * math.cos(b), oy - r * math.sin(b)
    s1 = (ox + ar * math.cos(a), oy - ar * math.sin(a))
    s2 = (ox + ar * math.cos(b), oy - ar * math.sin(b))
    mid = (a + b) / 2
    tx, ty = ox + (ar + 16) * math.cos(mid), oy - (ar + 16) * math.sin(mid)
    return (
        '<svg class="w2v-svg" viewBox="0 0 260 175" role="img">'
        f'<path d="M {ox + r} {oy} A {r} {r} 0 0 0 {ox - r} {oy}" fill="none" stroke="#d5dbe5" stroke-width="1.5" stroke-dasharray="4 5"/>'
        f'<line x1="{ox - r - 6}" y1="{oy}" x2="{ox + r + 6}" y2="{oy}" stroke="#e3e8f0" stroke-width="1.5"/>'
        f'<path d="M {s1[0]:.1f} {s1[1]:.1f} A {ar} {ar} 0 0 0 {s2[0]:.1f} {s2[1]:.1f}" fill="none" stroke="{_TGT}" stroke-width="2.5" class="pulse"/>'
        f'<text x="{tx:.1f}" y="{ty + 5:.1f}" text-anchor="middle" class="sv-t">&#952;</text>'
        + _arrow(ox, oy, ax, ay, ca, 3)
        + _arrow(ox, oy, bx, by, cb, 3)
        + f'<text x="{_fit_x(ax + 22 * math.cos(a), la):.1f}" y="{ay - 16 * math.sin(a) + 4:.1f}" text-anchor="middle" class="sv-b" fill="{ca}">{la}</text>'
        + f'<text x="{_fit_x(bx + 22 * math.cos(b), lb):.1f}" y="{by - 16 * math.sin(b) + 4:.1f}" text-anchor="middle" class="sv-b" fill="{cb}">{lb}</text>'
        + f'<circle cx="{ox}" cy="{oy}" r="4" fill="{_NAVY}"/>'
        + f'<text x="{ox + r - 4}" y="{oy + 18}" text-anchor="end" class="sv-s">length 1</text>'
        + "</svg>"
    )


def _map_before() -> str:
    return (
        '<svg class="w2v-svg" viewBox="0 0 300 180" role="img">'
        + _dot(40, 40, "holmes", _MUTED)
        + _dot(205, 48, "london", _MUTED)
        + _dot(150, 100, "watson", _MUTED)
        + _dot(60, 140, "paris", _MUTED)
        + _dot(270, 110, "lestrade", _MUTED, -9, 4, "end")
        + _dot(240, 158, "scotland", _MUTED, -9, 4, "end")
        + "</svg>"
    )


def _map_after() -> str:
    return (
        '<svg class="w2v-svg" viewBox="0 0 300 180" role="img">'
        '<ellipse cx="82" cy="66" rx="72" ry="48" fill="#e6efff" stroke="#b9cff5" stroke-width="1.5"/>'
        '<ellipse cx="220" cy="126" rx="72" ry="46" fill="#e8f5ee" stroke="#b6dcc4" stroke-width="1.5"/>'
        + _dot(42, 42, "holmes", _CTX)
        + _dot(58, 68, "watson", _CTX)
        + _dot(42, 94, "lestrade", _CTX)
        + _dot(178, 104, "london", _POS)
        + _dot(194, 130, "scotland", _POS)
        + _dot(178, 156, "paris", _POS)
        + '<text x="82" y="136" text-anchor="middle" class="sv-s">people</text>'
        + '<text x="220" y="70" text-anchor="middle" class="sv-s">places</text>'
        + "</svg>"
    )


def _star() -> str:
    cx, cy = 230, 95
    parts = ['<svg class="w2v-svg" viewBox="0 0 460 190" role="img">']
    spots = [("watson", 70, 38), ("detective", 390, 38), ("lestrade", 70, 152), ("inspector", 390, 152)]
    for _, x, y in spots:
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="#8fb2ee" stroke-width="2.5" class="flow"/>')
    for word, x, y in spots:
        w = len(word) * 8.5 + 26
        parts.append(
            f'<rect x="{x - w / 2:.1f}" y="{y - 15}" width="{w:.1f}" height="30" rx="15" fill="#e6efff" stroke="{_CTX}" stroke-width="1.5"/>'
            f'<text x="{x}" y="{y + 5}" text-anchor="middle" class="sv-c" fill="{_CTX}">{word}</text>'
        )
    parts.append(
        f'<rect x="{cx - 52}" y="{cy - 18}" width="104" height="36" rx="18" fill="{_NAVY}"/>'
        f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" class="sv-c" fill="#ffffff">holmes</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def _cand(word: str, values: list[float], score: float, hi: bool = False, prefix: str = "") -> str:
    label = f"{prefix}vector of <b>&ldquo;{word}&rdquo;</b>"
    cls = "w2v-score hi" if hi else "w2v-score"
    return f'<div class="w2v-vrow pv">{_nv(values, label)}<span class="{cls}">score {_num(score)}</span></div>'


def _shared() -> str:
    mid = 230
    words = [("examined", 30), ("letter", 66), ("case", 102), ("inspector", 138), ("Baker Street", 174)]
    parts = ['<svg class="w2v-svg" viewBox="0 0 460 204" role="img">']
    for word, y in words:
        w = len(word) * 8.2 + 26
        parts.append(_arrow(116, 102, mid - w / 2 - 5, y, _CTX, 2, False, "flow"))
        parts.append(_arrow(344, 102, mid + w / 2 + 5, y, _TGT, 2, False, "flow gold"))
    for word, y in words:
        w = len(word) * 8.2 + 26
        parts.append(
            f'<rect x="{mid - w / 2:.1f}" y="{y - 14}" width="{w:.1f}" height="28" rx="14" fill="#ffffff" stroke="#cfd6e2" stroke-width="1.5"/>'
            f'<text x="{mid}" y="{y + 5}" text-anchor="middle" class="sv-l">{word}</text>'
        )
    for word, x in (("holmes", 70), ("watson", 390)):
        parts.append(
            f'<rect x="{x - 46}" y="85" width="92" height="34" rx="17" fill="{_NAVY}"/>'
            f'<text x="{x}" y="107" text-anchor="middle" class="sv-c" fill="#ffffff">{word}</text>'
        )
    parts.append('<text x="70" y="140" text-anchor="middle" class="sv-s">must predict</text>')
    parts.append('<text x="390" y="140" text-anchor="middle" class="sv-s">must predict</text>')
    parts.append("</svg>")
    return "".join(parts)


def _analogy() -> str:
    man, woman, king, queen = (70, 176), (250, 176), (150, 56), (330, 56)
    return (
        '<svg class="w2v-svg" viewBox="0 0 420 215" role="img">'
        + _arrow(man[0], man[1], king[0] - 5, king[1] + 13, _ROYAL, 3, True, "flow")
        + _arrow(woman[0], woman[1], queen[0] - 5, queen[1] + 13, _ROYAL, 3, True, "flow")
        + _arrow(man[0] + 10, man[1], woman[0] - 10, woman[1], _TGT, 3.5, True, "flow gold")
        + _arrow(king[0] + 10, king[1], queen[0] - 10, queen[1], _TGT, 3.5, True, "flow gold")
        + '<text x="98" y="120" text-anchor="end" class="sv-r">+ royal</text>'
        + '<text x="302" y="120" text-anchor="start" class="sv-r">+ royal</text>'
        + '<text x="160" y="200" text-anchor="middle" class="sv-g">man &#8594; woman</text>'
        + '<text x="240" y="44" text-anchor="middle" class="sv-g">king &#8594; queen</text>'
        + _dot(man[0], man[1], "man", _NAVY, 0, 24, "middle")
        + _dot(woman[0], woman[1], "woman", _NAVY, 0, 24, "middle")
        + _dot(king[0], king[1], "king", _NAVY, 0, -14, "middle")
        + _dot(queen[0], queen[1], "queen", _NAVY, 0, -14, "middle")
        + "</svg>"
    )


def _embed_table() -> str:
    rows = [
        ("holmes", 0.42, -0.17, 0.31),
        ("watson", 0.38, -0.11, 0.29),
        ("lestrade", 0.35, -0.22, 0.26),
        ("london", -0.51, 0.64, -0.18),
        ("scotland", -0.46, 0.58, -0.24),
        ("paris", -0.55, 0.61, -0.12),
    ]
    body = "".join(
        f'<tr><td>{w}</td><td class="{_bucket(a / 0.75)}">{_num(a)}</td><td class="{_bucket(b / 0.75)}">{_num(b)}</td>'
        f'<td class="gap">&hellip;</td><td class="{_bucket(c / 0.75)}">{_num(c)}</td></tr>'
        for w, a, b, c in rows
    )
    return (
        '<table class="w2v-heat"><thead><tr><th></th><th>Dimension 1</th><th>Dimension 2</th>'
        '<th class="gap">&hellip;</th><th>Dimension 50</th></tr></thead>'
        f"<tbody>{body}</tbody></table>"
    )


def _steps(items: list[str], kind: str = "") -> str:
    out = []
    for i, item in enumerate(items):
        if i:
            out.append('<span class="w2v-conn"><i></i></span>')
        out.append(f'<span class="w2v-step {kind}">{item}</span>')
    return f'<div class="w2v-steps">{"".join(out)}</div>'


def _tokens(words: list[tuple[str, str, str]]) -> str:
    cells = "".join(
        f'<span class="tok {kind}"><span class="tok-w">{w}</span><span class="tok-l">{label}</span></span>'
        for w, kind, label in words
    )
    return f'<div class="w2v-win">{cells}</div>'


def _intro_html() -> str:
    sent = [
        ("the", "dim", ""), ("detective", "dim", ""), ("examined", "dim", ""),
        ("the", "ctx", "context"), ("strange", "ctx", "context"),
        ("letter", "tgt", "centre"), ("carefully", "ctx", "context"),
    ]
    window = [
        ("detective", "dim", ""), ("examined", "dim", ""), ("the", "ctx q0", "context"),
        ("strange", "ctx q1", "context"), ("letter", "tgt", "centre"), ("carefully", "ctx q2", "context"),
    ]
    stage = ['<div class="sgs-wrap"><div class="sgs">']
    for i, (w, kind, label) in enumerate(window):
        stage.append(
            f'<span class="tok {kind} t{i}"><span class="tok-w">{w}</span><span class="tok-l">{label}</span></span>'
        )
    stage.append('<span class="sgs-label">2 &middot; Each neighbour breaks off and pairs with the centre word</span>')
    for i, w in enumerate(["the", "strange", "carefully"]):
        stage.append(f'<span class="slot s{i}"><i></i></span>')
        stage.append(f'<span class="g gw ga{i}">letter</span><span class="g gc gb{i}">{w}</span>')
    stage.append("</div></div>")
    sg_stage = "".join(stage)

    def tree(words: list[str], kind: str, merge: bool) -> str:
        cells = "".join(
            f'<span class="cell">{_chip(w, kind)}<span class="w2v-vconn noh"><i></i></span></span>' if merge
            else f'<span class="cell"><span class="w2v-vconn"><i></i></span>{_chip(w, kind)}</span>'
            for w in words
        )
        bar = f'<div class="hb {"in" if merge else "out"}"><i class="l"></i><i class="r"></i></div>'
        return f'<div class="row">{cells}</div>{bar}' if merge else f'{bar}<div class="row">{cells}</div>'
    shared_r = "".join(_chip(w, "ctx") for w in ["ruled", "kingdom", "throne"])
    shared_s = "".join(_chip(w, "ctx") for w in ["wicket", "over", "ball", "stumps"])
    family_r = "".join(_chip(w, "royal") for w in ["king", "prince", "queen", "princess", "monarch"])
    family_s = "".join(_chip(w, "pos") for w in ["bowler", "batsman", "umpire", "captain", "fielder"])
    ctx3 = f'<span>{_chip("the", "ctx")}{_chip("strange", "ctx")}{_chip("carefully", "ctx")}</span>'
    ctx_vecs = {
        "the": [0.90, -0.30, 0.60],
        "strange": [0.60, -0.90, 0.15],
        "carefully": [0.30, -0.60, 0.45],
    }
    cbow_rows = "".join(_points(w, "ctx", v) for w, v in ctx_vecs.items())
    avg = [sum(col) / 3 for col in zip(*ctx_vecs.values())]
    letter_vec = [0.72, -0.41, 0.83]
    cbow_cands = "".join([
        _cand("letter", [0.55, -0.48, 0.43], 0.92, True),
        _cand("note", [0.31, -0.12, 0.05], 0.47),
        _cand("river", [-0.40, 0.52, -0.10], 0.06),
        _cand("wicket", [-0.12, 0.66, -0.58], 0.02),
    ])
    sg_rows = "".join(
        _cand(w, v, sc, True, f"prediction {i} &ndash; ")
        for i, (w, v, sc) in enumerate([
            ("the", [0.64, -0.30, 0.71], 0.81),
            ("strange", [0.58, -0.52, 0.60], 0.77),
            ("carefully", [0.69, -0.22, 0.80], 0.74),
        ], 1)
    )
    h50 = [round(v, 2) for v in _rand_vec(7, 50)]
    h50[0], h50[1], h50[49] = 0.42, -0.17, 0.31
    holmes50 = (
        '<span class="w2v-nvw"><em>vector of <b>&ldquo;holmes&rdquo;</b> &ndash; 50 numbers</em><span class="w2v-nv grid">'
        + "".join(_cell(v) for v in h50)
        + "</span></span>"
    )

    return f"""
<div class="w2v">
  <div class="w2v-kicker">Words to Vectors</div>
  <h2 class="w2v-title">Word2Vec &ndash; Learning Meaning from Context</h2>

  <p>A computer initially sees words only as symbols. The words {_chip("king", "plain")} {_chip("queen", "plain")}
  {_chip("river", "plain")} and {_chip("bank", "plain")} do not automatically carry any notion of meaning or similarity.
  Bag of Words, in the first tab, only counts them &ndash; to it, <i>king</i> and <i>queen</i> are as unrelated as
  <i>king</i> and <i>river</i>.</p>
  <p>Word2Vec gives every word a <b>vector</b> &ndash; simply a list of numbers, one list per word. It learns those
  numbers by looking at <b>which words tend to occur around each word</b>.</p>
  <blockquote>Words that occur in similar contexts tend to acquire similar vector representations.</blockquote>
  <p>Word2Vec does not learn from one sentence or one book. It reads a huge amount of text. Across all of it,
  words about the same theme keep meeting the <b>same surrounding words</b>. Read the sentences in each group and
  notice the underlined words that keep coming back &ndash;</p>
  <div class="w2v-two">
    <div class="w2v-panel fam r">
      <div class="w2v-ptitle">Royalty</div>
      <div class="w2v-sents fs">
        <div>the old <span class="fw r">king</span> <span class="sc">ruled</span> for forty years before he gave up the <span class="sc">throne</span></div>
        <div>crowds lined the streets as the young <span class="fw r">prince</span> rode back into the <span class="sc">kingdom</span></div>
        <div>the <span class="fw r">queen</span> <span class="sc">ruled</span> with patience, and the <span class="sc">kingdom</span> grew rich under her</div>
        <div>everyone whispered that the <span class="fw r">princess</span> would one day claim the <span class="sc">throne</span></div>
        <div>in a rare speech, the <span class="fw r">monarch</span> promised peace across the whole <span class="sc">kingdom</span></div>
      </div>
      <div class="fam-row"><span class="fam-k">Shared company</span>{shared_r}</div>
      <div class="fam-row"><span class="fam-k">Words that end up close</span>{family_r}</div>
    </div>
    <div class="w2v-panel fam s">
      <div class="w2v-ptitle">Cricket</div>
      <div class="w2v-sents fs">
        <div>the <span class="fw s">bowler</span> was tired, but still took a <span class="sc">wicket</span> in his final <span class="sc">over</span></div>
        <div>after a patient innings, the <span class="fw s">batsman</span> edged the <span class="sc">ball</span> and lost his <span class="sc">wicket</span></div>
        <div>standing behind the <span class="sc">stumps</span>, the <span class="fw s">umpire</span> slowly raised a finger</div>
        <div>with one <span class="sc">over</span> left, the <span class="fw s">captain</span> moved his players closer to the bat</div>
        <div>diving to his left, the <span class="fw s">fielder</span> stopped the <span class="sc">ball</span> and hit the <span class="sc">stumps</span></div>
      </div>
      <div class="fam-row"><span class="fam-k">Shared company</span>{shared_s}</div>
      <div class="fam-row"><span class="fam-k">Words that end up close</span>{family_s}</div>
    </div>
  </div>
  <p>Inside each group, different words keep the <b>same company</b> &ndash; king, prince, queen, princess and monarch
  keep turning up near <i>ruled</i>, <i>kingdom</i> and <i>throne</i>. Bowler, batsman, umpire, captain and fielder keep turning up near
  <i>wicket</i>, <i>over</i>, <i>ball</i> and <i>stumps</i>. Across the two groups there is almost no overlap &ndash;
  a king rarely meets a wicket.</p>
  <p>Nobody told the model which words belong together. Because each family shares its company across millions of
  sentences, their vectors land near each other and far from the other family.</p>
  <p>The meaning is <b>not supplied by a dictionary</b>. It emerges from patterns of word usage in the training text.</p>

  <h3>From words to training examples</h3>
  <p>Take one sentence from a detective story &ndash; <i>the detective examined the strange letter carefully</i>.
  Word2Vec moves a small <b>context window</b> through the text, one word at a time. Here <b>letter</b> is the centre word
  and the window is 2, so up to two words on each side become its context. The sentence ends after <i>carefully</i>,
  so the right side has only one word &ndash;</p>
  <div class="w2v-fig">{_tokens(sent)}</div>
  <p>The window decides how much neighbouring text Word2Vec uses when it learns relationships between words.
  A small window emphasises words that occur in very similar local situations. A larger window can capture
  broader topical relationships.</p>
  <p>Word2Vec can turn these windows into training examples in <b>two different ways</b>.</p>
  <div class="w2v-note"><b>Word2Vec is the framework.</b> CBOW and Skip-Gram are its two training architectures &ndash;
  two ways of turning a window into a prediction task.</div>

  <h3>CBOW &ndash; Context predicts the word</h3>
  <p><b>Continuous Bag of Words (CBOW)</b> looks at the surrounding words and tries to predict the word in the middle.</p>
  <div class="w2v-fig">
    <div class="w2v-flow"><span>{_chip("the", "ctx")}{_chip("strange", "ctx")}{_chip("?", "blank")}{_chip("carefully", "ctx")}</span>
    <span class="w2v-conn"><i></i></span><span class="w2v-op pulse">predict the gap</span>
    <span class="w2v-conn"><i></i></span>{_chip("letter", "tgt big")}</div>
  </div>
  <blockquote>Given the words around this position, which word is likely to belong here?</blockquote>

  <h3>What actually happens inside CBOW</h3>
  <p>Each word already has a vector, kept in a table with one row per word. At the beginning, those vectors contain essentially random values.
  CBOW looks up the vectors of the context words <b>the</b>, <b>strange</b> and <b>carefully</b>, and takes their
  <b>average</b> &ndash; one vector that stands for the whole context &ndash;</p>
  <div class="w2v-fig">
    <div class="w2v-flow">
      <div class="w2v-col">{cbow_rows}</div>
      <span class="w2v-conn"><i></i></span>
      <div class="w2v-col c"><span class="w2v-sub">average of the 3 vectors</span>{_nv(avg)}</div>
    </div>
    <div class="w2v-cap">Each word points to its vector &ndash; a list of numbers, random at the start. The colour of each box
    shows its value &ndash; blue for positive, orange for negative. Only the first three
    numbers are shown. Each number of the average is the mean of the three numbers in the same position &ndash;
    for the first one, (0.90 + 0.60 + 0.30) &divide; 3 = 0.60.</div>
  </div>
  <p>Now the prediction. The model compares that average with the vector of <b>every word in its vocabulary</b>
  (the list of all words it knows) and gives each word a <b>score</b> &ndash; the better the two vectors match, the higher
  the score. Training wants <b>letter</b> to get the highest score &ndash;</p>
  <div class="w2v-fig">
    <div class="w2v-flow">
      <div class="w2v-col c"><span class="w2v-sub">average</span>{_nv(avg)}</div>
      <span class="w2v-conn"><i></i></span>
      <div class="w2v-col">{cbow_cands}</div>
    </div>
    <div class="w2v-cap">Word2Vec keeps a second vector for every word, used when that word is the one being predicted.
    Only four words of the vocabulary are shown &ndash; the real comparison runs over all of them.</div>
  </div>
  <p>An average does not care about the order of the words &ndash; <i>the strange carefully</i> and <i>carefully the strange</i>
  give the same average.</p>
  <div class="w2v-note"><b>Why is it called Continuous Bag of Words?</b><br>
  <b>Bag of Words</b> &ndash; the context words are treated like words thrown into a bag. Their order is ignored, just
  as in the Bag of Words method from the first tab.<br>
  <b>Continuous</b> &ndash; instead of whole-number counts, every word is a vector of real numbers such as 0.42 or
  &minus;0.17, and those numbers can change smoothly as the model learns.<br>
  <b>Not the same method</b> &ndash; Bag of Words only counts words and learns nothing, giving one row of counts per
  sentence. CBOW is one of the two ways to train Word2Vec &ndash; it borrows only the idea that order is ignored, and it
  learns one vector for every word.</div>
  <p>If letter does not get the highest score, the model measures the <b>error</b> and adjusts the vectors involved slightly,
  using <b>gradient descent</b> &ndash; the same idea used to train neural networks. This happens again and again across the text &ndash;</p>
  <div class="w2v-fig">
    <div class="w2v-loop">{_steps(["context", "prediction", "error", "adjust vectors"], "loop")}
    <span class="w2v-repeat"><b class="spin">&#8635;</b> repeat across the whole text</span></div>
  </div>
  <p>After many examples, words that appear in similar contexts are repeatedly pushed toward representations
  that behave similarly. That learned table of vectors is what we ultimately want.</p>

  <h3>Skip-Gram &ndash; The word predicts its context</h3>
  <p><b>Skip-Gram reverses the task.</b> Instead of using the neighbouring words to predict the centre word,
  it takes the centre word and tries to predict its neighbours.</p>
  <div class="w2v-fig">
    <div class="w2v-flow"><span>{_chip("?", "blank")}{_chip("?", "blank")}{_chip("letter", "tgt")}{_chip("?", "blank")}</span>
    <span class="w2v-conn"><i></i></span><span class="w2v-op pulse">predict the neighbours</span>
    <span class="w2v-conn"><i></i></span>{ctx3}</div>
  </div>
  <blockquote>If I see this word, which words are likely to appear nearby?</blockquote>
  <p>A single window can therefore create several training pairs. Back to our detective sentence, with <b>letter</b>
  as the centre word and a window of 2 &ndash;</p>
  <div class="w2v-fig">
    <div class="w2v-sub">1 &middot; Scan the window around the centre word</div>
    {sg_stage}
    <div class="w2v-cap">One window, three training pairs &ndash; (letter, the), (letter, strange) and (letter, carefully).
    The exact pairs depend on the chosen window.</div>
  </div>

  <h3>What actually happens inside Skip-Gram</h3>
  <p>Skip-Gram looks up the vector of the centre word <b>letter</b>. It uses that <b>one vector</b> to predict each
  neighbour separately &ndash; <b>the</b>, <b>strange</b> and <b>carefully</b>. There is no averaging here. Every
  centre-neighbour pair is its own small prediction. For each pair, the vector of letter is compared with the vector of
  every word in the vocabulary, just as CBOW does with its average, and the true neighbour should get a high score &ndash;</p>
  <div class="w2v-fig">
    <div class="w2v-flow">
      <div class="w2v-col">{_points("letter", "tgt", letter_vec)}</div>
      <span class="w2v-conn"><i></i></span>
      <div class="w2v-col">{sg_rows}</div>
    </div>
    <div class="w2v-cap">The centre word &ldquo;letter&rdquo; points to its vector (first three numbers shown). The same vector
    is compared three times, once with the vector of each neighbour, and each true neighbour gets a high score.</div>
  </div>
  <p>If a prediction is poor, the vectors involved are adjusted, exactly as in CBOW. Over many windows, words that
  appear near the same neighbours are pushed toward similar vectors.</p>

  <h3>CBOW and Skip-Gram side by side</h3>
  <p>Both read the same window, <i>the strange letter carefully</i>, with <b>letter</b> as the centre word. They only
  turn it into a question in opposite directions.</p>
  <div class="w2v-two cmp">
    <div class="w2v-panel cbow">
      <div class="w2v-ptitle">CBOW</div>
      <div class="w2v-ask">Which word fills the gap?</div>
      <div class="w2v-line">the strange {_chip("?", "blank")} carefully</div>
      <div class="w2v-tree">{tree(["the", "strange", "carefully"], "ctx", True)}
        <span class="w2v-vconn"><i></i></span>{_chip("letter", "tgt big")}</div>
      <div class="w2v-tally"><span><b>3</b> words in</span><span><b>1</b> prediction out</span></div>
      <div class="w2v-rule">many &rarr; one</div>
    </div>
    <div class="w2v-panel sg">
      <div class="w2v-ptitle">Skip-Gram</div>
      <div class="w2v-ask">Which words appear near letter?</div>
      <div class="w2v-line">the strange {_chip("letter", "tgt")} carefully</div>
      <div class="w2v-tree">{_chip("letter", "tgt big")}<span class="w2v-vconn noh"><i></i></span>
        {tree(["the", "strange", "carefully"], "ctx", False)}</div>
      <div class="w2v-tally"><span><b>1</b> word in</span><span><b>3</b> predictions out</span></div>
      <div class="w2v-rule">one &rarr; many</div>
    </div>
  </div>

  <h3>What is Word2Vec actually learning?</h3>
  <p>This is the most important intuition. Word2Vec is <b>not useful because we care whether it can predict the
  missing word</b>. The prediction task is only the mechanism that forces the model to learn useful vectors.</p>
  <p>Here is a small piece of the vector table after training. Each row is one word's vector. Each column is one position
  in the vector, called a <b>dimension</b> &ndash; here every vector has 50 of them &ndash;</p>
  <div class="w2v-fig">{_embed_table()}</div>
  <p>Look at the numbers. The people &ndash; holmes, watson and lestrade &ndash; have similar rows. The places &ndash;
  london, scotland and paris &ndash; have similar rows of their own, and they look nothing like the people.
  But at the beginning every row was random. Training repeatedly adjusted those numbers until related words sat together &ndash;</p>
  <div class="w2v-two">
    <div class="w2v-panel"><div class="w2v-ptitle">At the beginning</div>{_img(_map_before())}<div class="w2v-pfoot">random vectors &ndash; people and places mixed up</div></div>
    <div class="w2v-panel"><div class="w2v-ptitle">After training</div>{_img(_map_after())}<div class="w2v-pfoot">holmes, watson and lestrade together, london, scotland and paris together, the two groups far apart</div></div>
  </div>
  <p>The <b>table of word vectors is the valuable product of training</b>. The prediction task is what teaches it.</p>

  <h3>Why does similarity emerge?</h3>
  <p>Go back to the prediction task, seen the Skip-Gram way. Every time <b>holmes</b> appears, its vector is used to predict the words around it.
  Every time <b>watson</b> appears, its vector does the same job for the words around watson. Now look at the company
  these two keep &ndash;</p>
  <div class="w2v-fig">
    <div class="w2v-sents ex">
      <div><span class="sn">1</span><span class="el">&hellip;</span> {_chip("Holmes", "tgt")} <span class="hl">examined</span> the <span class="hl">letter</span> by the fire <span class="el">&hellip;</span></div>
      <div><span class="sn">2</span><span class="el">&hellip;</span> {_chip("Watson", "tgt")} read the <span class="hl">letter</span> twice before he <span class="hl">examined</span> the seal <span class="el">&hellip;</span></div>
      <div><span class="sn">3</span><span class="el">&hellip;</span> the <span class="hl">inspector</span> asked {_chip("Holmes", "tgt")} for help with the <span class="hl">case</span> <span class="el">&hellip;</span></div>
      <div><span class="sn">4</span><span class="el">&hellip;</span> {_chip("Watson", "tgt")} told the <span class="hl">inspector</span> that the <span class="hl">case</span> was not closed <span class="el">&hellip;</span></div>
      <div><span class="sn">5</span><span class="el">&hellip;</span> {_chip("Holmes", "tgt")} hurried to <span class="hl">Baker Street</span> in the rain <span class="el">&hellip;</span></div>
      <div><span class="sn">6</span><span class="el">&hellip;</span> a telegram reached {_chip("Watson", "tgt")} at <span class="hl">Baker Street</span> that evening <span class="el">&hellip;</span></div>
    </div>
    <div class="w2v-cap">Six excerpts from different places in the text, the same company &ndash; examined, letter, inspector, case, Baker Street.</div>
  </div>
  <p>So the two vectors are being asked to make <b>the same predictions</b> &ndash;</p>
  <div class="w2v-fig">{_img(_shared())}
    <div class="w2v-cap">Two different words, one shared list of neighbours to predict.</div>
  </div>
  <p>Each time holmes is trained to predict <i>letter</i>, its vector is nudged a little in the direction that makes
  <i>letter</i> more likely. Each time watson is trained to predict <i>letter</i>, its vector is nudged <b>the same way</b>.
  The same happens for examined, case, inspector and Baker Street, across thousands of sentences. Two vectors that keep
  receiving the same nudges end up with similar numbers &ndash;</p>
  <div class="w2v-two">
    <div class="w2v-panel"><div class="w2v-ptitle">At the beginning</div>
      <div class="w2v-col">{_points("holmes", "tgt", [0.81, -0.62, 0.05])}{_points("watson", "tgt", [-0.44, 0.37, 0.90])}</div>
      <div class="w2v-pfoot">random &ndash; the numbers have nothing in common</div></div>
    <div class="w2v-panel"><div class="w2v-ptitle">After training</div>
      <div class="w2v-col">{_points("holmes", "tgt", [0.42, -0.17, 0.31])}{_points("watson", "tgt", [0.38, -0.11, 0.29])}</div>
      <div class="w2v-pfoot">similar numbers in the same positions &ndash; similar vectors</div></div>
  </div>
  <p><b>london</b> and <b>paris</b> never receive these nudges. Their company is different &ndash; <i>streets</i>,
  <i>city</i>, <i>lived in</i>, <i>travelled to</i> &ndash; so their vectors are pushed somewhere else. That is exactly
  the split between people and places we saw in the table above.</p>
  <p>Once training is done, the words whose vectors are closest to holmes form its <b>neighbourhood</b> &ndash;</p>
  <div class="w2v-fig">{_img(_star())}
    <div class="w2v-cap">The nearest words to holmes &ndash; all of them keep the same kind of company.</div>
  </div>
  <p>None of this was explicitly programmed. Similar vectors are simply the <b>easiest way to make the same
  predictions</b>, so they emerge from co-occurrence patterns in the text.</p>

  <h3>What does each dimension mean?</h3>
  <p>In the exercise the setting <code>vector_size = 50</code> gives every word 50 dimensions, so the word <b>holmes</b>
  is a list of 50 numbers &ndash;</p>
  <div class="w2v-fig"><div class="w2v-vrow pv">{_chip("holmes", "plain")}<span class="w2v-conn sm"><i></i></span>{holmes50}</div></div>
  <p>Do <b>not</b> read them one by one. Word2Vec does not learn clean human-labelled dimensions such as
  <span class="w2v-wrong">dimension 1 = person</span> <span class="w2v-wrong">dimension 2 = detective</span>
  <span class="w2v-wrong">dimension 3 = intelligence</span></p>
  <p>Meaning is <b>distributed across the whole vector</b>. What matters is the relationship between vectors &ndash;
  <span class="w2v-right">direction</span> <span class="w2v-right">distance</span> <span class="w2v-right">neighbourhood</span>.
  That is why words are compared with <b>cosine similarity</b>.</p>

  <h3>Cosine similarity</h3>
  <p>By now every word is a <b>vector</b> &ndash; an arrow pointing somewhere in space. Training pushes words that keep
  the same company to point in <b>similar directions</b>. So if two word vectors point almost the same way, those words
  carry <b>similar meaning</b>. If they point in very different directions, their meanings are unrelated.</p>
  <p><b>Cosine similarity</b> is the number that measures this. It looks only at the angle <b>&#952;</b> between the two
  arrows &ndash; the smaller the angle, the closer the meaning.</p>
  <div class="w2v-two">
    <div class="w2v-panel"><div class="w2v-ptitle">king and queen</div>{_img(_cosine_panel(38, 62, "king", "queen", _ROYAL, _ROYAL))}
    <div class="w2v-pfoot">small angle &ndash; <b class="good">high similarity (0.91)</b> &ndash; similar meaning</div></div>
    <div class="w2v-panel"><div class="w2v-ptitle">king and wicket</div>{_img(_cosine_panel(20, 105, "king", "wicket", _ROYAL, _POS))}
    <div class="w2v-pfoot">near right angle &ndash; <b class="bad">low similarity (0.09)</b> &ndash; unrelated meaning</div></div>
  </div>
  <p>A value near <b>1</b> means the words are used almost the same way. A value near <b>0</b> means they have little
  to do with each other &ndash; that is where most unrelated word pairs land. Negative values are possible, when two
  vectors point away from each other, but for words they are uncommon and rarely strongly negative.</p>
  <p>This is also why, in the exercise, the vectors are normalised to length 1 before plotting. Only their
  <b>directions</b> carry the meaning, so closeness on the map reflects closeness in meaning.</p>

  <h3>Why famous Word2Vec analogies appear</h3>
  <p>With enough suitable training data, the geometry can capture regular relationships. First, here is the famous equation &ndash;</p>
  <div class="w2v-fig">
    <div class="w2v-derive">
      <div class="dv"><span class="dn">1</span><span class="dl">The equation</span>
        <span class="de">{_chip("king", "plain")}<b>&minus;</b>{_chip("man", "plain")}<b>+</b>{_chip("woman", "plain")}<b>&asymp;</b>{_chip("?", "blank")}</span></div>
      <div class="dv"><span class="dn">2</span><span class="dl">What king is made of</span>
        <span class="de">{_chip("king", "plain")}<b>=</b>{_chip("man", "plain")}<b>+</b>{_chip("royal", "royal")}</span></div>
      <div class="dv"><span class="dn">3</span><span class="dl">Take away man</span>
        <span class="de">{_chip("king", "plain")}<b>&minus;</b>{_chip("man", "plain")}<b>=</b>{_chip("man", "gone")}<b>+</b>{_chip("royal", "royal")}<b>&minus;</b>{_chip("man", "gone")}<b>=</b>{_chip("royal", "royal")}</span></div>
      <div class="dv"><span class="dn">4</span><span class="dl">Add woman</span>
        <span class="de">{_chip("royal", "royal")}<b>+</b>{_chip("woman", "plain")}<b>=</b>{_chip("woman", "plain")}<b>+</b>{_chip("royal", "royal")}<b>&asymp;</b>{_chip("queen", "tgt big")}</span></div>
    </div>
  </div>
  <p>On the map this is two parallel arrows. The same <b>royal</b> direction takes man to king and woman to queen,
  so starting at king, stepping back by man and forward by woman lands next to queen &ndash;</p>
  <div class="w2v-fig">{_img(_analogy())}</div>
  <p>In practice the result lands <b>near</b> queen, not exactly on it &ndash; queen is simply the closest word to that point,
  once king, man and woman themselves are left out. That is why the equation uses &asymp;.</p>
  <p>This does not mean the model understands algebraic definitions, and no vector is labelled <i>royal</i>.
  Recurring language patterns simply produce roughly consistent <b>directions among the vectors</b>.
  This was one of the striking discoveries that made learned word vectors influential.</p>

  <h3>CBOW versus Skip-Gram</h3>
  <table class="w2v-table">
    <thead><tr><th></th><th>CBOW</th><th>Skip-Gram</th></tr></thead>
    <tbody>
      <tr><td>Input</td><td>surrounding words</td><td>centre word</td></tr>
      <tr><td>Predicts</td><td>centre word</td><td>surrounding words</td></tr>
      <tr><td>One window produces</td><td>roughly one prediction task</td><td>several word-context pairs</td></tr>
      <tr><td>Typical strength</td><td>efficient, strong on frequent patterns</td><td>often better vectors for rare words</td></tr>
      <tr><td>Training</td><td>generally faster</td><td>generally more computation</td></tr>
      <tr><td>Gensim setting (the library used in the exercise)</td><td><code>sg=0</code></td><td><code>sg=1</code></td></tr>
    </tbody>
  </table>
  <p>The difference is architectural. Both exploit the same principle.</p>
  <blockquote>A word can be learned from the company it keeps.</blockquote>

  <h3>The complete Word2Vec picture</h3>
  <div class="w2v-pipe">
    <span class="ps">Raw text</span><span class="pa"><i></i></span>
    <span class="ps">Clean words</span><span class="pa"><i></i></span>
    <span class="ps">Sliding window</span><span class="pa noh"><i></i></span>
    <div class="hbar fork"><i class="l"></i><i class="r"></i></div>
    <div class="pb">
      <div class="pc"><span class="pa"><i></i></span><span class="ps ctxb"><b>CBOW</b>context words &rarr; predict word</span><span class="pa noh"><i></i></span></div>
      <div class="pc"><span class="pa"><i></i></span><span class="ps tgtb"><b>Skip-Gram</b>word &rarr; predict context words</span><span class="pa noh"><i></i></span></div>
    </div>
    <div class="hbar merge"><i class="l"></i><i class="r"></i></div>
    <span class="pa"><i></i></span>
    <span class="ps">Prediction error</span><span class="pa"><i></i></span>
    <span class="ps">Gradient descent</span><span class="pa"><i></i></span>
    <span class="ps">Update the word vectors</span><span class="pa"><i></i></span>
    <span class="ps">&#8635; Repeat across the text</span><span class="pa"><i></i></span>
    <span class="ps final">Learned word vectors</span>
  </div>

  <div class="w2v-note"><b>Next</b> &ndash; open <b>Exercise 1</b> and train your own CBOW model on a book of your
  choice.</div>
</div>
"""


def render_intro() -> None:
    st.html(_intro_html())
