# 🎨 디자이너 (CDO) UI/UX 가이드라인 - cdo.md

* **호출 명령어:** `/cdo`
* **주요 역할:** UI/UX 레이아웃 설계, 프리미엄 글래스모피즘 테마 및 CSS 스타일링 관리, 데이터 시각화 스타일 가이드라인 수립

---

## 1. 디자인 철학 및 시스템 토큰 (Design System Tokens)
본 프로젝트는 심사위원들이 화면을 보자마자 **"성숙하고 완성도 높은 상용 서비스의 느낌"**을 받도록 하는 것을 목표로 합니다. 투박한 기본 Streamlit UI 대신 미려한 다크 모드 기반의 글래스모피즘(Glassmorphism) 스타일을 적용합니다.

### 1.1 컬러 팰럿 (Color Palette)
- **Primary Color:** `#6366F1` (Indigo - 주조색, 브랜드 정체성 제시)
- **Secondary Color:** `#A855F7` (Purple - 강조색, 포인트 버튼 및 하이라이트)
- **Background Color:** `#0F172A` (Slate 900 - 다크 모드 배경색)
- **Sidebar Background:** `#1E293B` (Slate 800 - 사이드바 배경색)
- **Card Background:** `rgba(30, 41, 59, 0.7)` (반투명 슬레이트 - 유리 질감 표현)
- **Text Color:** `#F8FAFC` (Slate 50 - 본문 및 제목 텍스트)

### 1.2 타이포그래피 (Typography)
- **폰트:** Google Fonts의 `Outfit` (영문/숫자) 및 `Noto Sans KR` (한글) 적용
- **제목 그라디언트:** `linear-gradient(135deg, #6366F1 0%, #A855F7 100%)` 효과로 세련되고 트렌디한 느낌 전달

---

## 2. 화면별 UI/UX 레이아웃 블루프린트

### 2.1 탭 1: 홈 대시보드 (Home Dashboard)
- **상단 메인 타이틀:** 그라디언트 타이틀과 가독성 높은 부제목
- **디스클레이머 배너:** 경고 아이콘(`⚠️`)과 함께 테두리가 강조된 위험도 경고용 카드 레이아웃
- **3단 그리드 배치:**
  - **좌:** 경매 뉴스 피드 (BeautifulSoup 크롤링 결과 - 스크롤 가능한 카드형태 리스트)
  - **중:** 매각통계 차트 (Plotly로 렌더링된 다크 테마 라인/도넛 차트)
  - **우:** 유튜브 AI 요약 (썸네일 카드, 클릭 시 상세 내용이 펼쳐지는 토글형 Expander)

### 2.2 탭 2: AI Q&A 대화창 (AI Counseling)
- **채팅 말풍선:** 사용자 말풍선(우측, 다크 슬레이트)과 에이전트 말풍선(좌측, 인디고 테마)의 구분을 명확히 함
- **에이전트 라벨 배지:** 답변 상단에 전문 분야를 나타내는 컴팩트 배지 탑재
  - `절차 안내`: 초록색 배지 (`badge-procedure`)
  - `권리분석 튜터`: 파란색 배지 (`badge-tutor`)
- **인용구 어코디언:** 답변 최하단에 참고 조문 및 판례 출처를 깔끔하게 여닫을 수 있는 Expander 배치

### 2.3 탭 3: 실전 권리분석 퀴즈 (Case Quiz)
- **2열 레이아웃:**
  - **좌열 (사례 현황):** 가상 매각물건명세서의 등기부 현황, 임차인 현황 표를 깔끔한 Grid 컴포넌트로 시각화
  - **우열 (답안 입력 폼):** 4가지 문제에 답할 수 있는 텍스트 필드와 하단의 네온 테마 "🎯 답안 채점하기" 제출 버튼
- **점수 메트릭:** 채점 후 게이지 바(Progress Bar)와 점수 메트릭을 동적으로 표기하여 직관적인 피드백 제공

### 2.4 탭 4: 경매 학습일기 (Auction Diary) - **[NEW]**
- **일기 작성 패널:** 에디터 느낌의 넓은 텍스트 영역 제공
- **분석 결과 보드:**
  - **감성 격려 카드:** 연보라색 배경의 파스텔 톤 카드 레이아웃
  - **권리분석 경고판:** 위험 플래그가 있을 시 빨간색 또는 주황색 테두리의 위험 알림판 표시
  - **추천 공부 링크:** 클릭 시 해당 주제 관련 퀴즈나 용어로 바로 연결되는 인터랙티브 링크 목록

---

## 3. Streamlit용 Custom CSS 템플릿 코드
`app.py` 최상단에서 주입할 프리미엄 스타일링 CSS 정의서입니다.

```css
/* Google Fonts 로드 */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

/* 전체 폰트 및 배경 설정 */
html, body, [class*="css"] {
    font-family: 'Outfit', 'Noto Sans KR', sans-serif;
    color: #F8FAFC;
}

/* 제목 그라디언트 효과 */
.title-gradient {
    background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
    font-size: 2.6rem;
    margin-bottom: 0.2rem;
}

/* 면책사항 카드 */
.disclaimer-card {
    background-color: rgba(239, 68, 68, 0.08);
    border-left: 4px solid #EF4444;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1.5rem;
}

/* 경매일기 분석 결과 카드 (글래스모피즘) */
.diary-result-card {
    background: rgba(30, 41, 59, 0.45);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 0.75rem;
    padding: 1.25rem;
    margin-top: 1rem;
}

/* 퀴즈/경매일기 경고 카드 */
.risk-warning-card {
    background-color: rgba(245, 158, 11, 0.08);
    border-left: 4px solid #F59E0B;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-top: 0.8rem;
}
```

---

## 4. 시각화 가이드라인 (Data Visualization)
1. **차트 라이브러리:** 복잡한 반응형 조작을 위해 `Plotly`를 최우선으로 채택합니다.
2. **테마 일관성:** 모든 차트는 `template="plotly_dark"`를 활성화하여 다크 톤 웹 페이지와의 이질감을 최소화합니다.
3. **색상 조화:** 차트 데이터 요소에는 주조색인 인디고(`#6366F1`)와 강조색인 퍼플(`#A855F7`)을 사용하여 시각적 정체성을 유지합니다.
