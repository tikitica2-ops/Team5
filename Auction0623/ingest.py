import argparse
import json
import re
from pathlib import Path

import config
from langchain_core.documents import Document
import chromadb
import providers

def parse_laws_file(file_path: Path):
    """
    Parses a laws markdown file and splits it into clause-aware chunks.
    Splits by '## 제' headers.
    """
    if not file_path.exists():
        print(f"Warning: File {file_path} not found.")
        return []
    
    content = file_path.read_text(encoding="utf-8")
    
    # Split content by line starting with '## 제'
    # Use lookahead to keep the separator
    sections = re.split(r'(?m)^(?=## 제\d+조)', content)
    
    docs = []
    # The first section might be the file header (e.g., # 민사집행법 핵심 조문)
    header_text = ""
    if sections and not sections[0].startswith("## 제"):
        header_text = sections[0].strip()
        sections = sections[1:]
        
    for section in sections:
        section = section.strip()
        if not section:
            continue
        # Extract clause number (e.g., 제91조) for metadata
        match = re.search(r'## (제\d+조)', section)
        clause = match.group(1) if match else "기타"
        
        # Construct the page content
        text = f"{header_text}\n\n{section}" if header_text else section
        
        doc = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "clause": clause,
                "type": "law"
            }
        )
        docs.append(doc)
        
    return docs

def parse_procedures_file(file_path: Path):
    """
    Parses a procedure guide markdown file and splits by '##' headers.
    """
    if not file_path.exists():
        print(f"Warning: File {file_path} not found.")
        return []
        
    content = file_path.read_text(encoding="utf-8")
    sections = re.split(r'(?m)^(?=## )', content)
    
    docs = []
    header_text = ""
    if sections and not sections[0].startswith("## "):
        header_text = sections[0].strip()
        sections = sections[1:]
        
    for idx, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue
        
        # Get step title
        first_line = section.split("\n")[0]
        step_title = first_line.replace("##", "").strip()
        
        text = f"{header_text}\n\n{section}" if header_text else section
        
        doc = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "step": step_title,
                "step_index": idx + 1,
                "type": "procedure"
            }
        )
        docs.append(doc)
        
    return docs

def parse_glossary_file(file_path: Path):
    """
    Parses a glossary JSON file and returns a list of Documents.
    """
    if not file_path.exists():
        print(f"Warning: File {file_path} not found.")
        return []
        
    with open(file_path, "r", encoding="utf-8") as f:
        terms = json.load(f)
        
    docs = []
    for item in terms:
        term = item["term"]
        definition = item["definition"]
        
        text = f"용어: {term}\n정의: {definition}"
        doc = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "term": term,
                "type": "glossary"
            }
        )
        docs.append(doc)
        
    return docs

