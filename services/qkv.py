from __future__ import annotations

from html import escape

import streamlit as st

DECK = (
    '<div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span>'
    '<span class="cmx-c1"></span><span class="cmx-c2"></span></div>'
)

MONEY = ["The", "bank", "approved", "the", "loan"]
SCENE = ["The", "bank", "on", "the", "river", "bank", "got", "robbed"]
BANK = 1
VECS = {
    "The": "0.2, -0.4, 0.1",
    "bank": "0.6, 0.3, -0.2",
    "approved": "0.1, 0.5, 0.4",
    "the": "0.2, -0.3, 0.0",
    "loan": "0.5, 0.4, -0.1",
}
SCORES = [0.18, 0.46, 0.81, 0.11, 1.62]
WEIGHTS = [0.04, 0.10, 0.18, 0.03, 0.65]
CTX = "0.41, -0.18, 0.77"


def _viz(inner: str, *, replay: bool = True) -> str:
    btn = (
        '<button type="button" class="qkv-replay" data-qkv-replay>Replay animation</button>'
        if replay
        else ""
    )
    return (
        '<div class="qkv-viz" data-qkv-viz>'
        f"{btn}"
        f'<div class="qkv-viz-body">{inner}</div>'
        "</div>"
    )


def _sec(num: int, title: str, body: str) -> str:
    return (
        f'<section class="qkv-sec" aria-labelledby="qkv-s{num}">'
        '<div class="qkv-sec-head">'
        f'<span class="qkv-sec-n">{num:02d}</span>'
        f'<h3 id="qkv-s{num}">{escape(title)}</h3>'
        "</div>"
        f"{body}"
        "</section>"
    )


def _p(text: str) -> str:
    return f'<p class="dtx-lead">{text}</p>'


def _quote(text: str) -> str:
    return f'<blockquote class="qkv-quote">{text}</blockquote>'


def _sub(title: str) -> str:
    return f'<h4 class="qkv-sub">{escape(title)}</h4>'


def _heat() -> str:
    cells = []
    for word, weight in zip(MONEY, WEIGHTS):
        pct = int(round(100 * weight))
        sel = " is-sel" if word == "bank" else ""
        cells.append(
            '<div class="qkv-heat-item">'
            f'<span class="qkv-heat-word{sel}">{escape(word)}</span>'
            f'<span class="qkv-heat-bar"><i style="height:{max(12, pct)}%"></i></span>'
            "</div>"
        )
    return (
        '<div class="qkv-heat" aria-label="Attention from bank">'
        f"{''.join(cells)}"
        "</div>"
        '<div class="qkv-heat-note">attention from <b>bank</b></div>'
    )


def _vec_cards() -> str:
    cards = []
    for index, word in enumerate(MONEY):
        cls = "qkv-vec is-sel" if index == BANK else "qkv-vec"
        cards.append(
            f'<div class="{cls}" style="--i:{index}">'
            f'<span class="qkv-vec-w">{escape(word)}</span>'
            f'<span class="qkv-vec-n">[ {escape(VECS[word])}, &hellip; ]</span>'
            "</div>"
        )
    return f'<div class="qkv-vecs">{"".join(cards)}</div>'


def _split() -> str:
    return """
      <div class="qkv-split">
        <div class="qkv-split-x">x(bank)</div>
        <div class="qkv-soft">incoming representation</div>
        <div class="qkv-split-stem"></div>
        <div class="qkv-split-row">
          <div class="qkv-split-arm">
            <span class="qkv-learned">learned during training</span>
            <span class="qkv-wmat">W<sub>Q</sub></span>
            <span class="qkv-arrow">&darr;</span>
            <span class="qkv-role q">Query</span>
          </div>
          <div class="qkv-split-arm">
            <span class="qkv-learned">learned during training</span>
            <span class="qkv-wmat">W<sub>K</sub></span>
            <span class="qkv-arrow">&darr;</span>
            <span class="qkv-role k">Key</span>
          </div>
          <div class="qkv-split-arm">
            <span class="qkv-learned">learned during training</span>
            <span class="qkv-wmat">W<sub>V</sub></span>
            <span class="qkv-arrow">&darr;</span>
            <span class="qkv-role v">Value</span>
          </div>
        </div>
      </div>
    """


