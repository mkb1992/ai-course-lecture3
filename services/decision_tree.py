from __future__ import annotations

import json

import streamlit as st

HEIGHT = 620

# The same 16 customers as the Exercise table and the split finder.
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

# Keep the exact 16 customers shown in the exercise. The split is deterministic
# and stratified: 12 are used to learn and 4 are held out until the end.
_TRAIN = [_CUSTOMERS[i] for i in (0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13)]
_TEST = [_CUSTOMERS[i] for i in (6, 7, 14, 15)]


def _rows(src) -> list[dict]:
    return [
        {"id": c, "age": a, "complaints": k, "tenure": t, "bill": b, "churned": ch}
        for c, a, k, t, b, ch in src
    ]


def render() -> None:
    render_grow()


def render_intuition() -> None:
    render_grow()


def render_grow() -> None:
    """Depth, the stopping dials, pruning, and the train/test gap."""
    html = (
        _GROW_PAGE
        .replace("__TRAIN__", json.dumps(_rows(_TRAIN)))
        .replace("__TEST__", json.dumps(_rows(_TEST)))
    )
    with st.container(key="dt_grow"):
        st.iframe(html, height=HEIGHT)


_GROW_PAGE = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: "Inter", sans-serif; color: #0b1f3a; background: transparent; font-size: 15px; }
  .wrap { display: flex; flex-direction: column; gap: 12px; padding: 4px 6px 8px 0; }
  html, body { overflow: hidden; }
  .card { border: 1.5px solid #0b1f3a; border-radius: 12px; background: #fff; padding: 14px 18px; }
  .ttl { font-size: 0.74rem; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: #475569; }

  .dials { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; align-items: end; }
  .dial label { display: block; font-size: 0.78rem; font-weight: 800; margin-bottom: 2px; }
  .dial small { display: block; color: #64748b; font-size: 0.72rem; margin-bottom: 7px; line-height: 1.35; min-height: 2.4em; }
  .dial input[type=range] { width: 100%; accent-color: #c9973a; }
  .dv { font-weight: 800; color: #0b1f3a; }
  .who { margin-top: 10px; font-size: 0.78rem; color: #64748b; }
  .who b { color: #0b1f3a; }

  .scores { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .score { border-radius: 12px; padding: 16px 18px; text-align: center; border: 1.5px solid; }
  .score .big { font-size: 2.6rem; font-weight: 800; line-height: 1; }
  .score .cap { font-size: 0.8rem; font-weight: 700; margin-top: 6px; }
  .score.seen { background: #eef4fc; border-color: #c9daf6; }
  .score.seen .big { color: #1d4ed8; }
  .score.unseen { background: #fdf8e9; border-color: #f1e4b8; }
  .score.unseen .big { color: #8a6412; }
  .score.unseen.bad { background: #fde8e8; border-color: #f5caca; }
  .score.unseen.bad .big { color: #B91C1C; }

  .verdict { padding: 12px 16px; border-radius: 10px; background: #e4eefb; font-size: 0.9rem;
             font-weight: 700; line-height: 1.5; min-height: 3.1rem; }
  .verdict.bad { background: #fde8e8; color: #7f1d1d; }
  .verdict.good { background: #e3f4e8; color: #14532d; }

  .tree { overflow-x: auto; padding-top: 4px; }
  .lv { display: flex; justify-content: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
  .nd { border-radius: 8px; padding: 5px 10px; font-size: 0.74rem; font-weight: 700; border: 1px solid;
        background: #e4eefb; border-color: #c9daf6; white-space: nowrap; }
  .nd.leaf { background: #f7f9fc; border-color: #e3e8f0; font-weight: 800; }
  .nd.leaf.c { background: #fde8e8; border-color: #f5caca; color: #B91C1C; }
  .nd.leaf.s { background: #e3f4e8; border-color: #c5e6d0; color: #1B7A47; }
  .nd small { font-weight: 500; color: #475569; }
  .pruned { opacity: .28; text-decoration: line-through; }
</style>
</head>
<body>
<div class="wrap">

  <div class="card">
    <div class="ttl" style="margin-bottom:10px">Four dials. None of them are the algorithm's.</div>
    <div class="dials">
      <div class="dial">
        <label>Max depth: <span class="dv" id="vD">1</span></label>
        <small>How many questions deep it may go.</small>
        <input type="range" id="d" min="1" max="6" step="1" value="1">
      </div>
      <div class="dial">
        <label>Min customers in a group: <span class="dv" id="vM">1</span></label>
        <small>Refuse to split a group smaller than this.</small>
        <input type="range" id="m" min="1" max="5" step="1" value="1">
      </div>
      <div class="dial">
        <label>Min worthwhile gain: <span class="dv" id="vG">0.00</span></label>
        <small>Ignore a split that barely helps. Past 0.20 it refuses to ask anything at all.</small>
        <input type="range" id="g" min="0" max="0.25" step="0.05" value="0">
      </div>
      <div class="dial">
        <label>Prune after growing</label>
        <small>Grow it fully, then cut it back using 3-fold cross-validation.</small>
        <input type="checkbox" id="p" style="width:auto;transform:scale(1.3);margin-top:4px">
      </div>
    </div>
    <div class="who">Every one of these is a number <b>a person typed in</b>. The algorithm chose none of them.</div>
  </div>

  <div class="scores">
    <div class="score seen"><div class="big" id="aTrain">&ndash;</div>
      <div class="cap">on 12 customers it learned from</div></div>
    <div class="score unseen" id="boxTest"><div class="big" id="aTest">&ndash;</div>
      <div class="cap">on 4 customers it has never seen</div></div>
  </div>

  <div class="verdict" id="verdict"></div>

  <div class="card">
    <div class="ttl" style="margin-bottom:8px">The tree it built <span id="leafN" style="font-weight:500;text-transform:none;letter-spacing:0"></span></div>
    <div class="tree" id="tree"></div>
  </div>

</div>

<script>
(function () {
  var TRAIN = __TRAIN__, TEST = __TEST__;
  var KEYS = [["complaints","Complaints"],["age","Age"],["tenure","Tenure"],["bill","Bill"]];
  var el = function (id) { return document.getElementById(id); };

  function H(rows) {
    if (!rows.length) return 0;
    var p = rows.filter(function (r) { return r.churned; }).length / rows.length;
    if (p === 0 || p === 1) return 0;
    return -p * Math.log2(p) - (1 - p) * Math.log2(1 - p);
  }
  function majority(rows) {
    var c = rows.filter(function (r) { return r.churned; }).length;
    return c * 2 >= rows.length;
  }

  // Greedy: try every midpoint of every feature, keep the split that drops
  // entropy the most. Same rule as the split finder, applied over and over.
  function grow(rows, depth, maxD, minLeaf, minGain) {
    if (depth >= maxD || rows.length < 2 * minLeaf || H(rows) === 0) {
      return { leaf: true, says: majority(rows), rows: rows };
    }
    var best = null, h = H(rows);
    KEYS.forEach(function (kv) {
      var k = kv[0];
      var vals = rows.map(function (r) { return r[k]; }).sort(function (a, b) { return a - b; });
      for (var i = 0; i < vals.length - 1; i++) {
        if (vals[i] === vals[i + 1]) continue;
        var t = (vals[i] + vals[i + 1]) / 2;
        var L = rows.filter(function (r) { return r[k] < t; });
        var R = rows.filter(function (r) { return r[k] >= t; });
        if (L.length < minLeaf || R.length < minLeaf) continue;
        var gain = h - (L.length * H(L) + R.length * H(R)) / rows.length;
        if (!best || gain > best.gain) best = { gain: gain, k: k, name: kv[1], t: t, L: L, R: R };
      }
    });
    if (!best || best.gain <= minGain) return { leaf: true, says: majority(rows), rows: rows };
    return {
      leaf: false, k: best.k, name: best.name, t: best.t, rows: rows,
      yes: grow(best.L, depth + 1, maxD, minLeaf, minGain),
      no:  grow(best.R, depth + 1, maxD, minLeaf, minGain)
    };
  }

  function predict(node, r) {
    while (!node.leaf) node = (r[node.k] < node.t) ? node.yes : node.no;
    return node.says;
  }
  function acc(node, rows) {
    var ok = rows.filter(function (r) { return predict(node, r) === r.churned; }).length;
    return ok / rows.length;
  }

  // Pruning is selected without looking at TEST. Three folds of TRAIN choose
  // how far the fully grown tree should be kept; TEST remains untouched.
  function cvAccuracy(depth, minLeaf, minGain) {
    var total = 0, count = 0;
    for (var f = 0; f < 3; f++) {
      var val = TRAIN.filter(function (r, i) { return i % 3 === f; });
      var fit = TRAIN.filter(function (r, i) { return i % 3 !== f; });
      var t = grow(fit, 0, depth, minLeaf, minGain);
      total += acc(t, val); count++;
    }
    return count ? total / count : 0;
  }
  function bestPruneDepth(maxD, minLeaf, minGain) {
    var chosen = 1, best = -1;
    for (var depth = 1; depth <= maxD; depth++) {
      var score = cvAccuracy(depth, minLeaf, minGain);
      if (score > best) { best = score; chosen = depth; }
    }
    return chosen;
  }
  function cutBack(node, depth, keepDepth) {
    if (node.leaf) return node;
    if (depth >= keepDepth) {
      return { leaf: true, says: majority(node.rows), rows: node.rows, wasPruned: true };
    }
    node.yes = cutBack(node.yes, depth + 1, keepDepth);
    node.no = cutBack(node.no, depth + 1, keepDepth);
    return node;
  }
  var ROOT = null;
  function reaches(from, target, r) {
    var n = from;
    while (n && !n.leaf) { if (n === target) return true; n = (r[n.k] < n.t) ? n.yes : n.no; }
    return n === target;
  }

  function money(k, t) { return k === "bill" ? "鈧�" + Math.round(t) : Math.round(t * 10) / 10; }

  function draw(root) {
    var levels = [], leaves = 0;
    (function walk(n, d) {
      (levels[d] = levels[d] || []).push(n);
      if (n.leaf) { leaves++; return; }
      walk(n.yes, d + 1); walk(n.no, d + 1);
    })(root, 0);
    el("leafN").textContent = "鈥� " + leaves + (leaves === 1 ? " group" : " groups") + " at the bottom";
    el("tree").innerHTML = levels.map(function (row) {
      return "<div class='lv'>" + row.map(function (n) {
        if (!n.leaf) {
          return "<span class='nd'>" + n.name + " &lt; " + money(n.k, n.t) +
                 "<small> &nbsp;(" + n.rows.length + ")</small></span>";
        }
        var c = n.rows.filter(function (r) { return r.churned; }).length;
        return "<span class='nd leaf " + (n.says ? "c" : "s") + (n.wasPruned ? " pruned" : "") + "'>" +
               (n.says ? "Churn" : "Stay") + "<small> &nbsp;" + c + "/" + (n.rows.length - c) + "</small></span>";
      }).join("") + "</div>";
    }).join("");
  }

  function run() {
    var d = +el("d").value, m = +el("m").value, g = +el("g").value, doPrune = el("p").checked;
    el("vD").textContent = d; el("vM").textContent = m; el("vG").textContent = g.toFixed(2);

    var tree = grow(TRAIN, 0, d, m, g);
    ROOT = tree;
    if (doPrune) tree = cutBack(tree, 0, bestPruneDepth(d, m, g));

    var aTr = acc(tree, TRAIN), aTe = acc(tree, TEST);
    el("aTrain").textContent = Math.round(aTr * 100) + "%";
    el("aTest").textContent  = Math.round(aTe * 100) + "%";
    el("boxTest").classList.toggle("bad", aTe < 0.6);

    var v = el("verdict"), gap = aTr - aTe;
    v.className = "verdict" + (gap >= 0.3 ? " bad" : (gap <= 0.1 && aTe >= 0.7 ? " good" : ""));
    if (gap >= 0.3) {
      v.textContent = "It is near perfect on the customers it learned from and falling apart on the ones it has not. "
        + "Nothing warned you: the left number went up the whole way.";
    } else if (aTr <= 0.78 && d === 1) {
      v.textContent = "One question. It is the same on both sets, which is what you want to see. "
        + "Now push the depth up and watch the two numbers come apart.";
    } else if (tree.leaf) {
      v.className = "verdict bad";
      v.textContent = "You set the bar so high it would not ask a single question. Every customer gets the same "
        + "answer, which is the sticky note from this morning. Dials have a bad end in both directions.";
    } else if (doPrune) {
      v.textContent = "Pruned. The full tree was grown first, then cross-validation selected a simpler depth. The four held-out customers were not used to make that choice.";
    } else {
      v.textContent = "Still roughly honest. Keep going.";
    }
    draw(tree);
    if (typeof fit === "function") fit();
  }

  ["d", "m", "g"].forEach(function (id) { el(id).addEventListener("input", run); });
  el("p").addEventListener("change", run);

  // ---------- sizing: same approach as the split finder ----------
  // Measure the Streamlit panel we sit inside and pin the iframe to it, so the
  // card does not get clipped or leave dead space under it.
  function pinTop() {
    var frame = window.frameElement;
    var body = frame && frame.closest(".st-key-dtx_body");
    if (!body) return;
    if (!body.__dtPinned) { body.__dtPinned = true; body.addEventListener("scroll", pinTop); }
    var shown = frame.getBoundingClientRect().width > 0;
    var panel = frame.closest(".st-key-lesson_block");
    for (var n = frame.parentElement; n && n !== panel; n = n.parentElement) {
      if (shown) {
        var ov = getComputedStyle(n).overflowY;
        if (ov === "auto" || ov === "scroll") n.__dtLocked = true;
        if (n.__dtLocked) { n.style.setProperty("overflow", "hidden", "important"); n.scrollTop = 0; }
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
    // This card is content-sized, so measure what it actually needs and ask
    // for that, capped by whatever room the panel has.
    var want = wrap.offsetHeight + 10;
    var panel = frame.closest(".st-key-lesson_block");
    var fr = frame.getBoundingClientRect();
    if (panel && fr.width > 0) {
      var room = Math.floor(panel.getBoundingClientRect().bottom - fr.top - 28);
      if (room > 260) want = Math.min(want, room);
    }
    var h = Math.max(460, want);
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

  run();
  fit();
})();
</script>
</body>
</html>
"""
