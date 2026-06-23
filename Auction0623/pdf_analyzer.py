import io
import json
from typing import Dict, Any
from pypdf import PdfReader
from langchain_core.messages import SystemMessage, HumanMessage
import providers

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from PDF bytes.
    """
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        text = ""
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"--- Page {idx + 1} ---\n{page_text}\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return ""

def analyze_property_pdf(pdf_text: str) -> Dict[str, Any]:
    """
    Analyzes the extracted PDF text using LLM and returns a structured JSON result.
    """
    if not pdf_text.strip():
        return {
            "case_number": "분석 불가",
            "address": "PDF 파일에서 텍스트 레이어를 찾을 수 없습니다. 이미지 전용 스캔본이거나 암호화된 파일일 수 있습니다.",
            "appraisal_value": "미상",
            "minimum_bid": "미상",
            "malso_standard_right": {
                "date": "확인 불가",
                "right_name": "확인 불가",
                "holder": "확인 불가"
            },
            "tenants": [],
            "takeover_rights": [
                {
                    "right_name": "추출 오류",
                    "description": "추출된 텍스트 내용이 비어 있어 분석을 진행할 수 없습니다."
                }
            ],
            "risk_rating": "위험",
            "risk_summary": "텍스트를 감지할 수 없는 PDF 파일입니다. 다른 파일로 시도해 주세요.",
            "special_notes": "스캔본 PDF의 경우 광학 문자 인식(OCR)을 거친 파일만 인식 가능합니다."
        }

    llm = providers.get_llm(temperature=0.0)

    system_prompt = """당신은 AntiG 플랫폼의 경매분석최고책임자(CAO)인 강대호 박사입니다.
법원 매각물건명세서(또는 등기부등본 및 임차인 정보가 섞인 경매 서류 텍스트)를 정밀 분석하여 입찰자가 인수해야 하는 위험 요소가 있는지 분석하는 것이 임무입니다.

사용자가 제공한 경매 서류 텍스트를 읽고, 아래의 권리분석 규칙에 따라 분석을 수행한 뒤 **오직 순수 JSON 포맷**으로만 응답해야 합니다.

[분석 규칙]
1. **사건 정보 및 소재지**: 사건번호(예: 2025타경104)와 대략적인 소재지 주소를 텍스트에서 찾아내세요. 감정평가액과 최저매각가격이 나와 있다면 추출하고, 없다면 "미상"으로 기재하세요.
2. **말소기준권리(최선순위 설정권리)**: 등기부 또는 명세서 상에 기재된 근저당, 가압류, 압류, 담보가등기, 경매개시결정 중 가장 설정 날짜가 빠른 권리를 찾으세요. 날짜와 권리명, 권리자를 기재하십시오.
3. **임차인 대항력 및 낙찰자 인수 판단**: 
   - 각 임차인에 대해, 전입신고일과 말소기준권리 설정일을 대조합니다.
   - 전입신고일이 말소기준권리 설정일보다 **빠르면 대항력 있음**, **늦으면 대항력 없음**입니다. (전입신고일과 설정일이 같은 날이면 전입효력은 다음날 0시에 발생하므로 대항력이 없습니다.)
   - 대항력이 있는 임차인이 보증금을 전액 배당받지 못하거나 배당요구를 하지 않은 경우, 낙찰자가 보증금을 **인수**해야 합니다. 대항력이 없으면 **소멸**입니다.
   - 대항력 판단 이유와 낙찰자 인수 금액을 구체적으로 `reason` 항목에 적어주세요.
