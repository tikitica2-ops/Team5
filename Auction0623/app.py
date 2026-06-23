import config  # MUST BE FIRST
import providers
import os
import sys
import streamlit as st
import pandas as pd
import asyncio
from router import orchestrator
from quiz import quiz_agent
from diary_agent import diary_agent
import ingest
import novel_loader
from pathlib import Path
from pdf_analyzer import extract_text_from_pdf
import time

# Import Dashboard modules
from dashboard.loader import load_dashboard_data
from dashboard.stats import get_bid_ratio_trend_chart, get_property_distribution_chart, get_regional_volume_chart

# Apply custom styling for a premium glassmorphic UI
st.set_page_config(
    page_title="AntiG 경매 스마트 에이전트",
    page_icon="🏛️",
    layout="wide"
)

# Custom CSS Injection (Revamped to match the template visual aesthetics)
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Reduce top padding of main block container to match Toss Securities compact layout */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* Hide Streamlit top header */
    header, .stAppHeader {
        display: none !important;
        height: 0px !important;
    }
    
    /* Reduce top padding of sidebar */
    [data-testid="stSidebarUserContent"] {
        padding-top: 1.5rem !important;
    }
    
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
        color: #111827;
    }
    
    /* Title Gradient */
    .title-gradient {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
    }
    
    /* Chat Agent Badges */
    .badge {
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 0.5rem;
    }
    .badge-procedure {
        background-color: rgba(5, 150, 105, 0.12);
        color: #059669;
        border: 1px solid rgba(5, 150, 105, 0.25);
    }
    .badge-tutor {
        background-color: rgba(79, 70, 229, 0.12);
        color: #4F46E5;
        border: 1px solid rgba(79, 70, 229, 0.25);
    }
    .badge-quiz {
        background-color: rgba(217, 119, 6, 0.12);
        color: #D97706;
        border: 1px solid rgba(217, 119, 6, 0.25);
    }
    
    /* Glassmorphism result card */
    .diary-result-card {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-top: 1rem;
        color: #1F2937;
    }
    
    /* Risk warning card */
    .risk-warning-card {
        background-color: rgba(217, 119, 6, 0.08);
        border-left: 4px solid #D97706;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 0.8rem;
        color: #78350F;
    }

    /* --- New Dashboard Styles matching the template --- */
    
    /* Metrics Cards */
    .dashboard-metric-card {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 1rem;
        padding: 1.25rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    }
    .metric-label {
        color: #4B5563;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .metric-val {
        color: #111827;
        font-size: 2rem;
        font-weight: 700;
        margin: 0.25rem 0;
    }
    .metric-sub {
        color: #6B7280;
        font-size: 0.75rem;
    }
    .metric-icon-bg {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }
    
    /* Section Main Cards (Apartment / Villa) */
    .section-card {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
    }
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .section-title {
        color: #111827;
        font-size: 1.2rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-btn {
        background: rgba(0, 0, 0, 0.03);
        border: 1px solid rgba(0, 0, 0, 0.08);
        color: #4B5563;
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.8rem;
        text-decoration: none;
        transition: all 0.2s;
    }
    .section-btn:hover {
        background: rgba(79, 70, 229, 0.08);
        color: #4F46E5;
        border-color: rgba(79, 70, 229, 0.2);
    }
    .section-content {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.5rem;
        margin-bottom: 1rem;
    }
    .section-metric-block {
        flex: 1;
        display: flex;
        flex-direction: column;
    }
    .section-metric-label {
        color: #6B7280;
        font-size: 0.75rem;
    }
    .section-metric-val {
        color: #111827;
        font-size: 1.5rem;
        font-weight: 700;
    }
    .badge-card {
        border-radius: 0.75rem;
        padding: 0.75rem 1rem;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-width: 120px;
    }
    .badge-card-label {
        font-size: 0.7rem;
        color: rgba(255, 255, 255, 0.95);
    }
    .badge-card-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .tag-container {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-top: 1px solid rgba(0, 0, 0, 0.05);
        padding-top: 0.75rem;
    }
    .tag-label {
        color: #4B5563;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .tag-item {
        background: rgba(0, 0, 0, 0.02);
        border: 1px solid rgba(0, 0, 0, 0.05);
        border-radius: 0.35rem;
        padding: 0.2rem 0.6rem;
        font-size: 0.75rem;
        color: #1F2937;
    }
    .tag-num {
        background: #0D9488;
        color: white;
        border-radius: 4px;
        padding: 1px 5px;
        margin-right: 6px;
        font-size: 0.7rem;
        font-weight: 700;
    }
    .tag-num-blue {
        background: #2563EB;
    }
    
    /* Right Panel (AI assistant & shortcuts) */
    .ai-panel {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 1rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .ai-panel-header {
        background: rgba(79, 70, 229, 0.08);
        border: 1px solid rgba(79, 70, 229, 0.15);
        border-radius: 0.5rem;
        padding: 0.6rem 0.8rem;
        color: #4F46E5;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .ai-task-card {
        background: rgba(0, 0, 0, 0.02);
        border: 1px solid rgba(0, 0, 0, 0.04);
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin-bottom: 0.75rem;
    }
    .ai-task-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #111827;
        margin: 0.25rem 0;
    }
    .ai-task-bullet {
        font-size: 0.75rem;
        color: #4B5563;
        margin-left: 0.25rem;
        margin-top: 0.15rem;
    }
    .badge-red {
        background: rgba(239, 68, 68, 0.12);
        color: #DC2626;
        border: 1px solid rgba(239, 68, 68, 0.25);
        padding: 0.1rem 0.4rem;
        border-radius: 0.25rem;
        font-size: 0.7rem;
        font-weight: 700;
    }
    .badge-orange {
        background: rgba(217, 119, 6, 0.12);
        color: #D97706;
        border: 1px solid rgba(217, 119, 6, 0.25);
        padding: 0.1rem 0.4rem;
        border-radius: 0.25rem;
        font-size: 0.7rem;
        font-weight: 700;
    }
    .badge-gray {
        background: rgba(107, 114, 128, 0.12);
        color: #4B5563;
        border: 1px solid rgba(107, 114, 128, 0.25);
        padding: 0.1rem 0.4rem;
        border-radius: 0.25rem;
        font-size: 0.7rem;
        font-weight: 700;
    }
    
    /* Quick Links Menu styling */
    .quick-link-container {
        background: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 1rem;
        padding: 0.5rem 1rem;
    }
    .quick-link-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.8rem 0.25rem;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        color: #1F2937;
        font-size: 0.85rem;
        text-decoration: none;
    }
    .quick-link-item:last-child {
        border-bottom: none;
    }
    .quick-link-arrow {
        color: #4B5563;
        font-weight: bold;
    }
    
    /* News specific lists */
    .news-card {
        background: rgba(0, 0, 0, 0.02);
        border: 1px solid rgba(0, 0, 0, 0.04);
        border-radius: 0.5rem;
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.6rem;
    }
    
    /* YouTube summaries custom styles */
    .yt-title-link {
        text-decoration: none;
        color: #4F46E5;
        transition: color 0.2s ease;
    }
    .yt-title-link:hover {
        color: #6366F1;
    }
    .yt-thumbnail {
        width: 100%;
        border-radius: 0.5rem;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
        transition: transform 0.2s ease, filter 0.2s ease;
        cursor: pointer;
        border: 1px solid rgba(0, 0, 0, 0.06);
    }
    .yt-thumbnail:hover {
        transform: scale(1.02);
        filter: brightness(1.05);
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.15);
    }
