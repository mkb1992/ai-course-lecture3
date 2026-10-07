from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

HEIGHT = 560
_SICK = {4, 14, 24, 27, 30, 33, 36, 39}
DATA_PATH = Path(__file__).resolve().parent.parent / "content" / "threshold_420.csv"


def _patients() -> list[dict]:
    scores = np.linspace(0.04, 0.96, 40)
    return [
        {"id": i + 1, "sick": i in _SICK, "score": round(float(scores[i]), 4)}
        for i in range(40)
    ]


def render() -> None:
    html = _PAGE.replace("__DATA__", json.dumps(_patients())).replace(
        "__CONFIG__", json.dumps({"mode": "standard"})
    )
    with st.container(key="cm_score"):
        st.iframe(html, height=HEIGHT)


def _churn_patients() -> list[dict]:
    df = pd.read_csv(DATA_PATH)
    return [
        {
            "id": str(row.customer_id),
            "sick": bool(row.actual),
            "score": round(float(row.risk), 4),
        }
        for row in df.itertuples(index=False)
    ]


def render_churn() -> None:
    html = _PAGE.replace("__DATA__", json.dumps(_churn_patients())).replace(
        "__CONFIG__",
        json.dumps(
            {
                "mode": "churn",
                "actualPositive": "Churned",
                "actualNegative": "Stayed",
                "predictedPositive": "Churn",
                "predictedNegative": "Stay",
                "entity": "customers",
                "scoreName": "Churn risk",
                "positivePlural": "churned",
                "negativePlural": "stayed",
                "costFp": 500,
                "costFn": 10000,
                "baseline": 580000,
            }
        ),
    )
    with st.container(key="cm2_score"):
        st.iframe(html, height=HEIGHT)