_CITY_LINK_SCRIPT = r"""
<script>
(function () {
  var root = document.getElementById("qkvCityMap");
  if (!root || root.getAttribute("data-links-ready") === "1") return;
  root.setAttribute("data-links-ready", "1");
  var scene = root.querySelector(".qkv-city-scene");
  var lines = Array.prototype.slice.call(root.querySelectorAll(".qkv-city-connector"));

  function localRect(rect, box) {
    return {
      left: rect.left - box.left,
      right: rect.right - box.left,
      top: rect.top - box.top,
      bottom: rect.bottom - box.top,
      cx: rect.left - box.left + rect.width / 2,
      cy: rect.top - box.top + rect.height / 2
    };
  }

  function placeSegment(segment, start, end, last) {
    var dx = end.x - start.x;
    var dy = end.y - start.y;
    segment.style.display = "block";
    segment.style.left = start.x + "px";
    segment.style.top = start.y + "px";
    segment.style.width = Math.hypot(dx, dy) + "px";
    segment.style.transform = "rotate(" + Math.atan2(dy, dx) + "rad)";
    segment.classList.toggle("is-last", last);
  }

  function place() {
    if (!scene) return;
    var box = scene.getBoundingClientRect();
    lines.forEach(function (line) {
      var fromPerson = root.querySelector('.qkv-city-person[data-who="' + line.dataset.from + '"]');
      var toPerson = root.querySelector('.qkv-city-person[data-who="' + line.dataset.to + '"]');
      if (!fromPerson || !toPerson) return;
      var fromCard = fromPerson.querySelector(".qkv-city-query");
      var toCard = toPerson.querySelector(".qkv-city-value");
      if (!fromCard || !toCard) return;
      var fromRect = fromCard.getBoundingClientRect();
      var toRect = toCard.getBoundingClientRect();
      var from = localRect(fromRect, box);
      var to = localRect(toRect, box);
      var route = line.dataset.route;
      var points;
      if (route === "top-left") {
        points = [
          { x: from.left, y: from.cy },
          { x: to.right + 24, y: from.cy },
          { x: to.right + 24, y: to.cy },
          { x: to.right, y: to.cy }
        ];
      } else if (route === "top-right") {
        points = [
          { x: from.cx, y: from.top },
          { x: from.cx, y: to.cy },
          { x: to.right, y: to.cy }
        ];
      } else {
        var channel = box.height - (route === "bottom-left" ? 30 : 12);
        points = [
          { x: from.cx, y: from.bottom },
          { x: from.cx, y: channel },
          { x: to.cx, y: channel },
          { x: to.cx, y: to.bottom }
        ];
      }
      var origin = line.querySelector(".qkv-city-origin");
      if (origin) {
        origin.style.left = points[0].x + "px";
        origin.style.top = points[0].y + "px";
      }
      var segments = Array.prototype.slice.call(line.querySelectorAll("span"));
      segments.forEach(function (segment, index) {
        if (index < points.length - 1) {
          placeSegment(segment, points[index], points[index + 1], index === points.length - 2);
        } else {
          segment.style.display = "none";
          segment.classList.remove("is-last");
        }
      });
    });
  }

  window.requestAnimationFrame(place);
  window.addEventListener("resize", place);
  if (window.ResizeObserver && scene) new ResizeObserver(place).observe(scene);
})();
</script>
"""


def _city_film() -> str:
    people = [
        ("A", "a novel to borrow", "a packed lunch"),
        ("B", "a quiet study desk", "a novel to borrow"),
        ("C", "something for lunch", "a bicycle pump"),
        ("D", "help with a flat tyre", "a quiet study desk"),
    ]
    cards = []
    for who, query, payload in people:
        cards.append(
            f'<div class="qkv-city-person" data-who="{who}">'
            '<div class="qkv-hold">'
            '<div class="qkv-city-query">'
            '<span class="qkv-tag">NEEDS</span>'
            f"<b>{query}</b></div>"
            '<div class="qkv-city-avatar" aria-hidden="true">'
            '<i class="qkv-arm is-l"></i>'
            '<i class="qkv-head"></i><i class="qkv-torso"></i>'
            '<i class="qkv-arm is-r"></i>'
            '<i class="qkv-leg is-l"></i><i class="qkv-leg is-r"></i>'
            "</div>"
            '<div class="qkv-city-value">'
            '<span class="qkv-tag">OFFERS</span>'
            '<div class="qkv-parcel" aria-hidden="true"></div>'
            f"<b>{payload}</b></div>"
            "</div>"
            f'<span class="qkv-city-name">Person {who}</span>'
            "</div>"
        )
    return (
        '<div class="qkv-cine qkv-city-map" id="qkvCityMap">'
        '<div class="qkv-cine-k">A self-contained city exchange</div>'
        '<div class="qkv-city-scene">'
        f'<div class="qkv-city-row">{"".join(cards)}</div>'
        '<div class="qkv-city-connectors" aria-hidden="true">'
        '<i class="qkv-city-connector" data-from="A" data-to="B" data-route="top-left" style="--delay:0s">'
        '<b class="qkv-city-origin"></b><span></span><span></span><span></span></i>'
        '<i class="qkv-city-connector" data-from="B" data-to="D" data-route="bottom-left" style="--delay:-0.25s">'
        '<b class="qkv-city-origin"></b><span></span><span></span><span></span></i>'
        '<i class="qkv-city-connector" data-from="D" data-to="C" data-route="bottom-right" style="--delay:-0.5s">'
        '<b class="qkv-city-origin"></b><span></span><span></span><span></span></i>'
        '<i class="qkv-city-connector" data-from="C" data-to="A" data-route="top-right" style="--delay:-0.75s">'
        '<b class="qkv-city-origin"></b><span></span><span></span><span></span></i></div>'
        "</div>"
        '<p class="qkv-cine-cap">Follow each animated dashed arrow from a need to the matching offer that solves it.</p>'
        "</div>"
        + _CITY_LINK_SCRIPT
    )


