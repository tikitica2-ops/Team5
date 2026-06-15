"""
cli.py

터미널에서 절차 안내 에이전트를 테스트한다.
(OPENAI_API_KEY 와 ingest.py 로 구축한 chroma_db/ 필요)

사용:
  python cli.py "경매 배당요구 종기가 뭐야?"
  python cli.py            # 인자 없으면 입력 프롬프트
"""

import sys

from agents import procedure_agent


def main():
    question = " ".join(sys.argv[1:]).strip() or input("질문: ").strip()
    if not question:
        print("질문이 비어 있습니다.")
        return

    result = procedure_agent.answer(question)

    print("\n=== 답변 ===")
    print(result["answer"])

    if result["sources"]:
        print("\n=== 검색된 출처 ===")
        for s in result["sources"]:
            print(" -", s)


if __name__ == "__main__":
    main()
