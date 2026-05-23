from __future__ import annotations

import re
from typing import Dict, List, Protocol


WordCatalog = Dict[str, Dict[str, List[str]]]
USER_WORDS_SUBJECT = "Свои слова"


def parse_user_words(raw_words: str) -> List[str]:
    seen = set()
    words = []
    for word in re.split(r"[\n,;]+", raw_words or ""):
        normalized = word.strip()
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        words.append(normalized)
    return words


class WordProvider(Protocol):
    def get_words(self, subject: str, difficulty_id: str, language_code: str = "ru") -> List[str]:
        ...

    def get_subjects(self, language_code: str = "ru") -> List[str]:
        ...

    def get_catalog(self, language_code: str = "ru") -> WordCatalog:
        ...


class StaticWordProvider:
    def __init__(self, base_catalog: WordCatalog, localized_catalogs: Dict[str, WordCatalog]):
        self._base_catalog = base_catalog
        self._localized_catalogs = localized_catalogs

    def get_words(self, subject: str, difficulty_id: str, language_code: str = "ru") -> List[str]:
        catalog = self.get_catalog(language_code)
        words = catalog.get(subject, {}).get(difficulty_id, [])
        if words:
            return list(words)

        fallback_words = self._base_catalog.get(subject, {}).get(difficulty_id, [])
        return list(fallback_words)

    def get_subjects(self, language_code: str = "ru") -> List[str]:
        catalog = self.get_catalog(language_code)
        subjects = list(catalog.keys())
        if subjects:
            return subjects
        return list(self._base_catalog.keys())

    def get_catalog(self, language_code: str = "ru") -> WordCatalog:
        if language_code == "ru":
            return self._base_catalog
        return self._localized_catalogs.get(language_code, self._base_catalog)


class UserWordProvider:
    def __init__(self, base_provider: WordProvider, custom_subject: str = USER_WORDS_SUBJECT):
        self._base_provider = base_provider
        self.custom_subject = custom_subject
        self._user_words: List[str] = []

    def set_user_words(self, words: List[str]):
        self._user_words = list(words)

    def get_user_words(self) -> List[str]:
        return list(self._user_words)

    def has_user_words(self) -> bool:
        return bool(self._user_words)

    def get_words(self, subject: str, difficulty_id: str, language_code: str = "ru") -> List[str]:
        if subject == self.custom_subject and self._user_words:
            return list(self._user_words)
        return self._base_provider.get_words(subject, difficulty_id, language_code)

    def get_subjects(self, language_code: str = "ru") -> List[str]:
        subjects = self._base_provider.get_subjects(language_code)
        if self._user_words:
            return [self.custom_subject, *[subject for subject in subjects if subject != self.custom_subject]]
        return [subject for subject in subjects if subject != self.custom_subject]

    def get_catalog(self, language_code: str = "ru") -> WordCatalog:
        catalog = self._base_provider.get_catalog(language_code)
        if not self._user_words:
            return catalog
        return {
            self.custom_subject: {
                "easy": list(self._user_words),
                "medium": list(self._user_words),
                "hard": list(self._user_words),
            },
            **catalog,
        }
