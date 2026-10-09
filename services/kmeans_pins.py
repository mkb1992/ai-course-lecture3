"""
K-means, the whole algorithm: drop the pins, walk, move, repeat.

A Streamlit teaching module in three beats, matching the Session 3 slide:
  1. Walk to the pins   - step through the algorithm one click at a time, or watch it run
  2. You chose k        - the Sorting Hat had four houses because somebody wrote four down
  3. Where the pins start - two random starts, two different answers, both valid

Run on its own:      streamlit run kmeans_pins.py
Inside another app:  from kmeans_pins import render;  render()

Needs only: streamlit, numpy, plotly.
"""

from itertools import permutations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Settings you may want to change
# ---------------------------------------------------------------------------
N_PEOPLE = 55              # dots in the room
ROOM_SEED = 3              # which "room" of people (changes where everyone stands)
DEFAULT_K = 4
DEFAULT_PIN_SEED = 2       # beat 1: a start that takes several rounds, so there is something to watch
BEAT3_SEEDS = (1, 7)       # beat 3: two starts that land on clearly different answers

# One colour per pin, in fixed order (never cycled)
PIN_COLOURS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
               "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
UNASSIGNED = "#b9b8b0"
INK = "#5f5e5a"


# ---------------------------------------------------------------------------
# The data: people standing in a room
# ---------------------------------------------------------------------------
@st.cache_data
def make_room(n=N_PEOPLE, seed=ROOM_SEED):
    """Five loose crowds in a 10 x 10 room. Loose on purpose: real people are not tidy."""
    rng = np.random.default_rng(seed)
    centres = np.array([[2.2, 7.6], [7.8, 7.9], [2.5, 2.4], [7.4, 2.6], [5.0, 5.2]])
    sizes = np.full(len(centres), n // len(centres))
    sizes[: n - sizes.sum()] += 1
    pts = np.vstack([rng.normal(c, 1.05, (s, 2)) for c, s in zip(centres, sizes)])
    return np.clip(pts, 0.3, 9.7)


# ---------------------------------------------------------------------------
# The algorithm, recorded step by step
# ---------------------------------------------------------------------------
def nearest(X, C):
    return ((X[:, None, :] - C[None, :, :]) ** 2).sum(axis=2).argmin(axis=1)


def walking_distance(X, C, labels):
    return float(np.sqrt(((X - C[labels]) ** 2).sum(axis=1)).sum())


@st.cache_data
def run_history(k, pin_seed, n=N_PEOPLE, room_seed=ROOM_SEED, max_rounds=40):
    """Every state the algorithm passes through.

    Each step is a dict: phase ('drop', 'walk', 'move', 'done'), round number,
    pin positions, who stands at which pin, how many switched, and the previous
    pin positions (for the arrows on a 'move').
    """
    X = make_room(n, room_seed)
    rng = np.random.default_rng(pin_seed)
    C = rng.uniform(0.6, 9.4, (k, 2))              # drop k pins anywhere
    steps = [dict(phase="drop", round=0, C=C.copy(), labels=None, switched=None, prev_C=None)]
    labels = None
    for r in range(1, max_rounds + 1):
        new = nearest(X, C)                          # everyone walks to the nearest pin
        switched = len(X) if labels is None else int((new != labels).sum())
        changed = None if labels is None else (new != labels)
        labels = new
        if r > 1 and switched == 0:
            steps.append(dict(phase="done", round=r, C=C.copy(), labels=labels.copy(), switched=0, prev_C=None))
            break
        steps.append(dict(phase="walk", round=r, C=C.copy(), labels=labels.copy(), switched=switched, prev_C=None,
                          ringed=None if r == 1 else changed))
        prev = C.copy()
        for j in range(k):                           # each pin moves to the middle of its crowd
            if (labels == j).any():
                C[j] = X[labels == j].mean(axis=0)
        steps.append(dict(phase="move", round=r, C=C.copy(), labels=labels.copy(), switched=None, prev_C=prev,
                          ringed=nearest(X, C) != labels))   # now closer to a different pin
    return steps


def final_state(k, pin_seed):
    return run_history(k, pin_seed)[-1]


def kept_together(a, b):
    """Share of pairs who share a pin in run a and still share one in run b."""
    same_a = a[:, None] == a[None, :]
    same_b = b[:, None] == b[None, :]
    off = ~np.eye(len(a), dtype=bool)
    return (same_a & same_b & off).sum() / (same_a & off).sum()


def match_colours(ref, other, k):
    """Relabel `other` so its groups get the colour of the `ref` group they overlap most."""
    overlap = np.zeros((k, k), dtype=int)
    for i, j in zip(ref, other):
        overlap[i, j] += 1
    if k <= 7:
        best = max(permutations(range(k)), key=lambda p: sum(overlap[p[j], j] for j in range(k)))
        mapping = {j: best[j] for j in range(k)}
    else:
        mapping, used = {}, set()
        for j in np.argsort(-overlap.max(axis=0)):
            choice = next(i for i in np.argsort(-overlap[:, j]) if i not in used)
            mapping[j] = choice
            used.add(choice)
    return np.array([mapping[j] for j in other]), mapping


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------
def base_layout(fig, height=520):
    fig.update_layout(
        height=height, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 10], visible=False, fixedrange=True),
        yaxis=dict(range=[0, 10], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1),
        hovermode="closest",
    )
    # the room's walls
    fig.add_shape(type="rect", x0=0, y0=0, x1=10, y1=10,
                  line=dict(color="#d3d1c7", width=1.5), fillcolor="rgba(0,0,0,0)", layer="below")
    return fig


