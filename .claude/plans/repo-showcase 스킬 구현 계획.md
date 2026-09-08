# 계획: `repo-showcase` — 오픈소스 레포의 첫인상을 근거로 만드는 스킬

## Context

성진의 GitHub 계정(`tjdwls101010`)에는 공개 레포 25개가 있고 대부분 별 0~4개, 17개는 description이 비어 있고 19개는 topics가 없다. Harness-Creator, Codex-in-Claude, Ultra-Search처럼 실제 쓸모 있는 도구가 그 안에 있다. 문제는 "가치 있는 프로젝트가 방문자에게 그 가치를 첫 화면에서 전달하지 못한다"는 것이고, 이 레포(`Skills for README`)는 그걸 고치는 Claude Code 스킬의 소스 레포다. 스킬은 여기서 만들고, 이후 `~/.claude/skills/repo-showcase`로 심링크/복사해 다른 프로젝트에서 쓴다.

한 문장 목표: **GitHub 방문자가 첫 화면에서 "이게 뭔지, 나한테 맞는지, 어떻게 써보는지"를 근거 있게 판단할 수 있도록, 소유자 인터뷰와 코퍼스 실측에 기반해 README·GitHub 메타데이터·소개 재료 파일(`LAUNCH-KIT.md`: 한 줄 정의·두 문장 피치·데모 GIF 경로·Show HN 제목 후보·제출 후보 목록)를 만들어 주는 자립형 스킬 `repo-showcase`를 만든다.**

## 확정된 결정 (성진, 2026-09-08)

| 결정 | 내용 | 파급 |
|---|---|---|
| 범위 | GitHub 첫인상 전환 + GitHub 안의 매력 신호(Releases, social preview, 프로필 README·핀, 스킬 마켓플레이스 제출 조건) + 소개 재료 파일(`LAUNCH-KIT.md`: 한 줄 정의·두 문장 피치·데모 GIF 경로·Show HN 제목 후보·제출 후보 목록) 파일. **범위 밖**(두 차례 재확인): 커뮤니티·SNS 채널 안내와 게시 자동화, 스타게이저 이메일 등 타겟 연락(GitHub 약관·정보통신망법·GDPR 위반 소지, 평판 역효과). 재개 조건: 성진이 채널 가이드를 요청하면 `references/launch.md`로 추가(근거는 이미 수집된 opensource.guide Finding Users·Show HN 가이드라인) | 스킬은 게시하지 않고 게시물 재료까지만 만든다 |
| 가중치 구조 | **채택을 막는 결손**(LICENSE 없음·표기 불일치, 전제조건·권한·비용 미표기, 외부인이 재현 못 하는 시작 경로, README 내부 모순) 먼저, 그다음 **설득력 개선**(한 줄 정의, 결과 증거, description, 데모) | audit 출력이 두 묶음 |
| 배포 | 이 레포에서 만들고 `~/.claude/skills/repo-showcase`로 심링크/복사 | 자립. `.tmp/`·`research/`를 가리키지 않음. `gh` 로그인 전제. `allowed-tools`는 절대경로 관례 |
| 완결성 | **다른 스킬에 의존하지 않는다.** 런타임 의존은 `gh` CLI, Python 3 표준 라이브러리, 선택적 `vhs`뿐. ultra-search·codex·harness-creator·tdd·claude-in-chrome은 개발·검증 단계에서만 쓰고 SKILL.md·references·scripts는 이들을 호출하거나 언급하지 않는다. 필요한 지식(코퍼스 결론, 인터뷰 로스터, 템플릿 원문)은 스킬 디렉터리 안에 담는다 | 3단계 완료 판정에 의존성 grep 추가 |
| README 언어 | 영어 기본, 한국어는 요청 시 `README.ko.md` + 언어 링크 | 한 줄 분기 |
| 소유자 인터뷰 | `AskUserQuestion`으로 소유자만 아는 사실·약속·셀링 포인트를 정한 뒤 작성. 한 줄 정의는 후보 3개 중 선택 | 로스터는 SKILL.md 본문(매 호출 필요) |
| 이름 | `repo-showcase` | 확정 |
| 테스트 | `tdd` 스킬, `./tests/` (pytest) | 순수 함수 seam |
| 코덱스 | `.codex → .claude` 심링크, E2E는 코덱스 실행 | 0단계 |
| 프레임 | `principle over rail`, `interface over document`, `for user not developer`, `dense information` | 아래 절 |
| E2E 대상 | Ultra-Search(빈 상태) + Harness-Creator(description 있음), 홀드아웃 Agentic-X | 격리 클론, 원격 쓰기 차단 |
| 스크립트의 역할 | 산문을 쓰지 않는다. (a) 자기 채점 방지 측정 (b) 추측하면 틀리는 사실 조회 (c) 부작용 안전장치 (d) 손으로 하면 틀리는 고정 절차(라이선스·CoC 원문, vhs). 템플릿으로 README를 찍는 스크립트는 만들지 않는다 | `propose_metadata.py` 제거, `gh repo edit` 한 줄로 대체 |

