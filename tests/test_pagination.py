from types import SimpleNamespace
from poly.pagination import collect


def _single_page(items):
    return SimpleNamespace(first_page=lambda: SimpleNamespace(items=items, has_next=False))


def _two_page_paginator(page1_items, page2_items):
    page2 = SimpleNamespace(items=page2_items, has_next=False)
    page1 = SimpleNamespace(items=page1_items, has_next=True, next_page=lambda: page2)
    return SimpleNamespace(first_page=lambda: page1)


def test_collect_first_page_limit():
    assert collect(_single_page([1, 2, 3, 4, 5]), limit=3) == [1, 2, 3]


def test_collect_no_limit_returns_all_first_page():
    assert collect(_single_page([1, 2, 3])) == [1, 2, 3]


def test_collect_all_traverses_two_pages():
    """all_=True must follow has_next and collect items from both pages."""
    pag = _two_page_paginator(["a", "b"], ["c", "d"])
    result = collect(pag, all_=True)
    assert result == ["a", "b", "c", "d"]
