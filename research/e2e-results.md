# 4단계 E2E 결과 (2026-09-08)

검증 목표는 "보기 좋아졌다"가 아니라 **"근거 있는 판단과 첫 실행을 돕는가"**다. 합격 기준은 **핵심 결손 개선 + 기존 정확성·사용성 비퇴행**이다.

## 조건

- 대상: `tjdwls101010/Ultra-Search`(description·topics 비어 있음), `tjdwls101010/Harness-Creator`(메타데이터 갖춰짐). 홀드아웃 `Agentic-X`는 이번에 쓰지 않았다.
- **격리**: `/tmp/rs-e2e/`에 클론한 뒤 `origin`을 존재하지 않는 `file://` 경로로 바꿔 **원격 쓰기를 물리적으로 차단**했다. 프롬프트로도 `gh repo edit`·push·PR을 금지했다.
- 실행 주체: 스킬을 처음 받은 별도 세션(코덱스, `gpt-6-astra`). 인터뷰 답은 성진이 제공한 것을 프롬프트로 넣었다.
- 산출물은 격리 클론에만 남긴다(성진 결정). 실제 레포 적용은 별도 결정 사항이다.

## 결과 1 — 감사 지표의 개선과 비퇴행

`audit_repo.py`를 before/after 같은 조건으로 돌렸다.

| | Ultra-Search before | after | Harness-Creator before | after |
|---|---|---|---|---|
| `prereq_unstated` | `undetermined` (전제조건이 첫 명령 뒤) | **`absent`** | `absent` | `absent` |
| `start_path_unreproducible` | `undetermined` (`git clone <this repo>`) | **`absent`** | `absent` | `absent` |
| `result_evidence` | `absent` | **`present`** (output_block) | `present` (screenshot) | `present` (output_block) |
| 한 줄 정의 길이 | 121자 | **84자** | 57자 | 71자 |
| 줄수 | 60 | 92 | 261 | **153** |
| 설치 헤딩 줄 | 17 | **없음** ⚠️ | 44 | 39 |

**개선**: Ultra-Search의 결손 두 개가 해소됐고 결과 증거가 생겼다. Harness-Creator는 261줄에서 153줄로 줄면서 결과 증거를 검증되지 않은 포스터 이미지에서 **실제로 실행한 구조 검사 출력**으로 바꿨다.

**퇴행 1건 (⚠️)**: Ultra-Search after에는 설치 헤딩이 없다. 설치 절차를 굵은 글씨(`**Try one page:**`)로만 표시해 목차 앵커가 사라졌다. 코퍼스상 설치 헤딩의 *위치*는 저관심과 고전을 가르지 못하지만, 헤딩이 **아예 없는 것**은 다른 문제다.

## 결과 2 — 블라인드 판정

before/after를 **순서 무작위·라벨 숨김**으로 A/B에 배치하고(`prep_blind.py`), 루브릭 없이 별도 코덱스 스레드에 "오늘 처음 보는 방문자" 역할로 세 질문에 답하게 했다. 판정자에게는 두 파일만 주고 정답표(`KEY.json`)는 주지 않았다. 각 답에 **근거가 된 원문 문구를 인용**하고, 인용할 것이 없으면 "근거 없음"이라고 쓰게 했다.

| 대상 | 배치 | 판정자가 고른 쪽 | 정답 |
|---|---|---|---|
| Ultra-Search | A=after, B=before | **A** | after |
| Harness-Creator | A=before, B=after | **B** | after |

**2/2 모두 after를 골랐다.** 이유는 인상이 아니라 항목이었다.

> "A를 선택하는 이유는 **실행 전에 거절할 조건과 실행 후 성공을 확인할 조건이 모두 있기 때문**이다." (Ultra-Search)

> "B는 적합한 사람뿐 아니라 **도입하지 말아야 할 사람도 더 빨리 판단하게 한다.** 이것이 선택 이유다." (Harness-Creator)

**판정자가 지적한 after의 손실도 그대로 기록한다** — 이쪽이 이 판정의 값이다.

- Harness-Creator after는 대안 비교 범위가 좁아졌다(before의 "Static template"·"Component collection" 비교가 사라짐).
- after는 `sync`(과거 결정과 디스크 상태를 맞추는 모드)를 분명히 드러내지 않는다.
- before의 "Scenarios that write **run against** an isolated project copy"가 after에서 "**should use**"로 약해져 보장처럼 읽히던 것이 권고가 됐다.
- after는 첫 실행에서 막혔을 때 갈 곳(Troubleshooting·FAQ 링크)이 줄었다.

## 결과 3 — 트리거 검증

스킬이 설치된 프로젝트에 헤드리스 세션 10개를 각각 띄워 실제 호출 여부를 봤다.

