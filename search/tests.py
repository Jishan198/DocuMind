import pytest
from search.services.retriever import HybridRetriever


@pytest.mark.django_db
class TestHybridRetriever:
    def test_retriever_returns_empty_for_no_docs(self, org, owner_membership):
        retriever = HybridRetriever(organization=org, top_k=5)
        results = retriever.retrieve('what is machine learning?')
        assert results == []

    def test_retriever_respects_top_k(self, org):
        retriever = HybridRetriever(organization=org, top_k=3)
        assert retriever.top_k == 3
# Create your tests here.
