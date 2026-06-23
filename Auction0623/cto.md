# 💻 개발자 (CTO) 기술 아키텍처 및 구현 가이드라인 - cto.md

* **호출 명령어:** `/cto`
* **주요 역할:** 시스템 기술 구조 설계, 데이터 인제스천(RAG/VectorDB), 에이전트 라우팅 구현, 멀티 LLM 프로바이더(Google Gemini, OpenAI, Anthropic) 연동 및 배포 최적화

---

## 1. 기술 아키텍처 개요
본 애플리케이션은 **Streamlit**을 런타임 UI로 채택한 파이썬 기반 서버리스형 웹앱 구조입니다. 평가지표를 극대화하기 위해 백엔드에 **멀티 에이전트 오케스트레이션** 모델을 장착하고, 각 에이전트의 성격에 적합한 LLM과 검색(ChromaDB RAG) 파이프라인을 탑재합니다.

```
+-------------------------------------------------------------+
|                     Streamlit App (app.py)                  |
+-------------------------------------------------------------+
                               |
       +-----------------------+-----------------------+
       | (비동기 데이터 로딩)  | (라우팅 & Q&A)        | (경매 학습일기)
       v                       v                       v
+---------------+      +---------------+      +-------------------+
|  dashboard/   |      |   router.py   |      |  core/            |
|  news, stats, |      | (Orchestrator)|      |  diary_agent.py   |
|  youtube.py   |      +---------------+      +-------------------+
+---------------+              |                       |
       |             +---------+---------+             |
       |             v                   v             v
       |      +-------------+     +-------------+ +---------------+
       |      | procedure   |     | tutor_agent | | Gemini Engine |
       |      | _agent.py   |     | (RAG)       | | 1.5 Flash     |
       |      +-------------+     +-------------+ +---------------+
       |             |                   |
       +-------------+---------+---------+
                               |
                               v
                       +---------------+
                       |  providers.py |
                       | (LLM Factory) |
                       +---------------+
                               |
               +---------------+---------------+
               v                               v
        [OpenAI GPT-4o-mini]     [Google Gemini 1.5 Flash]
```

---

## 2. 복수 LLM 프로바이더 연동 가이드 (`providers.py`)
발표 시 강력한 어필 포인트인 **멀티 모델 프로바이더(OpenAI, Anthropic, Gemini)**를 팩토리 패턴(`providers.py`) 형태로 추상화합니다.

```python
# providers.py 내에 구현될 Gemini 연동 로직
def get_gemini_llm(temperature=0.2):
    """
    Google Gemini 모델 객체를 반환합니다.
    """
    gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        try:
            import streamlit as st
            gemini_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass
            
    if not gemini_key:
        # 키 누락 시 OpenAI로 폴백(Fallback) 처리하여 시스템 마비 리스크 방지
        return get_llm(temperature=temperature)
        
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        google_api_key=gemini_key,
        model="gemini-1.5-flash",
        temperature=temperature
    )
```

---

## 3. 경매 학습일기 분석 에이전트 설계 (`core/diary_agent.py`)
사용자의 경매 학습 및 실습 기록을 정밀 진단하는 에이전트입니다.

### 3.1 기술 메커니즘
- **입력:** 사용자 학습 일지 텍스트
- **프롬프트 전략 (System Prompt):**
  - 분석 모델은 **Google Gemini 1.5 Flash**를 기본으로 사용합니다.
  - 사용자의 실수나 지식적 오류(예: 말소기준권리 선정 오류 등)를 찾아내 경고하고 올바른 상식을 교정합니다.
  - 응답은 Streamlit UI의 렌더링 호환성을 위해 **Strict JSON 포맷**으로 출력되도록 `Pydantic` 및 `with_structured_output` 기법을 적용합니다.

### 3.2 JSON 스키마 구조
```json
{
  "emotional_support": "공감과 격려가 담긴 2~3줄의 응답",
  "risk_flags": [
    {
      "issue": "오해하거나 놓친 권리분석 리스크 명칭",
      "warning": "구체적인 법률적 근거 기반 경고 메시지"
    }
  ],
  "recommended_study": [
    {
      "topic": "보완 학습이 필요한 주제어",
      "action": "취해야 할 학습 액션 가이드"
    }
  ]
}
```

---

## 4. 디렉터리 구조 및 파일 스펙 개요
- `config.py`: 데이터 경로, 컬렉션명, 기본 모델 정보 중앙 관리.
- `providers.py`: LLM 및 임베딩 팩토리. `openai`, `anthropic`, `gemini` 선택권 보장.
- `ingest.py`: `Ko-SRoberta` 혹은 `text-embedding-3-small` 기반 다중 RAG DB 적재기.
- `router.py`: 오케스트레이터 및 라우팅 로직.
- `quiz.py`: 등기부 기반 퀴즈 출제 및 채점 로직 (Evaluator-Optimizer).
- `core/diary_agent.py`: **[신규]** Google Gemini 기반 일기 분석 에이전트.
- `app.py`: Streamlit 프리미엄 CSS 및 멀티 탭 UI 렌더러.
