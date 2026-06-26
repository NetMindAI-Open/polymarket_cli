from types import SimpleNamespace
from poly.pagination import collect


def _single_page(items):
    return SimpleNamespace(first_page=lambda: SimpleNamespace(items=items, has_next=False))


def test_collect_first_page_limit():
    assert collect(_single_page([1, 2, 3, 4, 5]), limit=3) == [1, 2, 3]


def test_collect_no_limit_returns_all_first_page():
    assert collect(_single_page([1, 2, 3])) == [1, 2, 3]