## 근거 장부

### Fact — 코퍼스 실측 (2026-09-08, 스크래치패드 수집, 0단계에서 `.tmp/`로 이동)

가이드 25편, README 73개(5계층), 고전 도구 12개의 생성 3·9개월 README 24개.

| 계층 | n | 줄수 | 단어 | 배지 | 첫 이미지 줄 | 설치 헤딩 줄 | 첫 40줄 데모 | 한 줄 설명 위치/길이 | description | LICENSE | SECURITY | CoC | CONTRIB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mega | 8 | 125 | 533 | 6 | 4 | 31 | 7/8 | 12 / 69자 | 61자 | 8/8 | 5/8 | 4/8 | 8/8 |
| classic_solo 현재 | 20 | 460 | 1736 | 7 | 3 | 74 | 17/20 | 6 / 65자 | 49자 | 20/20 | 8/20 | 7/20 | 15/20 |
| **classic_solo 3개월** | 12 | **203** | **738** | 1 | 5 | **34** | **9/12** | 4 / 61자 | — | — | — | — | — |
| classic_solo 9개월 | 12 | 291 | 1416 | 4 | 5 | 46 | 11/12 | 6 / 48자 | — | — | — | — | — |
| trendshift 상승 | 21 | 408 | 2168 | 8 | 3 | 64 | 13/21 | 6 / 76자 | 87자 | 19/21 | 10/21 | 6/21 | 14/21 |
| **low_traction** | 20 | 221 | **1862** | **0** | 없음 16/20 | 64 | **3/20** | 2 / **81자** | **127자** | 17/20 | 7/20 | 4/20 | 9/20 |
| owner(성진) | 4 | 173 | 1488 | 1 | 2 | 43 | 3/4 | 4 / 109자 | 92자 | 3/4 | 3/4 | 3/4 | 3/4 |

읽어낸 것:
- **0-스타 레포의 모델은 "지금의 bat"이 아니라 "3개월째의 bat"이다.** 200줄, 설치 34번째 줄, 첫 화면 데모 9/12. 현재의 460줄·74번째 줄은 인지도 이후의 형태.
- 저관심을 가르는 가장 뚜렷한 변수는 **첫 화면의 결과 증거(3/20 vs 9/12·17/20)** 와 **한 줄 설명·description 길이(81자·127자 vs 61자·49자)**. "왜/Features" 섹션 유무(10/20)와 설치 위치는 가르지 못한다.
- 초기 고전의 한 줄 설명은 방문자가 아는 작업·대안에 연결한다: "A cat(1) clone with syntax highlighting", "a simple, fast alternative to find", "A faster way to navigate your filesystem".
- 배지 필수 아님(인기 24개 중 8개가 0, jq 0개·35k). SECURITY는 인기 레포도 절반 이하. CoC는 1인 프로젝트에 대부분 없음.
- awesome-readme 140개 추천 사유: badge 62, logo 56, demo 42, feature 41. 큐레이터 어휘이지 효과 증거 아님. Tools 절의 `vhs`/`terminalizer`/`asciinema`는 데모 GIF 인터페이스로 채택.
- 지표 스크립트 버그(코덱스 발견): 한국어 헤딩("설치") 누락, Mermaid 펜스를 코드로 셈 → 2단계 수정.

