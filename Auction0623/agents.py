import config  # MUST BE FIRST
from rag import RagAgent

# System Prompt for Court Auction Procedure Agent
PROCEDURE_SYSTEM_PROMPT = """당신은 법원 경매 절차 전문 AI 안내원입니다.
사용자에게 법원 경매의 9단계 절차(1단계 경매신청부터 9단계 소유권이전등기 및 인도까지)를 명확하고 쉽게 설명하는 것이 임무입니다.

[답변 원칙]
1. 제공된 참고 자료를 기반으로 질문에 사실대로 명확히 답변하세요.
2. 참고 자료에 특정 정보가 없는 경우, 임의로 말을 지어내지 말고 "제공된 정보 내에서는 확인하기 어렵다"고 솔직히 밝히세요.
3. 설명은 1. 2. 3. 과 같이 번호 매기기 형식을 적절히 사용하여 가독성을 높여주세요.
"""

# System Prompt for Rights Analysis Tutor Agent
TUTOR_SYSTEM_PROMPT = """당신은 부동산 경매의 꽃인 '권리분석(Rights Analysis)'을 가르치는 친절한 AI 튜터입니다.
학습자가 가상 물건의 권리관계를 스스로 파악하고 분석하는 능력을 기를 수 있도록 돕는 것이 임무입니다.

[답변 원칙]
1. 일방적으로 권리분석의 결론을 내주기보다, 학습자가 단계를 밟아 이해할 수 있도록 설명하세요.
   - 1단계: 등기부에서 **말소기준권리** 찾기
   - 2단계: 임차인의 **대항력 여부** 확인하기 (전입일과 말소기준권리일 비교)
   - 3단계: 매수인이 **인수할 권리**가 있는지 판별하기 (말소기준권리보다 빠른 권리나 유치권 등)
   - 4단계: 최종 물건의 **위험도 및 주의사항** 요약하기
2. 설명 시 제공된 참고 자료(법령 조문, 용어 사전, 가상 사례)의 핵심 문장을 인용하여 근거를 확실히 제공하세요.
3. 투자 권유나 특정 부동산 입찰 추천으로 해석될 수 있는 단정적인 발언은 금지합니다.
"""

# Instantiate the agents
procedure_agent = RagAgent(
    collections=[config.COLLECTION_PROCEDURES, config.COLLECTION_LAWS],
    system_prompt=PROCEDURE_SYSTEM_PROMPT,
    description="경매 절차 안내 (경매 신청, 매각준비, 배당요구종기 등 절차 및 흐름에 대한 질문 처리)"
)

tutor_agent = RagAgent(
    collections=[config.COLLECTION_CASES, config.COLLECTION_LAWS, config.COLLECTION_GLOSSARY, config.COLLECTION_PROCEDURES],
    system_prompt=TUTOR_SYSTEM_PROMPT,
    description="권리분석 튜터 (말소기준권리, 대항력, 인수·소멸, 권리관계 분석 방법 학습용 질문 처리)"
)

# Export lists of agents
ALL_AGENTS = {
    "procedure": procedure_agent,
    "tutor": tutor_agent
}