def people_trace(X, labels, colour_map=None):
    if labels is None:
        colours = [UNASSIGNED] * len(X)
        hover = ["Not at a pin yet"] * len(X)
    else:
        lab = labels if colour_map is None else colour_map
        colours = [PIN_COLOURS[i % len(PIN_COLOURS)] for i in lab]
        hover = [f"At pin {i + 1}" for i in lab]
    return go.Scatter(x=X[:, 0], y=X[:, 1], mode="markers",
                      marker=dict(size=13, color=colours, line=dict(color="white", width=1.5)),
                      text=hover, hovertemplate="%{text}<extra></extra>", name="people")


def pins_trace(C, colour_ids=None):
    ids = list(range(len(C))) if colour_ids is None else colour_ids
    return go.Scatter(x=C[:, 0], y=C[:, 1], mode="markers+text",
                      marker=dict(symbol="diamond", size=30, color=[PIN_COLOURS[i % 8] for i in ids],
                                  line=dict(color="#1a1a19", width=2.5)),
                      text=[str(i + 1) for i in ids], textfont=dict(color="white", size=12),
                      hovertemplate="Pin %{text}<extra></extra>", name="pins")


def lines_trace(X, C, labels):
    xs, ys = [], []
    for p, l in zip(X, labels):
        xs += [p[0], C[l][0], None]
        ys += [p[1], C[l][1], None]
    return go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="rgba(95,94,90,0.25)", width=1),
                      hoverinfo="skip", name="walks")