### Fact — 환경
- `.tmp/` gitignored. `gh` 로그인됨. Codex CLI 0.153.4, `~/.codex/skills`에 스킬 심링크 존재.
- ultra-search `search` 회당 ~50k 토큰(성진 구독), `fetch` 무료. README 원문은 `gh api`가 더 싸고 정확.
- trendshift.io 첫 페이지에서 상승 레포 21개 추출 가능.

### 코덱스 비판 레인 (계획 초안) — 채택
결손/개선 분리 · 세 질문의 관찰 가능한 답 · 로고/배지와 결과 이미지 구분 · 상승 이전 README와 저관심 비교군 · 구조 지표에 합격점 금지 · A/B 순서 무작위·라벨 숨김 · 합격 = 핵심 결손 개선 + 비퇴행 · 홀드아웃 1개 · audit 3상태(`present/absent/lookup_failed`) · SECURITY 다중 경로 · scaffold 덮어쓰기 금지 · E2E 원격 쓰기 차단 · 선정표·SHA·집계는 커밋. "첫 화면 픽셀 확인"은 E2E 스크린샷으로만 부분 채택.

### 코덱스 코퍼스 종합 레인 (recall) — 내 목록에 없던 것, 채택
1. 설치 완료가 아니라 **첫 성공(예상 출력)까지의 경로**(llm m3: 설치→키→질문→출력).
2. **필수/선택 전제조건 분리**, 도입을 막는 조건(관리자 권한·계정)은 첫 화면에.
3. **비교는 조건과 손해까지**(fd m3 벤치마크는 조건과 "`find -iname`이면 비슷하다"를 포함). 인용 수치를 제품 성능처럼 쓰지 않는다.
4. **분기는 프로젝트 유형이 아니라 진입 경로**: 온라인 체험 / CLI 설치 / import 라이브러리 / 호스트 플러그인(Claude Code 스킬·MCP) / 관리자 설정형 통합. Excalidraw는 앱이자 라이브러리라 유형 템플릿은 중복.
5. **현재 상태·지원 범위가 홍보보다 먼저**(rye). README 내부 모순(예정 기능을 예제로)은 판단을 멈춘다 → 검증의 주장-근거 대응표.
6. **라이선스 감지값·배지·문장·파일 일치 확인**(jq NOASSERTION vs 본문; vibe-toolkit 본문 MIT vs 파일 없음).
7. 인터뷰 8문항(목적/첫 설득 대상/없애려던 반복 작업/책임질 차이/보증 가능한 첫 체험 경로/지원 의무/받을 기여/권리 확보) → SKILL.md 로스터의 골격. 여기에 "약속하지 않을 것", "요구 권한·비용·계정", "가장 가까운 대안 레포(`--compare` 입력)" 3문항 추가.
8. 가이드 통념 중 코퍼스가 뒷받침하지 않는 것(Standard README 120자·TOC 필수·고정 순서, "짧기보다 긴 편", RDD, 커뮤니티 파일이 성장을 만든다) → `first-visit.md`의 "따르지 않는 규칙".
잔여 불확실성: 별 수는 노출·명성·시간의 혼합값, 전환 데이터 없음. 도출된 것은 "문서상 판단 가능성"의 원칙이지 인과 법칙이 아니다. SKILL.md에 한 줄로 명시.

