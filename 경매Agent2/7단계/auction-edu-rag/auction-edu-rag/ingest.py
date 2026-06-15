"""
ingest.py

지식베이스(data/)를 읽어 clause-aware 청킹 후 ChromaDB 4개 컬렉션으로 구축한다.

  - laws        : 법령(.md) -> '## 제○○조' 단위로 분할
  - procedures  : 절차 해설(.md) -> '## 단계' 단위로 분할
  - glossary    : 용어집(.json) -> 용어 1개당 1청크
  - cases       : 가상 사례(.json) -> 사례 1건당 1청크 (정답 포함)

실행:
  python ingest.py            # 실제 임베딩 + DB 구축 (OPENAI_API_KEY 필요)
  python ingest.py --dry-run  # 청킹 결과만 확인 (키/네트워크 불필요)
"""

import argparse
import json
from pathlib import Path

import config


# ---------------------------------------------------------------------------
# 텍스트 처리 유틸
# ---------------------------------------------------------------------------
def split_long_text(text, size, overlap):
    """size를 넘는 텍스트만 줄(문단) 단위로 overlap을 두고 분할."""
    if len(text) <= size:
        return [text]
    lines = text.split("\n")
    chunks, cur = [], ""
    for line in lines:
        if cur and len(cur) + len(line) + 1 > size:
            chunks.append(cur.strip())
            cur = (cur[-overlap:] + "\n" + line) if overlap else line
        else:
            cur = (cur + "\n" + line) if cur else line
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def load_markdown_clauses(path, collection_key, doc_type):
    """'## ' 헤더 단위로 마크다운을 분할해 청크 리스트 반환."""
    raw = Path(path).read_text(encoding="utf-8")
    docs, current_title, buf = [], None, []

    def flush():
        if current_title and buf:
            body = "\n".join(buf).strip()
            if body:
                full = f"[{current_title}]\n{body}"
                for chunk in split_long_text(full, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
                    docs.append({
                        "text": chunk,
                        "metadata": {
                            "source": Path(path).name,
                            "section": current_title,
                            "collection": collection_key,
                            "type": doc_type,
                        },
                    })

    for line in raw.splitlines():
        if line.startswith("## "):
            flush()
            current_title, buf = line[3:].strip(), []
        elif line.startswith("# "):
            continue  # 문서 최상단 제목은 제외
        elif current_title is not None:
            buf.append(line)
    flush()
    return docs


def _won(n):
    """금액 포맷 (정수면 콤마 + '원')."""
    if isinstance(n, (int, float)) and n:
        return f"{int(n):,}원"
    return None


# ---------------------------------------------------------------------------
# 컬렉션별 문서 빌더
# ---------------------------------------------------------------------------
def build_law_docs():
    laws_dir = config.DATA_DIR / "laws"
    docs = []
    for md in sorted(laws_dir.glob("*.md")):
        docs += load_markdown_clauses(md, "laws", "law")
    return docs


def build_procedure_docs():
    proc_dir = config.DATA_DIR / "procedures"
    docs = []
    for md in sorted(proc_dir.glob("*.md")):
        docs += load_markdown_clauses(md, "procedures", "procedure")
    return docs


def build_glossary_docs():
    data = json.loads((config.DATA_DIR / "glossary" / "glossary.json").read_text(encoding="utf-8"))
    docs = []
    for t in data["terms"]:
        text = f"용어: {t['term']}\n정의: {t['definition']}"
        if t.get("related"):
            text += f"\n관련 용어: {', '.join(t['related'])}"
        docs.append({
            "text": text,
            "metadata": {
                "source": "glossary.json",
                "term": t["term"],
                "collection": "glossary",
                "type": "glossary",
            },
        })
    return docs


def build_case_docs():
    data = json.loads((config.DATA_DIR / "cases" / "sample_cases.json").read_text(encoding="utf-8"))
    docs = []
    for c in data["cases"]:
        p = c["property"]
        lines = [
            f"[사례 {c['id']}] ({c['difficulty']}) {c['title']}",
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
            lines.append(f"임차인: 없음" + (f" ({t.get('note')})" if t.get("note") else ""))

        for sr in c.get("special_rights", []):
            lines.append(
                f"특수권리: {sr['type']} / 주장자 {sr.get('claimant','')} / 사유 {sr.get('basis','')} / "
                f"{_won(sr.get('amount'))} / {sr.get('status','')}"
            )

        lines.append(f"배당요구종기: {c.get('distribution_deadline','-')}")

        a = c["analysis"]
        lines += [
            "[정답 권리분석]",
            f"- 말소기준권리: {a['extinction_baseline']}",
            f"- 임차인 대항력: {a['tenant_opposability']}",
            f"- 인수권리: {', '.join(a['assumed_rights']) if a['assumed_rights'] else '없음'}",
            f"- 말소권리: {', '.join(a['extinguished_rights'])}",
            f"- 예상 추가부담: {a['estimated_extra_burden']}",
            f"- 위험도: {a['risk_level']}",
            f"- 코멘트: {a['comment']}",
            f"- 결론: {a['conclusion']}",
        ]
        docs.append({
            "text": "\n".join(lines),
            "metadata": {
                "source": "sample_cases.json",
                "case_id": c["id"],
                "difficulty": c["difficulty"],
                "title": c["title"],
                "collection": "cases",
                "type": "case",
            },
        })
    return docs


COLLECTION_BUILDERS = {
    "laws": build_law_docs,
    "procedures": build_procedure_docs,
    "glossary": build_glossary_docs,
    "cases": build_case_docs,
}


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------
def ingest(dry_run=False):
    if not dry_run:
        import chromadb
        from langchain_chroma import Chroma
        from langchain_core.documents import Document
        from providers import get_embeddings

        embeddings = get_embeddings()
        client = chromadb.PersistentClient(path=config.CHROMA_DIR)

    total = 0
    for key, builder in COLLECTION_BUILDERS.items():
        docs = builder()
        coll = config.COLLECTIONS[key]
        total += len(docs)
        print(f"[{key:10s}] -> '{coll}': {len(docs)} chunks")

        if dry_run:
            sample = docs[0]["text"].splitlines()[0] if docs else "(없음)"
            print(f"             예시: {sample}")
            continue

        # 기존 컬렉션 초기화(재실행 시 중복 방지)
        try:
            client.delete_collection(coll)
        except Exception:
            pass

        documents = [Document(page_content=d["text"], metadata=d["metadata"]) for d in docs]
        Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            collection_name=coll,
            persist_directory=config.CHROMA_DIR,
        )

    print(f"\n총 {total} chunks "
          + ("(dry-run: DB 미생성)" if dry_run else f"-> ChromaDB 구축 완료: {config.CHROMA_DIR}"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="청킹 결과만 출력하고 임베딩/DB는 건너뜀 (키 불필요)")
    args = parser.parse_args()
    ingest(dry_run=args.dry_run)
