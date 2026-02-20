"""Tests for search tools and search node."""

import pytest
from unittest.mock import patch, MagicMock

from agent.tools.search_tool import search_events, search_paid_events, search_by_category
from agent.nodes.search import search_activities


class TestSearchEvents:
    @patch("agent.tools.search_tool.TavilyClient")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_basic_search_returns_results(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = {
            "results": [
                {"title": "Art Workshop", "url": "https://example.com", "content": "Kids art class"},
                {"title": "Soccer Camp", "url": "https://example.com/2", "content": "Youth soccer"},
            ]
        }

        results = search_events("Los Altos", "California", "outdoor", "today", "family")
        assert len(results) == 2
        assert results[0]["title"] == "Art Workshop"

    @patch("agent.tools.search_tool.TavilyClient")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_search_handles_api_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.side_effect = Exception("API error")

        results = search_events("Los Altos", "California", "outdoor", "today", "family")
        assert results == []

    def test_search_missing_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="TAVILY_API_KEY"):
                search_events("Los Altos", "California", "outdoor", "today", "family")

    @patch("agent.tools.search_tool.TavilyClient")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_paid_search(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = {"results": [{"title": "Paid Event"}]}

        results = search_paid_events("Los Altos", "California", "indoor", "weekend")
        assert len(results) == 1


class TestSearchByCategory:
    @patch("agent.tools.search_tool.TavilyClient")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_sports_category_search(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = {
            "results": [{"title": "Soccer Clinic", "url": "https://example.com"}]
        }

        results = search_by_category("Los Altos", "California", "outdoor", "today", "Sports & Fitness")
        assert len(results) == 1
        assert results[0]["_target_category"] == "Sports & Fitness"

    @patch("agent.tools.search_tool.TavilyClient")
    @patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"})
    def test_all_categories_supported(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.search.return_value = {"results": [{"title": "Event"}]}

        categories = [
            "Sports & Fitness", "Arts & Crafts", "Nature & Outdoor",
            "Entertainment", "Educational", "Social & Community",
        ]
        for cat in categories:
            results = search_by_category("Los Altos", "CA", "indoor", "today", cat)
            assert len(results) == 1, f"Failed for category: {cat}"

    def test_unknown_category_returns_empty(self):
        with patch.dict("os.environ", {"TAVILY_API_KEY": "test_key"}):
            results = search_by_category("Los Altos", "CA", "indoor", "today", "FakeCategory")
            assert results == []


class TestSearchNode:
    @patch("agent.nodes.search.search_by_category")
    @patch("agent.nodes.search.search_paid_events")
    @patch("agent.nodes.search.search_events")
    def test_searches_all_age_groups(self, mock_search, mock_paid, mock_cat):
        mock_search.side_effect = lambda **kwargs: [{"title": "Event"}]
        mock_cat.return_value = []
        mock_paid.return_value = []

        state = {
            "location": {"city": "Los Altos", "state": "California"},
            "mode": "outdoor",
            "time_mode": "today",
        }
        result = search_activities(state)

        # Should call search_events 3 times (family, kids_8, teens_14)
        assert mock_search.call_count == 3

    @patch("agent.nodes.search.search_by_category")
    @patch("agent.nodes.search.search_paid_events")
    @patch("agent.nodes.search.search_events")
    def test_searches_diversity_categories(self, mock_search, mock_paid, mock_cat):
        """Should search 4 diversity categories."""
        mock_search.return_value = [{"title": "Event"}]
        mock_cat.side_effect = lambda **kwargs: [{"title": f"Cat event"}]
        mock_paid.return_value = []

        state = {
            "location": {"city": "Los Altos", "state": "California"},
            "mode": "indoor",
            "time_mode": "today",
        }
        result = search_activities(state)

        # 4 category-targeted searches
        assert mock_cat.call_count == 4
        # Total: 3 age-group + 4 category = 7 result sets
        assert len(result["raw_search_results"]) == 7

    @patch("agent.nodes.search.search_by_category")
    @patch("agent.nodes.search.search_paid_events")
    @patch("agent.nodes.search.search_events")
    def test_falls_back_to_paid_when_sparse(self, mock_search, mock_paid, mock_cat):
        mock_search.return_value = []
        mock_cat.return_value = []
        mock_paid.return_value = [{"title": "Paid Event"}]

        state = {
            "location": {"city": "Los Altos", "state": "California"},
            "mode": "indoor",
            "time_mode": "weekend",
        }
        result = search_activities(state)

        mock_paid.assert_called_once()
        assert len(result["raw_search_results"]) == 1

    @patch("agent.nodes.search.search_by_category")
    @patch("agent.nodes.search.search_paid_events")
    @patch("agent.nodes.search.search_events")
    def test_tags_age_query_on_results(self, mock_search, mock_paid, mock_cat):
        mock_search.side_effect = lambda **kwargs: [{"title": "Event"}]
        mock_cat.return_value = []
        mock_paid.return_value = []

        state = {
            "location": {"city": "Los Altos", "state": "California"},
            "mode": "outdoor",
            "time_mode": "today",
        }
        result = search_activities(state)

        age_queries = [r.get("_age_query") for r in result["raw_search_results"]]
        assert "family" in age_queries
        assert "kids_8" in age_queries
        assert "teens_14" in age_queries
