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
