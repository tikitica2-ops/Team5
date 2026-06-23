import config  # MUST BE FIRST
import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
import providers

class QuizAgent:
    """
    Manages loading property cases, outputting question cards, and grading
    user rights-analysis submissions using LLM evaluation.
    """
    def __init__(self):
        self.cases_file = config.CASES_FILE
        self.llm = providers.get_llm(temperature=0.0)

    def load_cases(self) -> List[Dict[str, Any]]:
        """Loads cases from the local JSON file."""
        if not self.cases_file.exists():
            return []
        with open(self.cases_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_question(self, case_id: str) -> Dict[str, Any]:
        """
        Retrieves case data excluding the ground-truth analysis to prevent leaks.
        """
        cases = self.load_cases()
        for case in cases:
            if case["id"] == case_id:
                # Return a copy without 'analysis'
                q = case.copy()
                if "analysis" in q:
                    del q["analysis"]
                return q
        raise ValueError(f"Case with ID {case_id} not found.")

    def grade(self, case_id: str, student_answers: Dict[str, str]) -> Dict[str, Any]:
        """
        Grades the student's submission against the ground-truth analysis.
        Uses the LLM to score (0-4) and provide detailed feedback.
        """
        cases = self.load_cases()
        target_case = None
        for case in cases:
            if case["id"] == case_id:
                target_case = case
                break
                
        if not target_case:
            raise ValueError(f"Case with ID {case_id} not found.")

        # Ground truth answers
        truth = target_case["analysis"]
        
        # Build prompt for grading LLM
        system_prompt = """당신은 부동산 경매 권리분석 채점 위원입니다.
학생의 권리분석 답안을 정답 키와 대조하여 엄격하고 상세하게 채점하십시오.

분석 항목은 다음 4가지입니다:
1. 말소기준권리 (판단 및 설정일)
2. 임차인 대항력 유무
3. 낙찰자 인수 권리 (인수 금액이나 권리 표시)
4. 최종 낙찰 위험성 평가

각 항목당 1점씩 부여하여 총 4점 만점으로 점수를 매기세요.
결과는 반드시 아래의 JSON 포맷으로만 응답해야 합니다:
{
  "score": 3,
  "feedback": {
    "malso_standard": "정확한 말소기준권리 날짜와 권리명을 잘 짚었습니다.",
    "opposing_power": "임차인의 대항력 유무를 올바르게 판정했습니다.",
    "takeover_rights": "매수인이 인수해야 하는 금액이나 조건을 오해했습니다. 실제로는 ~원 인수입니다.",
    "risk_assessment": "위험성 평가가 아주 구체적이고 현실적입니다."
  },
  "summary": "전체적으로 뛰어난 분석이나, 선순위 대항력 임차인의 인수 조건에 대한 추가 학습이 필요합니다."
}
"""

        human_content = f"""
[물건 정보]
- 물건명: {target_case['title']}
- 감정가: {target_case['appraised_value']}
- 최저가: {target_case['minimum_bid_price']}
- 등기부등본 현황: {json.dumps(target_case['registry_records'], ensure_ascii=False)}
- 임차인 현황: {json.dumps(target_case['tenant_records'], ensure_ascii=False)}
- 특이사항: {target_case.get('notes', '없음')}

[정답 키]
- 말소기준권리: {truth['malso_standard']}
- 대항력 여부: {truth['opposing_power']}
- 인수 권리: {truth['takeover_rights']}
- 최종 위험 평가: {truth['risk_assessment']}

[학생의 제출 답안]
1. 말소기준권리: {student_answers.get('malso_standard', '미작성')}
2. 임차인 대항력 유무: {student_answers.get('opposing_power', '미작성')}
3. 낙찰자 인수 권리: {student_answers.get('takeover_rights', '미작성')}
4. 최종 낙찰 위험성 평가: {student_answers.get('risk_assessment', '미작성')}

위 정답 키와 학생 답안의 실질적인 의미가 일치하는지 심사하여 점수를 부여하고 피드백을 JSON으로 작성하세요.
JSON 블록 이외의 말(예: ```json 등)은 절대 포함하지 말고 순수 JSON 문자열만 출력하세요.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_content)
        ]

        response = self.llm.invoke(messages)
        result_text = response.content.strip()

        # Clean codeblock wrappers if any
        if result_text.startswith("```json"):
            result_text = result_text.split("```json", 1)[1]
        if result_text.endswith("```"):
            result_text = result_text.rsplit("```", 1)[0]
        result_text = result_text.strip()

        try:
            grade_res = json.loads(result_text)
            # Ensure required keys exist
            if "score" not in grade_res:
                grade_res["score"] = 0
            if "feedback" not in grade_res:
                grade_res["feedback"] = {}
            if "summary" not in grade_res:
                grade_res["summary"] = "채점을 성공적으로 마쳤습니다."
            return grade_res
        except Exception as e:
            # Fallback in case of parse error
            print(f"Error parsing LLM grading JSON: {e}. Raw text was:\n{result_text}")
            return {
                "score": 2,
                "feedback": {
                    "malso_standard": "채점 분석 오류가 발생하여 기본 피드백을 제공합니다. 정답을 직접 비교해보세요.",
                    "opposing_power": "대항력 판정을 확인하세요.",
                    "takeover_rights": "인수 권리 항목을 확인하세요.",
                    "risk_assessment": "위험성 평가 항목을 확인하세요."
                },
                "summary": "결과 JSON 파싱 오류가 발생하여 기본 요약이 대체되었습니다."
            }

quiz_agent = QuizAgent()