### ultra-search 탐색 3건 — 완료 (a·b는 도구가 최종 답의 요약부만 저장, 출처 343·652건 보존)
- (a) 실증 연구: 스타/인기 관련 증거는 대규모지만 **거의 전부 상관**. MSR 종단 연구는 **인기가 문서 작업을 부른다**(역인과). 기여자 모집에는 README 포괄성·이슈/PR 템플릿의 전향적 근거. 첫 실행 성공에는 "명시적·완전한 설정 명령"의 근거. A/B 없음. → 스킬의 한계 문장과 "결손 먼저" 구조의 근거.
- (b) 발견 레버: 전통적 레포 프레젠테이션이 여전히 일반 발견을 지배. Agent Skills는 별도 마켓플레이스 형성. llms.txt는 사용성 보조이지 유입 채널 아님. description 잘림 기준은 미확인 → 1단계에서 GitHub 목록 화면을 직접 측정.
- (c) 에이전트 스킬·프롬프트 레포 관행(prompts.chat, awesome-claude-skills, awesome-agent-skills): 호환 호스트를 첫 문장 옆 산문으로 즉시 명시, 항목마다 "설치 후 에이전트가 할 수 있는 것", 설치 경로 호환표, 제3자 스킬 보안 고지, 데모 트랜스크립트는 없음. → `trial-paths.md` 호스트 플러그인 경로.

## 최종 디렉터리 구조

```
Skills for README/                          ← 스킬 소스 + 연구 기록
├── .claude/
│   └── skills/
│       └── repo-showcase/                  ← 자립형. 이 디렉터리만 심링크/복사하면 동작
│           ├── SKILL.md                    ← description(트리거·near-miss), 방문자 읽기 모델, 결손/개선 원칙, 소유자 인터뷰 로스터(AskUserQuestion 옵션 모양), 8단계 절차, 경계(원격 쓰기·범위 밖·한계). ~150줄
│           ├── references/                 ← 진짜 분기만 분리
│           │   ├── first-visit.md          ← README를 쓰는 호출만. 세 질문의 관찰 가능한 답, 초기 고전 vs 저관심 대비 사례(줄 번호·숫자), 따르지 않는 통념, 데모 GIF(`vhs`)
│           │   ├── trial-paths.md          ← 진입 경로별 시작 경로 5절(온라인 체험 / CLI 설치 / import 라이브러리 / 호스트 플러그인 / 관리자 설정형 통합). 호출당 한 절만 읽음. 120줄 넘으면 절별 파일로 분할
│           │   └── beyond-readme.md        ← 메타데이터·커뮤니티·신호 호출만. description/topics/homepage(`gh repo edit` 한 줄), social preview, Releases, 프로필 README·핀 레포, LICENSE 선택·일치, CONTRIBUTING·SECURITY·CoC 조건, 스킬 마켓플레이스·awesome 목록 제출 조건, 소개 재료 파일(`LAUNCH-KIT.md`: 한 줄 정의·두 문장 피치·데모 GIF 경로·Show HN 제목 후보·제출 후보 목록) 구성
│           └── scripts/
│               ├── audit_repo.py           ← CLI. `audit_repo.py <owner/repo | path> [--json] [--offline]`
│               ├── scaffold_community.py   ← CLI. `--file {license,contributing,code_of_conduct,security} --license {mit,apache-2.0,gpl-3.0,bsd-3-clause} --out DIR`. 기존 파일 있으면 비제로 종료
│               ├── similar_repos.py        ← CLI. `--query "..." [--topic T]... [--limit N] [--json]`. gh search로 유사 프로젝트 후보 표. 인터뷰에서 성진이 1~3개 선택
│               └── showcase/               ← 기능 단위 모듈. 파일 하나 = 기능 하나, 순수 함수 우선
│                   ├── __init__.py
│                   ├── github.py           ← gh api 래퍼. 3상태. SECURITY는 루트·.github·docs. 로컬 경로 입력 시 --offline
│                   ├── similar.py          ← 검색어 조합(한 줄 정의 키워드 + topics), gh search 결과 정규화, "Similar projects/Alternatives" 절 유무 탐지, 후보 정렬
│                   ├── readme_metrics.py   ← README 텍스트 → 구조 지표. 다국어 헤딩, Mermaid 제외, 로고·배지 vs 결과 이미지 구분
│                   ├── first_screen.py     ← 한 줄 정의(위치·길이·대안 언급), 결과 증거 유형(GIF/스크린샷/출력 블록/온라인 데모 링크), 시작 경로(전제조건·명령·예상 결과)
│                   ├── blockers.py         ← 결손 판정: LICENSE 존재·표기 일치, 전제조건·권한·비용, 재현 가능한 시작 경로(사설 IP·로컬 절대경로 감지), 상태 공지
│                   ├── report.py           ← 사람용/JSON. 판정마다 근거 줄 번호. 합격점 없음
│                   └── templates/          ← LICENSE 4종, Contributor Covenant 2.1, SECURITY, CONTRIBUTING 골격
├── .codex -> .claude                       ← 심링크
├── tests/                                  ← tdd. pytest
│   ├── fixtures/                           ← 성진 소유 README 4개 + 합성 README(초기 고전 패턴·저관심 패턴) + gh 응답 JSON
│   ├── test_readme_metrics.py
│   ├── test_first_screen.py
│   ├── test_blockers.py
│   ├── test_github.py                      ← gh mock, 3상태
│   ├── test_similar.py                     ← 검색어 조합, 결과 정규화, Similar-projects 절 탐지 (gh search mock)
│   └── test_scaffold.py                    ← 덮어쓰기 거부, 라이선스 선택 필수
├── research/                               ← 커밋되는 재현 자료
│   ├── corpus-manifest.json                ← 레포·계층·SHA·수집일·선정/제외 기준
│   ├── metrics-summary.md                  ← 실측 표 + 산출 명령
│   ├── codex-reviews.md                    ← 비판·종합·판정 레인 결과와 채택/기각
│   └── decisions.md                        ← 결정 기록(handoff): 범위 밖과 그 이유 포함
├── .tmp/                                   ← 원문 코퍼스 (gitignored): guides/, readmes/, readmes_early/, ultra-search 결과
├── README.md                               ← 이 레포 자체를 스킬로 작성(dogfood)
└── .gitignore                              ← `.codex-runs/`, `.ultra-search/` 추가
```

