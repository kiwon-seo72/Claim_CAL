"""Text extraction and evidence-oriented document review."""
import base64
import io
import json
import os
import re
import fitz
from openai import OpenAI

MAX_BYTES = 10 * 1024 * 1024
MAX_TEXT = 40000
IMAGE_MIMES = {'image/jpeg', 'image/png'}


def extract_text(content, mime_type):
    if mime_type != 'application/pdf':
        return ''
    with fitz.open(stream=content, filetype='pdf') as pdf:
        return '\n'.join(page.get_text() for page in list(pdf)[:30])[:MAX_TEXT]


def analyze_document(document):
    if not os.getenv('OPENAI_API_KEY'):
        raise RuntimeError('OPENAI_API_KEY가 설정되지 않았습니다.')
    mime = document['mime_type']
    contents = []
    if mime in IMAGE_MIMES:
        contents.append({'type':'input_image','image_url':f'data:{mime};base64,{base64.b64encode(bytes(document["content"])).decode()}'})
    elif mime == 'application/pdf':
        raw = document['extracted_text']
        if not raw.strip():
            raise ValueError('텍스트가 없는 스캔 PDF입니다. 현재는 이미지 파일로 올려 분석하세요.')
        contents.append({'type':'input_text','text':raw[:MAX_TEXT]})
    else:
        raise ValueError('지원하지 않는 문서 형식입니다.')
    contents.insert(0, {'type':'input_text','text':'''보험증권 또는 의료서류에서 확인 가능한 사실만 추출하세요. 추측한 담보, 진단, 금액을 만들지 마세요. 개인정보(성명, 주민번호, 주소)는 결과에 반복하지 마세요.
JSON 객체로만 응답하세요: {"document_type":"문서 종류", "facts":["근거가 있는 사실"], "coverages":[{"name":"확인된 담보명", "amount_manwon":null, "evidence":"원문 근거"}], "questions":["추가로 확인할 사항"]}. 금액을 알 수 없으면 null. 지급 가능 여부와 후유장해율을 확정하지 마세요.'''} )
    response = OpenAI().responses.create(model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'), input=[{'role':'user','content':contents}], text={'format':{'type':'json_object'}})
    data = json.loads(response.output_text)
    if not isinstance(data, dict): raise ValueError('분석 응답 형식이 올바르지 않습니다.')
    return data
