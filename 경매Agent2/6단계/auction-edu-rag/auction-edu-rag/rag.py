"""
rag.py

모든 에이전트가 공유하는 RAG 백본.
  - get_vectorstore: 영속화된 ChromaDB 컬렉션 핸들
  - RagAgent: 지정한 컬렉션에서 검색 -> 출처와 함께 LLM 답변 생성

heavy import(langchain/chroma)는 함수 안에서 지연 로딩하므로,
키/네트워크 없이도 모듈 import 와 로직 테스트가 가능하다.
"""

import config
import providers


def get_vectorstore(collection_key):
    """영속화된 Chroma 컬렉션을 반환."""
    from langchain_chroma import Chroma
    return Chroma(
        collection_name=config.COLLECTIONS[collection_key],
        embedding_function=providers.get_embeddings(),
        persist_directory=config.CHROMA_DIR,
    )


def _label(meta):
    """청크 메타데이터에서 사람이 읽을 출처 라벨 추출."""
    return (meta.get("section")
            or meta.get("term")
            or meta.get("title")
            or meta.get("source")
            or "출처미상")


class RagAgent:
    """검색 + 생성 에이전트. collection_keys 와 system_prompt 로 성격이 정해진다."""

    def __init__(self, name, collection_keys, system_prompt, description=""):
        self.name = name
        self.collection_keys = collection_keys
        self.system_prompt = system_prompt
        self.description = description  # 라우터(5단계)가 에이전트 선택에 사용
        self._stores = None
        self._llm = None

    def _ensure(self):
        if self._stores is None:
            self._stores = {k: get_vectorstore(k) for k in self.collection_keys}
        if self._llm is None:
            self._llm = providers.get_llm()

    def retrieve(self, question, k=None):
        """여러 컬렉션에서 검색해 거리순으로 상위 k개 청크 반환."""
        self._ensure()
        k = k or config.TOP_K
        hits = []
        for store in self._stores.values():
            for doc, score in store.similarity_search_with_score(question, k=k):
                hits.append((doc, score))
        hits.sort(key=lambda x: x[1])  # 거리가 작을수록 가까움
        return [doc for doc, _ in hits[:k]]

    def answer(self, question, k=None):
        """검색한 자료를 근거로 답변 생성. {answer, sources, docs} 반환."""
        self._ensure()
        docs = self.retrieve(question, k=k)

        if not docs:
            return {
                "answer": "관련 자료를 찾지 못했습니다. 질문을 더 구체적으로 적어 주세요.",
                "sources": [],
                "docs": [],
            }

        context = "\n\n".join(
            f"[출처: {_label(d.metadata)}]\n{d.page_content}" for d in docs
        )
        user_msg = (
            "다음 자료를 근거로 질문에 답하세요.\n\n"
            f"=== 자료 ===\n{context}\n\n"
            f"=== 질문 ===\n{question}"
        )
        # 메시지 튜플 형태는 ChatOpenAI/ChatAnthropic 모두 지원
        resp = self._llm.invoke([
            ("system", self.system_prompt),
            ("human", user_msg),
        ])
        answer_text = getattr(resp, "content", str(resp))

        # 출처 라벨 중복 제거(순서 유지)
        sources = list(dict.fromkeys(_label(d.metadata) for d in docs))
        return {"answer": answer_text, "sources": sources, "docs": docs}