## CLI 계약 (구현은 이 표를 `--help`로 옮긴다. 산문 복사 금지)

### `audit_repo.py`
```
audit_repo.py TARGET [--compare OWNER/REPO] [--json] [--offline] [--readme PATH]
```
| 인자 | 의미 | 기본값 |
|---|---|---|
| `TARGET` | `owner/repo`(gh api 조회) 또는 로컬 경로(README·LICENSE·커뮤니티 파일을 파일시스템에서 읽음) | 필수 |
| `--compare OWNER/REPO` | 유사 프로젝트의 description·topics·한 줄 정의를 함께 조회해 어휘 정렬 제안에 씀 | 없음 |
| `--json` | 사람용 보고 대신 JSON(아래 스키마) | 사람용 |
| `--offline` | gh 호출 없이 로컬 파일만. 원격 메타데이터 항목은 `lookup_failed`로 표기 | 끔 |
| `--readme PATH` | README 파일을 직접 지정(E2E에서 before/after 비교용) | 자동 탐지 |

출력(JSON 스키마의 뼈대):
```
{ "target": ..., "fetched": ISO날짜,
  "blockers": [ {"id": "license_missing" | "license_mismatch" | "prereq_unstated" | "start_path_unreproducible" | "status_contradiction", "state": "present"|"absent"|"lookup_failed"|"undetermined", "evidence": [{"line": N, "text": "..."}], "note": "..."} ],
  "persuasion": [ {"id": "one_liner" | "result_evidence" | "start_path" | "description" | "topics" | "homepage" | "social_preview" | "releases", "state": ..., "value": ..., "evidence": [...]} ],
  "metrics": { "lines", "words", "badges", "first_result_image_line", "first_code_line", "install_heading_line", "one_liner_line", "one_liner_len", "evidence_types": ["gif"|"screenshot"|"output_block"|"online_demo"] },
  "compare": { "repo": ..., "description": ..., "topics": [...], "shared_topics": [...], "missing_topics": [...] } | null }
```
종료 코드: 0 실행 성공(결손 유무와 무관) · 2 인자 오류 · 3 대상 접근 실패(gh 미로그인, 경로 없음). **합격/불합격 점수는 내지 않는다.**

