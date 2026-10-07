from __future__ import annotations

import json
from html import escape
from pathlib import Path

import streamlit as st
from lectures import LECTURES, SUB_LECTURES, TOPICS, get_lecture

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
STYLES = ROOT / "styles" / "app.css"
CHROME_JS = ROOT / "static" / "lecture_chrome.js"
FAVICON = ASSETS / "favicon.svg"

BITSOM_LOGO = (
    "https://www.bitsom.edu.in/wp-content/uploads/2023/04/zero_scroll_logo-icn-1.svg"
)


RACHIT = "Dr. Rachit Kamdar"
MEENAKSHI = "Dr. Meenakshi Balakrishna"
LECTURE_HOSTS = {
    1: (RACHIT,),
    2: (MEENAKSHI,),
    3: (MEENAKSHI,),
    4: (MEENAKSHI,),
    5: (RACHIT,),
    6: (RACHIT,),
    7: (RACHIT, MEENAKSHI),
    8: (RACHIT,),
    9: (MEENAKSHI,),
    10: (MEENAKSHI, RACHIT),
}


def lecture_number(lecture: str | None) -> int | None:
    if not lecture:
        return None
    token = lecture.split()[-1]
    return int(token) if token.isdigit() else None


def header_hosts(lecture: str | None) -> tuple[str, ...]:
    number = lecture_number(lecture)
    if number is None:
        return ()
    return LECTURE_HOSTS.get(number, ())


def header_greeting_html(lecture: str | None) -> str:
    hosts = header_hosts(lecture)
    if not hosts:
        return ""
    if len(hosts) > 1:
        hi = "Hi Professors!"
    else:
        hi = f"Hi {escape(hosts[0])}!"
    return (
        '<div class="lecture-header-cards">'
        '<div class="lecture-header-card">'
        f'<div class="lecture-header-greeting-hi">{hi}</div>'
        '<div class="lecture-header-greeting-wish">Welcome to your teaching space</div>'
        "</div>"
        "</div>"
    )


def inject_css() -> None:
    st.html(STYLES)
    code = json.dumps(CHROME_JS.read_text(encoding="utf-8"))
    with st.container(key="chrome_js"):
        st.iframe(
            "<script>(function () {"
            "var host = window.parent;"
            "if (host.__lectureChrome) return;"
            "var s = host.document.createElement('script');"
            f"s.textContent = {code};"
            "host.document.head.appendChild(s);"
            "})();</script>",
            height=1,
        )


def clear_sub_lecture() -> None:
    st.session_state.sub_lecture_select = None
    reset_topic()


def reset_topic() -> None:
    sub = st.session_state.get("sub_lecture_select")
    st.session_state[f"topic_select::{sub}"] = None


def reset_after_lecture() -> None:
    st.session_state.sub_lecture_select = None
    reset_topic()


def clear_topic() -> None:
    reset_topic()


def breadcrumb_html(
    lecture: str | None, sub_lecture: str | None, topic: str | None
) -> str:
    if not lecture:
        return ""
    parts: list[str] = []
    if sub_lecture:
        parts.append(
            f'<span class="crumb-link" role="button" tabindex="0" data-level="lecture">{lecture}</span>'
        )
        parts.append('<span class="crumb-sep">&gt;</span>')
        if topic:
            parts.append(
                f'<span class="crumb-link" role="button" tabindex="0" data-level="sub">{sub_lecture}</span>'
            )
            parts.append('<span class="crumb-sep">&gt;</span>')
            parts.append(f'<span class="crumb-current">{topic}</span>')
        else:
            parts.append(f'<span class="crumb-current">{sub_lecture}</span>')
    else:
        parts.append(f'<span class="crumb-current">{lecture}</span>')
    return f'<nav class="lesson-crumb" aria-label="Location">{"".join(parts)}</nav>'


def render_crumbs(lecture: str | None, sub_lecture: str | None, topic: str | None) -> None:
    if lecture and sub_lecture:
        st.button(
            lecture,
            key="crumb_lecture",
            type="tertiary",
            on_click=clear_sub_lecture,
        )
    if lecture and sub_lecture and topic:
        st.button(
            sub_lecture,
            key="crumb_sub",
            type="tertiary",
            on_click=clear_topic,
        )


