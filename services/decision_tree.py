from __future__ import annotations

import json

import streamlit as st

HEIGHT = 600
INTUITION_HEIGHT = 560

# Same 16 customers as the Exercise table: (id, age, complaints, tenure months, monthly bill, churned).
_CUSTOMERS = [
    ("C01", 24, 6, 5, 1450, True),
    ("C02", 29, 5, 8, 1180, True),
    ("C03", 32, 6, 14, 1620, True),
    ("C04", 36, 4, 22, 980, True),
    ("C05", 38, 5, 30, 1310, True),
    ("C06", 46, 4, 10, 1080, True),
    ("C07", 51, 2, 26, 1520, True),
    ("C08", 57, 1, 18, 890, True),
    ("C09", 26, 5, 16, 1260, False),
    ("C10", 35, 4, 28, 1100, False),
    ("C11", 31, 2, 7, 1480, False),
    ("C12", 43, 1, 13, 920, False),
    ("C13", 47, 2, 21, 1350, False),
    ("C14", 52, 1, 32, 1040, False),
    ("C15", 58, 2, 11, 1580, False),
    ("C16", 63, 1, 24, 960, False),
]


def _customers() -> list[dict]:
    return [
        {"id": c, "age": a, "complaints": k, "tenure": t, "bill": b, "churned": ch}
        for c, a, k, t, b, ch in _CUSTOMERS
    ]


def render() -> None:
    html = _PAGE.replace("__DATA__", json.dumps(_customers())).replace("__MODE__", "full")
    with st.container(key="dt_practical"):
        st.iframe(html, height=HEIGHT)


def render_intuition() -> None:
    html = _PAGE.replace("__DATA__", json.dumps(_customers())).replace("__MODE__", "intuition")
    with st.container(key="dt_intuition"):
        st.iframe(html, height=INTUITION_HEIGHT)