def state_figure(X, step, show_lines=True, height=520):
    fig = go.Figure()
    base_layout(fig, height)
    if step["labels"] is not None and show_lines and step["phase"] != "move":
        fig.add_trace(lines_trace(X, step["C"], step["labels"]))
    fig.add_trace(people_trace(X, step["labels"]))
    ring = step.get("ringed")
    if ring is not None and ring.any():
        fig.add_trace(go.Scatter(x=X[ring, 0], y=X[ring, 1], mode="markers",
                                 marker=dict(symbol="circle-open", size=24, color="#1a1a19",
                                             line=dict(width=2.5)),
                                 hoverinfo="skip", name="ringed"))
    if step["phase"] == "move" and step["prev_C"] is not None:
        # ghost of where each pin was, plus an arrow to where it went
        fig.add_trace(go.Scatter(x=step["prev_C"][:, 0], y=step["prev_C"][:, 1], mode="markers",
                                 marker=dict(symbol="diamond-open", size=26,
                                             color=[PIN_COLOURS[i] for i in range(len(step["C"]))],
                                             line=dict(width=2)),
                                 hoverinfo="skip"))
        for j, (a, b) in enumerate(zip(step["prev_C"], step["C"])):
            if np.hypot(*(b - a)) > 0.05:
                fig.add_annotation(x=b[0], y=b[1], ax=a[0], ay=a[1], xref="x", yref="y", axref="x", ayref="y",
                                   showarrow=True, arrowhead=3, arrowsize=1.4, arrowwidth=2.5,
                                   arrowcolor=PIN_COLOURS[j], text="")
    fig.add_trace(pins_trace(step["C"]))
    return fig


def animated_figure(X, steps, height=520):
    """The whole run as a Plotly animation, with its own play button."""
    def frame_data(s):
        labels = s["labels"]
        lines = lines_trace(X, s["C"], labels) if labels is not None else go.Scatter(x=[], y=[], mode="lines")
        return [lines, people_trace(X, labels), pins_trace(s["C"])]

    def caption(s):
        if s["phase"] == "drop":
            return "Pins dropped anywhere"
        if s["phase"] == "walk":
            return f"Round {s['round']}: everyone walks to the nearest pin ({s['switched']} moved)"
        if s["phase"] == "move":
            return f"Round {s['round']}: each pin moves to the middle of its crowd"
        return "Nobody moved. Done."

    fig = go.Figure(data=frame_data(steps[0]),
                    frames=[go.Frame(data=frame_data(s), name=str(i),
                                     layout=dict(title=dict(text=caption(s))))
                            for i, s in enumerate(steps)])
    base_layout(fig, height)
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=60),
        title=dict(text=caption(steps[0]), x=0.01, font=dict(size=15, color=INK)),
        updatemenus=[dict(type="buttons", showactive=False, x=0.0, y=-0.02, xanchor="left", yanchor="top",
                          direction="left",
                          buttons=[dict(label="▶  Play", method="animate",
                                        args=[None, dict(frame=dict(duration=1100, redraw=True),
                                                         transition=dict(duration=600, easing="cubic-in-out"),
                                                         fromcurrent=True, mode="immediate")]),
                                   dict(label="❚❚  Pause", method="animate",
                                        args=[[None], dict(frame=dict(duration=0, redraw=False),
                                                           mode="immediate")])])],
        sliders=[dict(active=0, x=0.22, y=-0.02, len=0.78, xanchor="left", yanchor="top",
                      currentvalue=dict(visible=False), pad=dict(t=0),
                      steps=[dict(label=str(i), method="animate",
                                  args=[[str(i)], dict(frame=dict(duration=0, redraw=True),
                                                       transition=dict(duration=300), mode="immediate")])
                             for i in range(len(steps))])],
    )
    return fig


