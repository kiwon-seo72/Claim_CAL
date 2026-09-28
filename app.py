"""AI 손해사정 플랫폼 화면 시제품. 실행: streamlit run app.py"""

from __future__ import annotations

import csv
import io
import json
import os
from datetime import date, datetime
from html import escape

import streamlit as st
from storage import initialize, list_cases, create_case, save_case, add_document, list_documents, get_document, save_analysis
from analysis import MAX_BYTES, extract_text, analyze_document


st.set_page_config(page_title="보상 분석 | Case Workspace", page_icon="📋", layout="wide")
PAGES = ["대시보드", "문서 업로드", "보장 분석", "예상 보험금", "진행 관리", "리포트"]


def require_access():
    password = os.getenv("APP_PASSWORD")
    if not password:
        st.error("APP_PASSWORD를 설정해야 문서와 케이스를 사용할 수 있습니다.")
        st.stop()
    if st.session_state.get("authorized"):
        return
    import hmac
    entered = st.text_input("접근 비밀번호", type="password")
    if st.button("로그인"):
        if hmac.compare_digest(entered, password):
            st.session_state.authorized = True
            st.rerun()
        st.error("비밀번호가 일치하지 않습니다.")
    st.stop()


require_access()

def money(value):
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        value = 0
    return f"{value:,.0f}만원"


def csv_report(case, rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["케이스번호", case[0], "고객명", case[1], "사고/상병", case[2]])
    writer.writerow(["상태", case[3], "작성일", date.today().isoformat()])
    writer.writerow(["담보 항목", "상태", "판정 사유", "예상액(만원)", "확정성"])
    for row in rows:
        writer.writerow([row.get(x, "") for x in ("담보 항목", "상태", "판정 사유", "예상액(만원)", "확정성")])
    writer.writerow(["안내", "예상액은 입력한 가정에 따른 예시이며 실제 지급액이 아닙니다."])
    return "\ufeff" + buffer.getvalue()


st.markdown("""
<style>
[data-testid="stAppViewContainer"] {background:#f4f7fc;color:#192949}
[data-testid="stHeader"] {background:#f4f7fc}
[data-testid="stSidebar"] {background:#142548}
[data-testid="stSidebar"] * {color:#e7eefb}
[data-testid="stSidebar"] button {border:0; background:#1d345e; width:100%;text-align:left}
[data-testid="stSidebar"] button:hover {background:#355482}
.block-container {padding-top:2rem; max-width:1480px}
.eyebrow {color:#3475bd;font-size:12px;font-weight:800;letter-spacing:.14em}
.hero {background:linear-gradient(110deg,#172d59,#204c88);color:white;padding:28px 32px;border-radius:16px;margin-bottom:20px}
.hero h1 {color:white;margin:.15em 0;font-size:31px}
.hero p {color:#cbdaf0;margin:0}
.card {background:#fff;border:1px solid #e2e9f3;border-radius:13px;padding:20px 22px;box-shadow:0 3px 15px #17375b0b;margin-bottom:14px;min-height:112px}
.card .label {font-size:13px;color:#667891;margin-bottom:11px}
.card .value {font-size:25px;font-weight:800;color:#193663}
.notice {background:#eaf2ff;border-left:4px solid #4c91e6;border-radius:5px;padding:12px 16px;margin:10px 0 18px;color:#274a78}
.brand {font-size:21px;font-weight:800;letter-spacing:-.03em;padding:15px 2px}
.subbrand {color:#a8c3e7;font-size:12px;margin-top:-8px;padding-left:2px;margin-bottom:22px}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brand">◈ CLAIM WORKSPACE</div><div class="subbrand">AI 손해사정 플랫폼 · 시제품</div>', unsafe_allow_html=True)
    for page_name in PAGES:
        if st.button(page_name, key=f"nav_{page_name}", width='stretch'):
            st.session_state.page = page_name
            st.rerun()
    st.divider()
    st.caption("저장 위치: PostgreSQL")

try:
    initialize()
    cases = list_cases()
    if "case_id" not in st.session_state:
        st.session_state.case_id = cases[0][0] if cases else None
    if "page" not in st.session_state:
        st.session_state.page = PAGES[0]
except Exception as exc:
    st.error(f"초기화 중 오류가 발생했습니다: {exc}")
    st.stop()