_PAGE = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: "Inter", sans-serif; color: #0b1f3a; background: transparent; font-size: 15px; }
  html, body { overflow: hidden; }
  .wrap { margin: 0; padding: 4px 6px 8px 0; height: 600px; }
  h2 { margin: 0 0 4px; font-size: 1.2rem; font-weight: 800; }
  .sub { margin: 0 0 10px; color: #334155; font-size: 0.88rem; line-height: 1.55; }
  svg { display: block; width: 100%; height: auto; overflow: visible; }
  #strip { flex: 0 0 auto; width: 100%; height: auto; }
  #matrix { flex: 1 1 0; min-height: 0; width: 100%; height: 0; }
  .mface { transition: transform .6s cubic-bezier(.2,.8,.2,1), opacity .35s ease; }
  svg text { font-family: "Inter", sans-serif; }
  svg text.glyph { font-family: "Inter", sans-serif; }
  .strip { cursor: ew-resize; touch-action: none; user-select: none; }
  .cellbox, .spot { transition: all .5s cubic-bezier(.2,.8,.2,1); }
  .layout { display: grid; grid-template-columns: minmax(0, 1fr) max-content; grid-template-rows: 100%; gap: 28px; height: 100%; }
  .left { display: flex; flex-direction: column; align-items: stretch; gap: 8px; min-width: 0; min-height: 0; height: 100%; }
  .right { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; min-height: 0; overflow: hidden; }
  .mcard { border: 1.5px solid #0b1f3a; border-radius: 12px; padding: 6px 16px; background: #fff; cursor: pointer;
           transition: background .2s ease, border-color .2s ease, box-shadow .2s ease; flex: 1 1 0; min-height: 0; overflow: hidden;
           display: grid; width: max-content; max-width: 100%; justify-content: start;
           grid-template-columns: 200px 136px 14px 44px 14px 58px 80px; align-items: center; column-gap: 8px; }
  .mspark { display: block; width: 80px; height: 38px; }
  .mcard:hover { background: #f7f9fc; }
  .mcard.on { border: 2.5px solid #c9973a; background: #fbf6ec; box-shadow: 0 2px 10px rgba(201,151,58,0.18); }
  .cost-card { display: block; cursor: default; padding: 10px 14px; }
  .cost-card h3 { margin: 0 0 5px; font-size: 0.95rem; }
  .cost-card p { margin: 3px 0; color: #475569; font-size: 0.74rem; line-height: 1.25; }
  .cost-card .cost-total { margin-top: 6px; padding-top: 6px; border-top: 1px solid #d7dde7; color: #0b1f3a; font-size: 1.1rem; font-weight: 800; }
  .cost-card .cost-save { color: #1b7a47; font-weight: 800; }
  .cost-card .cost-save.loss { color: #b91c1c; }
  .mtext b { display: block; font-size: 1rem; font-weight: 800; letter-spacing: -0.01em; }
  .mq { color: #475569; font-size: 0.74rem; line-height: 1.35; margin-top: 3px; }
  .sym, .num, .eq { display: flex; align-items: center; justify-content: center; color: #0b1f3a; }
  .sym .katex { font-size: 1.02em; }
  .num .katex { font-size: 1.22em; }
  .eq { font-size: 1.1rem; font-weight: 600; }
  .mval { font-size: 1.45rem; font-weight: 800; text-align: right; }
  .mval.undef { font-size: 0.72rem; color: #b91c1c; }
  .hf { display: inline-flex; flex-direction: column; align-items: center; font-weight: 700; }
  .hf .line { width: 100%; height: 1.5px; background: #0b1f3a; margin: 3px 0; }
  .sym .hf { font-size: 0.72rem; }
  .num .hf { font-size: 0.95rem; }
  .frac { display: flex; align-items: center; justify-content: center; font-size: 0.85rem; }
  .fr { display: inline-flex; flex-direction: column; align-items: center; }
  .fr b { padding: 0 6px; }
  .fr .line { width: 100%; height: 1.5px; background: #0b1f3a; margin: 2px 0; }
  .fr small { color: #5a6880; font-size: 0.66rem; }
  .undef { color: #b91c1c; font-weight: 800; }
  .tip { position: fixed; pointer-events: none; background: #0b1f3a; color: #fff; padding: 6px 9px; border-radius: 6px;
         font-size: 0.76rem; display: none; z-index: 5; white-space: nowrap; }
  @media (max-width: 820px) {
    .wrap { height: auto !important; }
    .layout { grid-template-columns: 1fr !important; grid-template-rows: auto; height: auto; }
    #matrix { flex: none; height: 420px; }
  }
</style>
</head>
<body>
<div class="wrap">
  <div class="layout">
    <div class="left" id="left">
      <svg id="strip" class="strip" viewBox="0 0 900 136" preserveAspectRatio="xMinYMid meet" role="img" aria-label="Patients by risk score"></svg>
      <svg id="matrix" viewBox="0 0 720 700" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Confusion matrix"></svg>
    </div>
    <div class="right" id="metrics"></div>
  </div>
</div>
<div class="tip" id="tip"></div>

<script>
(function () {
  var PATIENTS = __DATA__;
  var CONFIG = __CONFIG__;
  var CHURN = CONFIG.mode === "churn";
  var POSITIVE = CONFIG.actualPositive || "Sick";
  var NEGATIVE = CONFIG.actualNegative || "Not Sick";
  var PRED_POSITIVE = CONFIG.predictedPositive || POSITIVE;
  var PRED_NEGATIVE = CONFIG.predictedNegative || NEGATIVE;
  var ENTITY = CONFIG.entity || "patients";
  var SCORE_NAME = CONFIG.scoreName || "Risk score";
  var NS = "http://www.w3.org/2000/svg";
  var strip = document.getElementById("strip");
  var matrix = document.getElementById("matrix");
  var tip = document.getElementById("tip");
  var RED = "#B91C1C", GREEN = "#1B7A47", SICK = "\u2639", WELL = "\u263a";

  // Strip geometry: Actual on one row, Predicted on the row below it.
  // 40 patients at 18px must sit at least 18px apart on the axis, so faces only touch.
  var AX0 = 110, AX1 = 885, ACT_Y = 38, PRED_Y = 78, AXIS_Y = 110;
  // Matrix geometry: four equal squares, each holding up to 32 faces per triangle without overlap.
  // Each square has its own label band on top (Predicted) and on the left (Actually).
  var SQ = 300, BAND = 32, GAP = 14, GAP_X = 34, EDGE = 8;
  var FACE_SIZE = CHURN ? 7 : 20, FACE_STEP = CHURN ? 7 : 20;
  // n faces as a staircase triangle shaped like its half of the square (k rows: k, k-1, ..., 1),
  // placed so the gap to all three sides - both outer edges and the diagonal - is the same.
  // For a triangle of side L = (k - 1) * step that gap puts the corner face at c = (SQ - L) / (2 + sqrt 2)
  // from both outer edges. Faces fill in layers parallel to the diagonal from the corner outward,
  // and a partial last layer is centred. The upper-right half is the exact mirror of the lower-left.
  function triangleFaces(n, x, y, upper) {
    if (n <= 0) return [];
    var k = 1;
    while (k * (k + 1) / 2 < n) k++;
    var s = FACE_STEP, L = (k - 1) * s, c = (SQ - L) / (2 + Math.SQRT2);
    var pts = [];
    for (var d = 0; d < k; d++) {
      for (var i = 0; i <= d; i++) pts.push({ d: d, off: i - (d - i), px: c + i * s, py: SQ - c - (d - i) * s });
    }
    pts.sort(function (p, q) { return p.d - q.d || Math.abs(p.off) - Math.abs(q.off) || p.off - q.off; });
    return pts.slice(0, n).map(function (p) { return upper ? [x + p.py, y + p.px] : [x + p.px, y + p.py]; });
  }
  function sqX(col) { return EDGE + BAND + col * (BAND + SQ + GAP_X); }
  function sqY(row) { return EDGE + BAND + row * (BAND + SQ + GAP); }
  var POS = { tp: [0, 0], fn: [1, 0], fp: [0, 1], tn: [1, 1] };
  var CELLS = {};
  Object.keys(POS).forEach(function (k) {
    var x = sqX(POS[k][0]), y = sqY(POS[k][1]);
    CELLS[k] = [x - 8, x + SQ + 8, y - 8, y + SQ + 8];
  });
  var NAME = { tp: "True Positive", fn: "False Negative", fp: "False Positive", tn: "True Negative" };
  var LENSES = {
    accuracy: { name: "Accuracy", num: ["tp", "tn"], den: ["tp", "fp", "fn", "tn"], spot: "diag",
      q: "Of all " + ENTITY + ", how many were predicted correctly?",
      rule: "Accuracy looks along the <b>diagonal</b>, out of everyone." },
    precision: { name: "Precision", num: ["tp"], den: ["tp", "fp"], spot: "colSick",
      q: 'Of everyone Predicted "' + PRED_POSITIVE + '", how many are Actually "' + POSITIVE + '"?',
      rule: "Precision looks <b>down the Predicted \"" + PRED_POSITIVE + "\" column</b>." },
    recall: { name: "Recall", num: ["tp"], den: ["tp", "fn"], spot: "rowSick",
      q: 'Of everyone Actually "' + POSITIVE + '", how many were Predicted "' + PRED_POSITIVE + '"?',
      rule: "Recall looks <b>across the Actually \"" + POSITIVE + "\" row</b>." },
    specificity: { name: "Specificity", num: ["tn"], den: ["fp", "tn"], spot: "rowWell",
      q: 'Of everyone Actually "' + NEGATIVE + '", how many were Predicted "' + PRED_NEGATIVE + '"?',
      rule: "Specificity looks <b>across the Actually \"" + NEGATIVE + "\" row</b>." },
    f1: { name: "F1", num: ["tp"], den: ["tp", "fp", "fn"], spot: "f1",
      q: "High only when precision and recall are both high.",
      rule: "F1 combines the <b>Precision column and the Recall row</b>, and stays close to whichever is weaker." }
  };
  var state = { t: 0.55, lens: "accuracy", hover: null };

  function el(tag, attrs, parent) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(n);
    return n;
  }
  function text(parent, attrs, value) { var n = el("text", attrs, parent); n.textContent = value; return n; }
  // Filled face: coloured disc with white eyes and a white smile (not sick) or frown (sick).
  function face(parent, sick, size, cx, cy, cls) {
    var g = el("g", cls ? { class: cls } : {}, parent);
    if (cx !== undefined) g.setAttribute("transform", "translate(" + cx + "," + cy + ")");
    var r = size * 0.45;
    g._disc = el("circle", { r: r }, g);
    el("circle", { cx: -r * 0.36, cy: -r * 0.28, r: r * 0.14, fill: "#fff" }, g);
    el("circle", { cx: r * 0.36, cy: -r * 0.28, r: r * 0.14, fill: "#fff" }, g);
    g._mouth = el("path", { fill: "none", stroke: "#fff", "stroke-width": r * 0.17, "stroke-linecap": "round" }, g);
    g._r = r;
    setFace(g, sick);
    return g;
  }
  function setFace(g, sick) {
    var r = g._r;
    g._disc.setAttribute("fill", sick ? RED : GREEN);
    g._mouth.setAttribute("d", sick
      ? "M" + (-r * 0.45) + " " + (r * 0.5) + " Q0 " + (r * 0.12) + " " + (r * 0.45) + " " + (r * 0.5)
      : "M" + (-r * 0.45) + " " + (r * 0.2) + " Q0 " + (r * 0.62) + " " + (r * 0.45) + " " + (r * 0.2));
  }
  function cellOf(p, t) { var s = p.score >= t; return p.sick ? (s ? "tp" : "fn") : (s ? "fp" : "tn"); }
  function counts(t) {
    var c = { tp: 0, fp: 0, fn: 0, tn: 0 };
    PATIENTS.forEach(function (p) { c[cellOf(p, t)]++; });
    return c;
  }
  function ratio(n, d) { return d > 0 ? n / d : 0; }
  function metrics(c) {
    var P = ratio(c.tp, c.tp + c.fp), R = ratio(c.tp, c.tp + c.fn);
    return {
      accuracy: ratio(c.tp + c.tn, c.tp + c.fp + c.fn + c.tn), precision: P, recall: R,
      specificity: ratio(c.tn, c.tn + c.fp),
      f1: (P === null || R === null) ? null : (P + R === 0 ? 0 : 2 * P * R / (P + R))
    };
  }
  function pct(v) { return v === null ? "undefined" : Math.round(v * 100) + "%"; }
  function ax(s) { return AX0 + (AX1 - AX0) * s; }

  // ---------- strip ----------
  el("rect", { x: 0, y: 0, width: 900, height: 136, fill: "transparent" }, strip);
  el("rect", { x: AX0 - 12, y: ACT_Y - 16, width: AX1 - AX0 + 24, height: 32, rx: 10, fill: "#f7f9fc" }, strip);
  el("rect", { x: AX0 - 12, y: PRED_Y - 16, width: AX1 - AX0 + 24, height: 32, rx: 10, fill: "#f7f9fc" }, strip);
  text(strip, { x: AX0 - 18, y: ACT_Y + 5, "text-anchor": "end", "font-size": 14, "font-weight": 800, fill: "#0b1f3a" }, "Actual");
  text(strip, { x: AX0 - 18, y: PRED_Y + 5, "text-anchor": "end", "font-size": 14, "font-weight": 800, fill: "#0b1f3a" }, "Predicted");
  el("line", { x1: AX0, y1: AXIS_Y, x2: AX1, y2: AXIS_Y, stroke: "#b9c3d3", "stroke-width": 1.5 }, strip);
  [0, 0.2, 0.4, 0.6, 0.8, 1].forEach(function (s) {
    el("line", { x1: ax(s), y1: AXIS_Y, x2: ax(s), y2: AXIS_Y + 5, stroke: "#8190a5" }, strip);
    text(strip, { x: ax(s), y: AXIS_Y + 19, "text-anchor": "middle", "font-size": 12, fill: "#5a6880" }, s.toFixed(1));
  });
  text(strip, { x: AX0 - 18, y: AXIS_Y + 19, "text-anchor": "end", "font-size": 12, "font-weight": 700, fill: "#0b1f3a" }, SCORE_NAME);

  var shade = el("rect", { y: PRED_Y - 16, height: 32, rx: 10, fill: "rgba(185,28,28,0.07)" }, strip);

  var stripFaceSize = CHURN ? 7 : 18;
  var faces = {};
  PATIENTS.forEach(function (p) {
    var x = ax(p.score);
    var a = face(strip, p.sick, stripFaceSize, x, ACT_Y);
    var b = face(strip, p.sick, stripFaceSize, x, PRED_Y);
    faces[p.id] = { a: a, b: b };
    [a, b].forEach(function (n) {
      n.addEventListener("pointerenter", function () { state.hover = p.id; paintHover(); });
      n.addEventListener("pointermove", function (e) { showTip(e, p); });
      n.addEventListener("pointerleave", function () { state.hover = null; paintHover(); tip.style.display = "none"; });
    });
  });

  var tLine = el("line", { y1: 8, y2: AXIS_Y, stroke: "#c9973a", "stroke-width": 3.5 }, strip);
  var tKnob = el("rect", { y: 0, width: 70, height: 18, rx: 9, fill: "#c9973a" }, strip);
  var tLabel = text(strip, { y: 13, "text-anchor": "middle", "font-size": 12, "font-weight": 800, fill: "#111" }, "");

  function drawStrip() {
    var tx = ax(state.t);
    tLine.setAttribute("x1", tx); tLine.setAttribute("x2", tx);
    tKnob.setAttribute("x", tx - 35); tLabel.setAttribute("x", tx); tLabel.textContent = "t = " + state.t.toFixed(2);
    shade.setAttribute("x", tx); shade.setAttribute("width", Math.max(0, AX1 + 12 - tx));
    PATIENTS.forEach(function (p) {
      var sick = p.score >= state.t;
      setFace(faces[p.id].b, sick);
    });
    paintHover();
  }
  function paintHover() {
    PATIENTS.forEach(function (p) {
      var dim = state.hover !== null && state.hover !== p.id ? 0.25 : 1;
      faces[p.id].a.style.opacity = dim; faces[p.id].b.style.opacity = dim;
      if (mfaces[p.id]) mfaces[p.id].style.opacity = state.hover === null ? mfaces[p.id].dataset.op : dim;
    });
  }
  function showTip(e, p) {
    tip.style.display = "block";
    tip.style.left = (e.clientX + 12) + "px";
    tip.style.top = (e.clientY + 12) + "px";
    tip.textContent = SCORE_NAME + " " + p.score.toFixed(2) + "  •  " + (p.sick ? 'Actually "' + POSITIVE + '"' : 'Actually "' + NEGATIVE + '"') +
      "  •  " + (p.score >= state.t ? 'Predicted "' + PRED_POSITIVE + '"' : 'Predicted "' + PRED_NEGATIVE + '"') + "  •  " + NAME[cellOf(p, state.t)];
  }

  var dragging = false;
  function pointerT(e) {
    var pt = strip.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY;
    var local = pt.matrixTransform(strip.getScreenCTM().inverse());
    return Math.round(Math.max(0, Math.min(1, (local.x - AX0) / (AX1 - AX0))) * 100) / 100;
  }
  strip.addEventListener("pointerdown", function (e) { dragging = true; strip.setPointerCapture(e.pointerId); setThreshold(pointerT(e)); });
  strip.addEventListener("pointermove", function (e) { if (dragging) setThreshold(pointerT(e)); });
  strip.addEventListener("pointerup", function () { dragging = false; });
  strip.addEventListener("pointercancel", function () { dragging = false; });

  // ---------- matrix ----------
  var boxes = {}, parts = {}, nums = {}, actualNums = {}, slots = {};
  var clipRoot = el("defs", {}, matrix);
  var ACTUAL_OF = { tp: '"' + POSITIVE + '"', fn: '"' + POSITIVE + '"', fp: '"' + NEGATIVE + '"', tn: '"' + NEGATIVE + '"' };
  var PREDICTED_OF = { tp: '"' + PRED_POSITIVE + '"', fp: '"' + PRED_POSITIVE + '"', fn: '"' + PRED_NEGATIVE + '"', tn: '"' + PRED_NEGATIVE + '"' };
  Object.keys(POS).forEach(function (k) {
    var sx = sqX(POS[k][0]), sy = sqY(POS[k][1]);
    text(matrix, { x: sx + SQ / 2, y: sy - 10, "text-anchor": "middle", "font-size": 19, "font-weight": 800, fill: "#0b1f3a" },
      "Predicted " + PREDICTED_OF[k]);
    var lx = sx - 10, ly = sy + SQ / 2;
    text(matrix, { x: lx, y: ly, transform: "rotate(-90 " + lx + " " + ly + ")", "text-anchor": "middle",
      "font-size": 19, "font-weight": 800, fill: "#0b1f3a" }, "Actually " + ACTUAL_OF[k]);
  });
  // Outline around a square together with its two label bands.
  function group(keys) {
    var x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    keys.forEach(function (k) {
      var sx = sqX(POS[k][0]), sy = sqY(POS[k][1]);
      x0 = Math.min(x0, sx - BAND - 6); y0 = Math.min(y0, sy - BAND - 6);
      x1 = Math.max(x1, sx + SQ + 6); y1 = Math.max(y1, sy + SQ + 6);
    });
    return [x0, y0, x1 - x0, y1 - y0];
  }
  Object.keys(CELLS).forEach(function (k) {
    var b = CELLS[k];
    var pad = 8, x = b[0] + pad, y = b[2] + pad, w = b[1] - b[0] - pad * 2, h = b[3] - b[2] - pad * 2;
    var clip = el("clipPath", { id: "clip-" + k }, clipRoot);
    el("rect", { x: x, y: y, width: w, height: h, rx: 12 }, clip);
    boxes[k] = el("rect", { class: "cellbox", x: x, y: y, width: w, height: h, rx: 12,
      fill: "#f7f9fc", stroke: "#0b1f3a", "stroke-width": 1 }, matrix);
    var g = el("g", { "clip-path": "url(#clip-" + k + ")" }, matrix);
    el("line", { x1: x, y1: y, x2: x + w, y2: y + h, stroke: "#0b1f3a", "stroke-width": 1.4 }, g);
    // The square's name sits on the middle of the diagonal so it labels the whole square, not one half.
    // Its 17px half-height stays inside the face-free band either side of the diagonal (at least 37px).
    var tag = el("g", { transform: "translate(" + (x + w / 2) + "," + (y + h / 2) + ") rotate(45)" }, g);
    el("rect", { x: -92, y: -17, width: 184, height: 34, rx: 17, fill: "#fff", stroke: "#0b1f3a", "stroke-width": 1.5 }, tag);
    text(tag, { x: 0, y: 6.5, "text-anchor": "middle", "font-size": 19, "font-weight": 800, fill: "#0b1f3a" }, NAME[k]);
    // Upper-right: how many were predicted into this square (changes with the threshold).
    nums[k] = text(g, { x: x + w - 12, y: y + 30, "text-anchor": "end", "font-size": 30, "font-weight": 800, fill: "#000" }, "0");
    // Lower-left: everyone who is actually in this row (never changes).
    var sickRow = k === "tp" || k === "fn";
    // Circle sized to clear the nearest corner face even when this half holds 32 faces.
    el("circle", { cx: x + 24, cy: y + h - 24, r: 20, fill: "#fff", stroke: sickRow ? RED : GREEN, "stroke-width": 2.5 }, g);
    actualNums[k] = text(g, { x: x + 24, y: y + h - 16, "text-anchor": "middle", "font-size": 22, "font-weight": 800,
      fill: sickRow ? RED : GREEN }, "0");
    parts[k] = g;
    // Lower-left half: everyone actually in this row, fixed, sitting along the diagonal.
    var rowSick = k === "tp" || k === "fn";
    var members = PATIENTS.filter(function (p) { return p.sick === rowSick; })
      .sort(function (a, b) { return a.score - b.score; });
    var fixed = triangleFaces(members.length, x, y, false);
    members.forEach(function (p, i) {
      var s = fixed[i];
      face(g, rowSick, FACE_SIZE, s[0], s[1]);
    });
    // Upper-right half: slots for the faces predicted into this square.
    slots[k] = [x, y];
  });
  var mfaces = {};
  PATIENTS.forEach(function (p) {
    var n = face(matrix, p.sick, FACE_SIZE, undefined, undefined, "mface");
    n.dataset.op = 1;
    n.addEventListener("pointerenter", function () { state.hover = p.id; paintHover(); });
    n.addEventListener("pointermove", function (e) { showTip(e, p); });
    n.addEventListener("pointerleave", function () { state.hover = null; paintHover(); tip.style.display = "none"; });
    mfaces[p.id] = n;
  });
  var spots = [el("rect", { class: "spot", rx: 14, fill: "none", stroke: "#c9973a", "stroke-width": 4 }, matrix),
               el("rect", { class: "spot", rx: 14, fill: "none", stroke: "#c9973a", "stroke-width": 4 }, matrix)];
  function setSpot(r, b) {
    if (!b) { r.style.opacity = 0; return; }
    r.style.opacity = 1;
    r.style.x = b[0] + "px"; r.style.y = b[1] + "px"; r.style.width = b[2] + "px"; r.style.height = b[3] + "px";
  }
  function drawMatrix() {
    var c = counts(state.t), lens = LENSES[state.lens];
    var rowTotal = { tp: c.tp + c.fn, fn: c.tp + c.fn, fp: c.fp + c.tn, tn: c.fp + c.tn };
    var groups = { tp: [], fp: [], fn: [], tn: [] };
    PATIENTS.forEach(function (p) { groups[cellOf(p, state.t)].push(p); });
    Object.keys(CELLS).forEach(function (k) {
      var inNum = lens.num.indexOf(k) >= 0, inDen = lens.den.indexOf(k) >= 0;
      var pts = triangleFaces(groups[k].length, slots[k][0], slots[k][1], true);
      // Upper half shows the prediction, so faces take the predicted colour (lower half keeps the actual one).
      var predictedSick = k === "tp" || k === "fp";
      groups[k].sort(function (a, b) { return b.score - a.score; }).forEach(function (p, i) {
        var s = pts[i];
        setFace(mfaces[p.id], predictedSick);
        mfaces[p.id].style.transform = "translate(" + s[0] + "px," + s[1] + "px)";
        mfaces[p.id].dataset.op = 1;
      });
      boxes[k].setAttribute("fill", inNum ? "rgba(201,151,58,0.18)" : "#f7f9fc");
      boxes[k].style.opacity = inNum || inDen ? 1 : 0.4;
      parts[k].style.opacity = inNum || inDen ? 1 : 0.35;
      nums[k].textContent = c[k];
      actualNums[k].textContent = rowTotal[k];
    });
    var spot = {
      colSick: [group(["tp", "fp"])],
      rowSick: [group(["tp", "fn"])],
      rowWell: [group(["fp", "tn"])],
      diag: [group(["tp"]), group(["tn"])],
      f1: [group(["tp", "fp"]), group(["tp", "fn"])]
    }[lens.spot];
    setSpot(spots[0], spot[0]); setSpot(spots[1], spot[1] || null);
    paintHover();
  }

  // ---------- metric boxes ----------
  var metricBox = document.getElementById("metrics");
  var cards = {};
  Object.keys(LENSES).forEach(function (k) {
    var d = document.createElement("div");
    d.className = "mcard";
    d.onclick = function () { state.lens = k; render(); };
    metricBox.appendChild(d);
    cards[k] = d;
  });
  var costCard = null;
  if (CHURN) {
    costCard = document.createElement("div");
    costCard.className = "mcard cost-card";
    metricBox.appendChild(costCard);
  }
  function sum(c, keys) { return keys.reduce(function (a, k) { return a + c[k]; }, 0); }
  function texTerms(s) {
    return s.replace(/2·/g, "2\\,").replace(/\b(TP|FP|FN|TN)\b/g, "\\mathrm{$1}");
  }
  function frac(texTop, texBottom, top, bottom) {
    if (window.katex) {
      return window.katex.renderToString("\\dfrac{" + texTop + "}{" + texBottom + "}", { throwOnError: false });
    }
    return "<span class='hf'><span>" + top + "</span><span class='line'></span><span>" + bottom + "</span></span>";
  }
  // Each metric across every threshold, so the small chart only moves its marker while dragging.
  var CURVE = {};
  Object.keys(LENSES).forEach(function (k) { CURVE[k] = []; });
  for (var step = 0; step <= 100; step++) {
    var at = metrics(counts(step / 100));
    Object.keys(LENSES).forEach(function (k) { CURVE[k].push(at[k] || 0); });
  }
  function spark(k) {
    var pts = CURVE[k].map(function (v, i) { return (i / 100 * 76 + 2) + "," + (3 + (1 - v) * 30); }).join(" ");
    var x = state.t * 76 + 2;
    var y = 3 + (1 - CURVE[k][Math.round(state.t * 100)]) * 30;
    return "<svg class='mspark' viewBox='0 0 80 36' aria-hidden='true'>" +
      "<polyline points='" + pts + "' fill='none' stroke='#c5cedb' stroke-width='1.4' stroke-linejoin='round'/>" +
      "<line x1='" + x + "' y1='2' x2='" + x + "' y2='34' stroke='#c9973a' stroke-width='1.2'/>" +
      "<circle cx='" + x + "' cy='" + y + "' r='2.6' fill='#c9973a'/></svg>";
  }
  function drawMetric() {
    var c = counts(state.t), m = metrics(c);
    Object.keys(LENSES).forEach(function (k) {
      var lens = LENSES[k], n, d, top, bottom;
      if (k === "f1") {
        n = 2 * c.tp; d = 2 * c.tp + c.fp + c.fn; top = "2·TP"; bottom = "2·TP + FP + FN";
      } else {
        n = sum(c, lens.num); d = sum(c, lens.den);
        top = lens.num.map(function (x) { return x.toUpperCase(); }).join(" + ");
        bottom = lens.den.map(function (x) { return x.toUpperCase(); }).join(" + ");
      }
      var v = m[k];
      cards[k].classList.toggle("on", k === state.lens);
      cards[k].innerHTML =
        "<div class='mtext'><b>" + lens.name + "</b><div class='mq'>" + lens.q + "</div></div>" +
        "<span class='sym'>" + frac(texTerms(top), texTerms(bottom), top, bottom) + "</span>" +
        "<span class='eq'>=</span>" +
        "<span class='num'>" + frac(String(n), String(d), n, d) + "</span>" +
        "<span class='eq'>=</span>" +
        (v === null ? "<span class='mval undef'>Undefined</span>" : "<span class='mval'>" + pct(v) + "</span>") +
        spark(k);
    });
    if (costCard) {
      var couponCost = c.fp * CONFIG.costFp;
      var lostCost = c.fn * CONFIG.costFn;
      var totalCost = couponCost + lostCost;
      var saving = CONFIG.baseline - totalCost;
      var savingClass = saving >= 0 ? "cost-save" : "cost-save loss";
      var savingLabel = saving >= 0 ? "Savings" : "Extra cost";
      costCard.innerHTML =
        "<h3>Cost at this threshold</h3>" +
        "<p>Coupons: " + c.fp + " × ₹" + CONFIG.costFp.toLocaleString("en-IN") + " = ₹" + couponCost.toLocaleString("en-IN") + "</p>" +
        "<p>Lost customers: " + c.fn + " × ₹" + CONFIG.costFn.toLocaleString("en-IN") + " = ₹" + lostCost.toLocaleString("en-IN") + "</p>" +
        "<div class='cost-total'>Total: ₹" + totalCost.toLocaleString("en-IN") + "</div>" +
        "<p>Doing nothing: ₹" + CONFIG.baseline.toLocaleString("en-IN") + "</p>" +
        "<p class='" + savingClass + "'>" + savingLabel + ": ₹" + Math.abs(saving).toLocaleString("en-IN") + "</p>";
    }
  }

  function setThreshold(t) {
    if (Math.abs(t - state.t) < 1e-9) return;
    state.t = t;
    render();
  }
  function render() { drawStrip(); drawMatrix(); drawMetric(); fit(); }
  function pinTop() {
    var frame = window.frameElement;
    var body = frame && frame.closest(".st-key-cm_body");
    if (!body) return;
    if (!body.__cmPinned) {
      body.__cmPinned = true;
      body.addEventListener("scroll", pinTop);
    }
    var shown = frame.getBoundingClientRect().width > 0;
    var panel = frame.closest(".st-key-lesson_block");
    for (var el = frame.parentElement; el && el !== panel; el = el.parentElement) {
      if (shown) {
        var ov = getComputedStyle(el).overflowY;
        if (ov === "auto" || ov === "scroll") el.__cmLocked = true;
        if (el.__cmLocked) {
          el.style.setProperty("overflow", "hidden", "important");
          el.scrollTop = 0;
        }
      } else if (el.__cmLocked) {
        el.style.removeProperty("overflow");
      }
    }
    if (shown && body.scrollTop !== 0) body.scrollTop = 0;
  }
  function fit() {
    var frame = window.frameElement;
    if (!frame) return;
    pinTop();
    var wrap = document.querySelector(".wrap");
    var stacked = window.innerWidth <= 820;
    var avail = 600;
    // The lesson panel has a fixed height; cm_body grows with content, so measure against the panel.
    var panel = frame.closest(".st-key-lesson_block");
    var fr = frame.getBoundingClientRect();
    if (panel && fr.width > 0) avail = Math.max(420, Math.floor(panel.getBoundingClientRect().bottom - fr.top - 28));
    if (!stacked) {
      wrap.style.height = avail + "px";
    }
    var h = stacked ? wrap.offsetHeight + 8 : avail;
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
  render();
})();
</script>
</body>
</html>
"""