### `scaffold_community.py`
```
scaffold_community.py --file {license,contributing,code_of_conduct,security} [--license {mit,apache-2.0,gpl-3.0,bsd-3-clause}] [--holder NAME] [--year YYYY] [--contact EMAIL_OR_URL] [--out DIR] [--force]
```
| 인자 | 의미 | 기본값 |
|---|---|---|
| `--file` | 만들 파일. 반복 가능 | 필수 |
| `--license` | `--file license`일 때 필수. 원문은 `templates/`에서 글자 그대로 | 없음(없으면 종료 2) |
| `--holder`, `--year` | LICENSE 저작권 표기 | `git config user.name`, 올해 |
| `--contact` | CoC·SECURITY의 신고 연락처. 없으면 자리표시자를 넣고 경고 | 없음 |
| `--out DIR` | 출력 디렉터리 | `.` |
| `--force` | 기존 파일 덮어쓰기 허용 | 끔. 기존 파일이 있으면 종료 4, 아무것도 쓰지 않음 |

종료 코드: 0 생성 · 2 인자 오류 · 4 기존 파일 존재(`--force` 없음).

### `similar_repos.py`
```
similar_repos.py --query "..." [--topic T ...] [--language L] [--limit N] [--exclude OWNER/REPO] [--json]
```
| 인자 | 의미 | 기본값 |
|---|---|---|
| `--query` | 검색어. 한 줄 정의 후보의 핵심 명사·동사(스킬이 조합) | 필수 |
| `--topic` | GitHub topic 필터. 반복 가능. 대상 레포의 topics나 코드에서 뽑은 것 | 없음 |
| `--language` | 주 언어 필터 | 없음 |
| `--limit` | 후보 수 | 10 |
| `--exclude` | 결과에서 뺄 레포(대상 자신) | 없음 |
| `--json` | JSON 출력 | 사람용 표 |

출력 항목(후보마다): `repo`, `stars`, `description`, `topics`, `pushed_at`, `license`, `has_similar_section`(README에 "Similar projects/Alternatives/Comparison/Related" 헤딩 유무와 줄 번호), `homepage`. 정렬: 스타 내림차순, 단 1년 이상 미갱신은 뒤로. 종료 코드: 0 · 2 인자 오류 · 3 gh 접근 실패 · 5 결과 없음.

사용처(SKILL.md에 명시): 선택된 유사 레포는 (1) topics·description 어휘 정렬(`audit_repo.py --compare`), (2) README 비교표(조건·손해 포함), (3) 한 줄 정의의 앵커, (4) 소개 재료 파일(`LAUNCH-KIT.md`: 한 줄 정의·두 문장 피치·데모 GIF 경로·Show HN 제목 후보·제출 후보 목록)의 "Similar projects" PR 후보에 쓰인다. 스타게이저·기여자 개인 정보는 조회하지 않는다.

### 스킬이 직접 쓰는 외부 인터페이스 (래핑하지 않음)
- `gh repo edit OWNER/REPO --description "..." --add-topic a,b,c --homepage URL` — 메타데이터 적용. 사용자 승인 후.
- `gh api repos/OWNER/REPO/community/profile` — audit 내부에서 사용.
- `vhs demo.tape` — 데모 GIF. 테이프 파일은 스킬이 작성, 실행은 vhs 설치 시.

## 프레임 반영 (harness-creator)

