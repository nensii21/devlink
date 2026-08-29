"""
Global Search Engine service module.
Provides in-memory token indexing, keyword search, faceted filtering, and ranking.
"""

from typing import List, Dict, Set, Any, Optional
from dataclasses import dataclass, field
import re


@dataclass
class SearchResultItem:
    entity_id: str
    entity_type: str  # "project", "user", "issue", "doc"
    title: str
    description: str
    score: float = 1.0
    tags: List[str] = field(default_factory=list)


class SearchEngineService:
    """In-memory inverted index and multi-entity search service."""

    def __init__(self):
        self._index: Dict[str, Set[str]] = {}  # token -> set of entity keys
        self._entities: Dict[str, SearchResultItem] = {}  # key -> entity

    def _tokenize(self, text: str) -> List[str]:
        """Extracts and normalizes alphanumeric tokens."""
        return [t.lower() for t in re.findall(r'\w+', text) if len(t) > 1]

    def index_entity(self, item: SearchResultItem) -> None:
        """Indexes a project, user, or documentation item."""
        key = f"{item.entity_type}:{item.entity_id}"
        self._entities[key] = item
        combined_text = f"{item.title} {item.description} {' '.join(item.tags)}"
        tokens = self._tokenize(combined_text)

        for token in tokens:
            if token not in self._index:
                self._index[token] = set()
            self._index[token].add(key)

    def search(
        self, query: str, entity_type: Optional[str] = None, limit: int = 20
    ) -> List[SearchResultItem]:
        """Executes full-text keyword search across all indexed items."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        matched_keys: Set[str] = set()
        for token in query_tokens:
            if token in self._index:
                if not matched_keys:
                    matched_keys = set(self._index[token])
                else:
                    matched_keys.update(self._index[token])

        results: List[SearchResultItem] = []
        for key in matched_keys:
            item = self._entities.get(key)
            if item:
                if entity_type and item.entity_type != entity_type:
                    continue
                results.append(item)

        return results[:limit]

    def clear_index(self) -> None:
        self._index.clear()
        self._entities.clear()


search_engine_service = SearchEngineService()
