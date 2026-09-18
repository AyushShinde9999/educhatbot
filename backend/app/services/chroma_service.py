import os
import chromadb
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.embedding import embedding_service
import logging

logger = logging.getLogger(__name__)

class ChromaService:
    def __init__(self, persist_dir: str = settings.CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection_name = "kkwagh_knowledge_base"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "K.K. Wagh Polytechnic Institutional Knowledge Base"}
        )

    def add_chunks(self, chunks: List[Dict[str, Any]], doc_id: int):
        """
        Adds text chunks with embeddings and metadata to ChromaDB.
        """
        if not chunks:
            return

        texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.generate_embeddings(texts)
        
        ids = []
        metadatas = []
        documents = []

        for idx, chunk in enumerate(chunks):
            chunk_id = f"doc_{doc_id}_chunk_{idx}"
            ids.append(chunk_id)
            documents.append(chunk["text"])
            
            meta = chunk["metadata"].copy()
            meta["document_id"] = int(doc_id)
            meta["page_number"] = int(meta.get("page_number", 1))
            metadatas.append(meta)

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        logger.info(f"Added {len(chunks)} chunks for doc_id {doc_id} to ChromaDB")

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Queries ChromaDB for top_k relevant text chunks.
        """
        if not query:
            return []

        query_embedding = embedding_service.generate_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        formatted_results = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for doc, meta, dist in zip(docs, metas, distances):
                # distance to similarity conversion
                similarity_score = max(0.0, 1.0 - (dist / 2.0)) if dist is not None else 0.5
                formatted_results.append({
                    "text": doc,
                    "metadata": meta,
                    "distance": dist,
                    "score": round(similarity_score, 4)
                })

        return formatted_results

    def delete_document_chunks(self, doc_id: int):
        """
        Deletes all chunks associated with a specific document_id.
        """
        try:
            self.collection.delete(
                where={"document_id": int(doc_id)}
            )
            logger.info(f"Deleted ChromaDB chunks for document_id: {doc_id}")
        except Exception as e:
            logger.error(f"Error deleting chunks for document_id {doc_id}: {str(e)}")

chroma_service = ChromaService()
