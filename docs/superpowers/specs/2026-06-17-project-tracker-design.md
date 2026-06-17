# project-tracker 설계 (진척률 관리)

작성일: 2026-06-17
대상: Jarvis 개인 비서 시스템 (`C:\Users\Samsung\Jarvis`)

## 목적

인표님의 모든 프로젝트(개인·회사) 진척률을 한곳에서 관리한다.
- 단일 작업 공간: **`C:\project`** (앞으로 모든 프로젝트는 여기서 진행)
- 진척률 = 마일스톤 완료 비율(자동) + 수동 % 보정(D 방식)
- 신규 프로젝트는 폴더만 만들면 마일스톤이 자동 등록되어, 반복 수작업이 없다

## 진척률 정의 (D: 혼합)

```
progress = override_pct  (수동 보정값이 있으면 우선)
         = round(완료 마일스톤 수 / 전체 마일스톤 수 × 100)  (없으면 자동)
```

## 데이터 모델 (Markdown SSOT)

진척률 원본은 **프로젝트별 Markdown 파일**: `C:\project\<폴더>\PROJECT.md`
사람이 직접 읽고 편집할 수 있는 단일 소스(SSOT). 스크립트는 이 파일을 파싱/갱신한다.

```markdown
---
name: 유랑고
type: personal          # personal | work
override_pct:           # 비우면 자동계산, 0~100 숫자면 수동 보정
status: active          # active | pending(신규,추출대기) | archived
updated: 2026-06-17
---

# 유랑고  ·  진척률 33% (자동)

## 마일스톤
- [x] 기획
- [ ] 개발
- [ ] 배포

## 메모
-
```

- **식별 키 = 폴더명**(`C:\project\<폴더>`). frontmatter `name`은 표시용 한글명.
- **진척률** = `override_pct` 있으면 그 값, 없으면 `[x] 개수 / 전체 ×100`.
- `# 제목` 줄의 "진척률 NN%"는 스크립트가 갱신할 때 다시 써주는 **표시용**(파싱 기준 아님).
- 파싱 기준은 frontmatter + `## 마일스톤` 아래 `- [ ]`/`- [x]` 체크박스.
- 중앙 인덱스 파일은 두지 않는다. `project_tracker --list`가 모든 `PROJECT.md`를 모아 표를 생성(원하면 `C:\project\_DASHBOARD.md`로 출력 가능).

## 컴포넌트

### 1. `scripts/project_scan.py` — 폴더 동기화 (토큰 0)
- `C:\project` 하위 1단계 폴더를 훑어 `PROJECT.md` 존재 여부 확인
- 빌드/캐시/백업 폴더 제외 (아래 제외 규칙)
- `PROJECT.md` 없는 폴더 → **pending `PROJECT.md` 자동 생성**
  (frontmatter `status: pending`, `name`=폴더명, 마일스톤 비움)
- LLM 호출 없음. 순수 파일시스템 스캔.
- `--report` : 이번 스캔에서 새로 만든 pending 목록을 출력(모닝 브리핑/Jarvis가 후속 추출에 사용)

### 2. `scripts/project_extract.py` — 마일스톤 추출 후보 수집 (토큰 절약)
LLM이 마일스톤을 만들기 위한 **최소 입력**을 준비하는 헬퍼. 추출 판단은 LLM(Jarvis)이 한다.
- **1차 (토큰 0)**: 폴더 트리(2~3 depth) + 파일명 목록 + 프로젝트 유형 판별
  (`package.json`/`src` 있으면 code, 아니면 docs) 을 텍스트로 반환
- **2차 (선별 발췌)**: 우선순위 문서를 최대 1~2개 골라 앞부분만 발췌 반환
  - 우선순위: `README.md` > `CLAUDE.md` > 파일명에 `기획|계획|plan|proposal|정의서|요건` > 최근 mtime 보고서 1개
  - 발췌 상한: 문서당 약 2000자
  - 지원: md/txt(직접), docx/xlsx/pdf(텍스트 추출), **hwp는 미지원 → 파일명만 활용**
