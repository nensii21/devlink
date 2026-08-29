from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.search_analytics_metric_category_distribution import (
        SearchAnalyticsMetricCategoryDistribution,
    )
    from ..models.search_analytics_metric_top_queries_item import (
        SearchAnalyticsMetricTopQueriesItem,
    )
    from ..models.search_analytics_metric_zero_result_queries_item import (
        SearchAnalyticsMetricZeroResultQueriesItem,
    )


T = TypeVar("T", bound="SearchAnalyticsMetric")


@_attrs_define
class SearchAnalyticsMetric:
    """
    Attributes:
        total_searches (int):
        avg_latency_ms (float):
        top_queries (list[SearchAnalyticsMetricTopQueriesItem]):
        zero_result_queries (list[SearchAnalyticsMetricZeroResultQueriesItem]):
        category_distribution (SearchAnalyticsMetricCategoryDistribution):
    """

    total_searches: int
    avg_latency_ms: float
    top_queries: list[SearchAnalyticsMetricTopQueriesItem]
    zero_result_queries: list[SearchAnalyticsMetricZeroResultQueriesItem]
    category_distribution: SearchAnalyticsMetricCategoryDistribution
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_searches = self.total_searches

        avg_latency_ms = self.avg_latency_ms

        top_queries = []
        for top_queries_item_data in self.top_queries:
            top_queries_item = top_queries_item_data.to_dict()
            top_queries.append(top_queries_item)

        zero_result_queries = []
        for zero_result_queries_item_data in self.zero_result_queries:
            zero_result_queries_item = zero_result_queries_item_data.to_dict()
            zero_result_queries.append(zero_result_queries_item)

        category_distribution = self.category_distribution.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_searches": total_searches,
                "avg_latency_ms": avg_latency_ms,
                "top_queries": top_queries,
                "zero_result_queries": zero_result_queries,
                "category_distribution": category_distribution,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.search_analytics_metric_category_distribution import (
            SearchAnalyticsMetricCategoryDistribution,
        )
        from ..models.search_analytics_metric_top_queries_item import (
            SearchAnalyticsMetricTopQueriesItem,
        )
        from ..models.search_analytics_metric_zero_result_queries_item import (
            SearchAnalyticsMetricZeroResultQueriesItem,
        )

        d = dict(src_dict)
        total_searches = d.pop("total_searches")

        avg_latency_ms = d.pop("avg_latency_ms")

        top_queries = []
        _top_queries = d.pop("top_queries")
        for top_queries_item_data in _top_queries:
            top_queries_item = SearchAnalyticsMetricTopQueriesItem.from_dict(
                top_queries_item_data
            )

            top_queries.append(top_queries_item)

        zero_result_queries = []
        _zero_result_queries = d.pop("zero_result_queries")
        for zero_result_queries_item_data in _zero_result_queries:
            zero_result_queries_item = (
                SearchAnalyticsMetricZeroResultQueriesItem.from_dict(
                    zero_result_queries_item_data
                )
            )

            zero_result_queries.append(zero_result_queries_item)

        category_distribution = SearchAnalyticsMetricCategoryDistribution.from_dict(
            d.pop("category_distribution")
        )

        search_analytics_metric = cls(
            total_searches=total_searches,
            avg_latency_ms=avg_latency_ms,
            top_queries=top_queries,
            zero_result_queries=zero_result_queries,
            category_distribution=category_distribution,
        )

        search_analytics_metric.additional_properties = d
        return search_analytics_metric

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