_PAGE = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; }
  html, body { overflow: hidden; }
  body { margin: 0; font-family: "Inter", sans-serif; color: #0b1f3a; background: transparent; font-size: 15px; }
  .wrap { height: 600px; display: flex; flex-direction: column; gap: 12px; padding: 4px 6px 8px 0; }
  .card { border: 1.5px solid #0b1f3a; border-radius: 12px; background: #fff; padding: 10px 14px; }
  .ttl { font-size: 0.74rem; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; }
  .dot { display: inline-block; width: 14px; height: 14px; border-radius: 50%; transition: opacity .15s ease; }
  .dot.c { background: #B91C1C; }
  .dot.s { background: #1B7A47; }
  .r { color: #B91C1C; }
  .g { color: #1B7A47; }

  .top { flex: 0 0 auto; display: grid; grid-template-columns: minmax(0, 1fr); }
  .legend { display: flex; gap: 18px; font-size: 0.9rem; font-weight: 800; }

  .intro { padding: 12px 20px 10px; }
  .intro h3 { margin: 0 0 6px; font-size: 1.3rem; font-weight: 800; letter-spacing: -0.01em; }
  .intro p { margin: 0; color: #334155; font-size: 0.98rem; line-height: 1.5; }
  .goal { display: inline-flex; align-items: center; gap: 8px; margin-top: 10px; padding: 6px 14px; border-radius: 999px;
          background: #fbf6ec; border: 1.5px solid #c9973a; font-size: 0.9rem; font-weight: 800; color: #0b1f3a; }
  .gdot { width: 8px; height: 8px; border-radius: 50%; background: #c9973a; }
  .kid { border: 1px solid #e3e8f0; border-radius: 9px; padding: 5px 8px; background: #f7f9fc; }
  .klab { display: flex; justify-content: space-between; gap: 8px; font-size: 0.74rem; font-weight: 800; margin-bottom: 4px; white-space: nowrap; }
  .kdots { display: flex; flex-wrap: wrap; gap: 3px; min-height: 29px; align-content: flex-start; }
  .kdots .dot { width: 13px; height: 13px; }

  .panels { flex: 1 1 0; min-height: 0; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
  .panel { display: flex; flex-direction: column; gap: 6px; min-height: 0; overflow: hidden;
           transition: background .25s ease, border-color .25s ease; }
  .panel.lowest { background: #cdebd7; border-color: #1B7A47; border-width: 2px; }
  .panel.lowest .kid { background: #fff; }
  .phead { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
  .pval { font-size: 0.8rem; font-weight: 700; color: #475569; white-space: nowrap; }
  .panel svg { flex: 1 1 0; min-height: 70px; height: 0; width: 100%; display: block; overflow: visible;
               cursor: ew-resize; touch-action: none; user-select: none; }
  .panel svg text { font-family: "Inter", sans-serif; }
  .mv { transition: transform .5s cubic-bezier(.2,.8,.2,1), width .5s cubic-bezier(.2,.8,.2,1); }
  .dragging .mv { transition: none; }
  .gain { display: flex; align-items: baseline; justify-content: space-between; border-top: 1px solid #e3e8f0; padding-top: 6px; }
  .gain span { font-size: 0.72rem; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }
  .gain b { font-size: 1.35rem; font-weight: 800; }
  .tip { position: fixed; pointer-events: none; background: #0b1f3a; color: #fff; padding: 6px 9px; border-radius: 6px;
         font-size: 0.76rem; display: none; z-index: 7; white-space: nowrap; }
  .intuition .panels, .intuition .top { display: none; }
  .intuition .wrap { height: auto !important; }
  html.intuition-root { overflow-y: auto; }
  html.intuition-root body { overflow: visible; }
  .lesson { display: none; border: 1.5px solid #0b1f3a; border-radius: 14px; background: #fff; padding: 30px 34px 32px; }
  .intuition .wrap { padding: 8px 8px 10px 2px; }
  .intuition .lesson { display: block; }
  .lesson h3 { margin: 0 0 24px; font-size: 1.45rem; font-weight: 800; letter-spacing: -0.01em; color: #0b1f3a; }
  .lgrid { display: grid; grid-template-columns: minmax(0, 1fr) 36px minmax(0, 1fr) 36px minmax(0, 1fr); align-items: stretch; }
  .lgo { display: flex; align-items: center; justify-content: center; color: #64748b; font-size: 1.2rem; }
  .lcol { display: flex; flex-direction: column; gap: 16px; min-width: 0; padding: 18px 18px 20px; border-radius: 12px; border: 1px solid; }
  .c1 { background: #eef4fc; border-color: #d3e2f6; }
  .c2 { background: #fdf8e9; border-color: #f1e4b8; }
  .c3 { background: #eef8f1; border-color: #cfe9d8; }
  .lhead { display: flex; align-items: center; gap: 10px; }
  .num { flex: 0 0 auto; width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center;
         justify-content: center; font-weight: 800; font-size: 0.85rem; }
  .c1 .num { background: #d6e5fb; color: #1d4ed8; }
  .c2 .num { background: #f7e6ad; color: #8a6412; }
  .c3 .num { background: #d2efdb; color: #1b7a47; }
  .lesson h4 { margin: 0; font-size: 1rem; font-weight: 800; color: #0b1f3a; }
  .lesson p { margin: 0; color: #334155; font-size: 0.88rem; line-height: 1.65; }
  .lesson p b { font-weight: 800; color: #0b1f3a; }
  .lesson b.r { color: #B91C1C; }
  .lesson b.g { color: #1B7A47; }
  .wcard { background: #fff; border: 1px solid #e3e8f0; border-radius: 10px; }
  .lesson .dot { width: 11px; height: 11px; }
  .dots { display: flex; gap: 3px; flex: 0 0 auto; }
  .dots .gap { width: 5px; }

  .ex { display: grid; grid-template-columns: auto minmax(0, 1fr) 88px; align-items: stretch; gap: 12px; padding: 0 0 0 12px; overflow: hidden; }
  .ex .dots { align-self: center; }
  .ex .mid { padding: 13px 0; display: flex; flex-direction: column; justify-content: center; gap: 4px; }
  .ex .cnt { font-size: 0.84rem; font-weight: 800; }
  .ex .mid span.t { font-size: 0.8rem; color: #334155; line-height: 1.55; }
  .tag { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px; }
  .tag small { font-size: 0.7rem; color: #475569; }
  .tag b { font-size: 1.05rem; font-weight: 800; }
  .tag.high { background: #fde8e8; }
  .tag.high b { color: #B91C1C; }
  .tag.low { background: #e3f4e8; }
  .tag.low b { color: #1B7A47; }

  .qrow { display: grid; grid-template-columns: 134px minmax(0, 1fr) 62px; align-items: stretch; gap: 0; overflow: hidden; }
  .qrow .dots { align-self: center; justify-content: center; }
  .qrow .lab { padding: 11px 8px; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; font-size: 0.82rem; color: #0b1f3a; line-height: 1.5; }
  .qrow .lab small { color: #64748b; font-size: 0.74rem; margin-top: 1px; }
  .qv { display: flex; align-items: center; justify-content: center; font-size: 1.05rem; font-weight: 800; color: #0b1f3a; }
  .qv.v1 { background: #fde8e8; }
  .qv.v2 { background: #fdf3d6; }
  .qv.v3 { background: #e3f4e8; }
  .scale { margin-top: 2px; }
  .bar { height: 7px; border-radius: 4px; background: linear-gradient(90deg, #dc2626, #f59e0b 45%, #eab308 55%, #22c55e); }
  .slab { display: flex; justify-content: space-between; margin-top: 4px; font-size: 0.76rem; font-weight: 800; line-height: 1.5; }
  .slab span { display: flex; flex-direction: column; }
  .slab span:last-child { text-align: right; }
  .slab small { font-weight: 500; color: #64748b; }

  .tree { display: flex; flex-direction: column; align-items: stretch; }
  .tnode { align-self: center; display: flex; flex-direction: column; align-items: center; padding: 7px 18px;
           background: #e4eefb; border: 1px solid #c9daf6; border-radius: 8px; font-size: 0.86rem; font-weight: 800; color: #0b1f3a; }
  .tnode small { font-size: 0.74rem; font-weight: 500; color: #475569; }
  .stem { align-self: center; width: 1.5px; height: 10px; background: #64748b; }
  .fork { position: relative; width: 50%; height: 14px; margin: 0 auto; border: 1.5px solid #64748b; border-bottom: none; }
  .fork::before, .fork::after { content: ""; position: absolute; bottom: -5px; border-top: 6px solid #64748b;
                                border-left: 4px solid transparent; border-right: 4px solid transparent; }
  .fork::before { left: -4.75px; }
  .fork::after { right: -4.75px; }
  .kids { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 6px; }
  .kidbox { display: flex; flex-direction: column; align-items: center; gap: 6px; }
  .kidbox .dots { padding: 7px 10px; border-radius: 8px; border: 1px solid; }
  .kidbox.kc .dots { background: #fde8e8; border-color: #f5caca; }
  .kidbox.ks .dots { background: #e3f4e8; border-color: #c5e6d0; }
  .kidbox b { font-size: 0.86rem; font-weight: 800; }
  .kidbox.kc b { color: #B91C1C; }
  .kidbox.ks b { color: #1B7A47; }
  .kidbox small { margin-top: -4px; font-size: 0.78rem; color: #475569; }
  .kwhy { margin-top: 2px; text-align: center; font-size: 0.76rem; color: #64748b; line-height: 1.45; }
  .callout { display: flex; align-items: center; gap: 16px; padding: 14px 18px; border-radius: 10px; background: #e4eefb; margin-top: auto; }
  .callout svg { flex: 0 0 auto; width: 34px; height: 34px; }
  .cbar { flex: 0 0 auto; width: 1.5px; align-self: stretch; background: #b8cdef; }
  .callout b { font-size: 0.9rem; font-weight: 800; color: #0b1f3a; line-height: 1.5; }
  @media (max-width: 900px) {
    .wrap { height: auto !important; }
    .top { grid-template-columns: 1fr; }
    .panels { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .panel svg { flex: none; height: 150px; }
  }
</style>
</head>
<body class="__MODE__">
<div class="wrap">
  <div class="top">
    <div class="card">
      <div class="intro">
        <h3>Find the best split</h3>
        <p>Drag the split point for each feature and watch how the two resulting groups change. Find the split point that reduces
          entropy the most for each feature, then compare the features to determine which feature and split point the decision
          tree would choose for its first split.</p>
        <div class="goal"><span class="gdot"></span>Your goal &ndash; Reduce the uncertainty or entropy to the extent possible.</div>
      </div>
    </div>
  </div>
  <div class="lesson">
    <h3>How does a decision tree choose a split?</h3>
    <div class="lgrid">
      <div class="lcol c1">
        <div class="lhead"><span class="num">1</span><h4>A decision is hard when outcomes are mixed</h4></div>
        <p>If a group contains a similar number of <b class="r">Churned</b> and <b class="g">Stayed</b> customers,
          it is difficult to predict the next customer&rsquo;s outcome.</p>
        <p>When the evidence is evenly balanced between two choices, there is no clear direction, so the decision becomes harder.</p>
        <div class="wcard ex">
          <div class="dots"><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="gap"></span><span class="dot s"></span><span class="dot s"></span><span class="dot s"></span><span class="dot s"></span></div>
          <div class="mid"><span class="cnt"><span class="r">4 Churned</span> &middot; <span class="g">4 Stayed</span></span>
            <span class="t">Prediction is highly uncertain.</span></div>
          <div class="tag high"><small>Uncertainty</small><b>High</b></div>
        </div>
        <div class="wcard ex">
          <div class="dots"><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="gap"></span><span class="dot s"></span></div>
          <div class="mid"><span class="cnt"><span class="r">7 Churned</span> &middot; <span class="g">1 Stayed</span></span>
            <span class="t">Prediction is easier because one outcome is much more common than the other.</span></div>
          <div class="tag low"><small>Uncertainty</small><b>Low</b></div>
        </div>
      </div>
      <div class="lgo">&rarr;</div>
      <div class="lcol c2">
        <div class="lhead"><span class="num">2</span><h4>We quantify this uncertainty</h4></div>
        <p>We assign a number to how mixed the outcomes are in a group. This number is higher when the outcomes are evenly
          mixed and lower when one outcome dominates. This number is <b>Entropy</b>.</p>
        <div class="wcard qrow"><div class="dots"><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot s"></span><span class="dot s"></span><span class="dot s"></span><span class="dot s"></span></div>
          <div class="lab">Evenly mixed<small>(most uncertain)</small></div><div class="qv v1">1.00</div></div>
        <div class="wcard qrow"><div class="dots"><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot s"></span></div>
          <div class="lab">One outcome dominates<small>(less uncertain)</small></div><div class="qv v2">0.54</div></div>
        <div class="wcard qrow"><div class="dots"><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span></div>
          <div class="lab">All customers are the same<small>(no uncertainty)</small></div><div class="qv v3">0.00</div></div>
        <div class="scale">
          <div class="bar"></div>
          <div class="slab"><span class="r">Higher uncertainty<small>(more mixed)</small></span>
            <span class="g">Lower uncertainty<small>(more consistent)</small></span></div>
        </div>
      </div>
      <div class="lgo">&rarr;</div>
      <div class="lcol c3">
        <div class="lhead"><span class="num">3</span><h4>The tree searches for the best split</h4></div>
        <p>For each <b>feature</b>, the tree tries different <b>split points</b> and looks for the split that produces the
          two groups with the <b>lowest uncertainty</b>.</p>
        <div class="tree">
          <div class="tnode">Feature + split point<small>(e.g., Age &le; 30)</small></div>
          <div class="stem"></div>
          <div class="fork"></div>
          <div class="kids">
            <div class="kidbox kc"><div class="dots"><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot c"></span><span class="dot s"></span></div><b>More mixed group</b><small>(higher uncertainty)</small>
              <span class="kwhy">Both outcomes are present in similar amounts.</span></div>
            <div class="kidbox ks"><div class="dots"><span class="dot c"></span><span class="dot s"></span><span class="dot s"></span><span class="dot s"></span><span class="dot s"></span><span class="dot s"></span></div><b>Less mixed group</b><small>(lower uncertainty)</small>
              <span class="kwhy">One outcome clearly dominates.</span></div>
          </div>
        </div>
        <div class="callout">
          <svg viewBox="0 0 34 34" aria-hidden="true">
            <circle cx="17" cy="17" r="17" fill="#c9daf6"/>
            <circle cx="17" cy="17" r="10" fill="none" stroke="#1d4ed8" stroke-width="2"/>
            <circle cx="17" cy="17" r="5.5" fill="none" stroke="#1d4ed8" stroke-width="2"/>
            <circle cx="17" cy="17" r="1.8" fill="#1d4ed8"/>
            <path d="M17 17 L26 8" stroke="#1d4ed8" stroke-width="2" stroke-linecap="round"/>
            <path d="M23.5 7.5 L26.5 7.5 L26.5 10.5" fill="none" stroke="#1d4ed8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="cbar"></span>
          <b>The best split is the one that reduces uncertainty the most.</b>
        </div>
      </div>
    </div>
  </div>
  <div class="panels" id="panels"></div>
</div>
<div class="tip" id="tip"></div>

<script>
(function () {
  var C = __DATA__;
  var NS = "http://www.w3.org/2000/svg";
  var GOLD = "#c9973a", RED = "#B91C1C", GREEN = "#1B7A47";
  var byId = {};
  C.forEach(function (c) { byId[c.id] = c; });
  var FEATURES = [
    { key: "age", name: "Age", short: "Age", unit: "years", min: 20, max: 65, step: 1, ticks: [20, 30, 40, 50, 60], t: 40 },
    { key: "complaints", name: "Support complaints", short: "Complaints", unit: "complaints", min: 0, max: 7, step: 1, ticks: [0, 1, 2, 3, 4, 5, 6, 7], t: 5 },
    { key: "tenure", name: "Tenure (months)", short: "Tenure", unit: "months", min: 0, max: 35, step: 1, ticks: [0, 10, 20, 30], t: 18 },
    { key: "bill", name: "Monthly bill", short: "Bill", unit: "INR", min: 850, max: 1650, step: 10, ticks: [900, 1100, 1300, 1500], t: 1200, money: true }
  ];
  var state = { hover: null };
  var AX0 = 18, AX1 = 282, AXIS_Y = 116, TOP_Y = 32;

  function fmt(f, v) { return f.money ? "\u20b9" + v.toLocaleString("en-IN") : String(v); }
  function el(tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function div(cls, parent, html) {
    var n = document.createElement(cls === "span" ? "span" : "div");
    if (cls !== "span") n.className = cls;
    if (html !== undefined) n.innerHTML = html;
    if (parent) parent.appendChild(n);
    return n;
  }

  // ---------- uncertainty ----------
  function H(a, n) {
    if (!n || !a || a === n) return 0;
    var p = a / n;
    return -p * Math.log2(p) - (1 - p) * Math.log2(1 - p);
  }
  function churned(g) { return g.filter(function (c) { return c.churned; }).length; }
  function split(f, t) {
    var L = [], R = [];
    C.forEach(function (c) { (c[f.key] < t ? L : R).push(c); });
    return { L: L, R: R };
  }
  // Entropy after the split: each child's entropy weighted by its share of the 16 customers.
  function entropy(f, t) {
    var s = split(f, t), n = C.length;
    return s.L.length / n * H(churned(s.L), s.L.length) + s.R.length / n * H(churned(s.R), s.R.length);
  }
  function dots(g) {
    return g.slice().sort(function (a, b) { return (b.churned - a.churned) || (a.id < b.id ? -1 : 1); })
      .map(function (c) { return "<span class='dot " + (c.churned ? "c" : "s") + "' data-id='" + c.id + "'></span>"; }).join("");
  }
  function tally(g) {
    var ch = churned(g);
    return "<span class='r'>" + ch + "</span> + <span class='g'>" + (g.length - ch) + "</span>";
  }

  // ---------- parent ----------

  // ---------- feature panels ----------
  var panelsBox = document.getElementById("panels");
  var P = {};
  function px(f, v) { return AX0 + (AX1 - AX0) * (v - f.min) / (f.max - f.min); }
  FEATURES.forEach(function (f) {
    var box = div("card panel", panelsBox);
    var head = div("phead", box, "<span class='ttl'>" + f.name + "</span>");
    var val = div("pval", head);
    var svg = el("svg", { viewBox: "0 0 300 146", preserveAspectRatio: "xMidYMid meet", role: "img", "aria-label": f.name }, box);
    var shade = el("rect", { class: "mv", x: AX0 - 8, y: TOP_Y, height: AXIS_Y - TOP_Y + 4, rx: 8, fill: "rgba(11,31,58,0.05)" }, svg);
    el("line", { x1: AX0, y1: AXIS_Y, x2: AX1, y2: AXIS_Y, stroke: "#b9c3d3", "stroke-width": 1.5 }, svg);
    f.ticks.forEach(function (v) {
      el("line", { x1: px(f, v), y1: AXIS_Y, x2: px(f, v), y2: AXIS_Y + 5, stroke: "#8190a5" }, svg);
      var tx = el("text", { x: px(f, v), y: AXIS_Y + 19, "text-anchor": "middle", "font-size": 11, fill: "#5a6880" }, svg);
      tx.textContent = fmt(f, v);
    });
    // Customers with close values stack upward so no two dots overlap.
    var placed = [];
    C.slice().sort(function (a, b) { return a[f.key] - b[f.key] || (a.id < b.id ? -1 : 1); }).forEach(function (c) {
      var x = px(f, c[f.key]), lvl = 0;
      while (placed.some(function (q) { return q.l === lvl && Math.abs(q.x - x) < 15; })) lvl++;
      placed.push({ x: x, l: lvl });
      el("circle", { cx: x, cy: AXIS_Y - 12 - lvl * 15, r: 7, fill: c.churned ? RED : GREEN, "data-id": c.id }, svg);
    });
    var line = el("g", { class: "mv" }, svg);
    el("line", { x1: 0, y1: TOP_Y - 4, x2: 0, y2: AXIS_Y + 4, stroke: GOLD, "stroke-width": 3 }, line);
    var knob = el("g", { class: "mv" }, svg);
    el("rect", { x: -36, y: 4, width: 72, height: 20, rx: 10, fill: GOLD }, knob);
    var knobText = el("text", { x: 0, y: 18, "text-anchor": "middle", "font-size": 12, "font-weight": 800, fill: "#111" }, knob);

    var k1 = div("kid", box), k2 = div("kid", box);
    var l1 = div("klab", k1), l2 = div("klab", k2);
    var d1 = div("kdots", k1), d2 = div("kdots", k2);
    var g = div("gain", box, "<span>Entropy</span>");
    var gv = div("span", g);
    var gb = document.createElement("b"); gv.appendChild(gb);

    P[f.key] = { f: f, box: box, svg: svg, val: val, shade: shade, line: line, knob: knob, knobText: knobText,
                 l1: l1, l2: l2, d1: d1, d2: d2, gain: gb };
    // The lowest entropy this feature can reach at any split point.
    var low = Infinity;
    for (var t = f.min + f.step; t <= f.max; t += f.step) low = Math.min(low, entropy(f, t));
    P[f.key].low = low;
    wireDrag(P[f.key]);
  });

  function drawPanel(p) {
    var f = p.f, s = split(f, f.t), x = px(f, f.t - f.step / 2);
    p.line.style.transform = "translateX(" + x + "px)";
    p.knob.style.transform = "translateX(" + Math.max(38, Math.min(262, x)) + "px)";
    p.shade.style.width = Math.max(0, x - (AX0 - 8)) + "px";
    p.knobText.textContent = "< " + fmt(f, f.t);
    p.val.textContent = "Split = " + f.t.toLocaleString("en-IN") + " " + f.unit;
    p.l1.innerHTML = "<span>" + f.short + " &lt; " + fmt(f, f.t) + "</span><span>" + tally(s.L) + "</span>";
    p.l2.innerHTML = "<span>" + f.short + " \u2265 " + fmt(f, f.t) + "</span><span>" + tally(s.R) + "</span>";
    p.d1.innerHTML = dots(s.L);
    p.d2.innerHTML = dots(s.R);
    var e = entropy(f, f.t);
    p.gain.textContent = e.toFixed(2);
    p.box.classList.toggle("lowest", e <= p.low + 1e-9);
  }
  function drawAll() { FEATURES.forEach(function (f) { drawPanel(P[f.key]); }); paintHover(); }

  var dragging = null;
  function pointerT(p, e) {
    var f = p.f, pt = p.svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY;
    var local = pt.matrixTransform(p.svg.getScreenCTM().inverse());
    var v = f.min + (local.x - AX0) / (AX1 - AX0) * (f.max - f.min);
    var t = f.min + Math.round((v + f.step / 2 - f.min) / f.step) * f.step;
    return Math.max(f.min + f.step, Math.min(f.max, t));
  }
  function setT(p, t) {
    if (t === p.f.t) return;
    p.f.t = t;
    drawPanel(p);
    paintHover();
  }
  function wireDrag(p) {
    p.svg.addEventListener("pointerdown", function (e) {
      dragging = p; p.box.classList.add("dragging"); p.svg.setPointerCapture(e.pointerId);
      tip.style.display = "none"; setT(p, pointerT(p, e));
    });
    p.svg.addEventListener("pointermove", function (e) { if (dragging === p) setT(p, pointerT(p, e)); });
    function end() { if (dragging === p) { dragging = null; p.box.classList.remove("dragging"); } }
    p.svg.addEventListener("pointerup", end);
    p.svg.addEventListener("pointercancel", end);
  }

  // ---------- same customer everywhere ----------
  var tip = document.getElementById("tip");
  function paintHover() {
    document.querySelectorAll("[data-id]").forEach(function (n) {
      n.style.opacity = state.hover && n.getAttribute("data-id") !== state.hover ? 0.18 : 1;
    });
  }
  document.addEventListener("pointerover", function (e) {
    if (dragging) return;
    var n = e.target.closest ? e.target.closest("[data-id]") : null;
    var id = n ? n.getAttribute("data-id") : null;
    if (id !== state.hover) { state.hover = id; paintHover(); }
  });
  document.addEventListener("pointermove", function (e) {
    if (!state.hover || dragging) { tip.style.display = "none"; return; }
    var c = byId[state.hover];
    tip.style.display = "block";
    tip.style.left = (e.clientX + 12) + "px";
    tip.style.top = (e.clientY + 12) + "px";
    tip.textContent = c.id + "  \u00b7  Age " + c.age + "  \u00b7  " + c.complaints + " complaints  \u00b7  " + c.tenure +
      " months  \u00b7  \u20b9" + c.bill.toLocaleString("en-IN") + "  \u00b7  " + (c.churned ? "Churned" : "Stayed");
  });

  // ---------- sizing ----------
  var ONLY_TOP = document.body.classList.contains("intuition");
  if (ONLY_TOP) document.documentElement.classList.add("intuition-root");
  function pinTop() {
    if (ONLY_TOP) return;
    var frame = window.frameElement;
    var body = frame && frame.closest(".st-key-dtx_body");
    if (!body) return;
    if (!body.__dtPinned) {
      body.__dtPinned = true;
      body.addEventListener("scroll", pinTop);
    }
    var shown = frame.getBoundingClientRect().width > 0;
    var panel = frame.closest(".st-key-lesson_block");
    for (var n = frame.parentElement; n && n !== panel; n = n.parentElement) {
      if (shown) {
        var ov = getComputedStyle(n).overflowY;
        if (ov === "auto" || ov === "scroll") n.__dtLocked = true;
        if (n.__dtLocked) {
          n.style.setProperty("overflow", "hidden", "important");
          n.scrollTop = 0;
        }
      } else if (n.__dtLocked) {
        n.style.removeProperty("overflow");
      }
    }
    if (shown && body.scrollTop !== 0) body.scrollTop = 0;
  }
  function fit() {
    var frame = window.frameElement;
    if (!frame) return;
    pinTop();
    var wrap = document.querySelector(".wrap");
    var stacked = ONLY_TOP || window.innerWidth <= 900;
    var avail = 600;
    var panel = frame.closest(".st-key-lesson_block");
    var fr = frame.getBoundingClientRect();
    if (ONLY_TOP && fr.width === 0) return;
    var room = panel && fr.width > 0 ? Math.floor(panel.getBoundingClientRect().bottom - fr.top - 28) : 0;
    if (room) avail = Math.max(460, room);
    if (!stacked) wrap.style.height = avail + "px";
    var h = stacked ? wrap.offsetHeight + 8 : avail;
    if (ONLY_TOP && room > 200) h = Math.min(h, room);
    frame.style.setProperty("height", h + "px", "important");
    frame.style.setProperty("min-height", h + "px", "important");
    var box = frame.closest('[data-testid="stElementContainer"]');
    if (box) {
      box.style.setProperty("height", h + "px", "important");
      box.style.setProperty("min-height", h + "px", "important");
    }
  }
  window.addEventListener("resize", fit);
  window.addEventListener("resize", pinTop);
  try { window.parent.addEventListener("resize", fit); } catch (e) {}
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
  drawAll();
  fit();
})();
</script>
</body>
</html>
"""
