import pytest
from app.services.rag import rag_service, FALLBACK_MESSAGE

def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    
    assert round(rag_service._cosine_similarity(v1, v2), 2) == 1.0
    assert round(rag_service._cosine_similarity(v1, v3), 2) == 0.0

def test_rag_fallback_on_unrelated_query(db_session):
    unrelated_question = "What is the orbital speed of Jupiter in lightyears?"
    res = rag_service.generate_answer(unrelated_question, db_session)
    
    assert res["fallback_used"] is True
    assert res["sources"] == []
    assert res["answer"] == FALLBACK_MESSAGE