4. **등기부상 인수 권리**: 소유권이전등기청구권보전가등기, 선순위 가처분, 지상권, 말소기준권리보다 빠른 전세권 등 낙찰자가 추가로 인수해야 하거나 지워지지 않는 등기상 제한이 있다면 `takeover_rights` 목록에 추가하세요. 없으면 빈 목록으로 두세요.
5. **종합 위험 등급**: 
   - **안전**: 인수할 보증금이 전혀 없고 등기부상 모든 권리가 소멸하며 특이사항이 없는 경우.
   - **주의**: 대항력 없는 임차인이 있어 명도가 필요하거나, 인수 금액이 소액 발생할 여지가 있는 경우, 혹은 유치권 신고가 있으나 성립 가능성이 매우 희박한 경우.
   - **위험**: 대항력 있는 선순위 임차인이 보증금을 인수해야 하거나, 선순위 가등기/가처분이 존재해 소유권을 잃을 리스크가 있는 경우, 유치권/법정지상권 성립 가능성이 높은 경우.
6. **비고란 특이사항**: 유치권 신고, 법정지상권, 분묘기지권, 농지취득자격증명 필요 여부 등 법원 비고란에 적힌 주요 행정적/법률적 경고를 찾아내어 요약하세요.

결과는 반드시 아래의 JSON 포맷 스키마를 준수하여 출력해야 하며, markdown 코드 블록(예: ```json 등)이나 어떠한 부가 텍스트도 포함해서는 안 됩니다:
{
  "case_number": "사건번호",
  "address": "소재지 주소",
  "appraisal_value": "감정평가액 (예: 500,000,000원)",
  "minimum_bid": "최저매각가격 (예: 400,000,000원)",
  "malso_standard_right": {
    "date": "말소기준권리일 (예: 2024-05-12)",
    "right_name": "권리종류 (예: 근저당)",
    "holder": "권리자 (예: 신한은행)"
  },
  "tenants": [
    {
      "name": "임차인명",
      "deposit": "보증금 (예: 250,000,000원)",
      "move_in_date": "전입신고일 (예: 2024-02-15)",
      "fixed_date": "확정일자 (예: 2024-02-15)",
      "opposing_power": "대항력 여부 (대항력 있음 / 대항력 없음 / 미상)",
      "is_takeover": "낙찰자 인수 여부 (인수 / 소멸)",
      "reason": "대항력 및 인수 판단의 구체적인 이유"
    }
  ],
  "takeover_rights": [
    {
      "right_name": "인수 권리명",
      "description": "상세 부담 내역"
    }
  ],
  "risk_rating": "안전 / 주의 / 위험",
  "risk_summary": "종합 위험 평가 및 입찰 팁 요약",
  "special_notes": "비고란 특이사항 요약"
}
"""

    human_content = f"다음은 분석할 경매 서류 텍스트입니다:\n\n{pdf_text}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_content)
    ]

    try:
        response = llm.invoke(messages)
        result_text = response.content.strip()

        # Clean markdown formatting if present
        if result_text.startswith("```json"):
            result_text = result_text.split("```json", 1)[1]
        if result_text.endswith("```"):
            result_text = result_text.rsplit("```", 1)[0]
        result_text = result_text.strip()

        parsed = json.loads(result_text)
        return parsed
    except Exception as e:
        print(f"Error in PDF analysis LLM call: {e}")
        # Return fallback parsing dictionary in case of error
        return {
            "case_number": "분석 오류 발생",
            "address": "서류 내용을 파싱하는 데 실패했습니다.",
            "appraisal_value": "미상",
            "minimum_bid": "미상",
            "malso_standard_right": {
                "date": "확인 불가",
                "right_name": "확인 불가",
                "holder": "확인 불가"
            },
            "tenants": [],
            "takeover_rights": [
                {
                    "right_name": "시스템 파싱 실패",
                    "description": f"AI 분석 호출 도중 오류가 발생했습니다: {str(e)}"
                }
            ],
            "risk_rating": "위험",
            "risk_summary": "서류 텍스트를 정상적으로 읽지 못해 정밀 분석에 실패했습니다. 수동으로 문서를 확인해 주세요.",
            "special_notes": "API Key 설정 혹은 입력 텍스트 과다 여부를 확인해 주십시오."
        }