</style>
""", unsafe_allow_html=True)

# Helper to automatically build database if missing
def verify_and_build_db():
    # Check if database directory has subdirectories or files
    db_missing = True
    if config.CHROMA_DB_DIR.exists():
        files = list(config.CHROMA_DB_DIR.glob("*"))
        if len(files) > 1: # chroma.sqlite3 and subfolders
            db_missing = False
            
    if db_missing:
        st.info("📦 로컬 지식베이스가 구축되어 있지 않습니다. 자동 적재를 진행합니다...")
        try:
            # Check for API key
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                st.warning("⚠️ OPENAI_API_KEY 환경변수가 설정되지 않아 임베딩을 완료할 수 없습니다. .env 파일을 작성하거나 API 키를 설정해주세요.")
                return False
            ingest.ingest_data(dry_run=False)
            st.success("🎉 지식베이스 적재가 완료되었습니다. 에이전트가 정상 가동됩니다!")
            return True
        except Exception as e:
            st.error(f"❌ 데이터 적재 오류 발생: {e}")
            return False
    return True

# Handle pending tab changes before any widgets are instantiated
if "pending_tab_change" in st.session_state and st.session_state.pending_tab_change:
    target_tab = st.session_state.pending_tab_change
    st.session_state.navigation_radio = target_tab
    st.session_state.current_tab = target_tab
    if target_tab == "📝 실전 권리분석 퀴즈":
        st.session_state.quiz_active = True
    else:
        st.session_state.quiz_active = False
    st.session_state.pending_tab_change = None

# Initialize Session State
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "🏠 홈 대시보드"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False
if "current_case_id" not in st.session_state:
    st.session_state.current_case_id = "case_1"
if "quiz_graded" not in st.session_state:
    st.session_state.quiz_graded = False
if "grade_results" not in st.session_state:
    st.session_state.grade_results = None
if "diary_analysis" not in st.session_state:
    st.session_state.diary_analysis = None
if "diary_history" not in st.session_state:
    st.session_state.diary_history = diary_agent.load_history()
if "active_agent" not in st.session_state:
    st.session_state.active_agent = "idle"
if "pdf_analysis_result" not in st.session_state:
    st.session_state.pdf_analysis_result = None
if "pdf_chat_messages" not in st.session_state:
    st.session_state.pdf_chat_messages = []
if "analyzing_case_id" not in st.session_state:
    st.session_state.analyzing_case_id = None
if "analysis_completed" not in st.session_state:
    st.session_state.analysis_completed = False
if "analysis_results_text" not in st.session_state:
    st.session_state.analysis_results_text = None
if "show_analysis_dialog" not in st.session_state:
    st.session_state.show_analysis_dialog = False

@st.dialog("AI 권리분석 및 적정가 예측 결과 요약", width="large")
def show_analysis_popup(case_no, content):
    st.markdown(f"### 🏢 사건번호 {case_no} 권리분석 & 적정가 예측 리포트")
    st.markdown(f"""
    <div style="max-height: 500px; overflow-y: auto; padding: 15px; border: 1px solid rgba(0,0,0,0.1); border-radius: 8px; background-color: #f9fafb; color: #111827; font-family: 'Noto Sans KR', sans-serif; line-height: 1.6; white-space: pre-wrap;">{content}</div>
    """, unsafe_allow_html=True)
    if st.button("확인 및 닫기", use_container_width=True):
        st.session_state.show_analysis_dialog = False
        st.rerun()

def reset_chat():
    st.session_state.messages = []
    st.session_state.quiz_active = False
    st.session_state.quiz_graded = False
    st.session_state.grade_results = None
    st.session_state.diary_analysis = None
    st.session_state.diary_history = []
    st.session_state.active_agent = "idle"
    st.session_state.pdf_analysis_result = None
    st.session_state.pdf_chat_messages = []
    if "dashboard_data" in st.session_state:
        del st.session_state.dashboard_data
    st.session_state.analyzing_case_id = None
    st.session_state.analysis_completed = False
    st.session_state.analysis_results_text = None
    st.session_state.show_analysis_dialog = False
    diary_agent.save_history([])

@st.cache_data(ttl=3600)
def generate_ai_briefing(news_feed):
    """
    Generates a 3-line AI briefing of the current real estate auction market
    using the fetched news feed articles.
    """
    import providers
    if not news_feed:
        return [
            "수도권 아파트 낙찰가율이 고공행진을 보이며 선호 입지로의 쏠림 현상이 강화되고 있습니다.",
            "임차인의 대항력 여부에 따른 보증금 인수 조건 등 법적 인수 권리를 철저히 권리분석 해야 합니다.",
            "유치권 신고나 미납 관리비 등 추가 인수 비용이 발생할 수 있으므로 현장 임장 활동이 필수적입니다."
        ]
        
    compiled_news = ""
    for idx, item in enumerate(news_feed):
        compiled_news += f"{idx+1}. [{item.get('press', '언론사')}] {item.get('title', '제목 미상')}\n"
        
    system_prompt = (
        "당신은 부동산 경매 시장 분석 최고책임자(CAO) 강대호 박사입니다.\\n"
        "제공된 최신 부동산 경매 뉴스 헤드라인 목록을 종합하여, 오늘의 부동산 경매 시황과 트렌드를 분석해주세요.\\n"
        "사용자가 읽기 편하도록 명확하고 신뢰감 있는 구어체(~체)로 단 3개의 핵심 요약 문장(리스트 형태)으로만 응답해야 합니다.\\n"
        "어떤 마크다운 코드 블록(```json 등)도 포함하지 말고 오직 순수 JSON 배열 형식으로만 출력하십시오.\\n\\n"
        "출력 예시:\\n"
        "[\\n"
        "  \\\"서울 및 수도권 아파트 낙찰가율이 90%를 돌파하며 입찰 열기가 뜨거워지고 있습니다.\\\",\\n"
        "  \\\"선순위 임차인이 존재해 보증금 인수 리스크가 있는 물건의 입찰 시 권리분석 주의가 요구됩니다.\\\",\\n"
        "  \\\"지방 토지 경매 시장은 유찰이 늘며 낙찰률 하락세가 이어지고 있어 실수요자 위주 접근이 좋습니다.\\\"\\n"
        "]"
    )
    
    user_prompt = f"최신 뉴스 헤드라인 목록:\\n{compiled_news}"
    
    try:
        llm = providers.get_llm(temperature=0.3)
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        content = response.content.strip()
        
        if content.startswith("```json"):
            content = content.split("```json", 1)[1]
        if content.endswith("```"):
            content = content.rsplit("```", 1)[0]
        content = content.strip()
        
        import json
        briefing = json.loads(content)
        if isinstance(briefing, list) and len(briefing) >= 3:
            return briefing[:3]
        return [content]
    except Exception as e:
        print(f"Error generating AI briefing: {e}")
        return [
            "수도권 아파트 낙찰가율이 고공행진을 보이며 선호 입지로의 쏠림 현상이 강화되고 있습니다.",
            "임차인의 대항력 여부에 따른 보증금 인수 조건 등 법적 인수 권리를 철저히 권리분석 해야 합니다.",
            "유치권 신고나 미납 관리비 등 추가 인수 비용이 발생할 수 있으므로 현장 임장 활동이 필수적입니다."
        ]

def render_agent_monitor(placeholder=None):
    active = st.session_state.get("active_agent", "idle")
    
    agents_info = [
        ("router", "🧠 오케스트레이터 라우터"),
        ("procedure", "📋 절차 안내 에이전트"),
        ("tutor", "🎓 권리분석 튜터 에이전트"),
        ("quiz", "🎯 퀴즈 채점 에이전트"),
        ("diary", "📓 학습일기 분석 에이전트"),
    ]
    
    html_content = "--- \n### 🤖 에이전트 모니터링\n"
    for key, name in agents_info:
        if active == key:
            html_content += f"<div style='display:flex; justify-content:space-between; align-items:center; padding:4px 8px; background-color:rgba(16,185,129,0.1); border-radius:6px; border:1px solid rgba(16,185,129,0.3); margin-bottom:4px;'><strong style='color:#057A55;'>{name}</strong><span style='color:#057A55; font-size:0.8rem; font-weight:700;'>🟢 활성</span></div>"
        else:
            html_content += f"<div style='display:flex; justify-content:space-between; align-items:center; padding:4px 8px; margin-bottom:4px;'><span style='color:#374151;'>{name}</span><span style='color:#9CA3AF; font-size:0.8rem;'>⚪ 대기</span></div>"
            
    if placeholder is not None:
        placeholder.markdown(html_content, unsafe_allow_html=True)
    else:
        st.markdown(html_content, unsafe_allow_html=True)

# Sidebar Content
with st.sidebar:
    st.markdown("### 🏛️ Veteran AI 경매")
    
    
    st.markdown("---")
    st.markdown("### 🗺️ 네비게이션")
    menu_options = ["🏠 홈 대시보드", "💬 AI Q&A 대화방", "📝 실전 권리분석 퀴즈", "📓 나의 경매 학습일기", "📄 실전 명세서 PDF 분석", "👥 에이전트 People 소개"]
    
    default_idx = 0
    if st.session_state.get("quiz_active", False):
        default_idx = 2
    elif st.session_state.get("current_tab") == "💬 AI Q&A 대화방":
        default_idx = 1
    elif st.session_state.get("current_tab") == "📓 나의 경매 학습일기":
        default_idx = 3
    elif st.session_state.get("current_tab") == "📄 실전 명세서 PDF 분석":
        default_idx = 4
    elif st.session_state.get("current_tab") == "👥 에이전트 People 소개":
        default_idx = 5
        
    selected_menu = st.radio(
        "이동할 메뉴 선택",
        menu_options,
        index=default_idx,
        key="navigation_radio"
    )
    
    # Sync states
    if selected_menu == "🏠 홈 대시보드":
        st.session_state.quiz_active = False
        st.session_state.current_tab = "🏠 홈 대시보드"
    elif selected_menu == "💬 AI Q&A 대화방":
        st.session_state.quiz_active = False
        st.session_state.current_tab = "💬 AI Q&A 대화방"
    elif selected_menu == "📝 실전 권리분석 퀴즈":
        st.session_state.quiz_active = True
        st.session_state.current_tab = "📝 실전 권리분석 퀴즈"
    elif selected_menu == "📓 나의 경매 학습일기":
        st.session_state.quiz_active = False
        st.session_state.current_tab = "📓 나의 경매 학습일기"
    elif selected_menu == "📄 실전 명세서 PDF 분석":
        st.session_state.quiz_active = False
        st.session_state.current_tab = "📄 실전 명세서 PDF 분석"
    elif selected_menu == "👥 에이전트 People 소개":
        st.session_state.quiz_active = False
        st.session_state.current_tab = "👥 에이전트 People 소개"
        
    monitor_placeholder = st.empty()
    render_agent_monitor(monitor_placeholder)
    
    st.markdown("---")
    
    if st.button("🧹 대화 초기화", use_container_width=True):
        reset_chat()
        st.rerun()
        
    st.markdown("---")
    st.markdown("### ✏️ 실전 권리분석 퀴즈")
    st.write("가상 경매 물건의 권리관계를 직접 분석하고 AI의 상세 채점과 피드백을 받아보세요.")
    
    cases = quiz_agent.load_cases()
    if cases:
        case_options = {c["title"]: c["id"] for c in cases}
        selected_title = st.selectbox("물건 선택", list(case_options.keys()))
        case_id = case_options[selected_title]
        
        if st.button("🚀 퀴즈 풀기 시작", use_container_width=True):
            st.session_state.quiz_active = True
            st.session_state.current_case_id = case_id
            st.session_state.quiz_graded = False
            st.session_state.grade_results = None
            st.session_state.active_agent = "quiz"
            st.session_state.pending_tab_change = "📝 실전 권리분석 퀴즈"
            st.rerun()
    else:
        st.warning("불러올 수 있는 사례 데이터가 없습니다.")

# Main Page Layout

# Database Status Check (Legal disclaimer banner completely removed here)
db_ready = verify_and_build_db()

# Trigger dialog popup if completed
if st.session_state.get("show_analysis_dialog") and st.session_state.get("analysis_results_text"):
    show_analysis_popup(st.session_state.analyzing_case_id, st.session_state.analysis_results_text)

# Render content based on active tab
if st.session_state.current_tab == "🏠 홈 대시보드":
    # Header date, weather and main title (Mapped from template)
    st.markdown("""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 1.5rem;">
        <span style="color:#4B5563; font-weight:600; font-size:0.95rem;">📅 2026.06.20 (토) ☀️ 25°C</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Check/Load Dashboard Data with Session State Caching
    if "dashboard_data" not in st.session_state:
        with st.spinner("🔄 대시보드 데이터를 수집하고 있습니다..."):
            try:
                st.session_state.dashboard_data = asyncio.run(load_dashboard_data(limit=5))
            except TypeError: # Handle limit vs news_limit arg matching
                try:
                    st.session_state.dashboard_data = asyncio.run(load_dashboard_data(news_limit=5))
                except Exception:
                    st.session_state.dashboard_data = {"news": [], "youtube": []}
            except Exception:
                st.session_state.dashboard_data = {"news": [], "youtube": []}
                
    dash_data = st.session_state.dashboard_data
    
    # 2-Column Main Layout: col_main (left/mid dashboard), col_side (right panel)
    col_main, col_side = st.columns([2.1, 0.9])
    
    with col_main:
        # 1. AI 브리핑 (뉴스 3줄 요약)
        st.markdown("### ✨ AI 브리핑")
        briefing = generate_ai_briefing(dash_data.get("news", []))
        briefing_html = f"""
        <div style="background: linear-gradient(135deg, rgba(79, 70, 229, 0.05) 0%, rgba(124, 58, 237, 0.05) 100%);
                    border: 1px solid rgba(79, 70, 229, 0.15);
                    border-radius: 1rem;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;">
            <div style="font-weight: 700; font-size: 1.15rem; color: #4F46E5; margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                🔮 오늘의 부동산 경매시황 브리핑
            </div>
            <ul style="margin: 0; padding-left: 1.2rem; color: #1F2937; font-size: 0.92rem; line-height: 1.6;">
                <li>{briefing[0]}</li>
                <li>{briefing[1]}</li>
                <li>{briefing[2]}</li>
            </ul>
        </div>
        """
        st.markdown(briefing_html, unsafe_allow_html=True)
        
        # 2. 법원경매물건 리스트 (추천 3건 / 일반 11건)
        st.markdown("### 🏛️ 실전 법원경매물건 분석 & 추천")
        from dashboard.excel_loader import load_auction_excel
        excel_data = load_auction_excel()
        recommended = excel_data.get("recommended", [])
        general = excel_data.get("general", [])
        
        st.markdown("##### ⭐ 추천알짜 물건 (3선)")
        if recommended:
            rec_cols = st.columns(3)
            for idx, r in enumerate(recommended):
                with rec_cols[idx]:
                    case_no = r.get('사건번호', '').strip()
                    # Fetch real prices from MOLIT API
                    from dashboard.molit_api import fetch_real_prices
                    real_prices = fetch_real_prices(case_no, r.get('소재지 및 내역', ''), r.get('용도', ''))
                    
                    price_items = []
                    for p in real_prices:
                        floor_info = f" ({p['floor']})" if p.get('floor') else ""
                        price_items.append(f"• {p['date']} | <strong style='color:#111827;'>{p['price']}</strong>{floor_info}")
                    
                    if not price_items:
                        price_items_html = "• 최근 거래 내역 없음"
                    else:
                        price_items_html = "<br/>".join(price_items[:3])

                    st.markdown(f"""
                    <div style="background: rgba(255, 255, 255, 0.85);
                                border: 1px solid rgba(217, 119, 6, 0.25);
                                border-top: 4px solid #D97706;
                                border-radius: 0.75rem;
                                padding: 1.1rem;
                                min-height: 450px;
                                height: auto;
                                display: flex;
                                flex-direction: column;
                                justify-content: space-between;
                                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                                margin-bottom: 10px;">
                        <div>
                            <span style="background-color: rgba(217, 119, 6, 0.12); color: #D97706; font-size: 0.7rem; font-weight: 700; padding: 0.25rem 0.5rem; border-radius: 4px;">{r.get('recommend_tag', '추천')}</span>
                            <div style="font-weight: 700; font-size: 1.05rem; color: #111827; margin-top: 0.5rem; margin-bottom: 0.25rem;">{r.get('용도', '물건')}</div>
                            <div style="font-size: 0.78rem; color: #4B5563; font-weight: 600; margin-bottom: 0.6rem;">{r.get('사건번호', '사건번호 미상')}</div>
                            <div style="font-size: 0.8rem; color: #1F2937; line-height: 1.4; margin-bottom: 0.5rem; height: 3.2em; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                                {r.get('소재지 및 내역', '소재지 정보 없음')}
                            </div>
                            <div style="margin-top: 0.5rem; border-top: 1px solid rgba(0,0,0,0.05); padding-top: 0.5rem; margin-bottom: 0.5rem;">
                                <div style="font-size: 0.75rem; font-weight: 700; color: #4F46E5; margin-bottom: 0.25rem;">📈 국토부 실거래가 (최근)</div>
                                <div style="font-size: 0.72rem; color: #374151; line-height: 1.4;">
                                    {price_items_html}
                                </div>
                            </div>
                        </div>
                        <div>
                            <div style="border-top: 1px dashed rgba(0,0,0,0.08); padding-top: 0.5rem; margin-bottom: 0.4rem;">
                                <div style="display:flex; justify-content:space-between; font-size: 0.73rem; color:#6B7280;">
                                    <span>감정가</span>
                                    <span style="text-decoration: line-through;">{r.get('appraisal_formatted', '0')}</span>
                                </div>
                                <div style="display:flex; justify-content:space-between; align-items: center; margin-top: 0.1rem;">
                                    <span style="font-size: 0.75rem; font-weight: 700; color: #DC2626;">최저가 ({r.get('discount_percent', 0)}%↓)</span>
                                    <span style="font-size: 0.92rem; font-weight: 700; color: #111827;">{r.get('minimum_bid_formatted', '0')}</span>
                                </div>
                            </div>
                            <div style="background-color: rgba(0, 0, 0, 0.02); padding: 0.4rem; border-radius: 4px; font-size: 0.71rem; color: #4B5563; line-height: 1.35; border: 1px solid rgba(0,0,0,0.03); overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                                <strong>추천이유:</strong> {r.get('recommend_reason', '')}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Render AI Analysis button
                    case_no = r.get('사건번호', '').strip()
                    if st.button("🔍 AI 권리분석 & 적정가 예측", key=f"ai_analyze_btn_{idx}", use_container_width=True):
                        st.session_state.analyzing_case_id = case_no
                        st.session_state.analysis_completed = False
                        st.session_state.analysis_results_text = None
                        st.session_state.show_analysis_dialog = False
                        st.rerun()
            st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
        else:
            st.info("추천 물건이 없습니다.")
            
        st.markdown("##### 📋 일반 경매 매물 목록 (11건)")
        if general:
            gen_data = []
            for g in general:
                gen_data.append({
                    "사건번호": g.get("사건번호", "-"),
                    "용도": g.get("용도", "-"),
                    "소재지 및 내역": g.get("소재지 및 내역", "-"),
                    "감정평가액": g.get("appraisal_formatted", "-"),
                    "최저매각가격": g.get("minimum_bid_formatted", "-"),
                    "할인율": f"{g.get('discount_percent', 0)}%",
                    "유찰횟수": f"{int(g.get('유찰횟수', 0))}회",
                    "진행상태": g.get("진행상태", "-"),
                    "매각기일": str(g.get("매각기일", "-"))[:10]
                })
            df_gen = pd.DataFrame(gen_data)
            st.dataframe(df_gen, use_container_width=True, hide_index=True)
        else:
            st.info("일반 매물 목록이 비어 있습니다.")
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
            
        # 3. 유튜브 동영상 '김딸기' 가로 썸네일 배치
        st.markdown("### 🎬 경매 유튜버 '김딸기' 핵심 영상")
        from dashboard.youtube import get_video_list, get_youtube_summary
        yt_videos = get_video_list()
        if yt_videos:
            yt_cols = st.columns(3)
            for idx, y_vid in enumerate(yt_videos):
                v_id = y_vid["video_id"]
                y_item = get_youtube_summary(v_id)
                with yt_cols[idx]:
                    with st.container(border=True):
                        st.video(f"https://www.youtube.com/watch?v={v_id}")
                        st.markdown(f"""
                        <div style="margin-top: 0.5rem; margin-bottom: 0.5rem; height: 60px;">
                            <a href="https://www.youtube.com/watch?v={v_id}" target="_blank" style="text-decoration:none; color:#111827; font-weight:700; font-size:0.85rem; line-height:1.4; display:block; height:40px; overflow:hidden; text-overflow:ellipsis;">
                                {y_vid['title']}
                            </a>
                            <span style="color:#6B7280; font-size:0.7rem; display:block; margin-top:0.15rem;">채널: {y_vid['channel']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("🔍 AI 자막 요약 보기"):
                            for bullet in y_item.get("summary", []):
                                st.write(f"- {bullet}")
                            tags = y_item.get("keywords", [])
                            if tags:
                                st.caption(" ".join(tags))
        else:
            st.info("유튜브 요약 정보를 불러올 수 없습니다.")
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
            
        # 4. 소설 연재 (나의 경매일지)
        st.markdown("### 📓 나의 경매일지 - 경매로 만난 청춘남녀의 이야기")
        episodes = novel_loader.load_novel()
        if episodes:
            for ep in episodes:
                with st.expander(f"제 {ep['episode']}화: {ep['title']} ({ep['date']})"):
                    st.write(ep['content'])
        else:
            st.write("연재된 소설이 없습니다.")
        st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
            
        # 5. 경매 통계 및 시장 경제 지표 (Plotly)
        st.markdown("""
        <div class="section-card" style="margin-bottom: 0px; border-bottom-left-radius: 0px; border-bottom-right-radius: 0px;">
            <div class="section-header">
                <div class="section-title">📈 경매 통계 및 시장 경제 지표</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.container():
            stat_tabs = st.tabs(["📉 낙찰가율 추이", "🍩 매물 종류 분포", "📍 지역별 현황"])
            with stat_tabs[0]:
                st.plotly_chart(get_bid_ratio_trend_chart(), use_container_width=True, config={'displayModeBar': False})
            with stat_tabs[1]:
                st.plotly_chart(get_property_distribution_chart(), use_container_width=True, config={'displayModeBar': False})
            with stat_tabs[2]:
                st.plotly_chart(get_regional_volume_chart(), use_container_width=True, config={'displayModeBar': False})

    # Right Sidebar Panel (AI Helper box & Shortcuts/News/YouTube tabs)
    with col_side:
        analyzing_case = st.session_state.get("analyzing_case_id")
        if analyzing_case:
            st.markdown(f"""
            <div class="ai-panel" style="margin-bottom: 10px;">
                <div class="ai-panel-header">
                    🤖 AI가 분석중이예요
                </div>
                <div style="font-size: 0.85rem; font-weight: bold; color: #4B5563; margin-top: -5px; margin-bottom: 10px;">
                    사건번호: {analyzing_case}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show progress monitor area
            status_placeholder = st.empty()
            
            # 1. Find matching files and sort them according to categories
            matched_files = []
            import re
            match = re.search(r"(\d{4})타경(\d+)", analyzing_case)
            if match:
                year, num = match.groups()
                dir_path = Path(config.BASE_DIR) / "경매자료"
                if not dir_path.exists():
                    dir_path = Path(config.BASE_DIR).parent / "경매자료"
                if dir_path.exists():
                    for file in dir_path.glob("*.pdf"):
                        if year in file.name and num in file.name:
                            matched_files.append(file)
            
            categories_order = ["현황조사서", "매각물건명세서", "감정평가서", "건축물대장", "등기부등본", "전입세대확인서"]
            sorted_files = []
            file_to_category = {}
            for cat in categories_order:
                for f in matched_files:
                    if cat in f.name:
                        sorted_files.append(f)
                        file_to_category[f] = cat
                        break
            
            # Add other unmatched pdfs that contain the case number
            for f in matched_files:
                if f not in sorted_files:
                    sorted_files.append(f)
                    file_to_category[f] = f.name
            
            # Render function in Left agent monitor style
            def render_statuses(current_statuses):
                html = "<div style='margin-bottom:1.5rem;'>"
                for f in sorted_files:
                    cat_name = file_to_category[f]
                    status = current_statuses.get(f, "⚪ 대기")
                    if "분석 중" in status:
                        html += f"<div style='display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background-color:rgba(217,119,6,0.1); border-radius:6px; border:1px solid rgba(217,119,6,0.3); margin-bottom:6px;'><strong style='color:#D97706;'>{cat_name}</strong><span style='color:#D97706; font-size:0.8rem; font-weight:700;'>🟡 분석 중...</span></div>"
                    elif "분석 완료" in status:
                        html += f"<div style='display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background-color:rgba(16,185,129,0.1); border-radius:6px; border:1px solid rgba(16,185,129,0.3); margin-bottom:6px;'><strong style='color:#057A55;'>{cat_name}</strong><span style='color:#057A55; font-size:0.8rem; font-weight:700;'>🟢 분석 완료</span></div>"
                    else:
                        html += f"<div style='display:flex; justify-content:space-between; align-items:center; padding:6px 12px; margin-bottom:6px; background-color:rgba(0,0,0,0.02); border-radius:6px; border:1px solid rgba(0,0,0,0.05);'><span style='color:#374151;'>{cat_name}</span><span style='color:#9CA3AF; font-size:0.8rem;'>⚪ 대기</span></div>"
                
                # Append the virtual final step "실거래가 반영 예측중"
                pred_status = current_statuses.get("predict", "⚪ 대기")
                if "분석 중" in pred_status or "예측 중" in pred_status:
                    html += f"<div style='display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background-color:rgba(79,70,229,0.1); border-radius:6px; border:1px solid rgba(79,70,229,0.3); margin-bottom:6px;'><strong style='color:#4F46E5;'>실거래가 반영 예측중</strong><span style='color:#4F46E5; font-size:0.8rem; font-weight:700;'>🟡 예측 중...</span></div>"
                elif "분석 완료" in pred_status or "예측 완료" in pred_status:
                    html += f"<div style='display:flex; justify-content:space-between; align-items:center; padding:6px 12px; background-color:rgba(16,185,129,0.1); border-radius:6px; border:1px solid rgba(16,185,129,0.3); margin-bottom:6px;'><strong style='color:#057A55;'>실거래가 반영 예측중</strong><span style='color:#057A55; font-size:0.8rem; font-weight:700;'>🟢 예측 완료</span></div>"
                else:
                    html += f"<div style='display:flex; justify-content:space-between; align-items:center; padding:6px 12px; margin-bottom:6px; background-color:rgba(0,0,0,0.02); border-radius:6px; border:1px solid rgba(0,0,0,0.05);'><span style='color:#374151;'>실거래가 반영 예측중</span><span style='color:#9CA3AF; font-size:0.8rem;'>⚪ 대기</span></div>"
                
                html += "</div>"
                status_placeholder.markdown(html, unsafe_allow_html=True)
            
            if not st.session_state.get("analysis_completed"):
                # Initial statuses: all "⚪ 대기"
                statuses = {f: "⚪ 대기" for f in sorted_files}
                statuses["predict"] = "⚪ 대기"
                render_statuses(statuses)
                time.sleep(0.5)
                
                full_extracted_text = ""
                for idx, f in enumerate(sorted_files):
                    statuses[f] = "🟡 분석 중..."
                    render_statuses(statuses)
                    
                    try:
                        with open(f, "rb") as file_obj:
                            file_bytes = file_obj.read()
                        text = extract_text_from_pdf(file_bytes)
                        cat_name = file_to_category[f]
                        full_extracted_text += f"\n=== {cat_name} ({f.name}) ===\n{text}\n"
                    except Exception as e:
                        full_extracted_text += f"\n=== {file_to_category[f]} ({f.name}) ===\n오류: {e}\n"
                    
                    time.sleep(0.8) # Simulate processing delay
                    statuses[f] = "🟢 분석 완료"
                    render_statuses(statuses)
                    time.sleep(0.3)
                
                if not sorted_files:
                    status_placeholder.warning("해당 사건번호와 일치하는 경매자료 파일(PDF)이 존재하지 않습니다.")
                    full_extracted_text = "경매자료 폴더에 해당 사건 관련 분석할 파일이 존재하지 않습니다."
                
                # Update status for virtual final prediction step
                statuses["predict"] = "예측 중"
                render_statuses(statuses)
                time.sleep(1.0)
                
                # Fetch target property details and actual transaction prices
                r_item = None
                for r in recommended:
                    if r.get("사건번호", "").strip() == analyzing_case:
                        r_item = r
                        break
                
                address = r_item.get("소재지 및 내역", "") if r_item else ""
                use_type = r_item.get("용도", "") if r_item else ""
                appraisal_val = r_item.get("appraisal_formatted", "미상") if r_item else "미상"
                min_bid_val = r_item.get("minimum_bid_formatted", "미상") if r_item else "미상"
                
                from dashboard.molit_api import fetch_real_prices
                real_prices = fetch_real_prices(analyzing_case, address, use_type)
                
                prices_text = ""
                if real_prices:
                    for p in real_prices:
                        prices_text += f"- {p['date']} | {p['price']} ({p['floor']})\n"
                else:
                    prices_text = "- 최근 6개월 내 국토부 실거래 내역 없음\n"
                
                # Call LLM
                with st.spinner("🤖 CAO 에이전트가 권리관계 및 실거래가 기반 적정 입찰가를 분석 중입니다..."):
                    try:
                        llm = providers.get_llm(temperature=0.2)
                        system_prompt = (
                            "당신은 부동산 경매 최고 분석 책임자(CAO) 강대호 박사입니다.\n"
                            "첨부된 사건에 관련된 법원 서류들(현황조사서, 매각물건명세서 등)의 원본 내용 텍스트와 최근 국토부 실거래가 정보를 정밀 분석하여 "
                            "임차인의 대항력 유무 및 보증금 인수 가능성, 말소기준권리 정보, 인수 대상인 등기부상 권리 및 비고란 특이사항(유치권, 법정지상권 등)을 요약해주세요.\n"
                            "특히, 최근 실거래 시세와 권리분석상의 하자(인수해야 하는 임차보증금 등)를 종합적으로 고려하여 낙찰을 위한 'AI 산정 적정 입찰 가격 범위'를 도출하고 그 이유를 보고서의 최상단에 눈에 띄게 제시해 주십시오.\n"
                            "이 제안 섹션은 '📊 AI 산정 적정 입찰가 제안'이라는 제목 아래에 굵은 볼드체와 깔끔한 포맷(예: [추천 입찰가: XX억 ~ XX억])으로 돋보이게 작성해주세요.\n"
                            "※ 경고: 단위 계산(억 vs 천만 등)에 매우 각별히 유의하십시오. 감정가 및 최저가가 수십억 원 단위(예: 28억 5,000만원, 22억 8,000만원)인 매물의 경우, 적정 추천 입찰가 범위 역시 수십억 원 단위(예: [추천 입찰가: 23억 원 ~ 24억 원])로 올바르게 표시해야 하며, 2억 원 ~ 3억 원처럼 10배 작게 표시하는 단위 실수를 저질러서는 절대 안 됩니다.\n"
                            "답변은 가독성 좋고 신뢰감이 가는 어조의 한국어로 상세하게 요약해주십시오."
                        )
                        user_prompt = (
                            f"첨부된 자료와 실거래가를 분석하고 내용 요약 및 적정 낙찰가를 예측해줘.\n"
                            f"사건번호: {analyzing_case}\n"
                            f"감정가: {appraisal_val}\n"
                            f"최저가: {min_bid_val}\n\n"
                            f"[최근 국토교통부 실거래가 정보]\n{prices_text}\n"
                            f"[원본 데이터]\n{full_extracted_text[:12000]}"
                        )
                        
                        response = llm.invoke([
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ])
                        st.session_state.analysis_results_text = response.content
                    except Exception as e:
                        st.session_state.analysis_results_text = f"분석 중 오류가 발생했습니다: {e}"
                
                statuses["predict"] = "예측 완료"
                render_statuses(statuses)
                time.sleep(0.5)
                
                st.session_state.analysis_completed = True
                st.session_state.show_analysis_dialog = True
                st.rerun()
            else:
                # Completed state rendering
                statuses = {f: "🟢 분석 완료" for f in sorted_files}
                statuses["predict"] = "예측 완료"
                render_statuses(statuses)
                if st.button("🔄 재분석 시작", use_container_width=True):
                    st.session_state.analysis_completed = False
                    st.session_state.analysis_results_text = None
                    st.session_state.show_analysis_dialog = False
                    st.rerun()
                if st.button("📊 결과 보고서 다시보기", use_container_width=True):
                    st.session_state.show_analysis_dialog = True
                    st.rerun()
                if st.button("❌ 분석 종료", use_container_width=True):
                    st.session_state.analyzing_case_id = None
                    st.session_state.analysis_completed = False
                    st.session_state.analysis_results_text = None
                    st.session_state.show_analysis_dialog = False
                    st.rerun()
        else:
            # Default Helper Panel
            st.markdown("""
            <div class="ai-panel">
                <div class="ai-panel-header">
                    ✨ AI 비서 오늘의 추천 입찰 정보!
                </div>
                <div class="ai-task-card">
                    <span class="badge-red">긴급</span>
                    <div class="ai-task-title">선순위 배당요구종기 임박 물건</div>
                    <div class="ai-task-bullet">• 물건번호: 2025타경104</div>
                    <div class="ai-task-bullet">• 기한: 오늘 18:00 (배당요구 신청 마감)</div>
                </div>
                <div class="ai-task-card">
                    <span class="badge-orange">오늘의 물건</span>
                    <div class="ai-task-title">강남구 대치동 아파트 신건 입찰 추천</div>
                    <div class="ai-task-bullet">• 최저가: 12.5억 (감정가 대비 100%)</div>
                </div>
                <div class="ai-task-card">
                    <span class="badge-gray">주의 필요</span>
                    <div class="ai-task-title">유치권 신고 및 인수 권리 분석 3건</div>
                    <div class="ai-task-bullet">• 도곡동 상가 (유치권 신고서 접수됨)</div>
                    <div class="ai-task-bullet">• 방배동 빌라 (대항력 있는 임차인 존재)</div>
                    <div class="ai-task-bullet">• 신사동 빌딩 (법정지상권 성립 불분명)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Shortcuts & News inside right side tabs
        side_tabs = st.tabs(["⭐ 즐겨찾기", "📰 최신 뉴스"])
        
        with side_tabs[0]:
            st.markdown("<div class=\"quick-link-container\">", unsafe_allow_html=True)
            if st.button("📝 권리분석 퀴즈 시작하기", use_container_width=True):
                st.session_state.quiz_active = True
                st.session_state.pending_tab_change = "📝 실전 권리분석 퀴즈"
                st.rerun()
            if st.button("💬 AI 상담 에이전트 연결", use_container_width=True):
                st.session_state.quiz_active = False
                st.session_state.pending_tab_change = "💬 AI Q&A 대화방"
                st.rerun()
            if st.button("📓 나의 경매 일기 쓰기", use_container_width=True):
                st.session_state.quiz_active = False
                st.session_state.pending_tab_change = "📓 나의 경매 학습일기"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        with side_tabs[1]:
            news_feed = dash_data.get("news", [])
            if news_feed:
                for item in news_feed:
                    st.markdown(f"""
                    <div class="news-card">
                        <span style="color:#A855F7; font-size:0.75rem; font-weight:600;">[{item['press']}]</span><br/>
                        <a href="{item['link']}" target="_blank" style="text-decoration:none; color:#111827; font-weight:600; font-size:0.82rem;">
                            {item['title']}
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("뉴스를 불러오는 데 실패했습니다.")

elif st.session_state.current_tab == "📝 실전 권리분석 퀴즈":
    st.markdown("### 📝 실전 사례 권리분석 퀴즈 모드")
    
    # Load question data
    try:
        q_data = quiz_agent.get_question(st.session_state.current_case_id)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader(f"🏢 {q_data['title']} (난이도: {q_data['difficulty']})")
            st.write(q_data["description"])
            
            st.markdown(f"**💰 감정평가액:** `{q_data['appraised_value']}`")
            st.markdown(f"**📉 최저매각가격:** `{q_data['minimum_bid_price']}`")
            
            st.markdown("#### 📜 등기부등본 현황")
            reg_df = pd.DataFrame(q_data["registry_records"])
            # Rename columns for presentation
            reg_df.columns = ["순번", "등기일자", "등기목적", "권리자", "금액", "인수/소멸 여부(퀴즈 대상)"]
            # Exclude answer status columns so students analyze it
            st.dataframe(reg_df.iloc[:, :-1], use_container_width=True, hide_index=True)
            
            st.markdown("#### 👥 임차인 현황")
            ten_df = pd.DataFrame(q_data["tenant_records"])
            ten_df.columns = ["임차인명", "보증금", "주택인도 및 전입신고일", "확정일자", "점유범위", "대항력여부(퀴즈 대상)"]
            st.dataframe(ten_df.iloc[:, :-1], use_container_width=True, hide_index=True)
            
            if "notes" in q_data:
                st.info(f"💡 **참고사항:** {q_data['notes']}")
                
        with col2:
            st.subheader("🧐 당신의 권리분석 답안")
            st.write("아래 항목을 분석하여 기재한 뒤 채점 버튼을 누르세요.")
            
            with st.form("quiz_form"):
                ans_malso = st.text_input("1. 본 물건의 말소기준권리는 무엇이며 설정일은 언제인가요?", placeholder="예: 2023년 3월 15일 한국은행 근저당권")
                ans_opposing = st.text_input("2. 임차인은 낙찰자(매수인)에게 대항력이 존재하나요? 그 이유는 무엇인가요?", placeholder="예: 전입일이 말소기준권리보다 늦으므로 대항력이 없습니다.")
                ans_takeover = st.text_area("3. 낙찰자가 추가로 인수해야 하는 등기부상 권리나 임차보증금이 있습니까?", placeholder="예: 인수할 금액이나 등기상 제한물권은 없습니다. 모두 매각으로 소멸합니다.")
                ans_risk = st.text_area("4. 본 물건의 종합적인 위험 평가와 입찰 시 주의할 점을 적어주세요.", placeholder="예: 대항력 없는 임차인이므로 인도명령 대상이나, 명도 조율이 필요합니다.")
                
                submit_quiz = st.form_submit_button("🎯 답안 채점하기", use_container_width=True)
                
            if submit_quiz:
                st.session_state.active_agent = "quiz"
                with st.spinner("AI 채점 위원이 답안을 정밀 검토 중입니다..."):
                    student_answers = {
                        "malso_standard": ans_malso,
                        "opposing_power": ans_opposing,
                        "takeover_rights": ans_takeover,
                        "risk_assessment": ans_risk
                    }
                    results = quiz_agent.grade(st.session_state.current_case_id, student_answers)
                    st.session_state.grade_results = results
                    st.session_state.quiz_graded = True
            
            # Show grade report
            if st.session_state.quiz_graded and st.session_state.grade_results:
                res = st.session_state.grade_results
                st.markdown("### 📊 AI 채점 결과 통계")
                
                # Render score bar
                score = res["score"]
                st.metric(label="총점", value=f"{score} / 4 점")
                st.progress(score / 4.0)
                
                # Render section feedbacks
                feedbacks = res["feedback"]
                with st.expander("📍 항목별 피드백 보기", expanded=True):
                    st.markdown(f"**1. 말소기준권리:** {feedbacks.get('malso_standard', '-')}")
                    st.markdown(f"**2. 대항력 판정:** {feedbacks.get('opposing_power', '-')}")
                    st.markdown(f"**3. 인수 권리 판단:** {feedbacks.get('takeover_rights', '-')}")
                    st.markdown(f"**4. 최종 위험도 평가:** {feedbacks.get('risk_assessment', '-')}")
                    
                st.success(f"**📝 채점 총평:**\n{res.get('summary', '')}")
                
            if st.button("❌ 퀴즈 모드 종료 (대화창으로 돌아가기)", use_container_width=True):
                st.session_state.quiz_active = False
                st.session_state.quiz_graded = False
                st.session_state.grade_results = None
                st.session_state.pending_tab_change = "💬 AI Q&A 대화방"
                st.rerun()
                
    except Exception as e:
        st.error(f"퀴즈 구동 오류: {e}")
        if st.button("돌아가기"):
            st.session_state.quiz_active = False
            st.session_state.pending_tab_change = "💬 AI Q&A 대화방"
            st.rerun()

elif st.session_state.current_tab == "📓 나의 경매 학습일기":
    st.markdown("### 📝 나의 경매 학습일기 (with Google Gemini)")
    st.write("오늘 공부한 경매 개념, 법원 견학 기록, 분석한 물건의 권리관계 등을 일기 형식으로 자유롭게 기록하세요.")
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("✍️ 오늘의 경매 학습일기")
        with st.form("diary_form"):
            diary_text = st.text_area(
                "여기에 일기 내용을 작성해 주세요.",
                height=250,
                placeholder="예: 오늘 가상사례 2번 물건을 공부했다. 임차인의 전입신고일이 2024년 2월 2일이고 근저당설정일이 2024년 2월 1일이어서 임차인에게 대항력이 없다고 분석했다. 등기부상의 선순위 권리를 더 잘 파악해야겠다."
            )
            submit_diary = st.form_submit_button("🚀 일기 등록 및 AI 분석 시작", use_container_width=True)
            
        if submit_diary:
            if not diary_text.strip():
                st.warning("일기 내용을 입력해 주세요!")
            else:
                st.session_state.active_agent = "diary"
                with st.spinner("Google Gemini가 일기 내용을 바탕으로 맞춤 분석 보고서를 생성하고 있습니다..."):
                    analysis = diary_agent.analyze_diary(diary_text)
                    st.session_state.diary_analysis = analysis
                    
                    import datetime
                    new_entry = {
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "content": diary_text,
                        "analysis": analysis
                    }
                    st.session_state.diary_history.insert(0, new_entry)
                    diary_agent.save_history(st.session_state.diary_history)
                    st.rerun()
                    
        st.markdown("---")
        st.subheader("🕰️ 학습일기 기록 보관소")
        if st.session_state.diary_history:
            for idx, entry in enumerate(st.session_state.diary_history):
                with st.expander(f"📅 {entry['date']} - {entry['content'][:25]}..."):
                    st.write(f"**작성 내용:**\n{entry['content']}")
                    st.markdown("---")
                    st.markdown("**🔍 당시 AI 피드백 요약**")
                    st.info(f"💡 **AI 응원 메시지:**\n{entry['analysis'].get('emotional_support', '')}")
                    
                    risks = entry['analysis'].get('risk_flags', [])
                    if risks:
                        st.warning("⚠️ **검출된 권리분석 위험 요소:**")
                        for r in risks:
                            st.markdown(f"- **{r.get('issue', '')}**: {r.get('warning', '')}")
                    else:
                        st.success("✅ **검출된 위험 요소 없음**")
                        
                    recs = entry['analysis'].get('recommended_study', [])
                    if recs:
                        st.markdown("📚 **추천 공부:**")
                        for rec in recs:
                            st.markdown(f"- **{rec.get('topic', '')}**: {rec.get('action', '')}")
                            
                    if st.button("🗑️ 이 일지 삭제", key=f"del_diary_{idx}"):
                        st.session_state.diary_history.pop(idx)
                        diary_agent.save_history(st.session_state.diary_history)
                        if st.session_state.diary_analysis == entry['analysis']:
                            st.session_state.diary_analysis = None
                        st.rerun()
        else:
            st.caption("작성된 일기가 없습니다. 첫 일기를 기록해 보세요!")
            
    with col_right:
        st.subheader("🎨 실시간 AI 피드백 리포트 (Gemini)")
        if st.session_state.diary_analysis:
            analysis = st.session_state.diary_analysis
            
            # Emotional support card
            st.markdown(f"""
            <div class="diary-result-card">
                <h4 style="color:#A855F7; margin-top:0;">💖 AI 멘토의 응원 한마디</h4>
                <p style="font-size:1.05rem; line-height:1.6; color:#111827;">{analysis.get('emotional_support', '')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Risks & warning cards
            risks = analysis.get('risk_flags', [])
            if risks:
                st.markdown("#### ⚠️ 권리분석 및 절차적 오류 교정")
                for r in risks:
                    st.markdown(f"""
                    <div class="risk-warning-card">
                        <strong style="color:#EF4444; font-size:1.05rem;">📍 감지된 리스크: {r.get('issue', '')}</strong><br/>
                        <span style="color:#374151; font-size:0.95rem;">{r.get('warning', '')}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="diary-result-card" style="border-left: 4px solid #10B981;">
                    <strong style="color:#10B981; font-size:1.05rem;">✅ 권리분석 위험 요소 검출 없음</strong><br/>
                    <span style="color:#374151; font-size:0.95rem;">일기 내용 중에 명백한 권리분석 상의 오판이나 법률적 위험 요소가 검출되지 않았습니다. 바른 분석 능력을 기르고 계십니다!</span>
                </div>
                """, unsafe_allow_html=True)
                
            # Study recommendations cards
            recs = analysis.get('recommended_study', [])
            if recs:
                st.markdown("#### 📚 개인 맞춤형 후속 학습 추천")
                for rec in recs:
                    st.markdown(f"""
                    <div class="diary-result-card" style="border-left: 4px solid #6366F1;">
                        <strong style="color:#6366F1; font-size:1.05rem;">🔍 추천 주제: {rec.get('topic', '')}</strong><br/>
                        <span style="color:#374151; font-size:0.95rem;"><b>학습 가이드:</b> {rec.get('action', '')}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("왼쪽 작성 란에 일기를 적고 제출하면, 여기에 Google Gemini 모델이 실시간으로 작성한 심층 분석과 학습 가이드가 표시됩니다.")

elif st.session_state.current_tab == "👥 에이전트 People 소개":
    st.markdown("### 👥 AntiG 경매 에이전트 핵심 인력 및 역할 소개")
    st.write("부동산 경매 스마트 에이전트 플랫폼을 설계하고 감수하는 핵심 리더들을 소개합니다.")
    
    # 4 Profile Cards Grid (2x2)
    col1, col2 = st.columns(2)
    
    with col1:
        # PM Card
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 1rem; padding: 1.5rem; margin-bottom: 0.5rem;">
            <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
                <div style="font-size:3rem;">👑</div>
                <div>
                    <h4 style="margin:0; color:#111827;">총괄책임자 (PM)</h4>
                    <span style="color:#4F46E5; font-size:0.85rem; font-weight:600;">호출 명령어: <code>/admin</code></span>
                </div>
            </div>
            <p style="font-size:0.95rem; line-height:1.6; color:#374151; margin-bottom:0;">
                <b>역할:</b> 전체 기획, 요구사항 조율, 프로젝트 일정(WBS) 관리 및 최종 발표 시나리오 구성.<br/>
                <b>설명:</b> 5대 에이전트 패턴(라우팅, 병렬화, 평가자-최적화 등)이 누락 없이 애플리케이션 내에 조밀하게 융합되도록 WBS 일정을 지휘하며 리스크 방지를 감독합니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("📄 PM/CEO 상세 가이드라인 (admin.md) 보기"):
            try:
                with open(r"c:\AI-Agent\auction\admin.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            except Exception as e:
                st.error(f"파일을 읽을 수 없습니다: {e}")
        st.write("")
        
        # CDO Card
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 1rem; padding: 1.5rem; margin-bottom: 0.5rem;">
            <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
                <div style="font-size:3rem;">🎨</div>
                <div>
                    <h4 style="margin:0; color:#111827;">디자인최고책임자 (CDO)</h4>
                    <span style="color:#4F46E5; font-size:0.85rem; font-weight:600;">호출 명령어: <code>/cdo</code></span>
                </div>
            </div>
            <p style="font-size:0.95rem; line-height:1.6; color:#374151; margin-bottom:0;">
                <b>역할:</b> UI/UX 레이아웃 설계, 프리미엄 글래스모피즘 테마 및 CSS 스타일링 관리, 데이터 시각화 스타일 가이드라인 수립.<br/>
                <b>설명:</b> 투박한 기본 Streamlit UI 대신 미려하고 직관적인 글래스모피즘 인터페이스와 HSL 컬러 팔레트를 정의하여 플랫폼의 시각적 완성도와 신뢰감을 극대화합니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("📄 CDO 상세 가이드라인 (cdo.md) 보기"):
            try:
                with open(r"c:\AI-Agent\auction\cdo.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            except Exception as e:
                st.error(f"파일을 읽을 수 없습니다: {e}")
        st.write("")
        
    with col2:
        # CTO Card
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 1rem; padding: 1.5rem; margin-bottom: 0.5rem;">
            <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
                <div style="font-size:3rem;">💻</div>
                <div>
                    <h4 style="margin:0; color:#111827;">기술최고책임자 (CTO)</h4>
                    <span style="color:#4F46E5; font-size:0.85rem; font-weight:600;">호출 명령어: <code>/cto</code></span>
                </div>
            </div>
            <p style="font-size:0.95rem; line-height:1.6; color:#374151; margin-bottom:0;">
                <b>역할:</b> 시스템 기술 구조 설계, 데이터 인제스천(RAG/VectorDB), 에이전트 라우팅 구현, 멀티 LLM 프로바이더 연동 및 배포 최적화.<br/>
                <b>설명:</b> 비동기(`asyncio`) 데이터 크롤링 병렬화 패턴, 오케스트레이션-워커 구조를 설계하고 OpenAI 및 Gemini 모델 객체를 팩토리 패턴 형태로 안정적으로 핸들링합니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("📄 CTO 상세 가이드라인 (cto.md) 보기"):
            try:
                with open(r"c:\AI-Agent\auction\cto.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            except Exception as e:
                st.error(f"파일을 읽을 수 없습니다: {e}")
        st.write("")
        
        # CAO Card
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 1rem; padding: 1.5rem; margin-bottom: 0.5rem;">
            <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
                <div style="font-size:3rem;">⚖️</div>
                <div>
                    <h4 style="margin:0; color:#111827;">경매분석최고책임자 (CAO)</h4>
                    <span style="color:#4F46E5; font-size:0.85rem; font-weight:600;">호출 명령어: <code>/cao</code></span>
                </div>
            </div>
            <p style="font-size:0.95rem; line-height:1.6; color:#374151; margin-bottom:0;">
                <b>성명: 강대호 (CAO / 부동산학 박사, 전 서울중앙지법 경매계 사무관)</b><br/>
                <b>역할:</b> 권리분석 모델 검증, 가상 부동산 사례 설계, 민사집행법 및 임대차보호법 기반 가이드라인 수립.<br/>
                <b>설명:</b> 15년 이상의 대한민국 법원경매 실무 경력을 바탕으로 AI의 해석오류를 예방하고, 학습용 퀴즈 가이드라인이 실제 실무 및 대법원 판례와 완벽히 정합하도록 지식베이스를 최종 검수합니다.
            </p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("📄 CAO 상세 가이드라인 (auction.md) 보기"):
            try:
                with open(r"c:\AI-Agent\auction\auction.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read())
            except Exception as e:
                st.error(f"파일을 읽을 수 없습니다: {e}")
        st.write("")

elif st.session_state.current_tab == "📄 실전 명세서 PDF 분석":
    st.markdown("### 📄 매각물건명세서 자동 분석 & 권리 진단 (by 강대호 CAO)")
    st.write("법원 경매의 핵심 서류인 '매각물건명세서' PDF 파일을 업로드하면, AI가 말소기준권리, 임차인 대항력, 인수되는 권리를 입체 분석하여 위험도 보고서를 자동 작성합니다.")
    st.markdown("---")
    
    uploaded_file = st.file_uploader("명세서 PDF 파일을 업로드하세요 (텍스트 레이어가 있는 PDF만 가능)", type=["pdf"])
    st.write(f"DEBUG: uploaded_file={uploaded_file}, exists={os.path.exists(r'c:\\AI-Agent\\auction\\매각물건명세서_샘플.pdf')}")
    
    if uploaded_file:
        if "sample_pdf_bytes" in st.session_state:
            del st.session_state.sample_pdf_bytes
            del st.session_state.sample_pdf_name
            
    if not uploaded_file:
        sample_path = r"c:\AI-Agent\auction\매각물건명세서_샘플.pdf"
        if os.path.exists(sample_path):
            st.markdown("💡 **실습용 파일이 없으시다면?**")
            if st.button("📄 샘플 매각물건명세서 불러오기 (매각물건명세서_샘플.pdf)", use_container_width=True):
                with open(sample_path, "rb") as f:
                    st.session_state.sample_pdf_bytes = f.read()
                    st.session_state.sample_pdf_name = "매각물건명세서_샘플.pdf"
                    st.rerun()
                    
    if "sample_pdf_bytes" in st.session_state and not uploaded_file:
        from io import BytesIO
        uploaded_file = BytesIO(st.session_state.sample_pdf_bytes)
        uploaded_file.name = st.session_state.sample_pdf_name
        uploaded_file.size = len(st.session_state.sample_pdf_bytes)
        if st.button("❌ 샘플 파일 닫기"):
            del st.session_state.sample_pdf_bytes
            del st.session_state.sample_pdf_name
            st.session_state.pdf_analysis_result = None
            st.session_state.pdf_chat_messages = []
            st.rerun()
            
    if uploaded_file:
        st.write(f"📂 파일명: `{uploaded_file.name}` ({uploaded_file.size / 1024:.1f} KB)")
        
        if st.button("🔍 명세서 권리분석 시작", use_container_width=True):
            st.session_state.active_agent = "tutor"
            with st.spinner("PDF 파일을 파싱하고 권리관계를 정밀 분석하는 중입니다..."):
                try:
                    import pdf_analyzer
                    file_bytes = uploaded_file.read()
                    pdf_text = pdf_analyzer.extract_text_from_pdf(file_bytes)
                    analysis_res = pdf_analyzer.analyze_property_pdf(pdf_text)
                    st.session_state.pdf_analysis_result = analysis_res
                    st.session_state.pdf_chat_messages = []  # Reset Q&A history
                    st.rerun()
                except Exception as e:
                    st.error(f"명세서 분석 도중 오류 발생: {e}")
                    
    if st.session_state.pdf_analysis_result:
        res = st.session_state.pdf_analysis_result
        st.markdown("---")
        st.markdown(f"#### 🏛️ 분석 결과: {res.get('case_number', '사건번호 미상')}")
        st.markdown(f"**📍 물건 주소:** {res.get('address', '주소 미상')}")
        
        col_val1, col_val2 = st.columns(2)
        col_val1.metric("감정평가액", res.get("appraisal_value", "미상"))
        col_val2.metric("최저매각가격", res.get("minimum_bid", "미상"))
        
        # Risk Rating Card
        risk_rating = res.get("risk_rating", "안전").strip()
        if "안전" in risk_rating:
            bg_color = "rgba(16, 185, 129, 0.08)"
            border_color = "#10B981"
            text_color = "#047857"
            rating_label = "🟢 안전 (인수되는 권리 없음, 안심 입찰 가능)"
        elif "주의" in risk_rating:
            bg_color = "rgba(245, 158, 11, 0.08)"
            border_color = "#F59E0B"
            text_color = "#B45309"
            rating_label = "🟡 주의 (일부 명도 리스크 또는 비고란 특이사항 존재)"
        else:
            bg_color = "rgba(239, 68, 68, 0.08)"
            border_color = "#EF4444"
            text_color = "#B91C1C"
            rating_label = "🔴 위험 (선순위 대항력 임차권 인수 리스크 또는 치명적 권리 존재)"
            
        st.markdown(f"""
        <div style="background-color: {bg_color}; border-left: 5px solid {border_color}; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem;">
            <h4 style="margin: 0 0 0.5rem 0; color: {border_color}; font-weight:700;">🛡️ CAO 종합 위험도 진단: {rating_label}</h4>
            <p style="margin: 0; font-size: 0.95rem; line-height: 1.6; color: {text_color};"><b>진단 요약:</b> {res.get('risk_summary', '-')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Malso Standard Right Info
        st.markdown("##### 🔑 말소기준권리 (최선순위 설정권리)")
        malso = res.get("malso_standard_right", {})
        st.info(f"📅 **설정일자:** {malso.get('date', '-')} | 🔖 **권리종류:** {malso.get('right_name', '-')} | 👥 **권리자:** {malso.get('holder', '-')}")
        
        # Tenants Table
        st.markdown("##### 👥 임차인 현황 및 대항력 분석 결과")
        tenants = res.get("tenants", [])
        if tenants:
            ten_data = []
            for t in tenants:
                ten_data.append({
                    "임차인명": t.get("name", "-"),
                    "보증금": t.get("deposit", "-"),
                    "전입신고일": t.get("move_in_date", "-"),
                    "확정일자": t.get("fixed_date", "-"),
                    "대항력 여부": t.get("opposing_power", "-"),
                    "낙찰자 인수여부": t.get("is_takeover", "-"),
                    "분석 상세 사유": t.get("reason", "-")
                })
            st.dataframe(pd.DataFrame(ten_data), use_container_width=True, hide_index=True)
        else:
            st.success("점유 중인 신고 임차인이 없습니다. (소유자 직접 점유 등)")
            
        # Takeover Rights and Notes
        col_right1, col_right2 = st.columns(2)
        with col_right1:
            st.markdown("##### 📜 낙찰자 인수 권리 (등기부상)")
            takeovers = res.get("takeover_rights", [])
            if takeovers:
                for tk in takeovers:
                    st.warning(f"📍 **{tk.get('right_name', '-')}**\n{tk.get('description', '-')}")
            else:
                st.success("매각으로 소멸하지 않는 등기부상 권리가 없습니다. (모든 권리 소멸)")
        with col_right2:
            st.markdown("##### ⚠️ 법원 비고란 특이사항")
            st.warning(res.get("special_notes", "기재된 특이사항 없음"))
            
        # PDF Q&A Chatbot
        st.markdown("---")
        st.markdown("#### 💬 강대호 CAO에게 추가 질문하기")
        st.write("위 권리분석 결과에 대해 궁금한 점(예: 배당 가능액, 유치권 깨는 법, 명도 방향 등)을 자유롭게 논의해보세요.")
        
        # PDF Chat History
        for p_msg in st.session_state.pdf_chat_messages:
            with st.chat_message(p_msg["role"]):
                st.write(p_msg["content"])
                
        # PDF Chat Input
        if pdf_query := st.chat_input("명세서 분석에 관한 질문을 입력하세요", key="pdf_chat_input"):
            st.session_state.pdf_chat_messages.append({"role": "user", "content": pdf_query})
            with st.chat_message("user"):
                st.write(pdf_query)
                
            with st.chat_message("assistant"):
                st.session_state.active_agent = "tutor"
                with st.spinner("답변을 작성 중입니다..."):
                    try:
                        import json
                        import providers
                        llm_qa = providers.get_llm(temperature=0.3)
                        pdf_context = json.dumps(res, ensure_ascii=False, indent=2)
                        
                        chat_history = []
                        for m in st.session_state.pdf_chat_messages[:-1]:
                            chat_history.append({"role": m["role"], "content": m["content"]})
                            
                        sys_prompt_qa = f"""당신은 AntiG 플랫폼의 경매분석최고책임자(CAO)인 강대호 박사입니다.
방금 업로드 및 분석한 매각물건명세서 결과를 바탕으로 학습자(사용자)의 질문에 성실히 답변하십시오.
친절하고 전문적인 구어체(~해요 체 등)로 이야기하며, 법률적 근거(민사집행법, 주택임대차보호법)를 알기 쉽게 설명하세요.

[분석된 물건 정보]
{pdf_context}
"""
                        messages_qa = [
                            {"role": "system", "content": sys_prompt_qa}
                        ]
                        for chat_msg in chat_history:
                            messages_qa.append(chat_msg)
                        messages_qa.append({"role": "user", "content": pdf_query})
                        
                        response_qa = llm_qa.invoke(messages_qa)
                        ans_text_qa = response_qa.content.strip()
                        st.write(ans_text_qa)
                        st.session_state.pdf_chat_messages.append({"role": "assistant", "content": ans_text_qa})
                        st.rerun()
                    except Exception as ex_qa:
                        st.error(f"대화 생성 오류: {ex_qa}")

else:
    # Chat Interface
    st.markdown("### 💬 에이전트 실시간 Q&A 대화창")
    st.write("부동산 경매 절차나 권리분석 이론에 대해 궁금한 점을 물어보세요. 질문 의도에 맞춰 최적의 전문 에이전트가 답변합니다.")
    
    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                # Render Badge
                route = msg.get("route", "tutor")
                badge_class = f"badge-{route}"
                route_names = {
                    "procedure": "절차 안내 에이전트",
                    "tutor": "권리분석 튜터 에이전트",
                    "quiz": "사례 퀴즈 에이전트"
                }
                st.markdown(f'<span class="badge {badge_class}">{route_names.get(route, "튜터")}</span>', unsafe_allow_html=True)
                st.write(msg["content"])
                
                # Render expander for citations if any
                citations = msg.get("citations", [])
                if citations:
                    with st.expander("📚 참고 자료 및 법령 출처"):
                        for c_idx, cite in enumerate(citations):
                            st.markdown(f"**[{c_idx+1}] {cite['display_name']}**")
                            st.caption(cite["content"].replace("\n", "  \n"))
            else:
                st.write(msg["content"])

    # Chat input
    if query := st.chat_input("질문을 입력해 주세요 (예: '배당요구 종기 기한이 지나면 어떻게 되나요?', '말소기준권리가 뭐야?')"):
        # Append user message
        st.session_state.messages.append({"role": "user", "content": query})
        
        with st.chat_message("user"):
            st.write(query)
            
        with st.chat_message("assistant"):
            if not db_ready:
                ans_text = "지식베이스가 구축되어 있지 않고 API 키가 설정되지 않아 답변을 드릴 수 없습니다. .env 파일 및 환경변수를 확인해주세요."
                st.write(ans_text)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ans_text,
                    "route": "tutor",
                    "citations": []
                })
            else:
                st.session_state.active_agent = "router"
                render_agent_monitor(monitor_placeholder)
                with st.spinner("전문 에이전트가 문서를 탐색하여 답변을 생성 중입니다..."):
                    try:
                        result = orchestrator.handle_query(query)
                        st.session_state.active_agent = result["route"]
                        render_agent_monitor(monitor_placeholder)
                        
                        # Handle quiz activation route
                        if result["route"] == "quiz":
                            st.session_state.quiz_graded = False
                            st.session_state.grade_results = None
                            st.session_state.pending_tab_change = "📝 실전 권리분석 퀴즈"
                            st.rerun()
                        
                        # Render badge
                        route = result["route"]
                        badge_class = f"badge-{route}"
                        route_names = {
                            "procedure": "절차 안내 에이전트",
                            "tutor": "권리분석 튜터 에이전트"
                        }
                        st.markdown(f'<span class="badge {badge_class}">{route_names.get(route, "튜터")}</span>', unsafe_allow_html=True)
                        st.write(result["answer"])
                        
                        # Render citations
                        citations = result.get("citations", [])
                        if citations:
                            with st.expander("📚 참고 자료 및 법령 출처"):
                                for c_idx, cite in enumerate(citations):
                                    st.markdown(f"**[{c_idx+1}] {cite['display_name']}**")
                                    st.caption(cite["content"].replace("\n", "  \n"))
                                    
                        # Append assistant message to history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result["answer"],
                            "route": route,
                            "citations": citations
                        })
                    except Exception as e:
                        err_text = f"답변을 처리하는 도중 오류가 발생했습니다: {e}"
                        st.error(err_text)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": err_text,
                            "route": "tutor",
                            "citations": []
                        })