def _w_jobs() -> str:
    return """
      <div class="qkv-jobs">
        <div class="qkv-job" style="--i:0">
          <span class="qkv-wmat">W<sub>Q</sub></span>
          <span>learn how to ask</span>
          <span class="qkv-arrow">&darr;</span>
          <span class="qkv-role q">Query</span>
          <small>What information do I need?</small>
        </div>
        <div class="qkv-job" style="--i:1">
          <span class="qkv-wmat">W<sub>K</sub></span>
          <span>learn how to match</span>
          <span class="qkv-arrow">&darr;</span>
          <span class="qkv-role k">Key</span>
          <small>How well do I match a Query?</small>
        </div>
        <div class="qkv-job" style="--i:2">
          <span class="qkv-wmat">W<sub>V</sub></span>
          <span>learn what to contribute</span>
          <span class="qkv-arrow">&darr;</span>
          <span class="qkv-role v">Value</span>
          <small>What information can I carry forward?</small>
        </div>
      </div>
    """


def _roster() -> str:
    rows = []
    for index, word in enumerate(SCENE):
        mark = " is-ask" if index == 1 else ""
        if word == "bank":
            tag = "bank<sub>1</sub>" if index == 1 else "bank<sub>2</sub>"
        else:
            tag = escape(word)
        rows.append(
            f'<div class="qkv-roster-row{mark}" style="--i:{index}">'
            f"<span>x({tag})</span>"
            "<span>&rarr;</span>"
            f"<span>Q({tag})</span>"
            f"<span>K({tag})</span>"
            f"<span>V({tag})</span>"
            "</div>"
        )
    return f'<div class="qkv-roster">{"".join(rows)}</div>'


def _remember() -> str:
    return """
      <div class="qkv-remember">
        <div class="qkv-split-x">x</div>
        <div class="qkv-soft">incoming representation</div>
        <div class="qkv-split-stem"></div>
        <div class="qkv-split-row">
          <div class="qkv-split-arm">
            <span class="qkv-wmat">W<sub>Q</sub></span>
            <span class="qkv-arrow">&darr;</span>
            <span class="qkv-role q">QUERY</span>
            <small>asks</small>
          </div>
          <div class="qkv-split-arm">
            <span class="qkv-wmat">W<sub>K</sub></span>
            <span class="qkv-arrow">&darr;</span>
            <span class="qkv-role k">KEY</span>
            <small>matches</small>
          </div>
          <div class="qkv-split-arm">
            <span class="qkv-wmat">W<sub>V</sub></span>
            <span class="qkv-arrow">&darr;</span>
            <span class="qkv-role v">VALUE</span>
            <small>carries</small>
          </div>
        </div>
        <div class="qkv-remember-join">Query &harr; Key &ndash; relevance match</div>
        <span class="qkv-arrow">&darr;</span>
        <div class="qkv-remember-out is-val">later determines how much Value contributes</div>
      </div>
    """


def _key_lines(*, scores: bool) -> str:
    rows = []
    for index, word in enumerate(MONEY):
        strong = " is-hot" if word == "loan" else ""
        extra = ""
        if scores:
            extra = f'<span class="qkv-dot" style="--i:{index}">{SCORES[index]:.2f}</span>'
        rows.append(
            f'<div class="qkv-kline{strong}" style="--i:{index}">'
            '<span class="qkv-kline-bar"></span>'
            f'<span class="qkv-k">K({escape(word)})</span>'
            f"{extra}</div>"
        )
    return (
        '<div class="qkv-meet">'
        '<div class="qkv-qbox">Q(bank)</div>'
        f'<div class="qkv-klines">{"".join(rows)}</div>'
        "</div>"
    )


