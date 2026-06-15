"""
cli.py

터미널에서 멀티에이전트 라우터를 테스트한다.
(OPENAI_API_KEY 와 ingest.py 로 구축한 chroma_db/ 필요)

사용:
  python cli.py "배당요구 종기가 뭐야?"
  python cli.py "말소기준권리 개념 알려줘"
  python cli.py "권리분석 문제 하나 내줘"
  python cli.py            # 인자 없으면 입력 프롬프트
"""

import sys

import router


def main():
    question = " ".join(sys.argv[1:]).strip() or input("질문: ").strip()
    if not question:
        print("질문이 비어 있습니다.")
        return

    result = router.handle(question)

    print(f"\n[라우팅: {result['route']} -> {result['agent']}]")
    print("\n=== 답변 ===")
    print(result["answer"])

    if result.get("sources"):
        print("\n=== 검색된 출처 ===")
        for s in result["sources"]:
            print(" -", s)

    if result.get("quiz"):
        print(f"\n(퀴즈 사례 {result['quiz']['case_id']} 출제됨 — 답안을 작성해 quiz.grade로 채점하세요)")


if __name__ == "__main__":
    main()
