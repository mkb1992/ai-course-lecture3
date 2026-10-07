from __future__ import annotations

from types import ModuleType

from . import (
    lecture_01,
    lecture_02,
    lecture_03,
    lecture_04,
    lecture_05,
    lecture_06,
    lecture_07,
    lecture_08,
    lecture_09,
    lecture_10,
)

MODULES: list[ModuleType] = [
    lecture_01,
    lecture_02,
    lecture_03,
    lecture_04,
    lecture_05,
    lecture_06,
    lecture_07,
    lecture_08,
    lecture_09,
    lecture_10,
]

LECTURES = [module.TITLE for module in MODULES]
SUB_LECTURES = {module.TITLE: list(module.SUB_LECTURES) for module in MODULES}
TOPICS = {
    (module.TITLE, sub): list(topics)
    for module in MODULES
    for sub, topics in module.TOPICS.items()
}
BY_TITLE = {module.TITLE: module for module in MODULES}


def get_lecture(title: str | None) -> ModuleType | None:
    if not title:
        return None
    return BY_TITLE.get(title)
