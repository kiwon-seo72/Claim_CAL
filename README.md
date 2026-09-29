# Claim_CAL

Streamlit 케이스 관리, PostgreSQL 문서 저장, PDF 텍스트/이미지 OpenAI 사실 추출 시제품입니다.

## Railway 배포

1. GitHub 저장소를 Railway 서비스로 연결하고 PostgreSQL 서비스를 추가합니다.
2. 앱 서비스 Variables에서 `DATABASE_URL=${{Postgres.DATABASE_URL}}`(실제 DB 서비스 이름에 맞게 변경), `CLAIM_USERS_JSON`, `CLAIM_LEGACY_OWNER`, `OPENAI_API_KEY`를 설정합니다. 선택적으로 `OPENAI_MODEL=gpt-4.1-mini`를 설정할 수 있습니다.
3. Start Command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`.
4. 배포 후 각자 사용자명과 비밀번호로 로그인하여 케이스를 만들고 문서를 저장합니다.

### 세 명 테스트 계정

`CLAIM_USERS_JSON`은 정확히 세 계정의 JSON 배열입니다. Railway Variables에 **한 줄**로 입력하세요. 아래 값은 형식 예시이므로 실제로는 서로 다른 12자 이상의 임의 비밀번호를 사용하세요.

```json
[{"username":"adjuster1","password":"REPLACE_WITH_RANDOM_SECRET_1"},{"username":"adjuster2","password":"REPLACE_WITH_RANDOM_SECRET_2"},{"username":"adjuster3","password":"REPLACE_WITH_RANDOM_SECRET_3"}]
```

`CLAIM_LEGACY_OWNER=adjuster1`처럼 **기존 사건과 문서를 맡을 계정**을 명시하세요. 업그레이드 시 소유자가 없는 기존 사건만 그 계정에 배정됩니다. 다른 두 계정에서는 기존 자료가 보이지 않습니다. 배포 전에 PostgreSQL을 백업하고, 두 변수를 **같이 설정한 뒤** 새 버전을 배포하세요. `APP_PASSWORD`는 이 버전에서 사용하지 않습니다. 계정을 삭제하려면 JSON의 계정을 교체하고 다시 배포하세요. 계정명이 빠지면 로그인이 비활성화되지만 그 계정의 자료는 DB에 보존됩니다. 사용자명 변경은 신규 계정으로 취급하므로 기존 사건 담당자를 옮길 때는 DB 마이그레이션이 필요합니다.

기존 SQLite의 케이스는 자동 이전되지 않습니다. 백업 후 별도 마이그레이션이 필요합니다. 파일 원본은 PostgreSQL BYTEA에 저장되며 10MB 제한입니다. PDF는 처음 30쪽의 추출 가능한 텍스트를 최대 4만 자 분석합니다. 스캔 PDF는 이미지로 변환한 뒤 업로드하세요. AI는 문서의 사실을 추출하며 보험금 지급 판정을 자동 확정하지 않습니다.

계정별 사건과 문서 접근 제한을 적용한 **3명 테스트 시제품**입니다. 실고객 자료 운영 전에는 로그인 시도 제한, 감사 기록, 암호화 및 보존/삭제 정책을 추가하고 보안 점검을 진행하세요.
