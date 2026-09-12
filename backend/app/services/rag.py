import logging
import google.generativeai as genai
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.services.chroma_service import chroma_service
from app.models.faq import FAQ
from app.models.notice import Notice
from datetime import datetime

logger = logging.getLogger(__name__)

# Configure Gemini if key is provided
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=settings.GEMINI_API_KEY)

FALLBACK_MESSAGE = (
    "I apologize, but I do not have verified official information regarding your question "
    "in my database. Please contact the K.K. Wagh Polytechnic administration office directly "
    "or check the official notice board at https://kkwaghpoly.loukik.com/."
)

SYSTEM_PROMPT = """You are the official AI Institutional Assistant for K.K. Wagh Polytechnic, Nashik.
Your goal is to provide helpful, polite, and accurate information to students, parents, faculty, and visitors based STRICTLY on the official context provided below.

CRITICAL INSTRUCTIONS AGAINST HALLUCINATION:
1. Answer ONLY using the facts explicitly stated in the CONTEXT below.
2. Do NOT guess, speculate, extrapolate, or bring in outside knowledge about other colleges or general topics.
3. If the answer cannot be fully found in the provided CONTEXT, state clearly that you do not have verified official information for that specific query.
4. Keep your answer clear, concise, professional, and well-structured.
5. Reference official document names and page numbers in your text when explaining rules or procedures.

OFFICIAL CONTEXT:
{context}

USER QUESTION:
{question}

YOUR GROUNDED ANSWER:"""


class RAGService:
    def __init__(self):
        self.fallback_message = FALLBACK_MESSAGE

    def get_database_context(self, query: str, db: Session) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Searches active FAQs and active Notices in SQLite/Postgres.
        """
        extra_texts = []
        sources = []
        query_lower = query.lower()

        # Check FAQs
        faqs = db.query(FAQ).filter(FAQ.is_active == True).all()
        for faq in faqs:
            # Simple keyword matching for FAQs
            q_words = [w for w in query_lower.split() if len(w) > 3]
            faq_q_lower = faq.question.lower()
            match_count = sum(1 for w in q_words if w in faq_q_lower)

            if match_count >= 1 or query_lower in faq_q_lower or faq_q_lower in query_lower:
                extra_texts.append(f"FAQ [Category: {faq.category}]: Q: {faq.question} | A: {faq.answer}")
                sources.append({
                    "document_name": f"FAQ: {faq.question[:30]}...",
                    "page_number": None,
                    "score": 0.9,
                    "text_snippet": faq.answer[:150],
                    "category": faq.category
                })

        # Check active Notices
        now = datetime.utcnow()
        notices = db.query(Notice).filter(Notice.is_active == True).all()
        for notice in notices:
            if notice.expiry_date and notice.expiry_date < now:
                continue # Expired notice
            
            n_title_lower = notice.title.lower()
            if any(w in n_title_lower for w in query_lower.split() if len(w) > 3):
                extra_texts.append(f"Notice [{notice.title}]: {notice.content}")
                sources.append({
                    "document_name": f"Notice: {notice.title}",
                    "page_number": None,
                    "score": 0.85,
                    "text_snippet": notice.content[:150],
                    "category": "Notice"
                })

        return extra_texts, sources

    def generate_answer(self, question: str, db: Session) -> Dict[str, Any]:
        """
        Full RAG pipeline:
        1. Retrieve vector search chunks from ChromaDB.
        2. Retrieve database FAQs and Notices.
        3. Evaluate relevance threshold.
        4. Assemble strict prompt & call Gemini LLM.
        5. Return grounded answer + sources or fallback.
        """
        # 1. Vector Search
        vector_results = chroma_service.search_similar(question, top_k=4)
        
        # 2. Database FAQs & Notices Search
        db_texts, db_sources = self.get_database_context(question, db)

        # Build context string & source list
        context_parts = []
        sources = list(db_sources)
        valid_chunks_count = 0

        for res in vector_results:
            # Score filter threshold (accept score >= 0.45 or min distance)
            score = res.get("score", 0.0)
            meta = res.get("metadata", {})
            doc_name = meta.get("filename") or meta.get("title") or "Official PDF Document"
            page_num = meta.get("page_number")
            cat = meta.get("category", "General Document")
            text = res.get("text", "")

            if score >= 0.35: # Sufficient relevance
                valid_chunks_count += 1
                context_parts.append(
                    f"Document: {doc_name} (Page {page_num}) [Category: {cat}]\nContent: {text}"
                )
                
                # Avoid duplicate source entries for same doc & page
                already_added = any(
                    s.get("document_name") == doc_name and s.get("page_number") == page_num 
                    for s in sources
                )
                if not already_added:
                    sources.append({
                        "document_name": doc_name,
                        "page_number": page_num,
                        "score": score,
                        "text_snippet": text[:150] + "..." if len(text) > 150 else text,
                        "category": cat
                    })

        context_parts.extend(db_texts)
        
        # 3. Fallback Check: If no relevant information found in database or vector DB
        if not context_parts:
            return {
                "answer": self.fallback_message,
                "sources": [],
                "fallback_used": True
            }

        full_context = "\n\n---\n\n".join(context_parts)
        prompt = SYSTEM_PROMPT.format(context=full_context, question=question)

        # 4. Call Gemini LLM or Local Mock LLM
        answer = ""
        fallback_used = False

        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                # Try gemini-1.5-flash first, fallback to gemini-pro
                try:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(prompt)
                    answer = response.text.strip()
                except Exception as e1:
                    logger.warning(f"gemini-1.5-flash failed ({str(e1)}), trying gemini-pro...")
                    model = genai.GenerativeModel("gemini-pro")
                    response = model.generate_content(prompt)
                    answer = response.text.strip()
            except Exception as e:
                logger.error(f"Gemini API generation error: {str(e)}")
                # If LLM API fails, format grounded response directly from retrieved context
                answer = self._extrapolate_from_context(question, context_parts)
        else:
            # No API key provided - synthesize grounded response directly from retrieved context chunks
            answer = self._extrapolate_from_context(question, context_parts)

        # Check if the generated answer itself indicates insufficient info
        if "i apologize" in answer.lower() and "verified official information" in answer.lower():
            fallback_used = True
            sources = []

        return {
            "answer": answer,
            "sources": sources if not fallback_used else [],
            "fallback_used": fallback_used
        }

    def _extrapolate_from_context(self, question: str, context_parts: List[str]) -> str:
        """
        Extrapolates a clean, grounded answer directly from context when LLM API is unavailable.
        """
        if not context_parts:
            return self.fallback_message
            
        combined_info = "\n".join(context_parts)
        return (
            f"Based on the official K.K. Wagh Polytechnic documents:\n\n"
            f"{context_parts[0]}\n\n"
            f"For further official assistance, please refer to the administration office or official notices."
        )

rag_service = RAGService()
