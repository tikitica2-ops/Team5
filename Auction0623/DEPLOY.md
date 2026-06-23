# Streamlit Cloud 배포 가이드

본 프로젝트는 파이썬 기반 웹 애플리케이션으로, **Streamlit Cloud**를 통해 무료로 간편하게 호스팅할 수 있습니다. 아래 가이드에 따라 배포를 완료해 보세요.

---

## 1. 깃허브(GitHub) 저장소 설정 및 업로드

로컬 프로젝트 코드를 깃허브 원격 저장소에 업로드합니다.

1. **깃허브 저장소(Repository) 생성**
   - GitHub 사이트에서 새로운 public 또는 private 저장소를 생성합니다. (예: `auction-edu-rag`)

2. **깃허브에 코드 푸시(Push)**
   - 로컬 터미널에서 다음 명령어를 실행하여 코드를 올립니다:
     ```bash
     git init
     git add .
     git commit -m "Initial commit for auction edu rag agent"
     git branch -M main
     git remote add origin https://github.com/사용자이름/저장소이름.git
     git push -u origin main
     ```
   *주의: `.gitignore` 설정에 의해 `.env` 파일과 `chroma_db/` 디렉터리는 커밋에서 제외되므로 API Key가 공개 노출되지 않습니다.*

---

## 2. Streamlit Cloud 연결 및 배포 설정

1. **Streamlit Share 접속 및 로그인**
   - [Streamlit Cloud](https://share.streamlit.io/)에 접속하여 GitHub 계정으로 로그인합니다.

2. **새 앱 배포 (Deploy an app)**
   - 우측 상단의 **'New app'** 버튼을 클릭합니다.
   - 아래 항목들을 지정합니다:
     - **Repository**: 방금 푸시한 GitHub 저장소 선택 (`사용자이름/저장소이름`)
     - **Branch**: `main`
     - **Main file path**: `app.py`

---

## 3. 비밀 환경변수(Secrets) 등록 (★필수)

API Key를 주입하기 위해 Streamlit 앱 배포 화면 우측 하단의 **'Advanced settings...'** 또는 대시보드 앱 설정의 **'Secrets'** 메뉴에 접속합니다.

아래와 같이 TOML 형태로 API Key를 입력하고 저장합니다:

```toml
OPENAI_API_KEY = "sk-proj-yourOpenAiKey..."
# Anthropic 모델을 활성화하려면 아래 키도 등록하세요 (선택사항)
# ANTHROPIC_API_KEY = "sk-ant-..."
```

---

## 4. 첫 가동 및 자동 지식베이스 적재

- 설정 완료 후 **'Deploy!'** 버튼을 누르면 빌드가 진행됩니다.
- 배포 완료 후 브라우저창에 앱이 켜지면, 최초 1회 자동으로 `ingest.py` 스크립트가 기동되어 `data/` 내부의 법령, 절차, 용어, 사례 텍스트를 청킹하여 로컬 ChromaDB에 보존합니다.
- 빌드가 완료되면 대화창과 사이드바 퀴즈 시스템이 즉시 정상 작동합니다.

---

## 5. 트러블슈팅

* **임베딩/API 인증 에러**:
  - Streamlit Secrets에 `OPENAI_API_KEY`가 오타 없이 정확히 큰따옴표 안에 기입되었는지 점검하세요.
* **ChromaDB C++ 컴파일 빌드 오류**:
  - `requirements.txt`에 명시된 `chromadb` 라이브러리는 Streamlit Cloud 환경(Linux 기반)에서 추가 도구 없이 정상적으로 설치됩니다.
* **업데이트 반영**:
  - 로컬에서 코드를 수정하고 GitHub에 `git push`하면 Streamlit Cloud가 이를 실시간 감지하여 수초 내에 앱을 자동 재빌드하여 배포합니다.
