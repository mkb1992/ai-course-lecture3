from __future__ import annotations

import re
import tempfile
from html import escape
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from openai import OpenAI

from services.keys import openai_api_key

MODEL = "text-embedding-3-large"
DIMS = 3072
MAX_SENTENCES = 12
SPLIT_THRESHOLD = 0.07
GROUP_FILL = ("rgba(201,151,58,0.10)", "rgba(201,74,26,0.10)")
GROUP_LINE = ("rgba(201,151,58,0.55)", "rgba(201,74,26,0.55)")
MISSING_KEY = (
    "OpenAI API key was not found. For offline use, put it in openAI API.txt. "
    "On Streamlit Cloud, add OPENAI_API_KEY in Secrets."
)

PALETTE = (
    "#0b1f3a", "#c9973a", "#c94a1a", "#1b7a47", "#3a6ea5", "#8a5a9e",
    "#9b7229", "#2e8b8b", "#b91c1c", "#5a6880", "#6b8e23", "#d4679a",
)

CLAUSES = (
    ("Ending the contract", "Either party may end this agreement by giving thirty days' written notice to the other."),
    ("Non-payment", "If the client fails to pay any invoice within sixty days, the supplier may stop all services and close the account."),
    ("Payment terms", "Invoices are payable within thirty days of receipt, and late payments attract interest of 1.5% per month."),
    ("Confidentiality", "Neither party shall disclose the other's business information to any third party without prior written consent."),
    ("Ownership of work", "All software, designs and documents created under this contract belong to the client."),
    ("Liability", "The supplier's total liability under this contract shall not exceed the fees paid in the previous twelve months."),
    ("Events outside control", "Neither party is responsible for delays caused by floods, earthquakes, war or government action."),
    ("Governing law", "This contract is governed by the laws of India, and disputes will be settled by arbitration in Mumbai."),
)

QUERIES = (
    "termination",
    "how do I get out of this contract",
    "can I tell anyone about this deal",
    "who owns the work we create",
    "what happens if we pay late",
)

_STOP = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "as", "at", "be",
    "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "could", "did", "do",
    "does", "doing", "down", "during", "each", "few", "for", "from", "further", "get", "got", "had", "has", "have",
    "having", "he", "her", "here", "hers", "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "just",
    "let", "me", "more", "most", "much", "must", "my", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "out", "over", "own", "same", "shall", "she", "should", "so", "some", "such",
    "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "those", "through", "to",
    "too", "under", "until", "up", "us", "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "will", "with", "would", "you", "your", "yours", "may", "might", "anyone", "anything",
    "someone", "something", "happen", "happens",
}
_SUFFIXES = (
    ("ations", ""), ("ation", ""), ("ments", ""), ("ment", ""), ("ings", ""), ("ing", ""), ("ness", ""),
    ("able", ""), ("ible", ""), ("ies", "y"), ("ied", "y"), ("ers", ""), ("er", ""), ("es", ""), ("ed", ""),
    ("ly", ""), ("s", ""),
)


@st.cache_data(show_spinner=False, max_entries=1024)
def _embed(text: str) -> list[float]:
    client = OpenAI(api_key=openai_api_key())
    return client.embeddings.create(model=MODEL, input=text).data[0].embedding


def _vectors(texts: list[str]) -> np.ndarray:
    matrix = np.array([_embed(t) for t in texts], dtype=np.float64)
    return matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12)


def _pca2(matrix: np.ndarray) -> np.ndarray:
    centred = matrix - matrix.mean(axis=0)
    _, _, vt = np.linalg.svd(centred, full_matrices=False)
    coords = centred @ vt[:2].T
    if coords.shape[1] < 2:
        coords = np.hstack([coords, np.zeros((len(coords), 2 - coords.shape[1]))])
    return coords


