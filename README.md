# Claim_CAL

Streamlit 케이스 관리, PostgreSQL 문서 저장, PDF 텍스트/이미지 OpenAI 사실 추출 시제품입니다.

## Railway 배포

1. GitHub 저장소를 Railway 서비스로 연결하고 PostgreSQL 서비스를 추가합니다.
2. 앱 서비스 Variables에서 `DATABASE_URL=${{Postgres.DATABASE_URL}}`(실제 DB 서비스 이름에 맞게 변경), `APP_PASSWORD`(긴 임의 비밀번호), `OPENAI_API_KEY`를 설정합니다. 선택적으로 `OPENAI_MODEL=gpt-4.1-mini`를 설정할 수 있습니다.
3. Start Command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`.
4. 배포 후 비밀번호로 로그인하여 케이스를 만들고 문서를 저장합니다.

기존 SQLite의 케이스는 자동 이전되지 않습니다. 백업 후 별도 마이그레이션이 필요합니다. 파일 원본은 PostgreSQL BYTEA에 저장되며 10MB 제한입니다. PDF는 처음 30쪽의 추출 가능한 텍스트를 최대 4만 자 분석합니다. 스캔 PDF는 이미지로 변환한 뒤 업로드하세요. AI는 문서의 사실을 추출하며 보험금 지급 판정을 자동 확정하지 않습니다.

`APP_PASSWORD`는 시제품의 단일 공유 비밀번호입니다. 고객 실데이터를 여러 사람이 쓰는 운영 서비스에는 계정별 인증, 접근 권한, 감사 기록, 암호화 및 보존/삭제 정책을 먼저 구현하세요.