- **principle over rail**: 필수 섹션 템플릿과 줄수 임계값을 주지 않는다. 방문자의 세 질문과 관찰 가능한 답을 원칙으로 적고, 초기 bat·fd·llm과 저관심 CCC·mcp-re의 첫 화면을 줄 번호와 함께 대비한다. "설치를 200줄 뒤에 둔 fzf"가 인지도 이후의 형태임을 명시. 따르지 않는 통념 목록.
- **interface over document**: 체크리스트 대신 `audit_repo.py`가 근거 줄 번호와 함께 판정. description/topics는 `gh repo edit`. 데모 GIF는 `vhs`. 커뮤니티 파일은 `scaffold_community.py`. 본문은 플래그를 복사하지 않고 `--help`로 보낸다. 인터뷰 로스터는 `AskUserQuestion` 옵션 모양 그대로.
- **for user not developer**: README 독자는 방문자. 메인테이너가 자랑하고 싶은 것(아키텍처·기술 스택·개발 이력)이 아니라 방문자의 결정에 필요한 것 순으로. 스킬의 사용자는 성진(Claude 경유)이고 SKILL.md는 그 세션이 판단해야 할 것만 담는다.
- **dense information**: 코퍼스 결론은 references에 사례·숫자로. 원문은 `.tmp/`, 재현 자료는 `research/`, 스킬은 둘 다 가리키지 않는다.
- **progressive disclosure**: 분리 기준은 분량이 아니라 분기. 매 호출 읽히는 인터뷰 로스터는 본문에, README 작성 호출만 읽는 `first-visit.md`, 경로 하나만 읽는 `trial-paths.md`, 메타데이터·신호 호출만 읽는 `beyond-readme.md`로 나눈다.

## SKILL.md 절차

0. **대상·경계**: 대상(경로 또는 owner/repo). 원격 쓰기(`gh repo edit`, push)는 성진이 승인한 단계에서만. 범위 밖과 한계(전환 데이터 없음, 인기가 문서를 부르는 역인과) 명시.
1. **audit**: `audit_repo.py` → 결손 / 개선 두 묶음. 코드·README·메타데이터로 알 수 있는 건 여기서 끝.
2. **진입 경로 판정**: `trial-paths.md`의 해당 절만.
3. **유사 프로젝트 탐색**: `similar_repos.py`로 후보 표 → 인터뷰에서 성진이 1~3개 선택(또는 직접 지정). 선택된 레포는 `audit_repo.py --compare`로 재조회.
4. **소유자 인터뷰**(본문 로스터, 한 번에 한 결정): audit·탐색으로 답이 나온 것은 묻지 않는다.
5. **한 줄 정의 후보 3개** → 선택. 방문자가 아는 작업·유사 레포에 연결, 60자 안팎.
6. **README 작성/개선**(`first-visit.md`): 첫 화면 = 한 줄 정의 + 결과 증거 + 전제조건·최소 명령·예상 결과 + 현재 상태. 유사 레포 비교표는 조건·손해 포함. 기존 사실 보존, 확인 안 된 주장 제거. 한국어 요청 시 `README.ko.md`.
7. **메타데이터·커뮤니티 파일·신호**(`beyond-readme.md`): 유사 레포 topics와 정렬한 `gh repo edit` 명령 제시 → 승인 후 실행. LICENSE 없으면 인터뷰 답으로 scaffold. CONTRIBUTING/SECURITY/CoC는 조건 충족 시. Releases·social preview·프로필 핀은 제안.
8. **소개 재료 파일 `LAUNCH-KIT.md`**: 밖에 알릴 때 그대로 복사해 쓸 글감. 한 줄 정의, 두 문장 피치(누구의 어떤 반복 작업을 무엇으로 바꾸는지·대안과의 차이), 데모 GIF 경로, Show HN 형식 제목 후보 2~3개, 해당되면 스킬 마켓플레이스·awesome 목록 제출 조건, 유사 프로젝트의 "Similar projects" 절에 추가를 제안할 PR 후보(인터뷰의 "가장 가까운 대안" 답과 `--compare` 결과에서). 추적하지 않는 파일임을 안내. 게시·PR은 성진이. 스타게이저 이메일 등 비공개 채널 연락은 만들지 않는다(약관·법·평판).
9. **재audit·검증**: 설치 명령 실제 실행, 링크 확인, 주장-근거 대응표, 라이선스 표기 일치. 구조 지표는 비퇴행 확인용.