def render_header(lecture: str | None = None) -> None:
    greet_html = header_greeting_html(lecture)
    st.markdown(
        f"""
        <header class="lecture-header">
          <div class="lecture-header-inner">
            <div class="lecture-header-logo">
              <img src="{BITSOM_LOGO}" alt="BITSoM Logo" />
            </div>
            <div class="lecture-header-text">
              <span class="lecture-header-title">Foundations of AI</span>
              <span class="lecture-header-sub">AI Course</span>
            </div>
            {greet_html}
          </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_workspace(
    lecture: str | None, sub_lecture: str | None, topic: str | None
) -> None:
    chapter = get_lecture(lecture)
    render_fn = getattr(chapter, "render", None) if chapter else None
    if lecture and sub_lecture and topic and callable(render_fn):
        render_fn(
            lecture,
            sub_lecture,
            topic,
            crumbs=breadcrumb_html(lecture, sub_lecture, topic),
        )
        render_crumbs(lecture, sub_lecture, topic)
        return

    crumbs = breadcrumb_html(lecture, sub_lecture, topic)
    if lecture and sub_lecture:
        number = lecture.split()[-1]
        ring = number
        heading = sub_lecture
        topic_options = TOPICS.get((lecture, sub_lecture), [])
        pick_map = getattr(chapter, "PICK_TOPIC_BY_SUB", None) if chapter else None
        pick_topic = ""
        if isinstance(pick_map, dict):
            pick_topic = pick_map.get(sub_lecture, "")
        if not pick_topic:
            pick_topic = getattr(chapter, "PICK_TOPIC", "") if chapter else ""
        body = (
            pick_topic
            if topic_options and pick_topic
            else f"Content for {lecture} · {sub_lecture} will land here next."
        )
        pill = "Select a topic" if topic_options else sub_lecture
    elif lecture:
        number = lecture.split()[-1]
        subs = SUB_LECTURES.get(lecture, [])
        ring = number
        heading = f"{lecture} is selected"
        pick_sub = getattr(chapter, "PICK_SUB", "") if chapter else ""
        body = (
            pick_sub
            if subs and pick_sub
            else "Sub lectures are not wired yet for this lecture."
        )
        pill = "Select a sub lecture" if subs else "Sub lecture · coming soon"
    else:
        number = "—"
        ring = "AI"
        heading = "Welcome to the lecture workspace"
        body = "Choose a lecture from the side pane. Sub lectures appear when that lecture has them."
        pill = "Local preview"

    st.markdown(
        f"""
        <section class="lesson-block">
          <div class="lesson-block-header">
            <div class="lesson-number">{number}</div>
            {crumbs}
          </div>
          <div class="lesson-block-body">
            <div class="lesson-empty">
              <div class="lesson-empty-ring">{ring}</div>
              <p class="lesson-empty-title">{heading}</p>
              <p>{body}</p>
              <span class="lesson-pill">{pill}</span>
            </div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_crumbs(lecture, sub_lecture, topic)


st.set_page_config(
    page_title="Foundations of AI",
    page_icon=str(FAVICON),
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

with st.sidebar:
    lecture = st.selectbox(
        "Lecture",
        options=LECTURES,
        index=None,
        placeholder="Select a lecture",
        accept_new_options=False,
        key="lecture_select",
        on_change=reset_after_lecture,
    )
    sub_options = SUB_LECTURES.get(lecture or "", [])
    if sub_options:
        sub_lecture = st.selectbox(
            "Sub lecture",
            options=sub_options,
            index=None,
            placeholder="Select a sub lecture",
            accept_new_options=False,
            key="sub_lecture_select",
            on_change=reset_topic,
        )
    else:
        sub_lecture = None
        st.selectbox(
            "Sub lecture",
            options=["Coming soon"],
            index=0,
            disabled=True,
            accept_new_options=False,
            key="sub-disabled",
        )
    topic_options = TOPICS.get((lecture or "", sub_lecture or ""), [])
    if topic_options:
        topic = st.selectbox(
            "Topic",
            options=topic_options,
            index=None,
            placeholder="Select a topic",
            accept_new_options=False,
            key=f"topic_select::{sub_lecture}",
        )
        if topic not in topic_options:
            topic = None
    else:
        topic = None

render_header(lecture)
render_workspace(lecture, sub_lecture, topic)
