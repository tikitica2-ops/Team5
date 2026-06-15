"""
quiz.py

사례·퀴즈 에이전트.
벡터 검색이 아니라 사례 JSON을 직접 읽어 '정답 노출'을 직접 제어한다.
  - list_cases()           : 사례 목록(난이도/제목)
  - get_question(...)      : 정답을 뺀 '문제'(사실관계 + 분석 요구) 반환
  - grade(case_id, 답안)   : 정답과 대조해 LLM이 채점/피드백
"""

import json
import random

import config
import providers


def _won(n):
    if isinstance(n, (int, float)) and n:
        return f"{int(n):,}원"
    return None


def _load():
    path = config.DATA_DIR / "cases" / "sample_cases.json"
    return json.loads(path.read_text(encoding="utf-8"))["cases"]


def list_cases():
    return [{"id": c["id"], "difficulty": c["difficulty"], "title": c["title"]} for c in _load()]


def _facts_text(c):
    """정답(analysis)을 제외한 물건 사실관계만 직렬화."""
    p = c["property"]
    lines = [
        f"물건: {p.get('type','')}, {p.get('location','')}, "
        f"감정가 {_won(p.get('appraisal_value'))}, 최저매각가격 {_won(p.get('min_bid_price'))}"
        + (f" ({p['note']})" if p.get("note") else ""),
        "등기부(접수일순):",
    ]
    for r in c.get("registry", []):
        amt = _won(r.get("amount"))
        lines.append(f" - {r['date']} {r['type']} / {r.get('holder','')}" + (f" / {amt}" if amt else ""))

    t = c.get("tenant", {})
    if t.get("exists"):
        lines.append(
            f"임차인: 전입일 {t.get('move_in_date','-')}, 확정일자 {t.get('fixed_date','-')}, "
            f"보증금 {_won(t.get('deposit'))}, 배당요구 {'함' if t.get('demand_for_distribution') else '안함'}, "
            f"{'점유 중' if t.get('occupying') else '미점유'}"
        )
    else:
        lines.append("임차인: 없음" + (f" ({t.get('note')})" if t.get("note") else ""))

    for sr in c.get("special_rights", []):
        lines.append(
            f"특수권리: {sr['type']} / 주장자 {sr.get('claimant','')} / 사유 {sr.get('basis','')} / "
            f"{_won(sr.get('amount'))} / {sr.get('status','')}"
        )
    lines.append(f"배당요구종기: {c.get('distribution_deadline','-')}")
    return "\n".join(lines)


def _answer_key_text(c):
    a = c["analysis"]
    return (
        f"- 말소기준권리: {a['extinction_baseline']}\n"
        f"- 임차인 대항력: {a['tenant_opposability']}\n"
        f"- 인수권리: {', '.join(a['assumed_rights']) if a['assumed_rights'] else '없음'}\n"
        f"- 말소권리: {', '.join(a['extinguished_rights'])}\n"
        f"- 예상 추가부담: {a['estimated_extra_burden']}\n"
        f"- 위험도: {a['risk_level']}\n"
        f"- 결론: {a['conclusion']}"
    )


def _pick(case_id=None, difficulty=None):
    cases = _load()
    if case_id:
        return next((c for c in cases if c["id"] == case_id), None)
    if difficulty:
        pool = [c for c in cases if c["difficulty"] == difficulty]
        return random.choice(pool) if pool else None
    return random.choice(cases)


def get_question(case_id=None, difficulty=None):
    """정답을 뺀 문제를 반환. (case_id 또는 difficulty 지정, 없으면 랜덤)"""
    c = _pick(case_id, difficulty)
    if not c:
        return None
    question = (
        f"[사례 {c['id']}] (난이도: {c['difficulty']})\n"
        f"{_facts_text(c)}\n\n"
        "[문제] 위 물건의 권리관계를 분석하세요.\n"
        "1) 말소기준권리는 무엇인가?\n"
        "2) 임차인의 대항력 유무와 그 근거는?\n"
        "3) 매수인에게 인수되는 권리 / 말소되는 권리는?\n"
        "4) 예상 추가부담과 위험도는?"
    )
    return {"case_id": c["id"], "difficulty": c["difficulty"], "question": question}


_GRADER_SYSTEM = (
    "당신은 부동산 경매 권리분석을 채점하는 '교육용' 튜터입니다.\n"
    "주어진 [정답 권리분석]을 기준으로 [학습자 답안]을 채점하세요.\n"
    "채점 항목 4가지(① 말소기준권리 ② 대항력 ③ 인수/말소 권리 ④ 위험도)별로 "
    "'정답/부분정답/오답'을 매기고, 왜 그런지 정답 근거와 함께 짧게 설명하세요.\n"
    "마지막에 총평과 점수(4점 만점)를 주세요.\n"
    "비난하지 말고 격려하는 톤으로, 한국어로. 본 채점은 교육용이며 실제 입찰 판단은 전문가 확인이 필요함을 한 줄 덧붙이세요."
)


def grade(case_id, user_answer):
    """학습자 답안을 정답과 대조해 채점/피드백."""
    c = _pick(case_id=case_id)
    if not c:
        return {"case_id": case_id, "feedback": "해당 사례를 찾을 수 없습니다."}

    facts = _facts_text(c)
    key = _answer_key_text(c)
    human = (
        f"[물건 사실관계]\n{facts}\n\n"
        f"[정답 권리분석]\n{key}\n\n"
        f"[학습자 답안]\n{user_answer}\n\n"
        "위 기준으로 항목별 채점과 총평을 작성하세요."
    )
    llm = providers.get_llm()
    resp = llm.invoke([("system", _GRADER_SYSTEM), ("human", human)])
    feedback = getattr(resp, "content", str(resp))
    return {"case_id": case_id, "difficulty": c["difficulty"], "feedback": feedback}
