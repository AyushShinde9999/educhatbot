import json
import logging
import re
import google.generativeai as genai
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
from app.config import settings
from app.services.chroma_service import chroma_service
from app.services.embedding import embedding_service
from app.models.faq import FAQ
from app.models.notice import Notice

logger = logging.getLogger(__name__)

# Configure Gemini if key is provided
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=settings.GEMINI_API_KEY)

FALLBACK_MESSAGE = (
    "I apologize, but I do not have verified official information regarding your question "
    "in my database. Please contact the K.K. Wagh Polytechnic administration office directly "
    "or check the official notice board."
)

# Thresholds per context source type
PDF_SIMILARITY_THRESHOLD = 0.40
FAQ_SIMILARITY_THRESHOLD = 0.50
NOTICE_SIMILARITY_THRESHOLD = 0.45

SYSTEM_PROMPT = """You are the official AI Institutional Assistant for K.K. Wagh Polytechnic, Nashik.
Answer the user's question using ONLY the provided official context.

CRITICAL CONSTRAINTS:
1. Answer strictly using facts explicitly stated in the CONTEXT below.
2. Do NOT guess, speculate, or bring in outside information.
3. If the context does NOT contain enough information, set "fallback_status": true and answer with:
   "I apologize, but I do not have verified official information regarding your question in my database. Please contact the K.K. Wagh Polytechnic administration office directly or check the official notice board."
4. Respond in valid, strict JSON format with the following keys:
     {{
     "answer": "Your grounded response text here.",
     "citations": [
             {{"document_name": "Exact Document Name", "page_number": 1}}
     ],
     "confidence": 0.95,
     "fallback_status": false
     }}

OFFICIAL CONTEXT:
{context}

USER QUESTION:
{question}

YOUR JSON RESPONSE:"""