# ---------------------------------------------------------------------------
# The three beats
# ---------------------------------------------------------------------------
def beat_walk(X):
    st.markdown("#### Four pins. Everybody walks to the nearest one.")
    c1, c2, c3 = st.columns([1, 1, 2])
    k = c1.number_input("Pins (k)", 2, 8, DEFAULT_K, key="b1_k")
    seed = c2.number_input("Where the pins land (seed)", 0, 999, DEFAULT_PIN_SEED, key="b1_seed")
    show_lines = c3.toggle("Show who walks to which pin", value=True, key="b1_lines")

    steps = run_history(int(k), int(seed))
    key = f"b1_step_{k}_{seed}"
    if key not in st.session_state:
        st.session_state[key] = 0
    i = st.session_state[key]

    b1, b2, b3, b4 = st.columns(4)
    if b1.button("◀  Back", use_container_width=True, disabled=i == 0, key="b1_back"):
        st.session_state[key] = i = max(0, i - 1)
    if b2.button("Next step  ▶", type="primary", use_container_width=True,
                 disabled=i == len(steps) - 1, key="b1_next"):
        st.session_state[key] = i = min(len(steps) - 1, i + 1)
    if b3.button("Jump to the end", use_container_width=True, key="b1_end"):
        st.session_state[key] = i = len(steps) - 1
    if b4.button("Start again", use_container_width=True, key="b1_reset"):
        st.session_state[key] = i = 0

    s = steps[i]
    if s["phase"] == "drop":
        msg = f"**{k} pins, dropped anywhere.** Nobody has moved yet. Click *Next step*."
    elif s["phase"] == "walk" and s["round"] == 1:
        msg = "**Everybody walks to the nearest pin.** Each person takes the colour of their pin."
    elif s["phase"] == "walk":
        msg = (f"**Round {s['round']}. Walk again.** The pins moved, so some of you are now closer to a "
               f"different pin. **{s['switched']} {'person' if s['switched'] == 1 else 'people'} switched** (ringed).")
    elif s["phase"] == "move":
        n_ring = int(s["ringed"].sum())
        msg = ("**Each pin moves to the middle of its crowd.** The outline shows where it was. "
               + (f"**{n_ring} {'person is' if n_ring == 1 else 'people are'} now closer to a different pin** "
                  "(ringed). They will walk next." if n_ring else "Nobody is closer to a different pin now."))
    else:
        msg = (f"**Nobody moved. Done, after {s['round'] - 1} rounds.** "
               "That is the whole algorithm.")
    (st.success if s["phase"] == "done" else st.info)(msg)

    st.plotly_chart(state_figure(X, s, show_lines), use_container_width=True,
                    config={"displayModeBar": False}, key=f"b1_fig_{key}_{i}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Round", s["round"])
    m2.metric("People who switched pin", "-" if s["switched"] is None else s["switched"])
    m3.metric("Total walking distance",
              "-" if s["labels"] is None else f"{walking_distance(X, s['C'], s['labels']):.0f} m")

    with st.expander("Watch it run on its own"):
        st.plotly_chart(animated_figure(X, steps), use_container_width=True,
                        config={"displayModeBar": False}, key=f"b1_anim_{key}")


def beat_k(X):
    st.markdown("#### You chose k. The algorithm did not.")
    k = st.slider("How many pins?", 2, 8, DEFAULT_K, key="b2_k")
    s = final_state(int(k), DEFAULT_PIN_SEED)
    sizes = np.bincount(s["labels"], minlength=int(k))

    left, right = st.columns([3, 2])
    with left:
        st.plotly_chart(state_figure(X, s, show_lines=False, height=480), use_container_width=True,
                        config={"displayModeBar": False}, key=f"b2_fig_{k}")
    with right:
        st.markdown(f"### {k} groups")
        st.markdown("  \n".join(
            f"<span style='color:{PIN_COLOURS[j]}; font-size:1.3em'>◆</span> Pin {j + 1}: **{n}** people"
            for j, n in enumerate(sizes)), unsafe_allow_html=True)
        st.metric("Total walking distance", f"{walking_distance(X, s['C'], s['labels']):.0f} m")
        st.caption("More pins, less walking, every time. At 55 pins everyone stands on their own pin, "
                   "walks zero metres, and is their own segment.")
        st.warning("The Sorting Hat had four houses because somebody wrote four houses down. "
                   "The algorithm will happily give you any number you ask for.")


