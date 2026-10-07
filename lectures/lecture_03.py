from __future__ import annotations

import copy

import streamlit as st

TITLE = "Lecture 3"
SUB_LECTURES = ["Confusion Matrix", "Decision Tree", "Confusion Matrix 2"]
TOPICS = {
    "Confusion Matrix": ["Confusion Matrix"],
    "Decision Tree": ["Decision Tree"],
    "Confusion Matrix 2": ["Confusion Matrix 2"],
}
PICK_SUB = "Pick Confusion Matrix, Decision Tree, or Confusion Matrix 2 to open that section."
PICK_TOPIC = "Pick a topic to open that section."
PICK_TOPIC_BY_SUB = {
    "Confusion Matrix": "Pick Confusion Matrix to open that section.",
    "Decision Tree": "Pick Decision Tree to open that section.",
    "Confusion Matrix 2": "Pick Confusion Matrix 2 to open that section.",
}

TOPIC_NAME = "Neural Networks"
CONFUSION_TOPIC = "Confusion Matrix"
TREE_TOPIC = "Decision Tree"
CONFUSION_2_TOPIC = "Confusion Matrix 2"
BOW_TOPIC = "Bag of Words"
SE_TOPIC = "Sentence Embeddings"
WORD2VEC_COLAB = "https://colab.research.google.com/drive/1TveiLA0DLXDiq-MZZSHX9xwC1kJCBLm7?usp=sharing"
WORD_LAB_URL = "https://embedding-lab-7yduhyt8ixtatf2xgvxemy.streamlit.app/"

CANVAS_SIZE = 220
NEURON_GALLERY_K = 8
NEURON_GALLERY_COLS = 4
NEURON_GRID_COLS = 8
NEURON_INACTIVE_MAX = 0.01
TOP_K = 6

EMPTY_CANVAS = {"version": "4.4.0", "objects": []}


def render(
    lecture: str | None,
    sub_lecture: str | None,
    topic: str,
    *,
    crumbs: str,
) -> None:
    from html import escape

    number = (lecture or "3").split()[-1]
    header = (
        "<div class='lesson-block-header'>"
        f"<div class='lesson-number'>{escape(number)}</div>"
        f"{crumbs}"
        "</div>"
    )
    with st.container(key="lesson_block", gap=None):
        st.html(header)
        if topic == CONFUSION_TOPIC:
            with st.container(key="cm_body"):
                tab_problem, tab_drag = st.tabs(["Exercise", "Drag the threshold"])
                with tab_problem:
                    _render_confusion_problem()
                with tab_drag:
                    from services.confusion_matrix import render as render_confusion

                    render_confusion()
            return
        if topic == CONFUSION_2_TOPIC:
            with st.container(key="cm2_body"):
                tab_problem, tab_drag = st.tabs(["Exercise", "Drag the threshold"])
                with tab_problem:
                    _render_confusion_2_problem()
                with tab_drag:
                    from services.confusion_matrix import render_churn

                    render_churn()
            return
        if topic == TREE_TOPIC:
            with st.container(key="dtx_body"):
                tab_intuition, tab_exercise, tab_practical = st.tabs(["Intuition", "Exercise", "Visualisation"])
                with tab_intuition:
                    from services.decision_tree import render_intuition

                    render_intuition()
                with tab_exercise:
                    _render_decision_tree()
                with tab_practical:
                    from services.decision_tree import render as render_tree

                    render_tree()
            return
        if topic == BOW_TOPIC:
            with st.container(key="bow_body"):
                tab_bow, tab_what, tab_exercise, tab_lab, tab_attention = st.tabs(
                    ["What is Bag of Words", "What is Word2Vec", "Exercise 1", "Exercise 2", "Attention"]
                )
                from services import attention, bag_of_words

                with tab_bow:
                    bag_of_words.render()
                with tab_what:
                    _render_word2vec_intro()
                with tab_exercise:
                    _render_word2vec_exercise()
                with tab_lab:
                    _render_word_lab()
                with tab_attention:
                    attention.render()
            return
        if topic == SE_TOPIC:
            from services import sentence_embeddings as se

            with st.container(key="se_body"):
                tab_why, tab_ex, tab_space, tab_search = st.tabs(
                    ["From words to sentences", "Exercise", "Sentence space", "Semantic search"]
                )
                with tab_why:
                    se.render_why()
                with tab_ex:
                    se.render_exercise()
                with tab_space:
                    se.render_space()
                with tab_search:
                    se.render_search()
            return
        if topic != TOPIC_NAME:
            return
        with st.container(key="nn_body"):
            tab_exercise, tab_label, tab_draw = st.tabs(
                ["Exercise", "Label the neuron", "Draw a character"]
            )
            with tab_exercise:
                _render_exercise()
            with tab_label:
                with st.container(key="nn_label"):
                    _render_label()
            with tab_draw:
                _render_draw()


