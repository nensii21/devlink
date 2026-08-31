# Global Search Engine

The **Global Search Engine** in DevLink is designed to provide rapid, full-text discovery across all core platform entities, including Projects, Users, Issues, Organizations, and Posts.

## Architecture

The search subsystem uses a generic `SearchEngineProvider` interface. This pluggable design ensures that while local development and testing can utilize the default `InMemorySearchEngine` without any external dependencies, production environments can effortlessly substitute a more robust engine such as Elasticsearch, Redisearch, or Algolia by implementing the provider.

### Features
1. **Multi-Index Discovery**: Search seamlessly aggregates entities across varied types using unified generic indexing.
2. **Compound Ranking Algorithm**: A specialized ranking formula calculates real-time scores for each returned document:
   - *Relevance (TF)*: Basic Term Frequency match.
   - *Recency*: An exponential time-decay function (30-day halflife) prioritizes newer entities.
   - *Popularity*: A logarithmic scale is applied to `popularity_score` to prioritize active entities without drowning out highly relevant smaller entities.
3. **Filtering & Faceting**: Dynamic faceted grouping calculates total available entity types and tags within the search context. Results can be strictly filtered by `date_range`, `entity_type`, or specific `tags`.
4. **Autocomplete (Prefix Trie)**: As users type, the `/autocomplete` endpoint traverses an in-memory prefix trie, surfacing token suggestions mathematically ranked by index frequency.

## Usage

```python
from app.services.search_engine_service import search_engine_service, SearchResultItem

# 1. Indexing
search_engine_service.index_entity(SearchResultItem(
    entity_id="proj_123",
    entity_type="project",
    title="Next.js Starter",
    description="A great template for web apps.",
    popularity_score=150,
    tags=["react", "nextjs"]
))

# 2. Searching
response = search_engine_service.search("template", tags=["react"])
print(response.total_count) 
print(response.facets)
print(response.results[0].score)

# 3. Autocomplete
suggestions = search_engine_service.autocomplete("tem")
```

## Future Considerations
- Integrate standard stemming (NLTK/Snowball) or fuzzy matching (Levenshtein distance).
- Switch the deployment container in production to Elasticsearch by subclassing `SearchEngineProvider`.
