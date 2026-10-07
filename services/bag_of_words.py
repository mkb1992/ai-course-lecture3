from __future__ import annotations

import re
from collections import Counter

import streamlit as st

_PAIR = ("The bank raised interest rates", "We sat on the river bank")


def _vocab(sentences: tuple[str, ...]) -> list[str]:
    seen: list[str] = []
    for s in sentences:
        for w in re.findall(r"[a-z]+", s.lower()):
            if w not in seen:
                seen.append(w)
    return seen


def _count_table(sentences: tuple[str, ...]) -> str:
    vocab = _vocab(sentences)
    head = "".join(f"<th>{w}</th>" for w in vocab)
    rows = []
    for s in sentences:
        counts = Counter(re.findall(r"[a-z]+", s.lower()))
        cells = "".join(
            f'<td class="{"one" if counts[w] else "zero"}">{counts[w]}</td>' for w in vocab
        )
        rows.append(f"<tr><td><i>{s}</i></td>{cells}</tr>")
    return (
        '<div class="bow-wrap"><table class="w2x-set bow-t">'
        f"<thead><tr><th>Sentence</th>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def render() -> None:
    st.html(
        f"""
        <section class="cmx-card dtx-card w2x" aria-labelledby="bow-title">
          <div class="cmx-deco" aria-hidden="true"><span class="cmx-dots"></span><span class="cmx-c1"></span><span class="cmx-c2"></span></div>
          <div class="cmx-kicker">Bag of Words</div>
          <h2 id="bow-title">Counting words &ndash; the first way to turn text into numbers</h2>
          <p class="dtx-lead">A model can only work with numbers, so text has to become numbers first. The simplest way is
          <b>Bag of Words</b> &ndash; list every word that appears, then count how many times each word occurs in a
          sentence. That row of counts is the sentence&rsquo;s vector. The words are thrown into a bag, and only the
          counts are kept.</p>

          <h3>Turn two sentences into counts</h3>
          <p class="dtx-lead">Every word becomes a column. A sentence gets a <b>1</b> where the word appears and a
          <b>0</b> where it does not &ndash; a word used twice gets a 2.</p>
          {_count_table(_PAIR)}

          <h3>What the counts lose</h3>
          <ol class="w2x-steps">
            <li><b class="t">Word order</b>
            <i>The dog bit the man</i> and <i>The man bit the dog</i> have exactly the same counts &ndash; <i>the</i> twice,
            <i>dog</i>, <i>bit</i> and <i>man</i> once each. To Bag of Words they are the same sentence, although they
            describe very different events.</li>
            <li><b class="t">Meaning</b>
            <i>The meeting was cancelled</i> and <i>The session was called off</i> mean the same thing, but apart from
            <i>the</i> and <i>was</i> they share no words, so their counts look unrelated. Counting cannot know that
            <i>cancelled</i> and <i>called off</i> are close in meaning.</li>
            <li><b class="t">Context</b>
            In the table above, <i>bank</i> gets the same column in both sentences. The counts cannot say whether it is
            the bank that raised interest rates or the bank of a river.</li>
          </ol>

          <h3>Where it is still used</h3>
          <p class="dtx-lead">Bag of Words is fast, cheap and easy to explain, so it still powers simple spam filters,
          keyword search and quick topic tagging. A common upgrade, <b>TF-IDF</b>, gives rare words more weight than
          common ones such as <i>the</i> &ndash; but it still only counts.</p>

          <div class="w2x-note"><b>What comes next</b> &ndash; <b>Word2Vec</b> fixes the meaning problem. Instead of
          counting, it learns a place in space for every word from the words around it, so <i>cancelled</i> and
          <i>called off</i> end up as neighbours. Open <b>What is Word2Vec</b> to see how. Later,
          <b>Attention</b> fixes the context problem, and <b>Sentence Embeddings</b> turns a whole sentence into one
          vector.</div>
        </section>
        """
    )
