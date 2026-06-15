# 부동산 경매 교육 멀티에이전트 RAG (가칭)

부동산 법원경매를 **가르치고 연습시키는** 학습용 AI 서비스.
오케스트레이터가 질문을 전문 에이전트로 분배하는 멀티에이전트 RAG 구조.

> ⚠️ 본 서비스는 **교육·학습용**입니다. 특정 물건에 대한 투자·법률 자문이 아니며,
> 실제 입찰 전에는 반드시 전문가 확인이 필요합니다. 모든 답변에 출처(조문)를 함께 제시합니다.

## 에이전트 구성 (목표)
- **오케스트레이터(Router)**: 질문 의도를 분류해 적절한 에이전트로 분배
- **① 절차 안내**: 경매 흐름·단계 Q&A
- **② 권리분석 튜터**: 말소기준권리·대항력을 가상 사례로 단계별 학습 (단정 금지)
- **③ 법령·용어 사전**: 조문/용어를 출처와 함께 인용
- **④ 사례·퀴즈**: 가상 매각물건명세서로 권리분석 문제 출제·채점

## 지식베이스(ChromaDB) 4개 컬렉션
| 컬렉션 | 내용 | 데이터 |
|---|---|---|
| `auction_laws` | 법령 조문 | `data/laws/*.md` |
| `auction_procedures` | 절차 해설 | `data/procedures/*.md` |
| `auction_glossary` | 용어집 | `data/glossary/glossary.json` |
| `auction_cases` | 가상 사례 | `data/cases/sample_cases.json` |

## 현재 디렉터리 구조 (1단계 완료분)
```
auction-edu-rag/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── config.py                # LLM/임베딩/컬렉션/경로 중앙 설정 (GPT<->Claude 전환)
└── data/
    ├── laws/
    │   ├── civil_execution_act.md          # 민사집행법 핵심 조문
    │   └── housing_lease_protection_act.md # 주택임대차보호법 핵심 조문
    ├── procedures/
    │   └── auction_procedure_guide.md      # 9단계 절차 해설
    ├── glossary/
    │   └── glossary.json                   # 용어 21개
    └── cases/
        └── sample_cases.json               # 가상 사례 3건(입문/중급/고급) + 정답
```
> 이후 단계에서 `ingest.py`(청킹·DB구축), `agents/`, `app.py`(Streamlit) 등이 추가됩니다.

## 실행 준비 (지금 단계)
```bash
# 1) 가상환경
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate

# 2) 설치
pip install -r requirements.txt

# 3) 키 설정
cp .env.example .env   # 그리고 .env 안의 키를 채움
```
> 실제 동작(ingest/app)은 2단계 이후 코드가 추가되면 진행합니다.

### 동작 테스트 (2~3단계)
```bash
python ingest.py            # chroma_db/ 구축 (최초 1회, 키 필요)
python cli.py "배당요구 종기가 뭐야?"   # 절차 안내 에이전트에 질문
```

## LLM / 임베딩 전환
`.env`의 `LLM_PROVIDER`만 `openai` ↔ `anthropic`으로 바꾸면 GPT-4o-mini ↔ Claude 전환.
한국어 로컬 임베딩이 필요하면 `EMBEDDING_PROVIDER=huggingface`로 변경.

## 빌드 로드맵
- [x] **1단계**: 프로젝트 구조 + 샘플 지식베이스
- [x] **2단계**: clause-aware 청킹 → ChromaDB 4개 컬렉션 구축 (`ingest.py`)
- [x] **3단계**: 단일 RAG 에이전트(절차 안내) 동작 (`rag.py`, `agents.py`, `cli.py`)
- [x] **4단계**: 권리분석 튜터(`agents.py`) + 사례·퀴즈 에이전트(`quiz.py`)
- [x] **5단계**: 라우터로 멀티에이전트 통합 (`router.py`)
- [ ] 6단계: Streamlit UI + 출처 인용 표시
- [ ] 7단계: Streamlit Cloud 배포

## 팀 역할(제안)
- 팀장/기획·도메인: 시나리오·UX 설계, 권리분석 콘텐츠/사례 정합성, 라우팅 규칙 정의
- 데이터·지식베이스: 데이터 수집·정제, 청킹, 임베딩, ChromaDB 구축
- 에이전트·백엔드: LangChain 멀티에이전트·라우터, 프롬프트, RAG 파이프라인
- 프론트·통합: Streamlit UI, 통합, 배포, QA
