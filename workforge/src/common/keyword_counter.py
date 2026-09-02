import re
from collections import namedtuple
from functools import cached_property
from typing import Iterable

MarkersCountResult = namedtuple("MarkersCountResult", ["name", "count_kw", "matched_keywords"])


class AbstractKeywordCounter:

    def count_keywords(self, text: str) -> MarkersCountResult: ...


class BaseKeywordCounter(AbstractKeywordCounter):

    def matches(self, pattern: re.Pattern[str] | None, text: str) -> Iterable:
        if not pattern or not text:
            return tuple()

        unique_matches = {match.group(0).casefold() for match in pattern.finditer(text)}
        return unique_matches

    def _count_matches(self, pattern: re.Pattern[str] | None, text: str) -> int:
        if not pattern or not text:
            return 0

        markers = self._extract_markers_from_pattern(pattern)
        marker_patterns = self._build_marker_patterns(markers)
        return self._count_marker_matches(marker_patterns, text)

    def marker_matches(
        self, marker_patterns: Iterable[tuple[str, re.Pattern[str]]], text: str
    ) -> Iterable[str]:
        if not text:
            return tuple()
        return tuple(
            marker
            for marker, marker_pattern in marker_patterns
            if marker_pattern.search(text)
        )

    def _count_marker_matches(
        self, marker_patterns: Iterable[tuple[str, re.Pattern[str]]], text: str
    ) -> int:
        return len(tuple(self.marker_matches(marker_patterns, text)))

    def _build_marker_patterns(
        self, keywords: list[str]
    ) -> tuple[tuple[str, re.Pattern[str]], ...]:
        marker_patterns: list[tuple[str, re.Pattern[str]]] = []
        seen_normalized: set[str] = set()
        for keyword in keywords:
            if not keyword or not keyword.strip():
                continue
            marker = keyword.strip()
            normalized = marker.casefold()
            if normalized in seen_normalized:
                continue
            seen_normalized.add(normalized)

            pattern = self._build_pattern([marker])
            if pattern is not None:
                marker_patterns.append((marker, pattern))
        return tuple(marker_patterns)

    @staticmethod
    def _extract_markers_from_pattern(pattern: re.Pattern[str]) -> list[str]:
        raw = pattern.pattern
        prefix = r"(?<![\w-])(?:"
        if not (raw.startswith(prefix) and raw.endswith(")")):
            return []

        body = raw[len(prefix) : -1]
        markers: list[str] = []
        for token in body.split("|"):
            if not token.endswith(r"\w*"):
                continue
            escaped = token[: -len(r"\w*")]
            escaped = escaped.replace(r"\w{0,2}", "*")
            markers.append(re.sub(r"\\(.)", r"\1", escaped))
        return markers

    @staticmethod
    def _build_pattern(keywords: list[str]) -> re.Pattern[str] | None:
        cleaned = [
            keyword.strip() for keyword in keywords if keyword and keyword.strip()
        ]
        if not cleaned:
            return None

        escaped_keywords = []
        for keyword in cleaned:
            last_token = keyword.rsplit(None, 1)[-1]
            if last_token and all(ch == "*" for ch in last_token):
                continue

            escaped = re.escape(keyword).replace(r"\*", r"\w{0,3}")
            should_allow_right_continuation = "*" not in last_token
            escaped_keywords.append(
                escaped + (r"\w*" if should_allow_right_continuation else "")
            )
        if not escaped_keywords:
            return None
        # Match marker only when it starts a token; allow any continuation on the right.
        pattern = r"(?<![\w-])(?:" + "|".join(escaped_keywords) + r")"
        return re.compile(pattern, flags=re.IGNORECASE)


class MarkersCounter(BaseKeywordCounter):
    def __init__(self, keywords: list[str], name: str) -> None:
        self._keywords = keywords
        self.name = name

    @cached_property
    def pattern(self) -> re.Pattern | None:
        return self._build_pattern(self._keywords)

    @cached_property
    def marker_patterns(self) -> tuple[tuple[str, re.Pattern[str]], ...]:
        return self._build_marker_patterns(self._keywords)

    def count_keywords(self, text: str) -> MarkersCountResult:
        matched_keywords = list(self.marker_matches(self.marker_patterns, text))
        return MarkersCountResult(
            name=self.name,
            count_kw=len(matched_keywords),
            matched_keywords=matched_keywords,
        )