def _render_confusion_2_problem() -> None:
    st.html(
        """
        <section class="cmx-card" aria-labelledby="cm2-problem-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Exercise</div>
          <h2 id="cm2-problem-title">A model can be accurate and still be expensive</h2>
          <p class="cmx-lead">This model scores <b>420 customers</b> for churn risk. Of them, <b>58 actually churn</b>—a base rate of <b>13.8%</b>.</p>
          <div class="cmx-steps">
            <div class="cmx-step"><div class="cmx-num">1</div><div><h3>Choose a threshold</h3><p>Customers above the threshold receive a coupon.</p></div></div>
            <div class="cmx-step"><div class="cmx-num">2</div><div><h3>Count the mistakes</h3><p>A false positive costs <b>₹500</b>; a false negative costs <b>₹10,000</b>.</p></div></div>
            <div class="cmx-step"><div class="cmx-num">3</div><div><h3>Minimise total cost</h3><p>Drag the threshold and watch the confusion matrix, cost, and savings change.</p></div></div>
          </div>
        </section>
        """
    )


def _render_decision_tree() -> None:
    st.html(
        """
        <section class="cmx-card dtx-card" aria-labelledby="dtx-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Exercise</div>
          <h2 id="dtx-title">Which customers will churn?</h2>
          <p class="dtx-lead dtx-oneline">A telecom company looks at 16 existing customers.<br>For each one it knows the <b>age</b>, <b>support complaints</b>, <b>tenure</b>, <b>monthly bill</b>, and the eventual <b>outcome</b>.</p>
          <div class="dtx-scroll">
          <table class="dtx-table">
            <thead>
              <tr><th>Customer</th><th class="dtx-num">Age</th><th class="dtx-num">Support complaints</th><th class="dtx-num">Tenure (months)</th><th class="dtx-num">Monthly bill (&#8377;)</th><th>Outcome</th></tr>
            </thead>
            <tbody>
              <tr><td>C01</td><td class="dtx-num">24</td><td class="dtx-num">6</td><td class="dtx-num">5</td><td class="dtx-num">1,450</td><td class="dtx-churned">Churned</td></tr>
              <tr><td>C02</td><td class="dtx-num">29</td><td class="dtx-num">5</td><td class="dtx-num">8</td><td class="dtx-num">1,180</td><td class="dtx-churned">Churned</td></tr>
              <tr><td>C03</td><td class="dtx-num">32</td><td class="dtx-num">6</td><td class="dtx-num">14</td><td class="dtx-num">1,620</td><td class="dtx-churned">Churned</td></tr>
              <tr><td>C04</td><td class="dtx-num">36</td><td class="dtx-num">4</td><td class="dtx-num">22</td><td class="dtx-num">980</td><td class="dtx-churned">Churned</td></tr>
              <tr><td>C05</td><td class="dtx-num">38</td><td class="dtx-num">5</td><td class="dtx-num">30</td><td class="dtx-num">1,310</td><td class="dtx-churned">Churned</td></tr>
              <tr><td>C06</td><td class="dtx-num">46</td><td class="dtx-num">4</td><td class="dtx-num">10</td><td class="dtx-num">1,080</td><td class="dtx-churned">Churned</td></tr>
              <tr><td>C07</td><td class="dtx-num">51</td><td class="dtx-num">2</td><td class="dtx-num">26</td><td class="dtx-num">1,520</td><td class="dtx-churned">Churned</td></tr>
              <tr><td>C08</td><td class="dtx-num">57</td><td class="dtx-num">1</td><td class="dtx-num">18</td><td class="dtx-num">890</td><td class="dtx-churned">Churned</td></tr>
              <tr><td>C09</td><td class="dtx-num">26</td><td class="dtx-num">5</td><td class="dtx-num">16</td><td class="dtx-num">1,260</td><td class="dtx-stayed">Stayed</td></tr>
              <tr><td>C10</td><td class="dtx-num">35</td><td class="dtx-num">4</td><td class="dtx-num">28</td><td class="dtx-num">1,100</td><td class="dtx-stayed">Stayed</td></tr>
              <tr><td>C11</td><td class="dtx-num">31</td><td class="dtx-num">2</td><td class="dtx-num">7</td><td class="dtx-num">1,480</td><td class="dtx-stayed">Stayed</td></tr>
              <tr><td>C12</td><td class="dtx-num">43</td><td class="dtx-num">1</td><td class="dtx-num">13</td><td class="dtx-num">920</td><td class="dtx-stayed">Stayed</td></tr>
              <tr><td>C13</td><td class="dtx-num">47</td><td class="dtx-num">2</td><td class="dtx-num">21</td><td class="dtx-num">1,350</td><td class="dtx-stayed">Stayed</td></tr>
              <tr><td>C14</td><td class="dtx-num">52</td><td class="dtx-num">1</td><td class="dtx-num">32</td><td class="dtx-num">1,040</td><td class="dtx-stayed">Stayed</td></tr>
              <tr><td>C15</td><td class="dtx-num">58</td><td class="dtx-num">2</td><td class="dtx-num">11</td><td class="dtx-num">1,580</td><td class="dtx-stayed">Stayed</td></tr>
              <tr><td>C16</td><td class="dtx-num">63</td><td class="dtx-num">1</td><td class="dtx-num">24</td><td class="dtx-num">960</td><td class="dtx-stayed">Stayed</td></tr>
            </tbody>
          </table>
          </div>
        </section>
        """
    )


