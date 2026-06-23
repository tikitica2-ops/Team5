import config  # MUST BE FIRST
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_core.messages import SystemMessage, HumanMessage
import providers

class RagAgent:
    """
    RAG Agent Backbone that manages query retrieval from multiple collections,
    ranking, prompt assembly, and response generation with clean citations.
    """
    def __init__(self, collections: List[str], system_prompt: str, description: str = ""):
        self.collections = collections
        self.system_prompt = system_prompt
        self.description = description
        
        # Instantiate model and embedding
        self.embedding_model = providers.get_embedding_model()
        self.llm = providers.get_llm(temperature=0.0)
        
    def retrieve_context(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves matching documents across all specified collections,
        merges them, and sorts by similarity score (distance ascending).
        """
        all_results = []
        for col_name in self.collections:
            try:
                # Load chroma collection
                db = Chroma(
                    collection_name=col_name,
                    embedding_function=self.embedding_model,
                    persist_directory=str(config.CHROMA_DB_DIR)
                )
                
                # Check if collection exists and has items
                col_info = db._collection
                if col_info is None or col_info.count() == 0:
                    continue
                
                # Retrieve with distance score (lower is closer/more similar)
                docs_and_scores = db.similarity_search_with_score(query, k=k)
                for doc, score in docs_and_scores:
                    all_results.append((doc, score))
            except Exception as e:
                # Silently skip if collection does not exist yet
                print(f"Error searching collection {col_name}: {e}")
                continue
                
        # Sort by distance score ascending (lowest distance first)
        all_results = sorted(all_results, key=lambda x: x[1])
        
        # Take top k documents
        top_k = all_results[:k]
        
        formatted_docs = []
        for doc, score in top_k:
            formatted_docs.append({
                "content": doc.page_content,
                "score": float(score),
                "metadata": doc.metadata
            })
            
        return formatted_docs

    def generate_response(self, query: str, k: int = 4) -> Dict[str, Any]:
        """
        Retrieves context, formats prompt, calls LLM, and returns structured answer and sources.
        """
        # Retrieve documents
        context_docs = self.retrieve_context(query, k=k)
        
        # Build context string
        context_str = ""
        for idx, doc in enumerate(context_docs):
            meta = doc["metadata"]
            source_info = meta.get("source", "알 수 없음")
            
            # Sub-identifiers based on document type
            details = []
            if "clause" in meta:
                details.append(meta["clause"])
            if "step" in meta:
                details.append(meta["step"])
            if "term" in meta:
                details.append(f"용어: {meta['term']}")
            if "case_id" in meta:
                details.append(f"사례 ID: {meta['case_id']}")
                
            details_str = f" ({', '.join(details)})" if details else ""
            
            context_str += f"--- [참고자료 {idx+1}] 출처: {source_info}{details_str} ---\n"
            context_str += f"{doc['content']}\n\n"
            
        # Build messages for LLM
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"참고 문서:\n{context_str}\n사용자 질문: {query}\n\n위 참고 문서를 바탕으로 사용자 질문에 답변해주세요. 질문과 무관하거나 참고 문서에 없는 내용은 무리하게 지어내지 마세요.")
        ]
        
        # Generate LLM response
        response = self.llm.invoke(messages)
        answer = response.content
        
        # Format list of citations
        citations = []
        seen_citations = set()
        for doc in context_docs:
            meta = doc["metadata"]
            source = meta.get("source", "알 수 없음")
            doc_type = meta.get("type", "unknown")
            
            # Generate a unique key to prevent duplicate citation displays
            clause_val = meta.get("clause")
            step_val = meta.get("step")
            term_val = meta.get("term")
            case_val = meta.get("case_id")
            
            key_parts = [source]
            display_name = source
            
            if clause_val:
                key_parts.append(clause_val)
                display_name = f"{source} ({clause_val})"
            elif step_val:
                key_parts.append(step_val)
                display_name = f"{source} ({step_val})"
            elif term_val:
                key_parts.append(term_val)
                display_name = f"{source} (용어: {term_val})"
            elif case_val:
                key_parts.append(case_val)
                display_name = f"{source} (사례 ID: {case_val})"
                
            cite_key = "-".join(key_parts)
            if cite_key not in seen_citations:
                seen_citations.add(cite_key)
                citations.append({
                    "display_name": display_name,
                    "content": doc["content"],
                    "metadata": meta
                })
                
        return {
            "answer": answer,
            "citations": citations
        }
