import json
import re
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from providers import get_gemini_llm

class RiskFlag(BaseModel):
    issue: str = Field(description="오해하거나 분석을 놓친 권리분석 및 절차 리스크의 명칭")
    warning: str = Field(description="구체적인 민사집행법/임대차보호법에 근거한 상세 교정 및 경고 메시지")

class RecommendedStudy(BaseModel):
    topic: str = Field(description="보완이 필요한 경매 학습 주제 명칭")
    action: str = Field(description="추천하는 구체적인 학습 활동 가이드")

class DiaryAnalysisResult(BaseModel):
    emotional_support: str = Field(description="학습자의 경매 공부와 노력을 응원하고 지지하는 따뜻한 2-3줄의 멘트")
    risk_flags: List[RiskFlag] = Field(default=[], description="일기 내용 중 잘못 알고 있거나 주의가 필요한 권리관계/절차 위험 요소 목록")
    recommended_study: List[RecommendedStudy] = Field(default=[], description="오늘의 일기 맥락에 맞춤형으로 권장하는 추천 공부 목록")

class AuctionDiaryAgent:
    def __init__(self):
        # Always use the Gemini model configured in providers (falls back to OpenAI if key missing)
        self.llm = get_gemini_llm(temperature=0.3)

    def analyze_diary(self, diary_content: str) -> Dict[str, Any]:
        """
        Analyzes the user's auction diary and returns a structured dictionary.
        """
        if not diary_content.strip():
            return {
                "emotional_support": "오늘의 경매 학습 내용을 적어주시면 AI 튜터가 맞춤형 분석을 도와드려요!",
                "risk_flags": [],
                "recommended_study": []
            }

        system_prompt = (
            "당신은 부동산 법원경매 교육 플랫폼의 'AntiG 경매일기 AI 분석 위원'입니다.\n"
            "사용자가 그날 공부한 경매 개념, 임장 기록, 모의 입찰 경험, 소감 등을 '학습 일기' 형태로 적으면 이를 읽고 분석하여 교육적이고 따뜻한 피드백을 제공해야 합니다.\n\n"
            "다음 지침을 반드시 준수하여 응답해 주세요:\n"
            "1. **따뜻한 지지**: 학습을 계속할 수 있도록 친근하고 정중한 어조(해요체 등)로 따뜻하게 격려하세요.\n"
            "2. **리스크 감지 및 교정**: 사용자가 적은 일기 내용 중 권리분석 오류, 절차에 대한 오해, 또는 법률적 함정이 있는지 면밀히 감시하세요.\n"
            "   - 예: 전입신고일이 근저당설정일보다 늦음에도 대항력이 있다고 착각하는 경우.\n"
            "   - 예: 배당요구종기일이 지났는데도 우선변제권을 행사할 수 있다고 믿는 경우.\n"
            "   - 예: 입찰보증금(최저매각가격의 10%)을 본인이 입찰하려는 금액의 10%로 오해하는 경우.\n"
            "   - 오류나 위험 요소가 있다면 `risk_flags` 목록에 구체적인 이유와 함께 추가하세요. 오류가 없거나 평이한 내용이라면 비워두어도 좋습니다.\n"
            "3. **맞춤형 후속 학습 추천**: 오늘 일기 맥락에 맞춰, 추가로 학습하면 시너지가 날 만한 주제와 구체적인 학습 가이드를 제공하세요.\n\n"
            "반드시 아래 JSON 스키마 형식만을 준수하여 출력해야 하며, markdown 코드 블록이나 기타 텍스트를 섞지 말고 순수한 JSON만 반환해야 합니다.\n"
            "출력 JSON 구조:\n"
            "{\n"
            "  \"emotional_support\": \"따뜻하고 격려하는 피드백 문장 (2-3줄)\",\n"
            "  \"risk_flags\": [\n"
            "    {\"issue\": \"이슈 제목\", \"warning\": \"이유 및 법률적 근거 기반 교정 가이드\"}\n"
            "  ],\n"
            "  \"recommended_study\": [\n"
            "    {\"topic\": \"주제어\", \"action\": \"학습 액션 가이드\"}\n"
            "  ]\n"
            "}"
        )

        user_content = f"학습자의 경매 일기:\n\"\"\"\n{diary_content}\n\"\"\""

        try:
            # Check if structured output is supported directly by the model instance
            if hasattr(self.llm, "with_structured_output"):
                structured_llm = self.llm.with_structured_output(DiaryAnalysisResult)
                result = structured_llm.invoke([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ])
                # Convert Pydantic object to dictionary
                if isinstance(result, DiaryAnalysisResult):
                    return result.model_dump()
                elif isinstance(result, dict):
                    return result
            
            # Fallback to standard string invocation and JSON parsing
            response = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ])
            
            content = response.content.strip()
            # Clean json formatting if LLM wrapped it in markdown block
            content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.MULTILINE)
            content = re.sub(r"\s*```$", "", content, flags=re.MULTILINE)
            
            parsed_data = json.loads(content)
            
            # Ensure safety keys exist
            if "emotional_support" not in parsed_data:
                parsed_data["emotional_support"] = "오늘도 경매 공부를 위해 애쓰셨습니다! 한 걸음씩 나아가다 보면 어느새 전문가가 되어 있을 것입니다."
            if "risk_flags" not in parsed_data:
                parsed_data["risk_flags"] = []
            if "recommended_study" not in parsed_data:
                parsed_data["recommended_study"] = []
                
            return parsed_data

        except Exception as e:
            # Complete safety fallback in case of API issues or parsing errors
            return {
                "emotional_support": f"일기를 성공적으로 기록했습니다! (AI 분석 분석 중 일시적인 오류가 발생했으나 일기는 저장되었습니다: {str(e)})",
                "risk_flags": [
                    {
                        "issue": "AI 분석 지연",
                        "warning": "API 호출량이 초과되었거나 환경 변수 설정이 올바르지 않아 AI 피드백을 완성하지 못했습니다. 키 설정을 점검해 주세요."
                    }
                ],
                "recommended_study": [
                    {
                        "topic": "권리분석 기본기 학습",
                        "action": "사이드바에서 '권리분석 퀴즈'를 시작하여 말소기준권리와 대항력의 기본 원칙을 연습해 보세요."
                    }
                ]
            }

    def load_history(self) -> List[Dict[str, Any]]:
        import os
        history_file = os.path.join(os.path.dirname(__file__), "data", "diary_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_history(self, history: List[Dict[str, Any]]):
        import os
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)
        history_file = os.path.join(data_dir, "diary_history.json")
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

diary_agent = AuctionDiaryAgent()