def _fit_kmeans(matrix: np.ndarray, n_iter: int = 100) -> np.ndarray:
    dists = np.linalg.norm(matrix[:, None] - matrix[None, :], axis=-1)
    i0, i1 = np.unravel_index(np.argmax(dists), dists.shape)
    centroids = matrix[[i0, i1]].copy()
    labels = np.zeros(len(matrix), dtype=int)
    for _ in range(n_iter):
        d0 = np.linalg.norm(matrix - centroids[0], axis=1)
        d1 = np.linalg.norm(matrix - centroids[1], axis=1)
        new_labels = (d1 < d0).astype(int)
        if np.array_equal(new_labels, labels):
            break
        labels = new_labels
        for k in range(2):
            mask = labels == k
            if mask.any():
                centroids[k] = matrix[mask].mean(axis=0)
    return labels


def _silhouette(matrix: np.ndarray, labels: np.ndarray) -> float:
    dists = np.linalg.norm(matrix[:, None] - matrix[None, :], axis=-1)
    scores = []
    for i in range(len(matrix)):
        same = labels == labels[i]
        other = ~same
        same[i] = False
        if same.sum() == 0 or other.sum() == 0:
            return -1.0
        a = dists[i, same].mean()
        b = dists[i, other].mean()
        scores.append((b - a) / max(a, b, 1e-12))
    return float(np.mean(scores))


def _groups(matrix: np.ndarray) -> tuple[np.ndarray, int]:
    n = len(matrix)
    if n < 3:
        return np.zeros(n, dtype=int), 1
    labels = _fit_kmeans(matrix)
    if _silhouette(matrix, labels) >= SPLIT_THRESHOLD:
        return labels, 2
    return np.zeros(n, dtype=int), 1


def _ellipse_xy(pts: np.ndarray, n_std: float = 2.2) -> tuple[np.ndarray, np.ndarray]:
    theta = np.linspace(0, 2 * np.pi, 90)
    circle = np.stack([np.cos(theta), np.sin(theta)])
    center = pts.mean(axis=0)
    if len(pts) == 1:
        r = 0.25
        return center[0] + r * circle[0], center[1] + r * circle[1]
    if len(pts) == 2:
        std = np.std(pts, axis=0) + 0.15
        return center[0] + n_std * std[0] * circle[0], center[1] + n_std * std[1] * circle[1]
    vals, vecs = np.linalg.eigh(np.cov(pts.T))
    ellipse = vecs @ np.diag(np.sqrt(np.maximum(vals, 1e-8)) * n_std) @ circle
    return center[0] + ellipse[0], center[1] + ellipse[1]


def _stem(word: str) -> str:
    for suffix, repl in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            word = word[: -len(suffix)] + repl
            break
    if word.endswith("e") and len(word) > 4:
        word = word[:-1]
    return word


@st.cache_resource(show_spinner=False)
def _nlp():
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.stem import PorterStemmer, WordNetLemmatizer

        data_dir = Path(tempfile.gettempdir()) / "nltk_data"
        if str(data_dir) not in nltk.data.path:
            nltk.data.path.insert(0, str(data_dir))
        for resource, package in (("corpora/stopwords", "stopwords"), ("corpora/wordnet", "wordnet"),
                                  ("corpora/omw-1.4", "omw-1.4")):
            try:
                nltk.data.find(resource)
            except LookupError:
                nltk.download(package, download_dir=str(data_dir), quiet=True)
        lemmatizer = WordNetLemmatizer()
        lemmatizer.lemmatize("warmup")
        return set(stopwords.words("english")), lemmatizer, PorterStemmer()
    except Exception:
        return None


def _words(text: str) -> set[str]:
    tokens = [t for t in re.findall(r"[a-z]+", text.lower()) if len(t) > 1]
    nlp = _nlp()
    if nlp is None:
        return {_stem(t) for t in tokens if t not in _STOP}
    stop, lemmatizer, stemmer = nlp
    return {
        stemmer.stem(lemmatizer.lemmatize(lemmatizer.lemmatize(t, "v"), "n"))
        for t in tokens
        if t not in stop
    }


def _has_key() -> bool:
    if openai_api_key():
        return True
    st.info(MISSING_KEY)
    return False


def _api_error(exc: Exception) -> None:
    st.error(f"Could not get embeddings from OpenAI – {type(exc).__name__}: {exc}")