def beat_start(X):
    st.markdown("#### You chose where the pins started, or a random number did.")
    c1, c2, c3 = st.columns([1, 1, 1])
    k = c1.number_input("Pins (k)", 2, 8, DEFAULT_K, key="b3_k")
    if "b3_seeds" not in st.session_state:
        st.session_state.b3_seeds = list(BEAT3_SEEDS)
    if c3.button("🎲  Throw both sets of pins again", use_container_width=True, key="b3_throw"):
        st.session_state.b3_seeds = [int(x) for x in np.random.default_rng().integers(0, 1000, 2)]
    sa, sb = st.session_state.b3_seeds
    c2.markdown(f"<div style='padding-top:1.9rem;color:{INK}'>Run A seed <b>{sa}</b> · Run B seed <b>{sb}</b></div>",
                unsafe_allow_html=True)

    k = int(k)
    A, B = final_state(k, sa), final_state(k, sb)
    b_colours, mapping = match_colours(A["labels"], B["labels"], k)
    moved = int((b_colours != A["labels"]).sum())
    together = kept_together(A["labels"], B["labels"])

    def start_ghosts(fig, seed, ids):
        C0 = run_history(k, seed)[0]["C"]
        fig.add_trace(go.Scatter(x=C0[:, 0], y=C0[:, 1], mode="markers",
                                 marker=dict(symbol="diamond-open", size=22, color=[PIN_COLOURS[i] for i in ids],
                                             line=dict(width=2)),
                                 hovertemplate="Where this pin started<extra></extra>"))

    left, right = st.columns(2)
    with left:
        st.markdown("**Run A**")
        fa = go.Figure()
        base_layout(fa, 430)
        fa.add_trace(people_trace(X, A["labels"]))
        start_ghosts(fa, sa, list(range(k)))
        fa.add_trace(pins_trace(A["C"]))
        st.plotly_chart(fa, use_container_width=True, config={"displayModeBar": False}, key=f"b3_a_{k}_{sa}")
    with right:
        st.markdown("**Run B**")
        fig = go.Figure()
        base_layout(fig, 430)
        fig.add_trace(people_trace(X, B["labels"], colour_map=b_colours))
        start_ghosts(fig, sb, [mapping[j] for j in range(k)])
        fig.add_trace(pins_trace(B["C"], colour_ids=[mapping[j] for j in range(k)]))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False},
                        key=f"b3_b_{k}_{sb}")

    m1, m2 = st.columns(2)
    m1.metric("People who land in a different group", f"{moved} of {len(X)}")
    m2.metric("Pairs who stay together", f"{together:.0%}")
    if moved == 0:
        st.success("Same answer both times. Lucky throw. Click the dice and try again.")
    else:
        st.warning("Same people. Same k. Same algorithm. A different answer, and **both are valid**. "
                   "Neither run is wrong. A random number chose between them.")
    st.caption("Hollow diamonds show where each pin started. Colours in Run B are matched to the Run A group they overlap most, so a changed colour "
               "means that person really changed group.")


def render():
    st.html(
        """
        <div style="display:flex;align-items:center;gap:14px;padding:16px 20px;
                    border:1.5px solid #0b1f3a;border-radius:14px;background:
                    linear-gradient(135deg,#eef4fc 0%,#fffaf0 100%);margin-bottom:10px">
          <div style="font-size:2.2rem;line-height:1">📍</div>
          <div>
            <div style="font-size:1.35rem;font-weight:800;color:#0b1f3a">K-means clustering</div>
            <div style="font-size:.92rem;color:#475569;margin-top:3px">
              Drop the pins · walk to the nearest one · move each pin to the middle · repeat
            </div>
          </div>
        </div>
        """
    )
    st.markdown("## K-means, the whole algorithm")
    st.caption("Drop k pins anywhere · everyone walks to the nearest pin · each pin moves to the middle "
               "of its crowd · repeat until nobody moves")
    X = make_room()
    t1, t2, t3 = st.tabs(["1 · Walk to the pins", "2 · You chose k", "3 · Where the pins started"])
    with t1:
        beat_walk(X)
    with t2:
        beat_k(X)
    with t3:
        beat_start(X)


if __name__ == "__main__":
    st.set_page_config(page_title="K-means: drop the pins", page_icon="📍", layout="wide")
    render()