- 출력은 stdout 텍스트. Jarvis가 이를 읽고 마일스톤 JSON을 구성해 `--apply`로 기록.

### 3. `scripts/project_tracker.py` — 조회/편집 CLI
- `--list` : 전체 진척률 표 (개인/회사 구분, % 바, pending 표시)
- `--show "<이름|폴더>"` : 마일스톤 상세 + 남은 일
- `--done "<프로젝트>" "<마일스톤>"` : 완료 체크
- `--undone "<프로젝트>" "<마일스톤>"` : 체크 해제
- `--set "<프로젝트>" <0-100>` : override_pct 보정 (null로 되돌리려면 `auto`)
- `--add "<프로젝트>" "<마일스톤>"` / `--remove "<프로젝트>" "<마일스톤>"`
- `--note "<프로젝트>" "<메모>"`
- `--apply "<프로젝트>" <json파일|->` : 추출 결과(마일스톤 배열 JSON)를 해당 `PROJECT.md`에 일괄 등록, status→active
- 모든 한글 출력은 UTF-8 (`PYTHONIOENCODING=utf-8`)
- 편집 명령은 대상 `PROJECT.md`를 다시 써서 `updated`와 제목의 진척률 표시를 갱신
- 프로젝트 지정은 `name`(한글명) 또는 폴더명 둘 다 허용

### 4. 모닝 브리핑 통합 (`morning_briefing.py`)
- 시작 시 `project_scan.py` 실행 → 신규 폴더 동기화
- `status: pending`이 있으면 브리핑에 "🆕 새 프로젝트 N개 감지 — 마일스톤 추출 대기" 표시
- 🚀 개인 / 💼 회사 섹션을 "최근 변경"에서 **"진척률 % + 최근 활동"** 으로 업그레이드
  - 진척률: project_tracker 데이터
  - 최근 활동: 기존 work-status(파일변경) / github-monitor(커밋) 를 보조 신호로 유지

### 5. 신규 자동 마일스톤 (반복 작업 제거)
- `project_scan.py`는 매일 모닝 브리핑에서 자동 실행 → 신규를 pending 등록
- pending 처리(마일스톤 추출)는 LLM이 필요하므로:
  - 모닝 브리핑이 pending을 알림 → **메인 세션 Jarvis가 그날 자동으로 `project_extract`→`--apply`** 수행 후 인표님께 결과 보고
  - (선택) 전용 경량 cron 에이전트로 무인 처리 — 구현 계획에서 결정
- 결과적으로 인표님은 `C:\project`에 폴더만 만들면 마일스톤이 자동 등록된다

## 부트스트랩 (1회, 토큰 절약 모드)

1. `project_scan.py`로 기존 17개 폴더 등록 (전부 pending)
2. 활성/우선순위 높은 것부터 배치로 `project_extract` → 마일스톤 초안 → `--apply`
   - 1차(파일명/구조)만으로 충분하면 문서 읽기 생략
   - 배치 크기는 토큰 상황에 맞춰 조절 (한 번에 전부 X)
3. 인표님이 `--list`로 검토 → 마일스톤 보정 / `--set`으로 % 조정

## 제외 규칙

스캔에서 제외할 폴더/경로:
`.git`, `node_modules`, `.gradle`, `.claude`, `.pytest_cache`, `dist`, `build`,
`_*_backup_*`, `repo_temp`, `.next`, `.expo`, `.vercel`

## 범위 밖 (YAGNI)

- 간트차트/타임라인 시각화 (텍스트 % 바로 충분)
- 외부 도구(Notion 등) 동기화
- 마일스톤 마감일/담당자 (필요해지면 추가)
- hwp 본문 파싱 (파일명만 활용)

## 성공 기준

- `project_tracker.py --list`로 모든 프로젝트 진척률이 한눈에 보인다
- `C:\project`에 새 폴더 생성 → 다음 모닝 브리핑에서 자동 감지·마일스톤 초안 등록
- 마일스톤 완료를 말 한마디로 체크 → 진척률 갱신
- 부트스트랩/일상 운영 모두 토큰 과소비 없이 동작