def render_why() -> None:
    st.html(
        f"""
        <section class="cmx-card dtx-card w2x" aria-labelledby="se-why-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Sentence Embeddings</div>
          <h2 id="se-why-title">From word vectors to sentence embeddings</h2>
          <p class="dtx-lead">The <b>Attention</b> tab showed how context changes a word&rsquo;s representation in BERT.
          <i>Bank</i> did not have to mean the same thing everywhere &ndash; in one sentence its representation was
          shaped by words such as <i>river</i>, while in another it was shaped by words such as <i>loan</i>.</p>
          <p class="dtx-lead">But we still had <b>one contextual representation for each word</b>. What we did not yet
          have <b>in the exercise</b> was <b>one vector representing the meaning of the whole sentence</b>, designed so
          that complete sentences could be compared directly.</p>
          <p class="dtx-lead">That is what we introduce here. <b>OpenAI {MODEL}</b> takes a piece of text and returns a
          single <b>embedding</b> &ndash; a list of numbers representing the concepts in that text. If the input is a
          sentence, we can call it a <b>sentence embedding</b>. Sentences with related meanings tend to receive more
          similar embeddings, which lets us compare, search and group sentences by meaning rather than only by the words
          they share &ndash; and the trophy sentences, which BERT&rsquo;s attention could not separate, are worth testing
          again in the exercise.</p>
          <p class="dtx-lead">In <b>Exercise 2 of Bag of Words</b> you already met the word <b>embedding</b> as another
          name for a learned vector. There it was a <b>word embedding</b> &ndash; one vector for one word. Here the idea
          moves up a level &ndash; <b>one vector for the whole sentence</b>.</p>

          <h3>The whole journey in four steps</h3>
          <p class="dtx-lead">Steps 1 to 3 recap what you have seen so far, and step 4 is new. Follow two sentences
          through every step &ndash; <i>The bank raised interest rates</i> and <i>We sat on the river bank</i>. Each step
          fixes what the step before could not do.</p>
          <ol class="w2x-steps">
            <li><b class="t">Count the words &ndash; Bag of Words</b>
            Each sentence becomes a list of word counts. Word order and meaning are lost. Every sentence with
            <i>bank</i> looks alike, and <i>cancelled</i> and <i>called off</i> look unrelated because they share no
            words.</li>
            <li><b class="t">Give every word a place &ndash; Word2Vec</b>
            Words that keep the same company get nearby vectors, so <i>cancelled</i> and <i>called off</i> become
            neighbours. But every word gets <b>only one place</b> &ndash; <i>bank</i> sits somewhere between money and
            river, a blend of both meanings.</li>
            <li><b class="t">Let the words talk to each other &ndash; the transformer</b>
            Each word starts from its place and is then nudged by the other words in the sentence. In <i>The bank raised
            interest rates</i>, <i>interest</i> and <i>rates</i> pull <i>bank</i> towards money. In <i>We sat on the
            river bank</i>, <i>river</i> pulls it towards nature. <b>Attention helps produce this contextual
            representation</b> &ndash; the behaviour you explored in the Attention tab.</li>
            <li><b class="t">Give the whole sentence one place &ndash; the sentence embedding</b>
            Instead of keeping a separate output vector for every word, the embedding model returns <b>one vector for
            the complete sentence</b>. Now two whole sentences can be compared with cosine similarity. <i>The meeting
            was cancelled</i> and <i>The meeting was called off</i> tend to land close together, even though they share
            only <i>the</i> and <i>meeting</i>.</li>
          </ol>
          <div class="se-glance">
            <div class="gh">At a glance</div>
            <div class="gg">
              <div class="gc"><span class="gk">1 &middot; Bag of Words</span><b>&mdash; Counts words</b>
                <small><i>bank</i> &rarr; a count of 1</small></div>
              <div class="gc"><span class="gk">2 &middot; Word2Vec</span><b>&mdash; One place per word</b>
                <small><i>bank</i> &rarr; one blended point</small></div>
              <div class="gc"><span class="gk">3 &middot; Attention</span><b>&mdash; Places shift with the sentence</b>
                <small><i>bank</i> &rarr; money or river</small></div>
              <div class="gc end"><span class="gk">4 &middot; Sentence embedding</span><b>&mdash; One place per sentence</b>
                <small>whole sentence &rarr; one vector</small></div>
            </div>
          </div>

          <h3>What each step can tell apart</h3>
          <table class="w2x-set se-check">
            <thead><tr><th>Can it tell apart&hellip;</th><th>Bag of Words</th><th>Word2Vec</th><th>Sentence embedding</th></tr></thead>
            <tbody>
              <tr><td><i>cancelled</i> and <i>abandoned</i> are related</td><td class="no">No</td><td class="yes">Yes</td><td class="yes">Yes</td></tr>
              <tr><td><i>bank</i> for money and <i>bank</i> by the river</td><td class="no">No</td><td class="no">No</td><td class="yes">Yes</td></tr>
              <tr><td><i>dog bit man</i> and <i>man bit dog</i></td><td class="no">No</td><td class="no">No</td><td class="part">Only partly &ndash; you will test this</td></tr>
            </tbody>
          </table>

          <h3>How close is close?</h3>
          <p class="dtx-lead">Closeness is measured with the same <b>cosine similarity</b> from the Word2Vec lesson. A
          score near <b>1</b> means the two sentences mean almost the same thing. With this model even unrelated sentences
          rarely score below about 0.1, so <b>compare scores with each other</b> rather than reading one number on its
          own.</p>

          <h3>Why businesses care</h3>
          <ul class="w2x-list">
            <li><b>Search by meaning</b> &ndash; find the clause about ending a contract even when it never says
            &ldquo;termination&rdquo;.</li>
            <li><b>Routing and grouping</b> &ndash; send support tickets that mean the same thing to the same team, even
            when customers use different words.</li>
            <li><b>Duplicates and recommendations</b> &ndash; spot two listings that describe the same product, or suggest
            articles similar to the one being read.</li>
            <li><b>Assistants that read your documents</b> &ndash; a chatbot first finds the most similar passages in your
            files, then answers from them.</li>
          </ul>

          <h3>Read the map carefully</h3>
          <p class="dtx-lead">With the settings used here, each embedding has <b>3,072 numbers</b>. The map squeezes them into 2 with
          <b>PCA</b>, like the 3D view in Exercise 2 of Bag of Words, so some closeness is lost. Trust the <b>scores</b> more than the
          distances you see.</p>
        </section>
        """
    )


