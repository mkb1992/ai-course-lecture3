from __future__ import annotations

import re
from html import escape

import numpy as np
import streamlit as st

MODEL_NAME = "bert-base-uncased"

SMALL = {
    "a", "an", "the", "on", "of", "at", "in", "to", "by", "for", "with", "from", "and", "or", "but", "is", "was",
    "are", "were", "be", "been", "am", "i", "we", "you", "me", "us", "him", "her", "them", "my", "our", "your",
    "his", "their", "its", "had", "has", "have", "do", "did", "does", "this", "that", "because", "too", "so",
    "very", "can", "could", "will", "would", "as", "than", "then", "just",
}

EXAMPLES = (
    "We sat on the river bank",
    "The bank approved my loan",
    "The bank on the river bank got robbed",
    "The trophy did not fit in the suitcase because it was too big",
    "The trophy did not fit in the suitcase because it was too small",
)

@st.cache_resource(show_spinner=False)
def _model():
    from transformers import AutoModel, AutoTokenizer, logging

    logging.set_verbosity_error()
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME, output_attentions=True, attn_implementation="eager").eval()
    return tok, model


@st.cache_data(show_spinner=False, max_entries=300)
def _read(sentence: str) -> tuple[list[str], np.ndarray, np.ndarray]:
    import torch

    tok, model = _model()
    enc = tok(sentence, return_tensors="pt", truncation=True, max_length=64)
    with torch.no_grad():
        out = model(**enc)
    word_ids = enc.word_ids()
    n = max(w for w in word_ids if w is not None) + 1
    words = []
    for w in range(n):
        span = enc.word_to_chars(w)
        words.append(sentence[span.start:span.end])
    pieces = np.zeros((n, len(word_ids)))
    for t, w in enumerate(word_ids):
        if w is not None:
            pieces[w, t] = 1.0
    mean_rows = pieces / pieces.sum(axis=1, keepdims=True)
    att = torch.stack(out.attentions)[:, 0].mean(dim=(0, 1)).numpy()
    word_att = mean_rows @ att @ pieces.T
    word_vec = mean_rows @ out.last_hidden_state[0].numpy()
    return words, word_att, word_vec


def _load(sentences: list[str]) -> list[tuple[list[str], np.ndarray, np.ndarray]] | None:
    try:
        with st.spinner("Reading with BERT... the first time, the model takes about a minute to load."):
            return [_read(s) for s in sentences]
    except Exception as exc:
        st.error(f"BERT could not read the sentence – {type(exc).__name__}: {exc}")
        return None


def _is_punct(word: str) -> bool:
    return re.fullmatch(r"\W+", word) is not None


def _set_sentence(text: str) -> None:
    st.session_state.att_sentence = text


def _bars(words: list[str], weights: dict[int, float]) -> str:
    order = sorted(weights, key=lambda j: -weights[j])[:10]
    return "".join(
        f'<div class="att-row"><span class="w">{escape(words[j])}</span>'
        f'<span class="bar"><i style="width:{100 * weights[j]:.0f}%"></i></span>'
        f'<span class="p">{100 * weights[j]:.0f}%</span></div>'
        for j in order
    )


def _live(
    words: list[str],
    word_att: np.ndarray,
    *,
    scope: str = "",
) -> tuple[str, str] | None:
    active = [j for j, w in enumerate(words) if not _is_punct(w) and w.lower() not in SMALL]
    if len(active) < 2:
        return None
    lower = [w.lower() for w in words]
    default = next((lower.index(w) for w in ("bank", "it") if w in lower), active[-1])
    if default not in active:
        default = active[-1]

    weights: dict[int, dict[int, float]] = {}
    for i in active:
        raw = {j: float(word_att[i, j]) for j in active if j != i}
        total = sum(raw.values()) or 1.0
        weights[i] = {j: v / total for j, v in raw.items()}

    host = f".{scope}.att-live" if scope else ".att-live"
    rules = []
    for i in active:
        prefixes = [f"{host}:has(.hw{i}:hover)"]
        if i == default:
            prefixes.append(f"{host}:not(:has(.hw:hover))")

        def rule(suffix: str, body: str) -> None:
            rules.append(", ".join(p + suffix for p in prefixes) + " { " + body + " }")

        rule(f" .hw{i}", "background: #0b1f3a; color: #ffffff;")
        rule(f" .ap{i}", "display: block;")
        top = max(weights[i].values()) or 1.0
        for j, v in weights[i].items():
            rule(f" .hw{j}", f"background: rgba(201, 151, 58, {0.10 + 0.80 * v / top:.2f});")
            rule(f" .hw{j} .s{i}", "display: block;")

    parts = []
    for j, w in enumerate(words):
        if j in active:
            labels = "".join(
                f'<em class="s{i}">{100 * weights[i][j]:.0f}%</em>' for i in active if i != j
            )
            token = f'<span class="hw hw{j}">{escape(w)}{labels}</span>'
        else:
            token = f'<span class="sm">{escape(w)}</span>'
        if parts and _is_punct(w):
            parts[-1] += token
        else:
            parts.append(token)

    def title(i: int) -> str:
        if lower.count(lower[i]) < 2:
            return f"<b>{escape(words[i])}</b>"
        nth = lower[: i + 1].count(lower[i])
        return f"<b>{escape(words[i])}</b> ({nth}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(nth, 'th') })"

    panels = "".join(
        f'<div class="att-panel ap{i}"><div class="att-q">Where {title(i)} looks</div>'
        f'<div class="att-rows">{_bars(words, weights[i])}</div></div>'
        for i in active
    )
    cls = f"att-live {scope}" if scope else "att-live"
    return (
        f"<style>{' '.join(rules)}</style>",
        f'<div class="{cls}"><div class="att-words">{" ".join(parts)}</div>{panels}</div>',
    )


