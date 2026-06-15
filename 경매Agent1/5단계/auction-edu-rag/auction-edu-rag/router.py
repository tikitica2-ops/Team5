"""
router.py

오케스트레이터. 사용자 질문을 분류해 알맞은 에이전트로 분배한다.

  - procedure : 절차 안내 에이전트
  - tutor     : 권리분석 튜터 에이전트
  - quiz      : 사례·퀴즈 에이전트 (문제 출제) — 채점은 UI에서 quiz.grade로 별도 처리

벡터 검색이 필요 없는 분류 단계만으로 동작하며, LLM 한 번 호출로 라벨을 받는다.
"""

import providers
import quiz
from agents import procedure_agent, tutor_agent

ROUTES = {
    "procedure": "경매 절차·흐름·단계(신청, 경매개시결정, 배당요구, 매각, 대금납부, 배당 등) 자체에 대한 질문",
    "tutor": "권리분석의 개념과 방법(말소기준권리, 대항력, 인수/말소, 우선변제 등)을 설명·학습하려는 질문",
    "quiz": "권리분석 문제를 풀어보고 싶거나 퀴즈/연습문제를 내달라는 요청",
}

_CLASSIFIER_SYSTEM = (
    "당신은 부동산 경매 교육 시스템의 질문 분류기입니다.\n"
    "사용자 질문을 아래 라벨 중 '정확히 하나'로 분류하고, 그 라벨 단어 하나만 출력하세요. "
    "다른 설명·문장은 절대 출력하지 마세요.\n\n"
    "라벨:\n{routes}\n\n"
    "출력 예: procedure"
)


def classify(question):
    """질문을 procedure / tutor / quiz 중 하나로 분류."""
    routes_desc = "\n".join(f"- {k}: {v}" for k, v in ROUTES.items())
    llm = providers.get_llm()
    resp = llm.invoke([
        ("system", _CLASSIFIER_SYSTEM.format(routes=routes_desc)),
        ("human", question),
    ])
    raw = getattr(resp, "content", str(resp)).strip().lower()
    for key in ROUTES:
        if key in raw:
            return key
    return "tutor"  # 모호하면 튜터로


def handle(question):
    """질문을 분류해 처리하고 통일된 형태로 반환.

    반환: {route, agent, answer, sources, quiz?}
      - quiz 라우트일 때만 'quiz'(case_id 포함)가 들어 있어 UI가 채점에 사용.
    """
    route = classify(question)

    if route == "procedure":
        r = procedure_agent.answer(question)
        return {"route": route, "agent": procedure_agent.name,
                "answer": r["answer"], "sources": r["sources"]}

    if route == "quiz":
        q = quiz.get_question()
        return {"route": route, "agent": "사례·퀴즈",
                "answer": q["question"], "sources": [], "quiz": q}

    # 기본: 권리분석 튜터
    r = tutor_agent.answer(question)
    return {"route": route, "agent": tutor_agent.name,
            "answer": r["answer"], "sources": r["sources"]}
