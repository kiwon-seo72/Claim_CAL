"""AI 손해사정 플랫폼 화면 시제품. 실행: streamlit run claim_platform_app.py"""

from __future__ import annotations

import csv
import io
import json
import sqlite3
from datetime import date, datetime
from html import escape
from pathlib import Path

import streamlit as st


st.set_page_config(page_title="보상 분석 | Case Workspace", page_icon="📋", layout="wide")
DB = Path(__file__).with_name("claim_cases.sqlite3")
DEFAULT_ROWS = [
    {"담보 항목": "골절진단비", "상태": "가능", "판정 사유": "진단서·영상 소견 확인 필요", "예상액(만원)": 300, "확정성": "예시"},
    {"담보 항목": "상해수술비", "상태": "가능", "판정 사유": "수술 기록 확인 필요", "예상액(만원)": 800, "확정성": "예시"},
    {"담보 항목": "후유장해", "상태": "검토", "판정 사유": "장해율·약관 지급조건 평가 필요", "예상액(만원)": 1500, "확정성": "가정"},
    {"담보 항목": "입원일당", "상태": "가능", "판정 사유": "10일 × 5만원 가정", "예상액(만원)": 50, "확정성": "예시"},
    {"담보 항목": "실손", "상태": "별도", "판정 사유": "원본 영수증·세부내역서 확인", "예상액(만원)": 0, "확정성": "미산정"},
]
PAGES = ["대시보드", "문서 업로드", "보장 분석", "예상 보험금", "진행 관리", "리포트"]