def _lesson() -> str:
    return """
        <section class="cmx-card dtx-card w2x" aria-labelledby="att-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Before we move on</div>
          <h2 id="att-title">What is still missing &ndash; and how <span class="att-red">Attention</span> fixes it</h2>
          <p class="dtx-lead">You have counted words with <b>Bag of Words</b>, seen how <b>Word2Vec</b> learns a vector
          for every word, trained your own model in Exercise 1 and done arithmetic with word vectors in Exercise 2.
          Word2Vec learns meaning from context &ndash; <i>cancelled</i> and <i>called off</i> become neighbours, and
          <i>king &minus; man + woman</i> lands near <i>queen</i>. But two gaps are still open.</p>

          <h3>Two gaps word vectors cannot close</h3>
          <div class="att-gaps">
            <div class="gc"><span class="att-tag">Gap 1</span><b>One fixed vector per word</b>
              <small><i>bank</i> gets exactly the same vector in <i>We sat on the river bank</i> and in <i>The bank
              approved my loan</i> &ndash; a blend of both meanings. Meaning depends on the sentence, and a lookup table
              of word vectors has no way to know the sentence.</small></div>
            <div class="gc"><span class="att-tag">Gap 2</span><b>Nothing says which word points to which</b>
              <small><i>The trophy did not fit in the suitcase because it was too big.</i> Does <i>it</i> mean the
              trophy or the suitcase? Change <i>big</i> to <i>small</i> and the answer flips. The two sentences differ
              by one word, so no amount of better word vectors solves this &ndash; the answer lives in the sentence,
              not in any single word.</small></div>
          </div>

          <h3>Where Word2Vec stands today</h3>
          <p class="dtx-lead">Modern <b>transformer</b> models, the technology behind tools like ChatGPT, close these
          gaps with one idea &ndash; <b>attention</b> &ndash; and have replaced fixed word vectors for most tasks. So
          Word2Vec is <b>foundational intuition, not today&rsquo;s state of the art</b>. It is still the cleanest way to
          see how meaning can emerge from predicting words from their context.</p>

          <h3>The idea in one line</h3>
          <p class="dtx-lead">Before deciding what a word means, <b>look at the other words in the sentence</b>. You do
          this without thinking &ndash; when you read <i>We sat on the river bank</i>, the word <i>river</i> tells you
          which <i>bank</i> it is. Attention lets a model do the same.</p>

          <h3>How attention works</h3>
          <ol class="w2x-steps">
            <li><b class="t">Start from a place per word</b>
            Every word begins with a vector, just like Word2Vec &ndash; <i>bank</i> starts at its one blended point.</li>
            <li><b class="t">Every word looks at every other word</b>
            Each word gives every other word in the sentence a score &ndash; how much does that word matter to me? The
            scores are turned into weights that add up to 100%. These weights are the <b>attention</b>.</li>
            <li><b class="t">Take a weighted blend</b>
            The word&rsquo;s new vector is a blend of the other words, mixed by those weights. So its vector is
            <b>no longer fixed</b> &ndash; it depends on the sentence it is in. A real model repeats these steps many
            times, and each round sharpens the blend.</li>
          </ol>

          <div class="w2x-note"><b>The model used here</b> &ndash; <b>Bidirectional Encoder Representations from Transformers
          (BERT)</b>, Google&rsquo;s open transformer. It runs
          inside this app, so unlike the OpenAI models in the rest of the lecture, we can look inside it and read its
          <b>real attention</b>. What the lab shows is cleaned up so the pattern is easy to read &ndash;
          <ul class="w2x-list">
            <li><b>Averaged</b> &ndash; BERT has 12 layers with 12 attention heads each, which is 144 separate patterns.
            The lab shows their average, not any single one.</li>
            <li><b>Filtered and rescaled</b> &ndash; BERT&rsquo;s hidden start and end markers and punctuation are
            dropped. Small words like <i>the</i> and <i>a</i> are removed too, and the remaining shares are rescaled to
            add up to 100%. In the raw numbers those small words take a large share.</li>
            <li><b>Words joined up</b> &ndash; when BERT splits a word into pieces, the pieces are merged back into the
            whole word.</li>
          </ul></div>
        </section>
    """