def _dot_expand() -> str:
    return """
      <div class="qkv-dotbox">
        <div>Q(bank) = [ 0.7, 0.2, -0.4, &hellip; ]</div>
        <div>K(loan) = [ 0.6, 0.4, -0.1, &hellip; ]</div>
        <div class="qkv-dotbox-out">&darr; dot product &rarr; <b>1.62</b></div>
      </div>
    """


def _score_table() -> str:
    rows = "".join(
        f'<div class="qkv-score" style="--i:{index}">'
        f"<span>Q(bank) &middot; K({escape(word)})</span>"
        f"<b>{score:.2f}</b></div>"
        for index, (word, score) in enumerate(zip(MONEY, SCORES))
    )
    return (
        '<div class="qkv-k">Raw attention scores</div>'
        f'<div class="qkv-scores">{rows}</div>'
    )


def _weight_bars() -> str:
    rows = []
    for word, weight in zip(MONEY, WEIGHTS):
        pct = int(round(100 * weight))
        rows.append(
            '<div class="qkv-wrow">'
            f'<span class="qkv-wrow-w">{escape(word)}</span>'
            f'<span class="qkv-wrow-n">{weight:.2f}</span>'
            f'<span class="qkv-wrow-bar"><i style="width:{pct}%"></i></span>'
            "</div>"
        )
    return (
        f'<div class="qkv-weights">{"".join(rows)}</div>'
        '<div class="qkv-sum">sum 1.00</div>'
        '<div class="qkv-flag">Illustrative numbers</div>'
    )


def _value_mix() -> str:
    rows = []
    for word, weight in zip(MONEY, WEIGHTS):
        thick = " is-thick" if weight >= 0.5 else (" is-mid" if weight >= 0.15 else "")
        rows.append(
            f'<div class="qkv-vline{thick}">'
            f"<span>{weight:.2f} &times; V({escape(word)})</span>"
            '<span class="qkv-vstem"></span>'
            "</div>"
        )
    return (
        f'<div class="qkv-vmix">{"".join(rows)}'
        '<div class="qkv-sigma">&Sigma;</div></div>'
    )


