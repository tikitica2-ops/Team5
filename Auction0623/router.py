import config  # MUST BE FIRST
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
import providers
import agents

class OrchestratorRouter:
    """
    Orchestrator that routes user queries to the appropriate agent:
    - Procedure Agent
    - Rights Analysis Tutor Agent
    - Quiz Router (UI instructions)
    """
    def __init__(self):
        self.llm = providers.get_llm(temperature=0.0)
        self.agents = agents.ALL_AGENTS

    def classify_query(self, query: str) -> str:
        """
        Classifies the user query into: 'procedure', 'tutor', or 'quiz'.
        """
        prompt = """당신은 부동산 경매 질문 라우팅 오케스트레이터입니다.
사용자 질문을 분석하여 아래의 3가지 범주 중 하나로만 정확히 분류하십시오.

범주:
1. 'procedure': 경매 절차, 단계, 신청 시기, 입찰 방법, 인도명령 기한, 배당 마감일 등 경매의 '절차/행정 흐름'에 대한 질문
2. 'tutor': 권리분석 이론, 말소기준권리 개념, 대항력 요건, 유치권 성립조건 등 경매 '개념 학습 및 권리관계 분석 방법'에 대한 질문
3. 'quiz': '퀴즈', '문제', '테스트', '사례 풀기', '퀴즈 내줘' 등 퀴즈를 출제하고 문제를 풀어보고자 하는 요구

답변은 오직 단어 'procedure', 'tutor', 'quiz' 중 하나만 포함해야 하며, 어떠한 부가 설명이나 마침표도 포함해서는 안 됩니다.
"""

        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=f"사용자 질문: {query}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            label = response.content.strip().lower()
            
            # Substring checking to make routing robust
            if "procedure" in label or any(w in query for w in ["필터", "프롬프트", "알고리즘", "전략", "유찰"]):
                return "procedure"
            elif "quiz" in label or "문제" in label or "테스트" in label:
                return "quiz"
            elif "tutor" in label or "권리" in label or "개념" in label:
                return "tutor"
            else:
                return "tutor"  # Default fallback
        except Exception as e:
            print(f"Routing error: {e}")
            return "tutor"  # Default fallback

    def handle_query(self, query: str) -> Dict[str, Any]:
        """
        Classifies and routes query, executing the appropriate agent pipeline.
        Returns unified dictionary:
        {
          "route": "procedure" | "tutor" | "quiz",
          "answer": str,
          "citations": list
        }
        """
        route = self.classify_query(query)
        
        if route == "quiz":
            return {
                "route": "quiz",
                "answer": "사례 퀴즈 풀기 모드를 실행합니다. 사이드바 혹은 화면 하단의 퀴즈 입력 창에서 원하시는 물건(난이도별 3종)을 선택하고, 말소기준권리/대항력 유무/인수 권리/최종 위험성을 적어 '채점하기'를 눌러보세요!",
                "citations": []
            }
            
        agent = self.agents.get(route)
        if not agent:
            # Fallback to tutor agent
            agent = self.agents["tutor"]
            route = "tutor"
            
        result = agent.generate_response(query)
        result["route"] = route
        return result

orchestrator = OrchestratorRouter()