def connect():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS cases
        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
         injury TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
         rows_json TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '')""")
    con.commit()
    return con


def list_cases():
    with connect() as con:
        return con.execute("SELECT id, name, injury, status, created_at, rows_json, notes FROM cases ORDER BY id DESC").fetchall()


def create_case(name, injury):
    with connect() as con:
        cur = con.execute(
            "INSERT INTO cases(name,injury,status,created_at,rows_json,notes) VALUES(?,?,?,?,?,?)",
            (name, injury, "접수", datetime.now().strftime("%Y-%m-%d %H:%M"), json.dumps(DEFAULT_ROWS, ensure_ascii=False), ""),
        )
        con.commit()
        return cur.lastrowid


def save_case(case_id, *, rows=None, status=None, notes=None):
    with connect() as con:
        if rows is not None:
            con.execute("UPDATE cases SET rows_json=? WHERE id=?", (json.dumps(rows, ensure_ascii=False), case_id))
        if status is not None:
            con.execute("UPDATE cases SET status=? WHERE id=?", (status, case_id))
        if notes is not None:
            con.execute("UPDATE cases SET notes=? WHERE id=?", (notes, case_id))
        con.commit()


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
        if st.button(page_name, key=f"nav_{page_name}", use_container_width=True):
            st.session_state.page = page_name
            st.rerun()
    st.divider()
    st.caption("저장 위치: 이 앱과 같은 폴더의 claim_cases.sqlite3")

cases = list_cases()
if "case_id" not in st.session_state:
    st.session_state.case_id = cases[0][0] if cases else create_case("홍길동 (예시)", "상완 주관절 손상")
    cases = list_cases()
if "page" not in st.session_state:
    st.session_state.page = "대시보드"

st.markdown('<div class="hero"><div class="eyebrow" style="color:#9ac8ff">CASE WORKSPACE</div><h1>보험금을 찾아주는 시스템</h1><p>문서 접수 → 보장 분석 → 예상액 검토 → 진행 관리 → 리포트</p></div>', unsafe_allow_html=True)

select_col, new_col = st.columns([2, 1])
with select_col:
    ids = [x[0] for x in cases]
    current_id = st.session_state.case_id if st.session_state.case_id in ids else ids[0]
    labels = {x[0]: f"Case #{x[0]:04d}  |  {x[1]}  |  {x[2]}" for x in cases}
    picked = st.selectbox("케이스 선택", ids, index=ids.index(current_id), format_func=lambda x: labels[x])
    if picked != st.session_state.case_id:
        st.session_state.case_id = picked
        st.rerun()
with new_col:
    with st.popover("＋ 새 케이스"):
        with st.form("create_case_form"):
            new_name = st.text_input("고객명")
            new_injury = st.text_input("사고·상병")
            if st.form_submit_button("케이스 만들기"):
                if new_name.strip() and new_injury.strip():
                    st.session_state.case_id = create_case(new_name.strip(), new_injury.strip())
                    st.session_state.page = "대시보드"
                    st.rerun()
                else:
                    st.warning("고객명과 사고·상병을 입력하세요.")

case = next(x for x in cases if x[0] == st.session_state.case_id)
case_id, name, injury, status, created_at, rows_json, notes = case
rows = json.loads(rows_json)
possible = sum(1 for r in rows if r.get("상태") == "가능")
needs_review = sum(1 for r in rows if r.get("상태") == "검토")
estimate = sum(max(float(r.get("예상액(만원)") or 0), 0) for r in rows if r.get("상태") in ("가능", "검토"))
st.markdown(f'<div class="notice"><b>Case #{case_id:04d} | {escape(injury)}</b>　·　상태: {escape(status)}　·　접수: {escape(created_at)}<br>이 화면의 기본 보장 항목과 금액은 제안서 5쪽의 시연 예시입니다. 문서 업로드만으로 자동 판정되지는 않습니다.</div>', unsafe_allow_html=True)
page = st.session_state.page

if page == "대시보드":
    a, b, c, d = st.columns(4)
    for col, label, val in [(a,"지급 가능 표시",f"{possible}개"),(b,"예상 보험금 (가정 포함)",money(estimate)),(c,"추가 검토",f"{needs_review}건"),(d,"진행 상태",status)]:
        col.markdown(f'<div class="card"><div class="label">{escape(label)}</div><div class="value">{escape(val)}</div></div>', unsafe_allow_html=True)
    left, right = st.columns([2,1],gap="large")
    with left:
        st.subheader("보장 항목 요약")
        st.dataframe(rows, hide_index=True, use_container_width=True)
    with right:
        st.subheader("추천 확인 사항")
        st.info("① 후유장해: 전문의 소견과 장해율 자료 확인\n\n② 상해수술비: 수술 기록 확인\n\n③ 실손: 영수증과 세부내역서 수합")

elif page == "문서 업로드":
    st.subheader("문서 접수")
    st.write("보험증권, 약관, 진단서, 수술기록, 영수증을 첨부해 접수 현황을 확인합니다.")
    uploads = st.file_uploader("문서 선택", type=["pdf","png","jpg","jpeg"], accept_multiple_files=True, key=f"upload_{case_id}")
    if uploads:
        st.success(f"현재 브라우저 세션에 {len(uploads)}개 문서가 선택되어 있습니다.")
        st.dataframe([{"파일명": f.name, "크기(KB)": round(f.size/1024, 1)} for f in uploads], hide_index=True)
    st.caption("시제품은 파일을 서버에 보관하거나 OCR·약관 분석을 실행하지 않습니다. 다른 케이스를 열면 해당 케이스의 선택 상태만 표시됩니다.")

elif page == "보장 분석":
    st.subheader("담보별 검토표")
    st.write("상태와 예상액을 직접 수정하고 저장하면 케이스에 반영됩니다. '가능'도 지급 확정을 의미하지 않습니다.")
    edited = st.data_editor(rows, num_rows="dynamic", hide_index=True, use_container_width=True,
        column_config={"상태": st.column_config.SelectboxColumn("상태", options=["가능","검토","별도","제외"], required=True),
                       "예상액(만원)": st.column_config.NumberColumn("예상액(만원)", min_value=0, step=10),
                       "확정성": st.column_config.SelectboxColumn("확정성", options=["예시","가정","미산정","자료확인"], required=True)},
        key=f"editor_{case_id}")
    if st.button("검토표 저장", type="primary"):
        cleaned = [r for r in edited if (r.get("담보 항목") or "").strip()]
        save_case(case_id, rows=cleaned)
        st.success("검토표를 저장했습니다.")
        st.rerun()

elif page == "예상 보험금":
    st.subheader("예상액 구성")
    st.warning("아래 금액은 입력된 담보와 가정에 따른 합계입니다. 보험증권·약관·의료자료를 검토한 실제 지급 예상액이 아닙니다.")
    included = [r for r in rows if r.get("상태") in ("가능","검토")]
    st.dataframe(included, hide_index=True, use_container_width=True)
    st.metric("검토 대상 금액 합계", money(estimate))
    st.caption("제안서 5쪽의 기본 예시 2,650만원(300+800+1,500+50)을 표시합니다. 제안서 6쪽의 2,150만원은 장해율 10%와 후유장해 1,000만원을 둔 별도 가정입니다.")

elif page == "진행 관리":
    st.subheader("케이스 진행")
    with st.form(f"progress_{case_id}"):
        options = ["접수", "서류 보완", "분석 중", "고객 검토", "청구 진행", "종결"]
        new_status = st.selectbox("진행 상태", options, index=options.index(status) if status in options else 0)
        new_notes = st.text_area("담당자 메모 / 추가 서류", value=notes, height=180)
        if st.form_submit_button("진행 내용 저장", type="primary"):
            save_case(case_id, status=new_status, notes=new_notes)
            st.success("진행 내용을 저장했습니다.")
            st.rerun()

elif page == "리포트":
    st.subheader("케이스 리포트")
    st.write(f"**고객:** {name}　　**사고·상병:** {injury}　　**진행:** {status}")
    st.dataframe(rows, hide_index=True, use_container_width=True)
    st.write(f"**검토 대상 금액 합계:** {money(estimate)}")
    st.write(f"**담당자 메모:** {notes or '입력 없음'}")
    st.caption("예상액은 시연용 가정이며 실제 보험금 지급 여부와 금액은 약관 및 증빙 심사에 따릅니다.")
    st.download_button("CSV 리포트 다운로드", data=csv_report(case, rows).encode("utf-8"),
                       file_name=f"case_{case_id:04d}_report.csv", mime="text/csv")