def _matrix() -> str:
    head = "".join(f"<th>{escape(word)}</th>" for word in MONEY)
    rows = []
    for i, src in enumerate(MONEY):
        cells = []
        for j, _dst in enumerate(MONEY):
            cls = ""
            if i == BANK:
                cls = "is-row"
                if j == 4:
                    cls += " is-peak"
            cells.append(f'<td class="{cls}"></td>')
        cls = "is-row" if i == BANK else ""
        rows.append(
            f'<tr class="{cls}"><th>Q {escape(src)}</th>{"".join(cells)}</tr>'
        )
    return (
        '<div class="qkv-k">KEYS</div>'
        '<table class="qkv-mat" aria-label="Attention rows">'
        f"<thead><tr><th></th>{head}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _train() -> str:
    return """
      <div class="qkv-train">
        <div class="qkv-train-flow">
          <span>model output</span><span class="qkv-arrow">&darr;</span>
          <span>prediction error / loss</span><span class="qkv-arrow">&darr;</span>
          <span>backpropagation</span>
        </div>
        <div class="qkv-wrow3">
          <div class="qkv-wcard"><b>W<sub>Q</sub></b><span data-qkv-nudge>0.310 &rarr; 0.314</span></div>
          <div class="qkv-wcard"><b>W<sub>K</sub></b><span data-qkv-nudge>-0.180 &rarr; -0.176</span></div>
          <div class="qkv-wcard"><b>W<sub>V</sub></b><span data-qkv-nudge>0.420 &rarr; 0.417</span></div>
        </div>
      </div>
    """


def _equation() -> str:
    return """
      <div class="qkv-pipe">
        <span>QK<sup>T</sup> &ndash; compare Queries with Keys</span>
        <span>&darr;</span>
        <span>&divide; &radic;d<sub>k</sub> &ndash; scale the scores</span>
        <span>&darr;</span>
        <span>softmax &ndash; turn scores into attention weights</span>
        <span>&darr;</span>
        <span>&times; V &ndash; mix Values</span>
        <span>&darr;</span>
        <span>contextual representations</span>
      </div>
    """


def _heads() -> str:
    return """
      <div class="qkv-heads">
        <div class="qkv-split-x">Input</div>
        <div class="qkv-split-stem"></div>
        <div class="qkv-split-row">
          <div class="qkv-split-arm"><span class="qkv-role q">Head 1</span><span>Q K V</span></div>
          <div class="qkv-split-arm"><span class="qkv-role k">Head 2</span><span>Q K V</span></div>
          <div class="qkv-split-arm"><span class="qkv-role v">Head 3</span><span>Q K V</span></div>
        </div>
        <div class="qkv-split-stem"></div>
        <div class="qkv-ctx">concatenate &rarr; W<sub>O</sub> &rarr; multi-head output</div>
      </div>
    """


def _bert_parts(read, scope: str) -> tuple[str, str]:
    if not read:
        return "", ""
    words, att, _vec = read
    from services.attention import _live

    live = _live(words, att, scope=scope)
    if live is None:
        return "", ""
    return live


def _recall(bert_html: str) -> str:
    live = bert_html.strip()
    if live:
        body = (
            live
            + '<p class="qkv-mini">Hover a word to select it. Until you do, the first '
            "<b>bank</b> stays selected &ndash; the same default as Lecture 3.</p>"
        )
    else:
        body = (
            '<p class="qkv-mini">BERT could not load, so the live attention map is unavailable. '
            "The sentence is still <b>The bank on the river bank got robbed</b>.</p>"
        )
    return f'<div class="qkv-viz qkv-bert-box">{body}</div>'


def _eg_weights() -> str:
    return (
        '<div class="qkv-eg">'
        "<div><b>40%</b> attention to <code>robbed</code></div>"
        "<div><b>26%</b> attention to <code>river</code></div>"
        "<div><b>20%</b> attention to <code>bank</code></div>"
        "<div><b>15%</b> attention to <code>got</code></div>"
        "</div>"
    )


def _section_1(bert_html: str) -> str:
    return _sec(
        1,
        "From the Attention Map to the Mechanism",
        _p(
            "In Lecture 3, we moved from <b>Word2Vec</b> to <b>contextual representations</b>."
        )
        + _p(
            "Word2Vec gave us an important starting point &ndash; a word can be represented as a vector, and words used in "
            "similar contexts can acquire similar representations. But once Word2Vec has been trained, a word such as "
            "<i>bank</i> essentially has <b>one learned vector</b>. That same learned representation is used wherever "
            "the word appears."
        )
        + _p("BERT showed us what changes when we introduce <b>attention</b>.")
        + _p("Consider the sentence you explored earlier &ndash;")
        + _quote("<b>The bank on the river bank got robbed</b>")
        + _p(
            "The word <i>bank</i> appears twice, but the two occurrences do not play the same role in the sentence. "
            "When you selected each occurrence in the BERT attention visual, it did not interact with the surrounding "
            "tokens in exactly the same way. The second <i>bank</i>, for example, could place strong attention on "
            "<i>river</i>, while selecting the first <i>bank</i> produced a different pattern. Selecting <i>robbed</i> "
            "produced another pattern again."
        )
        + '<h4 class="qkv-sub">Recall the attention pattern</h4>'
        + _recall(bert_html)
        + (
            '<p class="qkv-try"><b>Try selecting</b> &ndash; <code>bank</code> <i>(first occurrence)</i> '
            "&middot; <code>bank</code> <i>(second occurrence)</i> &middot; <code>robbed</code></p>"
        )
        + _p(
            "What mattered in that exercise was not any one percentage by itself. An attention value does "
            "<b>not</b> mean that a certain percentage of a word's meaning comes from another word."
        )
        + _p("Instead, the visual showed a deeper idea &ndash;")
        + _quote(
            "<b>Each token can draw different amounts of information from the other tokens in its current context.</b>"
        )
        + _p(
            "The percentages you saw were <b>attention weights</b>. Within the attention head being visualised, they "
            "controlled how strongly information associated with different tokens contributed to the attention output "
            "for the selected token."
        )
        + _p(
            "This is what allows a Transformer to build <b>context-dependent representations</b>. The two occurrences "
            "of <i>bank</i> share the same underlying token identity, but they occur at different positions and in "
            "different contexts. As information moves through the Transformer, their representations can therefore "
            "develop differently."
        )
        + _p("In Lecture 3, however, we observed only the <b>result</b> of this process &ndash;")
        + _quote("<b>Which tokens does this token attend to, and by how much?</b>")
        + _p("We did not yet look inside the calculation that produced those percentages.")
        + _p(
            "BERT is built from <b>Transformer attention blocks</b>. Somewhere inside those blocks, the model must "
            "take the vectors representing the tokens and calculate numbers such as &ndash;"
        )
        + _eg_weights()
        + _p("So the question we carry forward is &ndash;")
        + _quote(
            "<b>Given a set of token representations, how does the Transformer decide where useful information may "
            "come from?</b>"
        )
        + _p(
            "The mechanism uses three roles called <b>Query</b>, <b>Key</b> and <b>Value</b>."
        )
        + _p(
            "Before looking at their vectors and mathematics, let us first build an intuition for what those three "
            "roles are doing."
        ),
    )


def _nudge_stop(
    number: int, prompt: str, role: str, answer: str, tone: str, figure: str = ""
) -> str:
    shown = f'<div class="qkv-s2-stop-fig">{figure}</div>' if figure else ""
    return (
        f'<details class="qkv-s2-stop is-{tone}">'
        '<summary>'
        f'<span class="qkv-s2-stop-n">STOP {number:02d}</span>'
        '<span class="qkv-s2-stop-prompt">'
        f"<b>{prompt}</b>"
        "<small>Pause, answer in your own words, then reveal.</small>"
        "</span>"
        '<i aria-hidden="true"></i>'
        "</summary>"
        '<div class="qkv-s2-stop-answer">'
        '<div class="qkv-s2-stop-line">'
        f'<span class="qkv-role {tone}">{role}</span>'
        f"<p>{answer}</p>"
        "</div>"
        f"{shown}"
        "</div></details>"
    )


def _query_card() -> str:
    return (
        '<div class="qkv-s2-drop is-q">'
        '<div class="qkv-s2-plate">'
        '<div class="qkv-s2-head">'
        '<span class="qkv-s2-who">Person A</span>'
        '<span class="qkv-s2-lab">Needs</span>'
        "</div>"
        "<strong>a novel to borrow</strong>"
        "</div>"
        '<i class="qkv-s2-stem" aria-hidden="true"></i>'
        '<em class="qkv-role q">Query</em>'
        "</div>"
    )


def _key_card() -> str:
    return (
        '<div class="qkv-s2-drop is-k">'
        '<div class="qkv-s2-plate">'
        '<div class="qkv-s2-head">'
        '<span class="qkv-s2-who">Person A</span>'
        '<span class="qkv-s2-lab">Offers</span>'
        "</div>"
        "<strong>a packed lunch</strong>"
        "<small>searchable as <b>food / lunch</b></small>"
        "</div>"
        '<i class="qkv-s2-stem" aria-hidden="true"></i>'
        '<em class="qkv-role k">Key</em>'
        "</div>"
    )


def _value_card() -> str:
    return (
        '<div class="qkv-s2-flow">'
        '<div class="is-q"><b>Person C&rsquo;s Query</b><span>something for lunch</span></div>'
        '<i aria-hidden="true"><small>matches</small>&darr;</i>'
        '<div class="is-k"><b>Key A</b><span>food / lunch</span></div>'
        '<i aria-hidden="true"><small>gives access to</small>&darr;</i>'
        '<div class="is-v"><b>Value A</b><span>a packed lunch</span></div>'
        "</div>"
    )


def _person_a_picture() -> str:
    cells = (
        ("q", "Query", "needs a novel", "what A seeks"),
        ("k", "Key", "food / lunch", "how A can be matched"),
        ("v", "Value", "packed lunch", "what A can contribute"),
    )
    row = "".join(
        f'<div class="is-{tone}"><b>{name}</b><strong>{item}</strong><span>{job}</span></div>'
        for tone, name, item, job in cells
    )
    return (
        '<div class="qkv-s2-trio">'
        '<div class="qkv-s2-trio-who">Person A</div>'
        f'<div class="qkv-s2-trio-row">{row}</div>'
        "</div>"
    )


def _everyone_picture() -> str:
    rows = (
        ("A", "A novel to borrow", "Food / lunch", "A packed lunch"),
        ("B", "A quiet study desk", "Books / lending", "A novel to borrow"),
        ("C", "Something for lunch", "Bicycle / repair", "A bicycle pump"),
        ("D", "Help with a flat tyre", "Study / workspace", "A quiet study desk"),
    )
    body = "".join(
        "<tr>"
        f"<th>Person {who}</th>"
        f"<td>{query}</td>"
        f"<td>{key}</td>"
        f"<td>{value}</td>"
        "</tr>"
        for who, query, key, value in rows
    )
    return (
        '<div class="qkv-s2-table-wrap">'
        '<table class="qkv-s2-table">'
        "<thead><tr>"
        "<th>Person</th>"
        "<th>Query &ndash; what are they looking for, and what kind of information would help them?</th>"
        "<th>Key &ndash; what makes them relevant to what someone else is looking for?</th>"
        "<th>Value &ndash; once matched as relevant, what useful information can they contribute?</th>"
        "</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table></div>"
    )


def _degrees_picture() -> str:
    keys = (
        ("Key A", "strong match", "is-strong"),
        ("Key B", "medium match", "is-medium"),
        ("Key C", "weak match", "is-weak"),
    )
    cells = "".join(
        f'<div class="{tone}"><b>{name}</b><span>{label}</span></div>'
        for name, label, tone in keys
    )
    return (
        '<div class="qkv-s2-degrees">'
        '<div class="qkv-s2-q">Query</div>'
        '<i aria-hidden="true"></i>'
        f'<div class="qkv-s2-keys">{cells}</div>'
        "</div>"
    )


def _memory_picture() -> str:
    return (
        '<div class="qkv-s2-memory">'
        '<div class="qkv-s2-mem is-q"><b>Query</b><span>What am I looking for, and what kind of information would help me?</span></div>'
        '<i class="qkv-s2-down" aria-hidden="true"><small>compare</small>&darr;</i>'
        '<div class="qkv-s2-mem is-k"><b>Key</b><span>Who might be relevant to that need, and how well does each one match what I am looking for?</span></div>'
        '<i class="qkv-s2-down" aria-hidden="true">&darr;</i>'
        '<div class="qkv-s2-mem is-v"><b>Value</b><span>Once someone is matched as relevant, what useful information can they actually contribute?</span></div>'
        "</div>"
    )


def _section_2() -> str:
    return _sec(
        2,
        "An Intuition for Query, Key and Value",
        _p(
            "In Section 1, we saw that attention determines <b>how strongly information from different tokens "
            "contributes to the token we are updating</b>."
        )
        + _p(
            "Before looking at the vectors and equations behind that calculation, let us first understand the three "
            "roles that make this possible."
        )
        + _p(
            "Imagine a small city in which every person can <b>look for something they need</b>, "
            "<b>be recognised as relevant to someone else&rsquo;s need</b>, and "
            "<b>contribute something useful when there is a match</b>."
        )
        + _city_film()
        + _sub("What did the city illustrate?")
        + _p(
            "Let us follow just <b>Person A</b>. Person A is doing two things at once &ndash; he is looking for "
            "something he needs, and he also has something that another person may find useful."
        )
        + _nudge_stop(
            1,
            "Person A needs <b>a novel to borrow</b>. Which role represents what Person A is currently looking for?",
            "Query",
            "Person A&rsquo;s Query represents his current need &ndash; <b>a novel to borrow</b>.",
            "q",
            _query_card(),
        )
        + _nudge_stop(
            2,
            "Person A also offers <b>a packed lunch</b>. If another person is looking for food, what should help them "
            "recognise that Person A may be relevant?",
            "Key",
            "Person A&rsquo;s Key is a <b>searchable description of what he can offer</b> &ndash; something like "
            "<b>food / lunch</b>.",
            "k",
            _key_card(),
        )
        + _nudge_stop(
            3,
            "Person A can offer lunch to someone who needs it. Here, Person C has that need. If Person C&rsquo;s Query matches Person A&rsquo;s Key strongly, what does Person A actually contribute?",
            "Value",
            "Person A&rsquo;s Value is the <b>information or content he actually has available to contribute</b> "
            "&ndash; in our analogy, <b>the packed lunch itself</b>.",
            "v",
            _value_card(),
        )
        + _p(
            "Person A therefore has all three roles at the same time. His <b>Query</b> describes what he is looking "
            "for. His <b>Key</b> describes how what he offers can be matched by someone else&rsquo;s Query. His "
            "<b>Value</b> is what he can actually contribute."
        )
        + _person_a_picture()
        + _quote(
            "<b>Person A is only one example &ndash; the same three roles exist for every participant in the city.</b>"
        )
        + _everyone_picture()
        + (
            '<div class="qkv-s2-note">Each person has something they are looking for, some way in which they can be '
            "recognised as relevant to what someone else is looking for, and some information or content they can "
            "contribute when what they offer matches someone else&rsquo;s Query or need.</div>"
        ),
    )


def _section_3_open() -> str:
    return _sec(
        3,
        "From One Representation to Query, Key and Value",
        _sub("From the analogy to the model")
        + _p("Every token enters an attention head with <b>one vector representation</b>.")
        + _p("For the first <i>bank</i>, call that incoming representation &ndash;"),
    )


def _section_2_split() -> str:
    return (
        _p(
            "The Transformer needs that same token to perform three different jobs &ndash; it must be able to "
            "<b>ask for information</b>, <b>be matched by other Queries</b>, and <b>carry information that can be "
            "contributed</b>."
        )
        + _p(
            "So the model learns three different transformations of the same incoming representation."
        )
        + _viz(_split(), replay=False)
        + _p("Mathematically &ndash;")
    )


def _section_2_explain() -> str:
    return (
        _p(
            "<i>x<sub>i</sub></i> is the representation of token <i>i</i> entering this attention head."
        )
        + _p(
            "<i>W<sub>Q</sub></i>, <i>W<sub>K</sub></i>, and <i>W<sub>V</sub></i> are <b>three different learned "
            "parameter matrices</b>."
        )
        + _p("Multiplying by them produces that token's Query, Key and Value vectors.")
        + _p("Then for the whole sequence &ndash;")
    )


def _section_2_why() -> str:
    return (
        _sub("Why three different W's?")
        + _p(
            "The same incoming representation has to perform three different jobs, so the model learns three different "
            "projections."
        )
        + _viz(_w_jobs(), replay=False)
        + _p(
            "<b>The <i>W</i>'s are different because asking, matching and carrying information are different jobs.</b>"
        )
        + _sub("Every token gets all three")
        + _viz(_roster(), replay=False)
        + _p(
            "<b>Query, Key and Value are not three different types of words. Every token produces all three.</b>"
        )
        + _p(
            "When we say &ldquo;the Query of the first <i>bank</i>,&rdquo; we are simply choosing that token's Query "
            "because that is the token whose attention output we are currently following."
        )
    )


def _section_2_learn() -> str:
    return (
        _sub("Where did the three W's come from?")
        + _p(
            "<i>W<sub>Q</sub></i>, <i>W<sub>K</sub></i>, and <i>W<sub>V</sub></i> are model weights learned during training."
        )
        + _p(
            "They are the same kind of learned numerical parameters you saw earlier being <b>nudged by the training "
            "signal</b>. As prediction errors are backpropagated through the model, these projection matrices are "
            "adjusted along with the other model weights."
        )
        + _sub("The picture to remember")
        + _viz(_remember(), replay=False)
        + _quote("<b>Query asks. Key matches. Value carries the information.</b>")
        + _p(
            "We now know <b>what</b> Queries, Keys and Values are and <b>where they come from</b>."
        )
        + _p("The next question is &ndash;")
        + _quote(
            "<b>How does the Transformer measure the match between one Query and all of those Keys?</b>"
        )
    )


_SCRIPT = """
<script>
(function () {
  function replay(viz) {
    viz.classList.remove("is-play");
    void viz.offsetWidth;
    viz.classList.add("is-play");
  }
  Array.prototype.forEach.call(document.querySelectorAll("[data-qkv-viz]"), function (viz) {
    if (viz.getAttribute("data-qkv-on") === "1") return;
    viz.setAttribute("data-qkv-on", "1");
    var btn = viz.querySelector("[data-qkv-replay]");
    if (btn) btn.addEventListener("click", function () { replay(viz); });
    if ("IntersectionObserver" in window) {
      var seen = false;
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && !seen) {
            seen = true;
            replay(viz);
          }
        });
      }, { threshold: 0.35 });
      io.observe(viz);
    } else {
      replay(viz);
    }
  });
  Array.prototype.forEach.call(document.querySelectorAll("[data-qkv-explore]"), function (explore) {
    if (explore.getAttribute("data-qkv-on") === "1") return;
    explore.setAttribute("data-qkv-on", "1");
    explore.addEventListener("click", function (event) {
      var sentBtn = event.target.closest("[data-qkv-sent]");
      if (!sentBtn) return;
      var sent = sentBtn.getAttribute("data-qkv-sent");
      explore.setAttribute("data-sent", sent);
      Array.prototype.forEach.call(explore.querySelectorAll("[data-qkv-sent]"), function (btn) {
        btn.classList.toggle("is-on", btn === sentBtn);
      });
      Array.prototype.forEach.call(explore.querySelectorAll("[data-sent-pane]"), function (pane) {
        pane.hidden = pane.getAttribute("data-sent-pane") !== sent;
      });
    });
  });
})();
</script>
"""


def _block(inner: str) -> str:
    return f'<div class="qkv-lesson w2x">{inner}</div>'


def _header() -> str:
    return _block(
        f"{DECK}"
        '<h2 id="qkv-title">Inside the Attention Mechanism</h2>'
        + _p(
            "In Lecture 3, we saw that attention allows a token to draw differently on the words around it, helping "
            "the model build representations that depend on context."
        )
        + _p(
            "We could see the <b>attention pattern</b> &ndash; which tokens received more attention and which received less."
        )
        + _p("Now we go inside the Transformer and ask &ndash;")
        + _quote("<b>Where do those attention weights come from?</b>")
    )


def render_how() -> None:
    from services.attention import _load

    packed = _load(["The bank on the river bank got robbed"])
    read = packed[0] if packed else None
    css, mark = _bert_parts(read, "qkv-bert-recall")
    if css:
        st.html(css)

    st.html(_header())
    st.html(_block(_section_1(mark)))
    st.html(_block(_section_2()), unsafe_allow_javascript=True)


def render() -> None:
    tab_how = st.tabs(["Inside Attention – QKV"])[0]
    with tab_how:
        render_how()