def _render_lab() -> None:
    state = st.session_state
    state.setdefault("att_sentence", EXAMPLES[0])
    st.html(
        '<div class="att-head"><span class="att-tag">Lab</span>See where a word looks</div>'
        '<p class="se-hint">Type any sentence and press Enter. BERT reads it, then <b>hover over any word</b> to see '
        "where it looks &ndash; the other words light up, and the number above each one is its share of the "
        "attention. The shares add up to 100%.</p>"
    )
    sentence = st.text_input(
        "Sentence",
        key="att_sentence",
        placeholder="Type a sentence and press Enter",
        label_visibility="collapsed",
    ).strip()
    with st.container(key="att_examples", horizontal=True, gap="small", vertical_alignment="center"):
        st.html('<span class="att-exlabel">Try an example</span>', width="content")
        for text in EXAMPLES:
            st.button(text, key=f"att_ex_{text}", width="content", on_click=_set_sentence, args=(text,))
    if not sentence:
        return
    read = _load([sentence])
    if read is None:
        return
    words, word_att, _ = read[0]
    live = _live(words, word_att)
    if live is None:
        st.info("Type a sentence with at least two words that carry meaning.")
        return
    style, markup = live
    st.html(style)
    st.html(
        markup
        + '<p class="se-cap">Small words such as <i>the</i>, <i>a</i> and <i>was</i> are greyed out and left out of '
        "the shares &ndash; real models park a large share of attention on them, which hides the interesting "
        "part.</p>"
    )


def _closing() -> str:
    return """
        <section class="cmx-card dtx-card w2x att-after" aria-labelledby="att-close-title">
          <div class="cmx-kicker">What the lab shows</div>
          <h2 id="att-close-title">This is how a transformer reads</h2>
          <p class="dtx-lead">The percentages you hovered over are the weights from step 2 of <b>How attention
          works</b>. Each word&rsquo;s new vector is the blend from step 3, mixed by exactly those shares. That is
          attention, and every transformer reads text this way &ndash; from BERT to the models behind ChatGPT.</p>
          <ul class="w2x-list">
            <li><b><i>bank</i> follows its sentence</b> &ndash; hover over <i>bank</i> in the first two examples. It
            looks at <i>river</i> in one and at <i>approved</i> and <i>loan</i> in the other. Its new vector is blended
            from different words, so it is different in every sentence.</li>
            <li><b>Even inside one sentence</b> &ndash; in <i>The bank on the river bank got robbed</i>, hover over each
            <i>bank</i>. The first looks most at <i>robbed</i> &ndash; the bank with money in it. The second looks most
            at <i>river</i> &ndash; the riverside. Same word, same sentence, two different vectors.</li>
            <li><b><i>it</i> looks for what it points to</b> &ndash; hover over <i>it</i> in the example ending in <i>too big</i>. Most of
            its attention goes to <i>big</i>, <i>trophy</i> and <i>suitcase</i> &ndash; exactly the words that decide
            the answer &ndash; and <i>trophy</i> gets more than <i>suitcase</i>, which is right.</li>
            <li><b>But it does not flip</b> &ndash; now try the example ending in <i>too small</i>. The answer should be
            the suitcase, yet <i>it</i> still gives <i>trophy</i> more attention than <i>suitcase</i> &ndash; about 28%
            against 20%. <i>it</i> is looking at the right words, but BERT has not learned which one to pick here.</li>
          </ul>

          <h3>Not yet the state of the art</h3>
          <p class="dtx-lead">That last result is one example of why BERT is not the state of the art. What you see is <b>one
          picture</b> &ndash; the average of all of BERT&rsquo;s rounds of attention squeezed together. BERT itself is
          from 2018 and small by today&rsquo;s standards &ndash; about 110 million learned numbers and 12 rounds of
          attention. The models behind ChatGPT stack many more rounds, with billions of numbers and far more text, so
          each word can keep refining what it has picked up &ndash; and they usually get the <i>small</i> version
          right.</p>
          <p class="dtx-lead">So do not expect such a neat picture for every sentence you type. With a model the size
          of BERT, attention is often spread out or points somewhere unexpected &ndash; the examples above are among its
          clearer cases.</p>

          <div class="w2x-note w2x-next"><b>Next &ndash; Sentence Embeddings</b> &ndash; in the <b>Topic</b> menu, pick
          <b>Sentence Embeddings</b>. Attention has given every word a vector that fits its sentence. There a much
          larger model goes one step further and turns a <b>whole sentence</b> into one vector, so that sentences can be
          compared, grouped and searched by meaning &ndash; and in its exercise you put the trophy sentences to the
          test again.</div>
        </section>
    """


def render() -> None:
    st.html(_lesson())
    with st.container(key="att_lab"):
        _render_lab()
    st.html(_closing())
