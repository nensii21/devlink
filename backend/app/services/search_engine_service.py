"""
Global Search Engine service module.
Provides in-memory token indexing, keyword search, faceted filtering, ranking, and autocomplete.
"""

from typing import List, Dict, Set, Any, Optional, Tuple
from dataclasses import dataclass, field
import re
from datetime import datetime, timezone
import math


@dataclass
class SearchResultItem:
    entity_id: str
    entity_type: str  # e.g., "project", "user", "issue", "org", "post"
    title: str
    description: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    popularity_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    custom_attributes: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0  # Dynamic ranking score computed during search


@dataclass
class SearchFacetResult:
    entity_types: Dict[str, int]
    tags: Dict[str, int]


@dataclass
class SearchResponse:
    results: List[SearchResultItem]
    total_count: int
    facets: SearchFacetResult


class SearchEngineProvider:
    """Abstract interface for pluggable search engines (e.g., Elasticsearch, Redisearch)."""
    def index_entity(self, item: SearchResultItem) -> None:
        raise NotImplementedError

    def search(
        self, query: str, entity_type: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 20
    ) -> SearchResponse:
        raise NotImplementedError
        
    def autocomplete(self, prefix: str, limit: int = 5) -> List[str]:
        raise NotImplementedError

    def clear_index(self) -> None:
        raise NotImplementedError


class InMemorySearchEngine(SearchEngineProvider):
    """In-memory multi-entity search engine with ranking, filtering, and autocomplete."""

    def __init__(self):
        self._index: Dict[str, Set[str]] = {}  # token -> set of entity keys
        self._entities: Dict[str, SearchResultItem] = {}  # key -> entity
        self._autocomplete_trie: Dict[str, Set[str]] = {} # Prefix to tokens

    def _tokenize(self, text: str) -> List[str]:
        """Extracts and normalizes alphanumeric tokens."""
        return [t.lower() for t in re.findall(r'\w+', text) if len(t) > 1]

    def _add_to_autocomplete(self, token: str):
        """Indexes all prefixes of a token for fast autocomplete."""
        for i in range(1, len(token) + 1):
            prefix = token[:i]
            if prefix not in self._autocomplete_trie:
                self._autocomplete_trie[prefix] = set()
            self._autocomplete_trie[prefix].add(token)

    def index_entity(self, item: SearchResultItem) -> None:
        """Indexes an entity with all its metadata."""
        key = f"{item.entity_type}:{item.entity_id}"
        self._entities[key] = item
        
        combined_text = f"{item.title} {item.description} {' '.join(item.tags)}"
        tokens = self._tokenize(combined_text)

        for token in set(tokens):
            if token not in self._index:
                self._index[token] = set()
            self._index[token].add(key)
            self._add_to_autocomplete(token)

    def _calculate_score(self, item: SearchResultItem, query_tokens: List[str]) -> float:
        """
        Ranking algorithm combining relevance (TF), recency, and popularity.
        """
        # Relevance: very basic token match counting
        combined_text = f"{item.title} {item.description} {' '.join(item.tags)}".lower()
        relevance = sum(combined_text.count(token) for token in query_tokens)

        # Recency: decay over time (e.g., halflife of 30 days)
        age_days = (datetime.now(timezone.utc) - item.created_at).days
        recency_score = math.exp(-age_days / 30.0) if age_days > 0 else 1.0

        # Popularity: log-scaled to avoid overwhelming other signals
        popularity = math.log1p(item.popularity_score)

        # Weighted combination
        return (relevance * 2.0) + (recency_score * 1.5) + (popularity * 1.0)

    def search(
        self, 
        query: str, 
        entity_type: Optional[str] = None, 
        tags: Optional[List[str]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 20
    ) -> SearchResponse:
        """Executes full-text keyword search with filtering, ranking, and faceting."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return SearchResponse(results=[], total_count=0, facets=SearchFacetResult({}, {}))

        matched_keys: Set[str] = set()
        for token in query_tokens:
            if token in self._index:
                if not matched_keys:
                    matched_keys = set(self._index[token])
                else:
                    # AND logic for multiple tokens
                    matched_keys.intersection_update(self._index[token])
            else:
                # If a token isn't found at all, AND logic means 0 matches
                matched_keys = set()
                break

        results: List[SearchResultItem] = []
        facets = SearchFacetResult(entity_types={}, tags={})

        for key in matched_keys:
            item = self._entities.get(key)
            if not item:
                continue
                
            # Filtering
            if entity_type and item.entity_type != entity_type:
                continue
                
            if tags and not all(t.lower() in [it.lower() for it in item.tags] for t in tags):
                continue
                
            if date_range:
                start_date, end_date = date_range
                if not (start_date <= item.created_at <= end_date):
                    continue

            # Compute rank
            scored_item = SearchResultItem(
                entity_id=item.entity_id,
                entity_type=item.entity_type,
                title=item.title,
                description=item.description,
                created_at=item.created_at,
                popularity_score=item.popularity_score,
                tags=item.tags,
                custom_attributes=item.custom_attributes,
                score=self._calculate_score(item, query_tokens)
            )
            results.append(scored_item)
            
            # Aggregate Facets
            facets.entity_types[item.entity_type] = facets.entity_types.get(item.entity_type, 0) + 1
            for tag in item.tags:
                facets.tags[tag] = facets.tags.get(tag, 0) + 1

        # Sort by computed score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return SearchResponse(
            results=results[:limit],
            total_count=len(results),
            facets=facets
        )

    def autocomplete(self, prefix: str, limit: int = 5) -> List[str]:
        """Returns autocomplete suggestions based on prefix matching."""
        prefix = prefix.lower().strip()
        if not prefix or prefix not in self._autocomplete_trie:
            return []
            
        matched_tokens = list(self._autocomplete_trie[prefix])
        
        # Rank suggestions by how many documents contain them (frequency)
        token_freq = {t: len(self._index.get(t, [])) for t in matched_tokens}
        matched_tokens.sort(key=lambda x: token_freq[x], reverse=True)
        
        return matched_tokens[:limit]

    def clear_index(self) -> None:
        self._index.clear()
        self._entities.clear()
        self._autocomplete_trie.clear()


# Default singleton instance (pluggable in the future)
search_engine_service = InMemorySearchEngine()