def _render_word2vec_intro() -> None:
    from services.word2vec import render_intro

    render_intro()


def _render_word2vec_exercise() -> None:
    st.html(
        f"""
        <section class="cmx-card dtx-card w2x" aria-labelledby="w2v-ex-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Exercise 1</div>
          <h2 id="w2v-ex-title">Train your own Word2Vec</h2>
          <p class="dtx-lead">In this exercise you run the whole Word2Vec pipeline from the lesson yourself &ndash; on a real
          book of your choice. You clean the text, train a <b>CBOW</b> model on it, and then explore a map of the word
          vectors it learns.</p>
          <div class="w2x-note"><b>Before you start</b> &ndash; the notebook runs in <b>Google Colab</b> on your own Google
          account. Sign in, then choose <b>File &rarr; Save a copy in Drive</b> so you work on your own copy. Run the cells
          from top to bottom.</div>

          <h3>What you will do</h3>
          <ol class="w2x-steps">
            <li><b class="t">Install and import the libraries</b>
            <code>gensim</code> trains the model, <code>nltk</code> supplies the stop-word list, <code>scikit-learn</code>
            squeezes each vector down to two numbers for the map, and <code>plotly</code> draws the map.</li>
            <li><b class="t">Choose the text</b>
            Open <a href="https://www.gutenberg.org/" target="_blank" rel="noopener">Project Gutenberg</a>, pick any book,
            click <b>Other formats &amp; older devices</b>, open <b>Plain Text</b> and copy the address ending in
            <code>.txt</code>. Paste it when the notebook asks. No book in mind? Use <i>The Return of Sherlock Holmes</i> &ndash;
            <code>https://www.gutenberg.org/cache/epub/108/pg108.txt</code>. The notebook keeps only the story, drops the
            licence text around it, and shows you the opening, the ending and the word count.</li>
            <li><b class="t">Prepare the text for CBOW</b>
            Every line is lowercased, punctuation and numbers are removed, <b>stop words</b> such as <i>the</i>, <i>was</i>
            and <i>and</i> are dropped, and very short words are left out. Each line becomes a list of words &ndash;
            these are the sentences CBOW reads.</li>
            <li><b class="t">Train CBOW</b>
            Pick the four settings from the menus and press <b>Train CBOW</b>. The model is trained with <code>sg=0</code>,
            which means CBOW.
              <table class="w2x-set">
                <thead><tr><th>Setting</th><th>What it controls</th><th>Choices</th><th>Default</th></tr></thead>
                <tbody>
                  <tr><td>Vector size</td><td>how many numbers each word gets</td><td>10, 25, 50, 100, 200</td><td>50</td></tr>
                  <tr><td>Window</td><td>how many words on each side count as context</td><td>2, 3, 5, 7, 10</td><td>5</td></tr>
                  <tr><td>Min count</td><td>a word seen fewer times than this is left out</td><td>1, 2, 5, 10, 20</td><td>5</td></tr>
                  <tr><td>Epochs</td><td>how many times CBOW reads the whole book</td><td>5 to 200</td><td>10</td></tr>
                </tbody>
              </table>
            </li>
            <li><b class="t">See the words</b>
            The most common words are taken, each vector is scaled to length 1 so only its <b>direction</b> counts, and
            <b>t-SNE</b> turns each vector into two numbers &ndash; one point per word on a flat map. Hover over a point
            to read its word.</li>
          </ol>

          <h3>What to look for</h3>
          <ul class="w2x-list">
            <li>Small groups of related words &ndash; names of characters, places, words about time, words about speech
            such as <i>said</i>, <i>asked</i> and <i>replied</i>.</li>
            <li>For each group, ask what the words have in common. CBOW only saw which words were near each other &ndash;
            nobody told it what any word means.</li>
            <li>Some groups are about meaning, and some only reflect how this particular author writes.</li>
          </ul>

          <h3>Read the map carefully</h3>
          <ul class="w2x-list">
            <li>A gap between two groups is <b>not a real distance</b>. t-SNE keeps close neighbours close, but stretches
            and squeezes everything else.</li>
            <li>Run it again and the layout can rotate or flip. The neighbours stay similar, the positions do not mean anything.</li>
            <li>The model learned from <b>one book</b>. With so little text, some neighbours are accidents of the story.</li>
          </ul>

          <h3>Try this</h3>
          <ul class="w2x-list">
            <li>Change the <b>Window</b> or the <b>Epochs</b>, train again and redraw. Do the same words stay together?</li>
            <li>Try a very small <b>Vector size</b> such as 10, then a large one such as 200. Which map has cleaner groups?</li>
            <li>Load a different book. Does <i>said</i> land near the same words in both books?</li>
          </ul>

          <a class="w2v-link" href="{WORD2VEC_COLAB}" target="_blank" rel="noopener">Open the Colab notebook</a>
          <div class="w2x-note w2x-next"><b>Next</b> &ndash; open <b>Exercise 2</b> to do arithmetic with word vectors
          learned from far more text.</div>
        </section>
        """
    )