class RAGService:
    def __init__(self):
        self.fallback_message = FALLBACK_MESSAGE

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def search_faqs_and_notices(self, question: str, db: Session) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Uses vector embedding semantic similarity to retrieve relevant active FAQs and Notices.
        """
        context_parts = []
        sources = []
        query_embedding = embedding_service.generate_embedding(question)

        # 1. Search Active FAQs
        faqs = db.query(FAQ).filter(FAQ.is_active == True).all()
        for faq in faqs:
            faq_text = f"Q: {faq.question} A: {faq.answer}"
            faq_emb = embedding_service.generate_embedding(faq_text)
            sim = self._cosine_similarity(query_embedding, faq_emb)

            if sim >= FAQ_SIMILARITY_THRESHOLD:
                doc_title = f"FAQ: {faq.question[:35]}..."
                context_parts.append(
                    f"Document: {doc_title} [Category: {faq.category}]\nQuestion: {faq.question}\nAnswer: {faq.answer}"
                )
                sources.append({
                    "document_name": doc_title,
                    "page_number": None,
                    "score": round(sim, 4),
                    "text_snippet": faq.answer[:150],
                    "category": faq.category
                })

        # 2. Search Active Notices (Non-expired)
        now = datetime.utcnow()
        notices = db.query(Notice).filter(Notice.is_active == True).all()
        for notice in notices:
            if notice.expiry_date and notice.expiry_date < now:
                continue

            notice_text = f"Title: {notice.title} Content: {notice.content}"
            notice_emb = embedding_service.generate_embedding(notice_text)
            sim = self._cosine_similarity(query_embedding, notice_emb)

            if sim >= NOTICE_SIMILARITY_THRESHOLD:
                doc_title = f"Notice: {notice.title}"
                context_parts.append(
                    f"Document: {doc_title} [Category: Notice]\nTitle: {notice.title}\nContent: {notice.content}"
                )
                sources.append({
                    "document_name": doc_title,
                    "page_number": None,
                    "score": round(sim, 4),
                    "text_snippet": notice.content[:150],
                    "category": "Notice"
                })

        return context_parts, sources

    def generate_answer(self, question: str, db: Session) -> Dict[str, Any]:
        """
        Full Production RAG pipeline with Citation Verification and Structured JSON Enforcement.
        """
        # 1. Vector Search for PDF Chunks
        vector_results = chroma_service.search_similar(question, top_k=5)
        
        # 2. Semantic Search for FAQs & Notices
        db_context, db_sources = self.search_faqs_and_notices(question, db)

        context_parts = list(db_context)
        sources = list(db_sources)
        retrieved_doc_names = set(s["document_name"] for s in sources)

        # 3. Apply PDF similarity threshold
        for res in vector_results:
            score = res.get("score", 0.0)
            meta = res.get("metadata", {})
            doc_name = meta.get("filename") or meta.get("title") or "Official Document"
            page_num = meta.get("page_number")
            cat = meta.get("category", "General")
            text = res.get("text", "")

            if score >= PDF_SIMILARITY_THRESHOLD:
                retrieved_doc_names.add(doc_name)
                context_parts.append(
                    f"Document: {doc_name} (Page {page_num}) [Category: {cat}]\nContent: {text}"
                )
                
                already_added = any(
                    s.get("document_name") == doc_name and s.get("page_number") == page_num 
                    for s in sources
                )
                if not already_added:
                    sources.append({
                        "document_name": doc_name,
                        "page_number": page_num,
                        "score": score,
                        "text_snippet": text[:150],
                        "category": cat
                    })

        # 4. Fallback check if no context met confidence thresholds
        if not context_parts:
            return {
                "answer": self.fallback_message,
                "sources": [],
                "fallback_used": True,
                "confidence": 0.0
            }

        full_context = "\n\n---\n\n".join(context_parts)
        prompt = SYSTEM_PROMPT.format(context=full_context, question=question)

        # 5. Call Gemini LLM
        raw_response = ""
        parsed_json = None
        fallback_used = False

        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")
                res = model.generate_content(prompt)
                raw_response = res.text.strip()
                
                # Extract JSON block
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    parsed_json = json.loads(json_match.group(0))
            except Exception as e:
                logger.warning(f"Gemini structured JSON generation error ({str(e)}). Using grounded synthesis.")

        # 6. Post-generation Verification
        if parsed_json and isinstance(parsed_json, dict):
            answer_text = str(parsed_json.get("answer", "")).strip()
            fallback_used = bool(parsed_json.get("fallback_status", False))
            try:
                confidence = max(0.0, min(1.0, float(parsed_json.get("confidence", 0.0))))
            except (TypeError, ValueError):
                confidence = 0.0

            if fallback_used or "i apologize" in answer_text.lower():
                return {
                    "answer": self.fallback_message,
                    "sources": [],
                    "fallback_used": True,
                    "confidence": 0.0
                }

            # Grounding Citation Verification: Verify citations returned by LLM actually exist in context
            valid_citations = []
            llm_citations = parsed_json.get("citations", [])
            if not answer_text or not isinstance(llm_citations, list):
                return {
                    "answer": self.fallback_message,
                    "sources": [],
                    "fallback_used": True,
                    "confidence": 0.0
                }

            for cite in llm_citations:
                if not isinstance(cite, dict):
                    continue
                cite_name = cite.get("document_name", "")
                cite_page = cite.get("page_number")
                if any(
                    cite_name == doc_name
                    and (cite_page is None or cite_page == source_page)
                    for doc_name, source_page in (
                        (source.get("document_name"), source.get("page_number"))
                        for source in sources
                    )
                ):
                    valid_citations.append(cite)

            # Answers without citations cannot be verified as grounded.
            if not valid_citations:
                return {
                    "answer": self.fallback_message,
                    "sources": [],
                    "fallback_used": True,
                    "confidence": 0.0
                }

            sources = [
                source for source in sources
                if any(
                    citation.get("document_name") == source.get("document_name")
                    and (
                        citation.get("page_number") is None
                        or citation.get("page_number") == source.get("page_number")
                    )
                    for citation in valid_citations
                )
            ]

            return {
                "answer": answer_text,
                "sources": sources,
                "fallback_used": False,
                "confidence": confidence
            }

        # Fallback synthesis if raw text returned without JSON
        return {
            "answer": context_parts[0].split("\nContent: ")[-1][:300] if context_parts else self.fallback_message,
            "sources": sources,
            "fallback_used": False,
            "confidence": 0.8
        }

rag_service = RAGService()