## 실행 단계와 완료 판정

### 0단계. 준비
완료: `ln -s .claude .codex`, `.gitignore`에 `.codex-runs/`·`.ultra-search/`, 스크래치패드 코퍼스를 `.tmp/`로 이동, `research/corpus-manifest.json`, 브랜치 `feat/repo-showcase`, `TaskCreate` 트래커에 단계별 완료 판정 등록.

### 1단계. 코퍼스 종합 마무리
완료: `research/codex-reviews.md`, `metrics-summary.md` 작성. description 잘림 기준을 GitHub 목록 화면(claude-in-chrome)에서 직접 측정해 확정.

### 2단계. 스크립트 (tdd)
완료: `tests/` red → green. `audit_repo.py`를 코퍼스 73개 + 초기 24개에 돌려 실측 표 재현(버그 2개 수정 반영). `scaffold_community.py` 기존 파일 시 비제로 종료. 모든 인자 `help=`, 닫힌 집합 `choices=`. `--help`만으로 사용법이 드러남.

### 3단계. SKILL.md·references
완료: `validate_harness.py` 통과. description에 의도 트리거(영/한: "README 써줘", "레포 소개 좋게", "깃허브 매력", "스타 늘리고 싶어", "write a README", "make my repo presentable")와 near-miss(docstring·코드 주석, 문서 사이트 구축, API 레퍼런스, 블로그·홍보 글 작성, 커뮤니티 게시). 본문에 `.tmp/`·`research/` 참조 없음, 플래그 복사 없음. `grep -rn -E "ultra-search|codex|harness-creator|tdd|claude-in-chrome|\.tmp/|research/" .claude/skills/repo-showcase/`가 0건. 스킬 디렉터리만 임시 위치로 복사해 `python3 scripts/audit_repo.py --help`와 `--offline` 실행이 그대로 되는지 확인(자립 검증). 코덱스 precision 레인: "이 스킬로 처음 README를 쓰는 세션" 관점으로 읽고 재도출 불가한 규칙·중복·누락 지적 → 반영.

### 4단계. E2E (코덱스 실행, 격리 클론, 원격 쓰기 차단)
완료:
- Ultra-Search·Harness-Creator를 격리 클론에서 코덱스가 `/repo-showcase`로 처리. 인터뷰 답은 성진이 제공.
- 홀드아웃 Agentic-X는 최종 검증에만.
- 블라인드 판정: 별도 코덱스 스레드에 루브릭 없이 before/after를 순서 무작위·라벨 없이 제시, "처음 온 방문자" 역할로 세 질문에 답하고 근거 문구·알 수 없는 사항 제출. 합격 = 핵심 결손 개선 + 기존 정확성·사용성 비퇴행.
- claude-in-chrome으로 격리 클론 README 렌더 스크린샷(1280px) 확인.
- 트리거 검증: 의도 요청 6개, near-miss 4개.
- 실제 레포 적용은 성진이 별도 결정.

### 5단계. 기록·머지
완료: `research/decisions.md`(범위 밖 결정과 이유 포함). 이 레포 README를 스킬로 작성(dogfood). PR `feat: 오픈소스 첫인상 스킬 repo-showcase 추가`, `## 검증`에 4단계 수치. squash merge.

## 미해결 / 유보

| 항목 | 소유자 | 결정 시점 | 영향 |
|---|---|---|---|
| description 잘림 기준 | 나 | 1단계 | 직접 측정값으로 확정 |
| 인기 README를 fixtures로 복사할지 | 나 | 2단계 | 성진 소유 + 합성 픽스처로 회피 |
| `trial-paths.md` 절별 파일 분할 | 나 | 3단계 | 120줄 초과 시 분할 |
| ultra-search (a)(b) 전문 | 나 | 필요 시 | `resume`로 재요청 가능(회당 ~50k 토큰). 현재 요약으로 충분 |