def _render_word_lab() -> None:
    st.html(
        f"""
        <section class="cmx-card dtx-card w2x" aria-labelledby="w2v-lab-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Exercise 2</div>
          <h2 id="w2v-lab-title">Do arithmetic with word vectors</h2>
          <p class="dtx-lead">In Exercise 1 your vectors came from one book. Here you use vectors that were learned from
          a <b>huge amount of text</b> &ndash; all of Wikipedia plus years of news articles. With that much text, the
          patterns from the lesson become strong enough to test yourself &ndash; nearest neighbours, cosine similarity and
          the famous <b>king &minus; man + woman</b>.</p>
          <p class="dtx-lead">The vectors come from <b>GloVe</b>, a close cousin of Word2Vec that also learns from which
          words occur together. It has <b>400,000 words</b>, and every word is a vector of <b>300 numbers</b>.</p>

          <h3>Step 1 &ndash; Make your guesses</h3>
          <p class="dtx-lead">Remember how the lesson solved <b>king &minus; man + woman</b> &ndash; king is roughly
          man + royal, so removing man leaves the <i>royal</i> part, and adding woman lands near <b>queen</b>.
          Solve the expressions below the same way, <b>before</b> you open the lab. For each one, ask yourself &ndash;</p>
          <div class="w2x-note w2x-ask">
          <ul class="w2x-list">
            <li>what meaning does the first word carry?</li>
            <li>what part does the subtracted word remove, and what is left?</li>
            <li>what does the added word bring in &ndash; and which word do you expect to land on?</li>
          </ul>
          </div>
          <div class="w2x-caps">
            <span class="cap"><i>1</i>(cats <em>&minus;</em> cat) <em>+</em> dog</span>
            <span class="cap"><i>2</i>(cricket <em>&minus;</em> india) <em>+</em> brazil</span>
            <span class="cap"><i>3</i>(sushi <em>&minus;</em> japan) <em>+</em> italy</span>
            <span class="cap"><i>4</i>(sanskrit <em>&minus;</em> india) <em>+</em> rome</span>
            <span class="cap"><i>5</i>(death <em>&minus;</em> care) <em>+</em> money</span>
            <span class="cap"><i>6</i>(teacher <em>&minus;</em> school) <em>+</em> hospital</span>
            <span class="cap"><i>7</i>(xbox <em>&minus;</em> microsoft) <em>+</em> sony</span>
            <span class="cap"><i>8</i>(gandhi <em>&minus;</em> india) <em>+</em> germany</span>
            <span class="cap"><i>9</i>(atom <em>&minus;</em> physics) <em>+</em> biology</span>
            <span class="cap"><i>10</i>(sand <em>&minus;</em> desert) <em>+</em> polar</span>
          </div>
          <p class="dtx-lead">Write down your guess for each one.</p>

          <h3>Step 2 &ndash; Check your guesses in the lab</h3>
          <div class="w2x-note"><b>Before you open the lab</b> &ndash; it opens in a new tab and needs no sign-in. The app
          is called <b>Embedding Lab</b> &ndash; <i>embedding</i> is simply another name for a word vector. If the app has
          been asleep, it takes a minute to wake up. Press <b>Load Model</b> and wait for the progress bar &ndash; loading
          the vectors takes another minute.</div>
          <p class="dtx-lead">The lab works in three stages, shown at the top of the app &ndash;
          <b>Build expression &rarr; Compute &rarr; Discover</b>.</p>
          <ol class="w2x-steps">
            <li><b class="t">Build expression</b>
            Type a word in <b>Term</b> and press <b>+ Add</b> or <b>&minus; Sub</b>. Added words appear as green chips,
            subtracted words as red chips. Click a chip to remove it, or press <b>Clear</b> to start again. For
            <b>(cats &minus; cat) + dog</b> &ndash; type <i>cats</i> and press + Add, type <i>cat</i> and press &minus; Sub,
            type <i>dog</i> and press + Add. The lab writes it back to you as <i>(cats - cat) + dog</i>.</li>
            <li><b class="t">Compute</b>
            Press <b>Compute</b>. The lab adds and subtracts the vectors of your words, exactly like the analogy in the
            lesson, and finds the <b>5 closest words</b> to the result using <b>cosine similarity</b>. The words you typed
            are left out, so you only see new words.</li>
            <li><b class="t">Discover</b>
            The <b>Closest Words</b> panel lists the 5 words with their similarity scores. Compare the top 3 with your
            guess. The <b>Vector Space Visualization</b> first shows each added and subtracted word as a green or red arrow,
            and after Compute it shows the result with its closest words. It squeezes 300 numbers into 3, so trust the
            <b>scores</b> more than the distances you see.</li>
          </ol>
          <p class="dtx-lead">Every computed expression is kept in <b>Experiment History</b>, so you can press
          <b>Restore</b> to go back to an earlier one. Under each closest word, <b>Add</b>, <b>Subtract</b> and
          <b>Start Fresh</b> let you keep exploring from it. Your professor will go through the answers in class.</p>

          <h3>Tips</h3>
          <ul class="w2x-list">
            <li>Type single words. Capital letters are fine, but numbers are not allowed.</li>
            <li>If a word is <b>not in vocabulary</b>, try a more common spelling or a different word.</li>
            <li>If the lab says <b>Expression unchanged</b>, you already computed that expression &ndash; add or remove a
            word first.</li>
          </ul>

          <a class="w2v-link" href="{WORD_LAB_URL}" target="_blank" rel="noopener">Open the lab</a>
          <div class="w2x-note w2x-next"><b>Next</b> &ndash; when you are done, open <b>Attention</b> to see what word
          vectors still cannot do, and how attention fixes it.</div>
        </section>
        """
    )