| 종류 | n | `repo-showcase` 호출 |
|---|---|---|
| 의도 요청 ("이 레포 README 좀 제대로 써줘", "사람들이 이 프로젝트를 안 써", "make this repo presentable", "write a README for this project", "내 깃허브 프로젝트가 매력이 없어 보이는데", "오픈소스로 공개하려는데 뭘 준비해야 하지") | 6 | **6/6** |
| near-miss (docstring 붙이기, mkdocs 문서 사이트, 소개 블로그 글, API 레퍼런스 문서) | 4 | **0/4** |

## E2E가 실제로 찾아낸 스킬·스크립트 결함 4건

이것이 E2E의 주된 수확이다. 넷 다 테스트를 먼저 쓰고 고쳤다.

1. **` ```text `를 코드 블록에서 제외한 것.** Mermaid와 함께 묶었는데, `text`는 명령과 출력을 보여 주는 가장 흔한 표기다. E2E가 만든 README의 **실제 검증 출력이 통째로 "결과 증거 없음"으로 판정**됐다. 제외 대상을 `mermaid`·`math`·`latex`로 좁혔다.
2. **프롬프트 기호 없는 출력 블록 누락.** "Expected output:" 다음의 JSON 블록이 증거로 안 세어졌다. 펜스 바로 앞 문장이 결과를 예고하면 증거로 센다.
3. **`--offline`이 라이선스를 NOASSERTION으로 오판.** 감지값을 *조회하지 않은* 것(None)을 *조회했는데 식별 실패*로 옮겨, 파일이 멀쩡한 레포에 jq식 경고를 붙였다. `lookup_failed`로 고쳤다.
4. **자리표시자를 놓쳤다.** 블라인드 판정자가 `git clone <this repo>`에서 실제로 막혔는데, 감사는 사설 IP·홈 경로만 찾느라 `absent`를 냈다. 공백이 든 `<...>`를 `undetermined`로 잡는다(`<DIR>` 같은 옵션 표기는 제외).

1과 2를 고치기 전후로 판정이 뒤집힌다: 두 after 모두 `result_evidence`가 `absent` → `present`가 됐다. **고치기 전이었다면 "결과 증거를 잃었다"는 잘못된 퇴행 보고를 낼 뻔했다.**

## 결과 4 — 1280px 렌더 확인

GitHub 자체 렌더러(`gh api /markdown`)로 HTML을 만들고 GitHub 스타일을 입힌 뒤, 1280×900 뷰포트에서 스크롤 없이 보이는 첫 화면을 찍었다.

| 대상 | 스크롤 없이 보이는 것 | 판정 |
|---|---|---|
| Ultra-Search **before** | 제목, 한 줄 정의(121자), "왜", 역량 목록 5개, 설치 헤딩이 화면 맨 아래 걸침 | **결과 증거 없음.** 첫 명령의 `<this repo>`가 화면에 그대로 보인다 |
| Ultra-Search **after** | 한 줄 정의, 무엇을 대체하는지, 전제조건, 권한·한계, 실행 가능한 설치 명령, 성공 판정 기준, 첫 fetch 명령 | 세 질문 모두 스크롤 전에 답한다. 다만 **설치가 헤딩이 아니라 굵은 글씨**라 앵커가 없다(위 퇴행 1건) |
| Harness-Creator **after** | 한 줄 정의, 대상 사용자와 하는 일, 요구 조건, **약속하지 않는 것**, 설치 명령, 호출, 예상 결과 | 세 질문 모두 스크롤 전에 답한다 |
| 이 레포 (dogfood) | 한 줄 정의, 대안(readme-ai·readme-md-generator)과의 차이, 실제 감사 출력 | 세 질문 모두 스크롤 전에 답한다 |

**이 확인이 찾아낸 것**: 이 레포 README는 영어인데 화면에 보이는 도구 출력은 한국어였고, 그 사실을 어디에도 적지 않았다. 영어권 방문자에게는 이것이 "나한테 맞나"의 답을 바꾸는 조건이다. 한 줄 추가했다. **줄 번호 기반 판정으로는 안 잡히고 렌더 화면에서만 보이는 종류의 결함이다.**

## 검증하지 못한 것

- **3단계(유사 프로젝트 탐색).** 코덱스 샌드박스가 네트워크를 막아 `similar_repos.py`가 두 실행 모두 종료 코드 3으로 끝났다. 스크립트 자체는 샌드박스 밖에서 정상 동작을 확인했지만(`--query "fast alternative to find" --topic cli`가 `sharkdp/fd` 등을 반환), **E2E 흐름 안에서는 미검증**이다.
- **대화형 인터뷰.** 비대화형 실행이라 `AskUserQuestion` 흐름을 타지 못했다. 인터뷰 답을 프롬프트로 주입해 그 *이후* 단계만 검증했다. 질문 선택과 승인 동작은 대화형 세션에서 따로 봐야 한다.
- **홀드아웃 `Agentic-X`.** 이번에 쓰지 않았다. 위 4건을 고친 뒤의 스킬로 한 번도 안 쓴 레포에 돌려 보는 것이 남은 검증이다.
- **실제 사람의 이해도.** 판정자는 모델이다. 초심자의 실제 이해가 아니다.