def parse_cases_file(file_path: Path):
    """
    Parses a cases JSON file and returns a list of Documents.
    """
    if not file_path.exists():
        print(f"Warning: File {file_path} not found.")
        return []
        
    with open(file_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    docs = []
    for case in cases:
        cid = case["id"]
        title = case["title"]
        difficulty = case["difficulty"]
        desc = case["description"]
        val = case["appraised_value"]
        min_bid = case["minimum_bid_price"]
        
        # Construct string for registry records
        registry_str = ""
        for r in case["registry_records"]:
            registry_str += f"- 번호 {r['no']}: {r['date']} | {r['right_name']} | 권리자 {r['holder']} | 금액 {r['amount']} ({r['status']})\n"
            
        # Construct string for tenant records
        tenant_str = ""
        for t in case["tenant_records"]:
            tenant_str += f"- 임차인 {t['name']}: 보증금 {t['deposit']} | 전입일 {t['move_in_date']} | 확정일자 {t['fixed_date']} | 점유범위 {t['share']} | 대항력 {t['opposing_power']}\n"
            
        notes_str = f"특이사항: {case['notes']}\n" if "notes" in case else ""
        
        analysis = case["analysis"]
        analysis_str = (
            f"[권리분석 정답]\n"
            f"- 말소기준권리: {analysis['malso_standard']}\n"
            f"- 대항력 여부: {analysis['opposing_power']}\n"
            f"- 인수 권리: {analysis['takeover_rights']}\n"
            f"- 최종 위험 평가: {analysis['risk_assessment']}\n"
        )
        
        text = (
          f"[가상 물건 사례 - {difficulty}]\n"
          f"제목: {title}\n"
          f"개요: {desc}\n"
          f"감정평가액: {val}\n"
          f"최저매각가격: {min_bid}\n"
          f"\n[등기부등본 현황]\n{registry_str}"
          f"\n[임차인 현황]\n{tenant_str}"
          f"\n{notes_str}"
          f"\n{analysis_str}"
        )
        
        doc = Document(
            page_content=text,
            metadata={
                "source": file_path.name,
                "case_id": cid,
                "difficulty": difficulty,
                "type": "case"
            }
        )
        docs.append(doc)
        
    return docs

def ingest_data(dry_run=False):
    """
    Reads all documents, chunks them, and uploads to ChromaDB collections.
    """
    # 1. Parse all files
    print("=== 데이터 파싱 시작 ===")
    
    # Laws
    law_docs = []
    for file_path in config.LAWS_DIR.glob("*.md"):
        law_docs.extend(parse_laws_file(file_path))
    print(f"법령 문서 청크 수: {len(law_docs)}")
    
    # Procedures
    procedure_docs = []
    for file_path in config.PROCEDURES_DIR.glob("*.md"):
        procedure_docs.extend(parse_procedures_file(file_path))
    print(f"절차 가이드 청크 수: {len(procedure_docs)}")
    
    # Glossary
    glossary_docs = parse_glossary_file(config.GLOSSARY_FILE)
    print(f"용어 사전 청크 수: {len(glossary_docs)}")
    
    # Cases
    case_docs = parse_cases_file(config.CASES_FILE)
    print(f"가상 사례 청크 수: {len(case_docs)}")
    
    total_chunks = len(law_docs) + len(procedure_docs) + len(glossary_docs) + len(case_docs)
    print(f"총 청크 수: {total_chunks}")
    print("=========================")
    
    if dry_run:
        print("\n[Dry Run] 데이터베이스 구축을 건너뜁니다.")
        if case_docs:
            print("\n--- 사례 청크 직렬화 예시 (Case 1) ---")
            print(case_docs[0].page_content[:400] + "...\n")
        return
        
    # 2. Setup Vector DB and upload
    print("\nChromaDB 컬렉션 구축 중...")
    
    # Connect to local ChromaDB
    db_client = chromadb.PersistentClient(path=str(config.CHROMA_DB_DIR))
    
    # Get embedding model
    embedding_model = providers.get_embedding_model()
    
    # Helper to clean and build collection
    def rebuild_collection(name, documents):
        if not documents:
            return
        print(f" 컬렉션 '{name}' 적재 중 ({len(documents)}개)...")
        # Try to delete existing collection to make ingestion idempotent
        try:
            db_client.delete_collection(name)
        except Exception:
            pass
            
        from langchain_community.vectorstores import Chroma
        Chroma.from_documents(
            documents=documents,
            embedding=embedding_model,
            persist_directory=str(config.CHROMA_DB_DIR),
            collection_name=name
        )
        
    rebuild_collection(config.COLLECTION_LAWS, law_docs)
    rebuild_collection(config.COLLECTION_PROCEDURES, procedure_docs)
    rebuild_collection(config.COLLECTION_GLOSSARY, glossary_docs)
    rebuild_collection(config.COLLECTION_CASES, case_docs)
    
    print("\nChromaDB 데이터 적재가 완료되었습니다!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="경매 RAG 지식베이스 구축 스크립트")
    parser.add_argument("--dry-run", action="store_true", help="실제 DB 빌드 없이 청킹 결과만 검증합니다.")
    args = parser.parse_args()
    
    ingest_data(dry_run=args.dry_run)
