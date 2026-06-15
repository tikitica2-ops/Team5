"""
app.py

Streamlit 채팅 UI.
  - 채팅 입력 -> router.handle -> 답변 + 출처 표시(어느 에이전트로 갔는지 배지)
  - 퀴즈 라우트면 사례 출제 -> 답안 입력칸 + 채점 버튼 -> quiz.grade 피드백

실행:
  streamlit run app.py
(사전에 python ingest.py 로 chroma_db/ 구축, .env 에 키 설정 필요)
"""

import streamlit as st

import config
import quiz
import router

st.set_page_config(page_title="부동산 경매 학습 도우미", page_icon="⚖️", layout="centered")

st.title("부동산 경매 학습 도우미")
st.caption("멀티에이전트 RAG · 절차 안내 / 권리분석 튜터 / 사례 퀴즈")
st.warning(
    "본 서비스는 **교육·학습용**입니다. 특정 물건의 투자·법률 자문이 아니며, "
    "실제 입찰 전에는 반드시 전문가 확인이 필요합니다."
)

# --- 사이드바 ---
with st.sidebar:
    st.subheader("설정")
    st.text(f"LLM      : {config.LLM_PROVIDER} / {config.LLM_MODEL}")
    st.text(f"임베딩   : {config.EMBEDDING_PROVIDER} / {config.EMBEDDING_MODEL}")
    st.divider()
    st.subheader("퀴즈 난이도")
    difficulty = st.radio("문제 출제 시", ["랜덤", "입문", "중급", "고급"], index=0)
    st.divider()
    st.subheader("예시 질문")
    st.markdown(
        "- 배당요구 종기가 뭐야?\n"
        "- 말소기준권리 개념 알려줘\n"
        "- 대항력이 뭔지 사례로 설명해줘\n"
        "- 권리분석 문제 하나 내줘"
    )
    if st.button("대화 초기화"):
        st.session_state.clear()
        st.rerun()

# --- 상태 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_quiz" not in st.session_state:
    st.session_state.pending_quiz = None

# --- 지난 대화 렌더 ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("sources"):
            with st.expander("출처"):
                for s in m["sources"]:
                    st.markdown(f"- {s}")

# --- 입력 처리 ---
if prompt := st.chat_input("경매에 대해 물어보세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            try:
                res = router.handle(prompt)
                # 퀴즈면 사이드바 난이도 반영해 재출제
                if res["route"] == "quiz":
                    diff = None if difficulty == "랜덤" else difficulty
                    qz = quiz.get_question(difficulty=diff)
                    res["answer"] = qz["question"]
                    res["quiz"] = qz
                    st.session_state.pending_quiz = qz["case_id"]
            except Exception as e:  # DB 미구축/키 누락 등
                res = {
                    "route": "error", "agent": "-", "sources": [],
                    "answer": (f"오류가 발생했습니다: {e}\n\n"
                               "`python ingest.py`로 chroma_db를 만들고 `.env`에 API 키를 설정했는지 확인하세요."),
                }

        content = f"`{res['agent']}`\n\n{res['answer']}"
        st.markdown(content)
        if res.get("sources"):
            with st.expander("출처"):
                for s in res["sources"]:
                    st.markdown(f"- {s}")

    st.session_state.messages.append(
        {"role": "assistant", "content": content, "sources": res.get("sources")}
    )

# --- 퀴즈 답안/채점 영역 ---
if st.session_state.pending_quiz:
    st.divider()
    st.subheader(f"권리분석 답안 작성 (사례 {st.session_state.pending_quiz})")
    user_ans = st.text_area(
        "말소기준권리 / 대항력 / 인수·말소 / 위험도를 직접 분석해 보세요",
        key="quiz_answer", height=160,
    )
    col1, col2 = st.columns(2)
    if col1.button("채점하기", type="primary"):
        if user_ans.strip():
            with st.spinner("채점 중..."):
                try:
                    feedback = quiz.grade(st.session_state.pending_quiz, user_ans)["feedback"]
                except Exception as e:
                    feedback = f"채점 오류: {e}"
            st.session_state.messages.append(
                {"role": "assistant", "content": "**[채점 결과]**\n\n" + feedback}
            )
            st.session_state.pending_quiz = None
            st.rerun()
        else:
            st.warning("답안을 입력해 주세요.")
    if col2.button("그만두기"):
        st.session_state.pending_quiz = None
        st.rerun()
