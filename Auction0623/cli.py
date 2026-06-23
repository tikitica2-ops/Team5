import config  # MUST BE FIRST
import sys
import argparse
from router import orchestrator

def main():
    parser = argparse.ArgumentParser(description="부동산 경매 RAG CLI 테스트 도구")
    parser.add_argument("query", nargs="?", type=str, help="테스트할 질문 내용")
    args = parser.parse_args()
    
    if args.query:
        # Single query execution
        print(f"사용자 질문: {args.query}\n")
        print("라우팅 및 답변 생성 중...")
        result = orchestrator.handle_query(args.query)
        
        route_mapping = {
            "procedure": "절차 안내 에이전트",
            "tutor": "권리분석 튜터 에이전트",
            "quiz": "사례 퀴즈 에이전트"
        }
        
        print(f"\n[라우팅결과]: {route_mapping.get(result['route'], result['route'])}")
        print("\n--- [답변] ---")
        print(result["answer"])
        print("\n--- [출처 목록] ---")
        if result.get("citations"):
            for idx, cite in enumerate(result["citations"]):
                print(f"{idx+1}. {cite['display_name']}")
        else:
            print("인용 출처 없음")
    else:
        # Interactive CLI mode
        print("=== 부동산 경매 에이전트 대화형 CLI ===")
        print("질문을 입력하세요. 종료하려면 'exit' 또는 'quit'을 입력하세요.\n")
        while True:
            try:
                query = input("사용자 > ").strip()
                if not query:
                    continue
                if query.lower() in ["exit", "quit"]:
                    break
                
                result = orchestrator.handle_query(query)
                route_mapping = {
                    "procedure": "절차 안내",
                    "tutor": "권리분석 튜터",
                    "quiz": "사례 퀴즈"
                }
                print(f"\n[{route_mapping.get(result['route'], result['route'])} 에이전트 처리]")
                print(f"AI > {result['answer']}\n")
                if result.get("citations"):
                    print("[참고 출처]")
                    for cite in result["citations"]:
                        print(f" - {cite['display_name']}")
                print("-" * 50)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"오류 발생: {e}\n")

if __name__ == "__main__":
    main()
