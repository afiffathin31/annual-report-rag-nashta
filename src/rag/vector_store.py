import os
from typing import List, Dict, Optional
from pathlib import Path
import chromadb
from mistralai.client import Mistral
import config

class VectorStoreManager:
    """Manages ChromaDB persistent vector database with Mistral Embeddings."""

    def __init__(self, persist_dir: Path = config.CHROMA_DB_DIR):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.chroma_client.get_or_create_collection(
            name="nashta_emiten_rag",
            metadata={"description": "Annual report chunks for Nashta 10 Pillars RAG"}
        )
        self.mistral_client = Mistral(api_key=config.MISTRAL_API_KEY)

    def get_embeddings(self, texts: List[str], batch_size: int = 40, max_retries: int = 5) -> List[List[float]]:
        """Generates embeddings in batches using Mistral Embed with resilient retry logic."""
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            success = False
            for attempt in range(1, max_retries + 1):
                try:
                    resp = self.mistral_client.embeddings.create(
                        inputs=batch,
                        model=config.MISTRAL_EMBED_MODEL
                    )
                    for item in resp.data:
                        all_embeddings.append(item.embedding)
                    success = True
                    break
                except Exception as e:
                    wait_time = attempt * 3
                    print(f"Embedding API retry {attempt}/{max_retries} (error: {e}). Waiting {wait_time}s...")
                    import time
                    time.sleep(wait_time)
            
            if not success:
                raise RuntimeError(f"Failed to generate embeddings after {max_retries} retries.")
            
            # Small pause between batches to respect rate limits
            import time
            time.sleep(0.3)

        return all_embeddings

    def add_chunks(self, chunks: List[Dict]):
        """Adds or updates chunks in the ChromaDB collection."""
        if not chunks:
            return

        ids = [c["id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        print(f"Generating embeddings for {len(chunks)} chunks in batch size 50...")
        embeddings = self.get_embeddings(texts, batch_size=50)

        # Batch upsert into ChromaDB
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i:i+batch_size],
                embeddings=embeddings[i:i+batch_size],
                documents=texts[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )
        print(f"Successfully saved {len(chunks)} chunks to ChromaDB.")

    def query(self, query_text: str, emiten_code: str, top_k: int = 5) -> List[Dict]:
        """Queries the vector database for relevant chunks filtered by emiten."""
        query_emb = self.get_embeddings([query_text], batch_size=1)[0]
        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            where={"emiten_code": emiten_code.upper()}
        )

        matched_chunks = []
        if results and results["documents"] and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0]*len(docs)

            for doc, meta, dist in zip(docs, metas, distances):
                matched_chunks.append({
                    "text": doc,
                    "metadata": meta,
                    "score": dist
                })
        return matched_chunks

    def get_available_emitens(self) -> List[str]:
        """Returns list of distinct emiten codes."""
        # Static fast list of supported emitens
        return ["KLBF", "SIDO", "BANK", "CARE", "HEAL", "PDSB"]

    def get_stats(self) -> Dict:
        """Returns total chunks and emitens count safely."""
        try:
            count = self.collection.count()
        except Exception:
            count = 0
        emitens = self.get_available_emitens()
        return {
            "total_chunks": count,
            "emitens_count": len(emitens),
            "emitens": emitens
        }