def render_exercise() -> None:
    st.html(
        f"""
        <section class="cmx-card dtx-card w2x" aria-labelledby="se-ex-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Exercise</div>
          <h2 id="se-ex-title">One word, many meanings</h2>
          <p class="dtx-lead">Many words have more than one meaning &ndash; <i>bank</i> can hold your money or sit beside a
          river. This is called <b>polysemy</b>. Word2Vec gives such a word one fixed vector. In this exercise you test
          whether sentence embeddings can tell the meanings apart, then push the model with the trophy sentences,
          negation, opinions and a contract search. Everything runs in the next two tabs &ndash; <b>Sentence space</b> and
          <b>Semantic search</b>.</p>
          <div class="w2x-note"><b>The model</b> &ndash; <b>OpenAI {MODEL}</b>. Every sentence you add is sent to OpenAI,
          which sends back its sentence embedding &ndash; a list of <b>{DIMS:,} numbers</b>. The model learned from a very
          large amount of text and, unlike Word2Vec, it reads the whole sentence, so every word is understood in its
          context. Each new sentence is one small paid request, so keep sentences short and do not add the same one
          twice.</div>

          <div class="w2x-note"><b>How the map shows groups</b> &ndash; sentences that sit together are circled. The map
          draws at most <b>two</b> circles, so plan every step around two meanings or two sides. If the sentences do not
          split clearly, one circle holds them all. Press <b>Reset</b> before every step.</div>

          <h3>Words with two meanings</h3>
          <div class="w2x-caps">
            <span class="cap"><i>1</i>bank <em>&ndash;</em> money / river</span>
            <span class="cap"><i>2</i>bat <em>&ndash;</em> cricket / animal</span>
            <span class="cap"><i>3</i>apple <em>&ndash;</em> fruit / company</span>
            <span class="cap"><i>4</i>crane <em>&ndash;</em> bird / machine</span>
            <span class="cap"><i>5</i>match <em>&ndash;</em> game / matchstick</span>
            <span class="cap"><i>6</i>mouse <em>&ndash;</em> animal / computer</span>
            <span class="cap"><i>7</i>seal <em>&ndash;</em> animal / stamp</span>
          </div>

          <h3>What you will do</h3>
          <ol class="w2x-steps">
            <li><b class="t">Pick a word and predict</b>
            Choose one word from the list above. Write three short sentences for each of its two meanings &ndash; for
            <i>bat</i>, three about cricket and three about the animal. Before adding anything, write down which
            sentences you expect to share a circle.</li>
            <li><b class="t">Add them and check the groups</b>
            Open <b>Sentence space</b> and add all six sentences. Do the circles split by <b>meaning</b>, or does the
            shared word pull everything into one group? Read the <b>Closest</b> line on every card &ndash; does any
            sentence find its closest match in the other meaning?</li>
            <li><b class="t">The tricky middle</b>
            Add one sentence that could be read either way &ndash; for <i>apple</i>, <i>I left my apple on the desk</i>.
            Which circle does it join? Is its best score higher or lower than the others, and why?</li>
            <li><b class="t">The trophy and the suitcase</b>
            Back to Gap 2 from the Attention tab. Press <b>Reset</b> and add four sentences &ndash;
            <i>The trophy did not fit in the suitcase because it was too big</i>, the same sentence ending in
            <i>too small</i>, <i>The trophy was too big</i> and <i>The suitcase was too small</i>. Read the
            <b>Closest</b> line of the first two. If the model understood <i>it</i>, the <i>big</i> sentence sits closest
            to <i>The trophy was too big</i> and the <i>small</i> sentence closest to <i>The suitcase was too small</i>.
            Or are the first two simply closest to each other, because they share almost every word?</li>
            <li><b class="t">Negation</b>
            Press <b>Reset</b> and add <i>The food was good</i>, <i>The food was not good</i> and
            <i>The food was delicious</i>. Which pair scores highest? Is <i>not good</i> as far from <i>good</i> as its
            meaning is? Think of a company searching complaints &ndash; could it get praise back instead?</li>
            <li><b class="t">Topic or opinion?</b>
            Press <b>Reset</b> and add <i>The phone battery is excellent</i>, <i>The phone battery is terrible</i>,
            <i>The pizza was excellent</i> and <i>The pizza was terrible</i>. Do the circles split by <b>topic</b>
            (phone and pizza) or by <b>opinion</b> (excellent and terrible)? What does that mean for a company that wants
            to sort reviews into happy and unhappy customers?</li>
            <li><b class="t">Meaning against words</b>
            Open <b>Semantic search</b>. Every question is ranked twice &ndash; all 8 clauses <b>by meaning</b> in the
            first box and <b>by words</b> in the second. The word box first cleans both texts with standard NLP steps
            using NLTK &ndash; lowercasing, removing punctuation and numbers, stop-word removal, lemmatisation and
            stemming &ndash; and then counts the words they share. Search for <i>termination</i>. Where does <b>Ending the contract</b> rank in each box? Now try
            <i>late delivery</i>. Which clause does each box put first, and why? Finish with two questions of your own,
            written the way a manager would ask them, and note where the two boxes disagree.</li>
          </ol>

          <h3>What to write down</h3>
          <ul class="w2x-list">
            <li>For steps 1 to 3 &ndash; your prediction, the groups the map actually drew, and the sentence that
            surprised you.</li>
            <li>For step 4 &ndash; the Closest match of the <i>big</i> and the <i>small</i> sentence, and whether the
            model seems to know what <i>it</i> points to.</li>
            <li>For steps 5 and 6 &ndash; the highest-scoring pair in each, and what the model seems to pay attention to
            &ndash; meaning, topic or the words themselves.</li>
            <li>For step 7 &ndash; one question where the two boxes disagree, which box found the right clause, and
            why the other one missed it.</li>
            <li>For every step &ndash; one place in a business where this behaviour would matter.</li>
          </ul>
        </section>
        """
    )