def _render_confusion_problem() -> None:
    st.html(
        """
        <section class="cmx-card" aria-labelledby="cm-problem-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Exercise</div>
          <h2 id="cm-problem-title">A high score can still hide mistakes</h2>
          <div class="cmx-steps">
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">1</span>
                <h3>A rare disease,<br>one threshold</h3>
                <span class="cmx-icon cmx-icon-people"></span>
              </div>
              <ul class="cmx-points">
                <li>Forty patients. A few are actually sick. A screening test gives each person a risk score from 0 to 1.</li>
                <li>Anyone at or above the decision threshold is predicted sick. Everyone below it is predicted not sick.</li>
                <li>Moving that one line changes who is predicted sick and who is predicted not sick.</li>
              </ul>
            </article>
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">2</span>
                <h3>Four kinds of result</h3>
                <span class="cmx-icon cmx-icon-result"></span>
              </div>
              <ul class="cmx-points">
                <li><strong>True positive</strong> &mdash; actually sick, and predicted sick.</li>
                <li><strong>False negative</strong> &mdash; actually sick, but predicted not sick.</li>
                <li><strong>False positive</strong> &mdash; actually not sick, but predicted sick.</li>
                <li><strong>True negative</strong> &mdash; actually not sick, and predicted not sick.</li>
              </ul>
            </article>
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">3</span>
                <h3>Why one percentage<br>is not enough</h3>
                <span class="cmx-icon cmx-icon-bars"></span>
              </div>
              <ul class="cmx-points">
                <li><strong>Accuracy</strong> counts every correct box. With few sick patients, predicting the healthy ones as not sick can make accuracy look strong.</li>
                <li><strong>Precision</strong> asks: of everyone predicted sick, how many are actually sick?</li>
                <li><strong>Recall</strong> asks: of everyone actually sick, how many were predicted sick?</li>
              </ul>
            </article>
          </div>
          <div class="cmx-next">
            <span class="cmx-arrow"></span>
            <span class="cmx-sep"></span>
            <span><strong>Next</strong> &mdash; Open <strong>Drag the threshold.</strong> Drag the gold line and watch those four boxes change.</span>
          </div>
        </section>
        """
    )


