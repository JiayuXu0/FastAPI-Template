import importlib
import sys
import types

import pytest


class FakeAutomaton:
    def __init__(self):
        self._words: list[tuple[str, tuple[int, str]]] = []

    def add_word(self, word: str, value: tuple[int, str]) -> None:
        self._words.append((word, value))

    def make_automaton(self) -> None:  # pragma: no cover - nothing to build for the fake
        return None

    def iter(self, text: str):
        lower = text.lower()
        for word, value in self._words:
            start = lower.find(word)
            if start != -1:
                end_index = start + len(word) - 1
                yield end_index, value


@pytest.fixture()
def filter_module(monkeypatch):
    fake_settings = types.SimpleNamespace(
        ENABLE_SENSITIVE_WORD_FILTER=True,
        SENSITIVE_WORD_RESPONSE="命中敏感词",
        SENSITIVE_WORDS=["敏感词", "违禁"],
    )

    fake_settings_module = types.ModuleType("settings.config")
    fake_settings_module.settings = fake_settings
    fake_settings_package = types.ModuleType("settings")
    fake_settings_package.config = fake_settings_module

    monkeypatch.setitem(sys.modules, "settings.config", fake_settings_module)
    monkeypatch.setitem(sys.modules, "settings", fake_settings_package)
    monkeypatch.setitem(sys.modules, "ahocorasick", types.SimpleNamespace(Automaton=FakeAutomaton))

    sys.modules.pop("src.utils.sensitive_word_filter", None)
    module = importlib.import_module("src.utils.sensitive_word_filter")
    try:
        yield module, fake_settings
    finally:
        sys.modules.pop("src.utils.sensitive_word_filter", None)


def test_contains_sensitive_word_detects_match(filter_module):
    module, _ = filter_module
    filter_instance = module.SensitiveWordFilter()

    has_match, word = filter_instance.contains_sensitive_word("这里包含敏感词内容")

    assert has_match is True
    assert word == "敏感词"


def test_filter_text_returns_response_for_sensitive_content(filter_module):
    module, _ = filter_module
    filter_instance = module.SensitiveWordFilter()

    assert filter_instance.filter_text("安全内容") == "安全内容"
    assert filter_instance.filter_text("违禁行为") == "命中敏感词"


def test_streaming_chunk_with_sensitive_answer_is_blocked(filter_module):
    module, _ = filter_module
    filter_instance = module.SensitiveWordFilter()

    chunk = "data: {\"answer\": \"包含敏感词\"}"
    assert filter_instance.filter_streaming_chunk(chunk) is None


def test_streaming_chunk_with_invalid_json_falls_back_to_text(filter_module):
    module, _ = filter_module
    filter_instance = module.SensitiveWordFilter()

    chunk = "data: 原始违禁文本"
    assert filter_instance.filter_streaming_chunk(chunk) is None


def test_reload_sensitive_words_uses_updated_list(filter_module):
    module, settings_stub = filter_module
    filter_instance = module.SensitiveWordFilter()

    settings_stub.SENSITIVE_WORDS = ["全新词"]
    assert filter_instance.reload_sensitive_words() is True

    has_match, word = filter_instance.contains_sensitive_word("这里有全新词")
    assert has_match is True
    assert word == "全新词"


def test_disabled_filter_bypasses_checks(monkeypatch, filter_module):
    module, settings_stub = filter_module
    monkeypatch.setattr(settings_stub, "ENABLE_SENSITIVE_WORD_FILTER", False)

    filter_instance = module.SensitiveWordFilter()

    assert filter_instance.enabled is False
    assert filter_instance.contains_sensitive_word("违禁") == (False, None)
    assert filter_instance.filter_streaming_chunk("data: {\"answer\": \"违禁\"}") == "data: {\"answer\": \"违禁\"}"