def _sentence_cards(sentences: list[str], sims: np.ndarray) -> str:
    items = []
    for i, text in enumerate(sentences):
        colour = PALETTE[i % len(PALETTE)]
        near = ""
        if len(sentences) > 1:
            row = sims[i].copy()
            row[i] = -2
            j = int(np.argmax(row))
            near = f'<div class="near">Closest &ndash; <b>S{j + 1}</b> &middot; score <b>{row[j]:.2f}</b></div>'
        items.append(
            f'<div class="se-item" style="border-left-color:{colour}">'
            f'<div class="sid" style="color:{colour}">S{i + 1}</div>'
            f'<div class="txt">{escape(text)}</div>{near}</div>'
        )
    return '<div class="se-list">' + "".join(items) + "</div>"


def _map_figure(sentences: list[str], coords: np.ndarray, matrix: np.ndarray) -> go.Figure:
    fig = go.Figure()
    labels, n_groups = _groups(matrix)
    xs, ys = [coords[:, 0]], [coords[:, 1]]
    for k in range(n_groups):
        mask = labels == k
        if not mask.any():
            continue
        ex, ey = _ellipse_xy(coords[mask])
        xs.append(ex)
        ys.append(ey)
        fig.add_trace(
            go.Scatter(
                x=[*ex, ex[0]],
                y=[*ey, ey[0]],
                mode="lines",
                fill="toself",
                fillcolor=GROUP_FILL[k],
                line=dict(color=GROUP_LINE[k], width=1.5, dash="dot"),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    for i, text in enumerate(sentences):
        fig.add_trace(
            go.Scatter(
                x=[float(coords[i, 0])],
                y=[float(coords[i, 1])],
                mode="markers+text",
                marker=dict(size=16, color=PALETTE[i % len(PALETTE)], line=dict(color="#ffffff", width=2)),
                text=[f"S{i + 1}"],
                textposition="top center",
                textfont=dict(family="Inter, sans-serif", size=13, color="#0b1f3a"),
                hovertext=[text],
                hoverinfo="text",
                showlegend=False,
            )
        )
    all_x, all_y = np.concatenate(xs), np.concatenate(ys)
    span_x = float(np.ptp(all_x)) or 1.0
    span_y = float(np.ptp(all_y)) or 1.0
    axis = dict(showticklabels=False, showgrid=False, zeroline=False, showline=False)
    title_font = dict(family="Inter, sans-serif", size=13, color="#0b1f3a")
    fig.update_layout(
        height=430,
        margin=dict(l=40, r=10, t=10, b=40),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", color="#0b1f3a"),
        hoverlabel=dict(font_family="Inter, sans-serif", bgcolor="#ffffff", bordercolor="#0b1f3a"),
        xaxis=dict(**axis, title=dict(text="PC 1", font=title_font),
                   range=[all_x.min() - 0.08 * span_x, all_x.max() + 0.08 * span_x]),
        yaxis=dict(**axis, title=dict(text="PC 2", font=title_font),
                   range=[all_y.min() - 0.1 * span_y, all_y.max() + 0.1 * span_y]),
    )
    return fig


def _matrix_figure(sims: np.ndarray) -> go.Figure:
    labels = [f"S{i + 1}" for i in range(len(sims))]
    fig = go.Figure(
        go.Heatmap(
            z=sims,
            x=labels,
            y=labels,
            zmin=0,
            zmax=1,
            colorscale=[[0.0, "#ffffff"], [0.5, "#c9d6ea"], [1.0, "#0b1f3a"]],
            text=[[f"{v:.2f}" for v in row] for row in sims],
            texttemplate="%{text}",
            textfont=dict(family="Inter, sans-serif", size=12),
            hovertemplate="%{y} and %{x} – %{text}<extra></extra>",
            showscale=False,
            xgap=2,
            ygap=2,
        )
    )
    size = 60 + 44 * len(sims)
    fig.update_layout(
        height=size,
        width=size + 40,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", color="#0b1f3a"),
        yaxis=dict(autorange="reversed"),
    )
    return fig


def render_space() -> None:
    state = st.session_state
    state.setdefault("se_sentences", [])

    with st.container(key="se_space"):
        st.html(
            '<p class="se-hint">Type a sentence and press <b>Add</b>. '
            f"Up to {MAX_SENTENCES} sentences &ndash; press <b>Reset</b> to start again.</p>"
        )
        with st.form("se_add_form", clear_on_submit=True, border=False):
            col_in, col_add, col_reset = st.columns([6, 1, 1], vertical_alignment="bottom")
            text = col_in.text_input(
                "Sentence",
                placeholder="e.g. I deposited my salary at the bank.",
                label_visibility="collapsed",
            )
            added = col_add.form_submit_button("Add", type="primary", width="stretch")
            reset = col_reset.form_submit_button("Reset", width="stretch")

        if reset:
            state.se_sentences = []
            added = False

        if added and text.strip():
            sentence = text.strip()
            if sentence in state.se_sentences:
                st.warning("That sentence is already on the map.")
            elif len(state.se_sentences) >= MAX_SENTENCES:
                st.warning(f"The map holds {MAX_SENTENCES} sentences. Press Reset to start again.")
            else:
                state.se_sentences = [*state.se_sentences, sentence]

        sentences = state.se_sentences
        if not sentences:
            st.html('<div class="se-empty">The space is empty. Type a sentence and press Add.</div>')
            return
        if not _has_key():
            return
        try:
            with st.spinner("Getting sentence embeddings..."):
                matrix = _vectors(sentences)
        except Exception as exc:
            _api_error(exc)
            return

        sims = np.clip(matrix @ matrix.T, -1.0, 1.0)
        col_map, col_list = st.columns([3, 2], gap="large")
        with col_map:
            if len(sentences) == 1:
                st.html('<div class="se-empty">Add one more sentence to see the map.</div>')
            else:
                with st.container(key="se_mapbox"):
                    st.plotly_chart(
                        _map_figure(sentences, _pca2(matrix), matrix),
                        width="stretch",
                        config={"displayModeBar": False},
                        key="se_map",
                    )
                st.html(f'<p class="se-cap">{DIMS:,} numbers per sentence, squeezed into 2 with PCA. '
                        "Hover a dot to read its sentence.</p>")
        with col_list:
            st.html(_sentence_cards(sentences, sims))

        if len(sentences) > 1:
            st.html('<h3 class="se-h">Similarity scores</h3>'
                    '<p class="se-cap">Cosine similarity between every pair of sentences. Darker means closer in meaning.</p>')
            with st.container(key="se_matbox", width="content"):
                st.plotly_chart(
                    _matrix_figure(sims),
                    width="content",
                    config={"displayModeBar": False},
                    key="se_matrix",
                )


def _rows(order, values, labels, tags, extra, highlight=None) -> str:
    rows = []
    for rank, idx in enumerate(order, start=1):
        title, clause = CLAUSES[idx]
        bar = ""
        if values is not None:
            bar = f'<div class="bar"><span style="width:{values[idx]:.0f}%"></span></div>'
        rows.append(
            f'<div class="se-res{" top" if (highlight[idx] if highlight else rank == 1 and values is not None) else ""}">'
            f'<div class="rk">{rank}</div>'
            f'<div class="bd"><div class="hd"><b>{escape(title)}</b>{tags[idx]}</div>'
            f'<div class="cl">{escape(clause)}</div>{extra[idx]}{bar}</div>'
            f'<div class="sc">{labels[idx]}</div></div>'
        )
    return '<div class="se-results">' + "".join(rows) + "</div>"


def _box(title: str, caption: str, body: str) -> str:
    return (
        f'<div class="se-box"><h3 class="se-h">{title}</h3><p class="se-cap">{caption}</p>{body}</div>'
    )


_MEANING_CAP = "All 8 clauses ranked by cosine similarity between the question and each clause."
_WORDS_CAP = (
    "All 8 clauses ranked by shared words. Both texts are first cleaned with standard NLP steps using "
    "<b>NLTK</b> &ndash; lowercasing, removing punctuation and numbers, <b>stop-word removal</b> "
    "(<i>the</i>, <i>is</i>, <i>can</i>), <b>lemmatisation</b> (<i>paid</i> &rarr; <i>pay</i>) and "
    "<b>stemming</b> (<i>created</i> &rarr; <i>creat</i>)."
)


def _empty_boxes() -> str:
    n = len(CLAUSES)
    order = list(range(n))
    blank = [""] * n
    body = _rows(order, None, blank, blank, blank)
    return (
        '<div class="se-pair">'
        + _box("By meaning", _MEANING_CAP, body)
        + _box("By words", _WORDS_CAP, body)
        + "</div>"
    )


def _result_rows(query: str, scores: np.ndarray) -> str:
    q_terms = _words(query)
    clause_terms = [_words(c) for _, c in CLAUSES]
    shared = [q_terms & t for t in clause_terms]
    none_tag = '<span class="se-tag">no word in common</span>'
    tags = [none_tag if not sh else "" for sh in shared]
    blank = [""] * len(CLAUSES)

    order_m = list(np.argsort(scores)[::-1])
    low, high = float(scores.min()), float(scores.max())
    widths_m = [12 + 88 * (float(v) - low) / (high - low or 1.0) for v in scores]
    labels_m = [f"{float(v):.2f}" for v in scores]
    meaning = _rows(order_m, widths_m, labels_m, tags, blank)

    total = len(q_terms)
    counts = [len(sh) for sh in shared]
    order_w = sorted(range(len(CLAUSES)), key=lambda i: (-counts[i], i))
    widths_w = [100 * c / total if total else 0 for c in counts]
    labels_w = [f"{c}/{total}" for c in counts]
    matched = [
        '<div class="se-match">matched &ndash; ' + ", ".join(f"<b>{escape(w)}</b>" for w in sorted(sh)) + "</div>"
        if sh else '<div class="se-match none">no match</div>'
        for sh in shared
    ]
    words = _rows(order_w, widths_w, labels_w, blank, matched, [c > 0 for c in counts])

    terms = ", ".join(f"<b>{escape(w)}</b>" for w in sorted(q_terms)) or "none"
    words_cap = _WORDS_CAP + f" Your question after cleaning &ndash; {terms}."
    return (
        '<div class="se-pair">'
        + _box("By meaning", _MEANING_CAP, meaning)
        + _box("By words", words_cap, words)
        + "</div>"
    )


def _set_query(q: str) -> None:
    st.session_state.se_query = q


def render_search() -> None:
    with st.container(key="se_search"):
        st.html(
            '<p class="se-hint">Eight clauses from a service contract. <b>Type your own question</b> in the box '
            "below, the way a manager would ask it, and press Enter. Each question is ranked twice &ndash; "
            "<b>by meaning</b> in the first box and <b>by words</b> in the second.</p>"
        )
        query = st.text_input(
            "Question",
            key="se_query",
            placeholder="Type your question here and press Enter",
            label_visibility="collapsed",
        ).strip()
        st.html('<p class="se-cap se-try">Not sure what to ask? Try an example &ndash; you can edit it afterwards.</p>')
        cols = st.columns(len(QUERIES))
        for col, q in zip(cols, QUERIES):
            col.button(q, key=f"se_q_{q}", width="stretch", on_click=_set_query, args=(q,))

        if not query:
            st.html(_empty_boxes())
            return
        if not _has_key():
            return
        try:
            with st.spinner("Searching by meaning and by words..."):
                _nlp()
                clauses = _vectors([c for _, c in CLAUSES])
                q_vec = _vectors([query])[0]
        except Exception as exc:
            _api_error(exc)
            return
        st.html(_result_rows(query, clauses @ q_vec))