def _render_exercise() -> None:
    st.html(
        """
        <section class="cmx-card" aria-labelledby="nn-exercise-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Exercise</div>
          <h2 id="nn-exercise-title">Discover what a neuron detects</h2>
          <div class="cmx-steps">
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">1</span>
                <h3>Study a neuron</h3>
                <span class="cmx-icon cmx-icon-neurons"></span>
              </div>
              <ul class="cmx-points">
                <li>Open <strong>Label the neuron</strong> and select any navy neuron &mdash; the selected neuron turns gold.</li>
                <li>Examine its eight strongest examples. Ignore the letter labels and identify the shared visual pattern, such as a diagonal, loop, curve, or crossbar.</li>
                <li>Form a hypothesis &mdash; &ldquo;Neuron 02 detects loops.&rdquo;</li>
              </ul>
            </article>
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">2</span>
                <h3>Test your idea</h3>
                <span class="cmx-icon cmx-icon-pen"></span>
              </div>
              <ul class="cmx-points">
                <li>Remember the neuron number and open <strong>Draw a character</strong>.</li>
                <li>Clearly recreate the common visual pattern you identified.</li>
                <li>Focus on the pattern rather than copying a particular letter. The activation grid shows how strongly each of the 24 neurons responds.</li>
              </ul>
            </article>
            <article class="cmx-step">
              <div class="cmx-head">
                <span class="cmx-num">3</span>
                <h3>Check the result</h3>
                <span class="cmx-icon cmx-icon-activation"></span>
              </div>
              <ul class="cmx-points">
                <li>Find the neuron number you studied in the activation grid.</li>
                <li>A <strong>brighter</strong> neuron indicates a stronger response; a <strong>dark</strong> neuron indicates a weak or absent response.</li>
                <li>If your neuron lights up, the result supports your hypothesis. If it remains dark, try a clearer variation before reconsidering what the neuron detects.</li>
              </ul>
            </article>
          </div>
          <div class="cmx-next">
            <span class="cmx-arrow"></span>
            <span class="cmx-sep"></span>
            <span><strong>Remember</strong> &mdash; Note the neuron number before switching tabs. It will not be highlighted automatically in the activation grid.</span>
          </div>
        </section>
        """
    )


def _model():
    from services.neural_interpretability import CHECKPOINT_PATH
    from services.neural_interpretability import load_model

    if not CHECKPOINT_PATH.is_file():
        st.error("The Neural Networks model file is not in the project yet.")
        st.stop()
    if "nn_model" not in st.session_state:
        st.session_state["nn_model"] = load_model()
    return st.session_state["nn_model"]


def _bank():
    from services.neural_interpretability import BANK_PATH
    from services.neural_interpretability import load_bank

    if not BANK_PATH.is_file():
        st.error("The neuron examples are not in the project yet.")
        st.stop()
    if "nn_bank" not in st.session_state:
        st.session_state["nn_bank"] = load_bank()
    return st.session_state["nn_bank"]


def _render_label() -> None:
    import numpy as np

    from services.neural_interpretability import plot_top_firing_examples
    from services.neural_interpretability import top_firing_examples

    st.write(
        "Pick a latent cell. The pictures are the handwritten characters that turn that cell on most strongly."
    )
    model = _model()
    bank = _bank()
    latent_dim = model.config.latent_dim
    st.session_state.setdefault("nn_selected_neuron", 0)
    selected = int(st.session_state["nn_selected_neuron"])
    if selected < 0 or selected >= latent_dim:
        selected = 0
        st.session_state["nn_selected_neuron"] = 0

    neuron_max = np.max(bank.latents, axis=0)
    active_mask = neuron_max >= NEURON_INACTIVE_MAX
    if not np.any(active_mask):
        st.warning("No active neurons in the saved examples.")
        return
    if not active_mask[selected]:
        selected = int(np.where(active_mask)[0][0])
        st.session_state["nn_selected_neuron"] = selected

    pick_col, gallery_col = st.columns(
        [0.78, 1.22], gap="large", vertical_alignment="center"
    )
    with pick_col:
        with st.container(key="nn_neuron_picker", border=True):
            st.html('<div class="nn-picker-title">Select a neuron</div>')
            with st.container(key="nn_neurons"):
                _neuron_grid(latent_dim, active_mask, selected)
    with gallery_col:
        with st.container(key="nn_gallery"):
            st.html(
                f'<h3 class="nn-gallery-title">Neuron {selected:02d}</h3>'
            )
            examples = top_firing_examples(bank, selected, top_k=NEURON_GALLERY_K)
            st.pyplot(
                plot_top_firing_examples(
                    examples,
                    neuron_idx=selected,
                    cols_per_row=NEURON_GALLERY_COLS,
                ),
                clear_figure=True,
                width="content",
            )


def _neuron_grid(latent_dim: int, active_mask, selected: int) -> None:
    for row in range((latent_dim + NEURON_GRID_COLS - 1) // NEURON_GRID_COLS):
        cols = st.columns(NEURON_GRID_COLS, gap="small")
        for col_idx in range(NEURON_GRID_COLS):
            neuron_idx = row * NEURON_GRID_COLS + col_idx
            if neuron_idx >= latent_dim:
                break
            with cols[col_idx]:
                label = f"{neuron_idx:02d}"
                if active_mask[neuron_idx]:
                    if st.button(
                        label,
                        key=f"nn_neuron_{neuron_idx}",
                        type="primary" if neuron_idx == selected else "secondary",
                        width="stretch",
                    ):
                        st.session_state["nn_selected_neuron"] = neuron_idx
                        st.rerun()
                else:
                    st.button(
                        label,
                        key=f"nn_neuron_dead_{neuron_idx}",
                        disabled=True,
                        width="stretch",
                    )


def _shift_2d_zeros(image, *, dy: int, dx: int):
    import numpy as np

    height, width = image.shape
    out = np.zeros((height, width), dtype=np.float32)
    src_y0 = max(0, -dy)
    src_y1 = min(height, height - dy)
    src_x0 = max(0, -dx)
    src_x1 = min(width, width - dx)
    dst_y0 = max(0, dy)
    dst_x0 = max(0, dx)
    if src_y1 <= src_y0 or src_x1 <= src_x0:
        return out
    dst_y1 = dst_y0 + (src_y1 - src_y0)
    dst_x1 = dst_x0 + (src_x1 - src_x0)
    out[dst_y0:dst_y1, dst_x0:dst_x1] = image[src_y0:src_y1, src_x0:src_x1]
    return out


def _normalize_ink(ink):
    import numpy as np
    from PIL import Image
    values = np.asarray(ink, dtype=np.float32)
    if values.max() < 0.05:
        return None
    mask = values >= 0.10
    if not np.any(mask):
        return None
    ys, xs = np.where(mask)
    cropped = values[int(ys.min()) : int(ys.max()) + 1, int(xs.min()) : int(xs.max()) + 1]
    if cropped.size == 0 or cropped.max() < 0.05:
        return None
    pil = Image.fromarray((cropped * 255).astype(np.uint8), mode="L")
    width, height = pil.size
    scale = 20 / float(max(width, height))
    new_w = max(1, int(round(width * scale)))
    new_h = max(1, int(round(height * scale)))
    pil = pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
    frame = Image.new("L", (28, 28), color=0)
    frame.paste(pil, ((28 - new_w) // 2, (28 - new_h) // 2))
    arr = np.asarray(frame, dtype=np.float32) / 255.0
    total = float(arr.sum())
    if total <= 1e-6:
        return None
    ys_f = np.arange(28, dtype=np.float32)
    xs_f = np.arange(28, dtype=np.float32)
    cy = float((arr.sum(axis=1) * ys_f).sum() / total)
    cx = float((arr.sum(axis=0) * xs_f).sum() / total)
    center = 13.5
    dy = int(round(center - cy))
    dx = int(round(center - cx))
    if dy or dx:
        arr = _shift_2d_zeros(arr, dy=dy, dx=dx)
    return arr


def _canvas_to_vector(image_data):
    import numpy as np
    import torch
    from PIL import Image

    if image_data is None:
        return None
    rgba = np.asarray(Image.fromarray(image_data.astype("uint8"), "RGBA").convert("RGBA"))
    ink = np.clip(rgba[:, :, :3].mean(axis=2) / 255.0, 0.0, 1.0)
    arr = _normalize_ink(ink)
    if arr is None:
        return None
    return torch.from_numpy(arr.reshape(-1))


def _encode(model, vector):
    import torch

    from services.neural_interpretability import tensor_to_image

    with torch.no_grad():
        recon, latent = model(vector.float().view(1, -1))
    return (
        vector.numpy().reshape(28, 28),
        tensor_to_image(recon[0]),
        latent[0].detach().cpu().numpy(),
    )


def _init_draw_canvas() -> None:
    version = "nn-draw-v2"
    if st.session_state.get("nn_draw_version") != version:
        st.session_state["nn_draw_version"] = version
        st.session_state["nn_canvas_version"] = 1
        st.session_state["nn_canvas_state"] = copy.deepcopy(EMPTY_CANVAS)
        st.session_state["nn_draw_result"] = None
    st.session_state.setdefault("nn_canvas_version", 1)
    st.session_state.setdefault("nn_canvas_state", copy.deepcopy(EMPTY_CANVAS))
    st.session_state.setdefault("nn_draw_result", None)


def _render_draw() -> None:
    _init_draw_canvas()
    model = _model()
    with st.container(key="nn_draw"):
        _render_draw_body(model)


def _render_draw_body(model) -> None:
    from streamlit_drawable_canvas import st_canvas

    from services.neural_interpretability import plot_latent_grid
    from services.neural_interpretability import plot_single_digit
    from services.neural_interpretability import top_active_neurons

    st.write(
        "Draw one character to see the cleaned input, its reconstruction, and the latent cells it activates."
    )

    clear_col, _ = st.columns([1, 5])
    if clear_col.button("Clear canvas", key="nn_clear_canvas"):
        st.session_state["nn_canvas_state"] = copy.deepcopy(EMPTY_CANVAS)
        st.session_state["nn_canvas_version"] += 1
        st.session_state["nn_draw_result"] = None
        st.rerun()

    canvas_col, image_col, reconstruction_col, latent_col = st.columns(
        [1, 1, 1, 1.45], gap="large", vertical_alignment="top"
    )
    with canvas_col:
        st.html('<div class="nn-panel-title nn-canvas-title">Canvas</div>')
        canvas = st_canvas(
            fill_color="#000000",
            stroke_width=10,
            stroke_color="#FFFFFF",
            background_color="#000000",
            height=CANVAS_SIZE,
            width=CANVAS_SIZE,
            drawing_mode="freedraw",
            update_streamlit=True,
            initial_drawing=copy.deepcopy(st.session_state["nn_canvas_state"]),
            display_toolbar=True,
            key=f"nn_canvas_{st.session_state['nn_canvas_version']}",
        )

    vector = _canvas_to_vector(canvas.image_data)
    if vector is not None:
        drawn, recon, latent = _encode(model, vector)
        result = {"input": drawn, "output": recon, "latent": latent}
        st.session_state["nn_draw_result"] = result
    else:
        result = st.session_state.get("nn_draw_result")

    with image_col:
        st.html('<div class="nn-panel-title">Your drawing</div>')
        if result is None:
            st.html(
                '<div class="nn-preview-placeholder nn-preview-square" '
                'role="img" aria-label="Your drawing preview is empty"></div>'
            )
        else:
            st.pyplot(
                plot_single_digit(result["input"]),
                clear_figure=True,
                width="content",
            )

    with reconstruction_col:
        st.html('<div class="nn-panel-title">Model reconstruction</div>')
        if result is None:
            st.html(
                '<div class="nn-preview-placeholder nn-preview-square" '
                'role="img" aria-label="Model reconstruction preview is empty"></div>'
            )
        else:
            st.pyplot(
                plot_single_digit(result["output"]),
                clear_figure=True,
                width="content",
            )

    with latent_col:
        st.html('<div class="nn-panel-title">Activated latent cells</div>')
        if result is None:
            st.html(
                '<div class="nn-preview-placeholder nn-preview-latent" '
                'role="img" aria-label="Activated latent cells preview is empty"></div>'
            )
        else:
            st.pyplot(
                plot_latent_grid(result["latent"]),
                clear_figure=True,
                width="content",
            )
            leaders = top_active_neurons(result["latent"], top_k=TOP_K)
            chips = "".join(
                '<div class="nn-active-chip">'
                f'<span class="nn-active-rank">{rank}</span>'
                f'<span class="nn-active-name">Neuron {idx:02d}</span>'
                f'<strong>{value:.2f}</strong>'
                "</div>"
                for rank, (idx, value) in enumerate(leaders, start=1)
            )
            st.html(
                '<div class="nn-active-summary">'
                '<div class="nn-active-title">Most active neurons</div>'
                f'<div class="nn-active-chips">{chips}</div>'
                "</div>"
            )
