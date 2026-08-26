---
name: log-bug
description: "Log bug lên tracker (Redmine / GitLab / Jira) theo template QA chuẩn — title [ticket cha][màn hình] nội dung, description đủ 3 phần (nội dung / mô tả tái hiện / label), bắt buộc phân loại UI-logic, chống log bug trùng và gộp bug UI theo đúng 2 ngoại lệ được phép. Dùng sau khi test fail. Triggers (VI): 'log bug', 'tạo bug', 'báo bug', 'log bug lên Redmine', 'log bug lên Jira', 'ghi nhận lỗi'."
---

# Skill: log-bug

## 1. Mục tiêu

Biến một kết quả test fail thành một ticket bug **đủ để dev fix được ngay**, trên
đúng tracker của project, không trùng với bug đã có.

Skill lo ba việc mà con người hay làm sai khi log bug tay:
- **Thiếu field tái hiện** → dev phải quay lại hỏi QA. Skill chặn ngay từ đầu.
- **Log bug trùng** → tracker mất tin cậy. Skill dedup 2 tầng.
- **Log rời từng lỗi UI nhỏ** → mất thời gian. Skill gộp theo đúng 2 case được phép.

## 2. Phạm vi

Dùng được cho:
- Bug tìm ra khi execute test case (nối tiếp skill `execute-testcase`)
- Bug tìm ra khi test tay / test khám phá
- Bug UI (chính tả, phông chữ, cỡ chữ, vị trí item) và bug logic
- Log 1 bug hoặc log cả loạt bug trong một lần

**Không** dùng cho:
- Lỗi môi trường / thiếu quyền / thiếu data / chưa deploy → đây **không phải bug ứng dụng**,
  phải để `Pending` ở test case kèm Remark, không đẩy lên tracker
- Bug chưa tái hiện được (chưa có steps chắc chắn)
- Yêu cầu thay đổi nghiệp vụ (đó là change request, không phải bug)

## 3. Tracker được hỗ trợ

Cả ba đều **implement thật**, gọi API thật, đổi bằng một dòng `tracker.system`:

| System | API | Markup description | Field nhận native |
|---|---|---|---|
| `redmine` | `/issues.json`, header `X-Redmine-API-Key` | textile (`h3.`) | priority, assignee, **start_date**, due_date, tracker, status, parent |
| `gitlab` | `/api/v4/projects/:id/issues`, header `PRIVATE-TOKEN` | markdown (`###`) | assignee, due_date, labels |
| `jira` | `/rest/api/2/issue`, Basic auth (email + api_token) | wiki (`h3.`) | priority, assignee, due_date, labels, issuetype, parent |

Ghi chú kỹ thuật đã chốt:
- **Jira dùng API v2, không dùng v3.** v3 bắt `description` phải là ADF (cây JSON
  lồng nhau) → không dùng chung được bộ render text với Redmine/GitLab. v2 nhận
  description là string wiki-markup thuần và vẫn được support trên Jira Cloud.
- **GitLab không có `start_date` cho issue** (chỉ Epic có) → field này bị nhúng
  xuống description thay vì bị âm thầm đánh rơi.
- **GitLab `assignee` phải là user ID dạng số**, không nhận username. Điền
  username sẽ bị chặn với message rõ ràng thay vì lỗi 400 khó hiểu.

Đổi `default_system` trong profile sang tracker dự án bạn đang dùng
trong profile.

## 4. Cách gọi

```
/log-bug --bug-file <duong-dan-bug.json>
```

Đầy đủ:

```
/log-bug --bug-file inputs/bugs_event_editing.json \
         --manifest inputs/log_bug_manifest.yaml \
         --profile configs/log_bug_project_profile.yaml
```

## 4A. Scripts đi kèm

Toàn bộ I/O xác định nằm trong `scripts/`, agent **không improvise** các bước này:

| Script | Trách nhiệm |
|---|---|
| `log_bug_cli.py` | Entry point duy nhất — 6 subcommand. Output **luôn** JSON, exit 0 ok / 1 lỗi — kể cả khi YAML sai cú pháp hay bug file méo, không bao giờ trả traceback với stdout rỗng |
| `commands.py` | Handler các subcommand chỉ đọc/kiểm tra |
| `create_command.py` | Riêng `create` — subcommand duy nhất ghi ra ngoài (tạo issue thật + ghi registry) |
| `bug_batch.py` | Áp kế hoạch gộp: danh sách bug thô → danh sách bug sẽ tạo |
| `preflight_checks.py` | Bắt config tracker sai trước khi tạo bug thật |
| `cli_io.py` | Đọc bug file, in JSON, nạp config, áp `defaults` |
| `config_loader.py` | Merge profile < manifest < CLI; resolve credential `env:` |
| `bug_template.py` | Render title + description theo template I / II / III |
| `bug_validator.py` | Chặn bug thiếu field, thiếu phân loại UI/logic |
| `ui_bug_merger.py` | Quyết định nhóm bug UI nào được gộp |
| `dedup_checker.py` | Dấu vân tay bug + chống log trùng 2 tầng |
| `adapters/` | 3 adapter tracker sau một interface chung |

**Phân công rõ:**
- **Script làm**: validate, render, dedup, gọi API, ghi registry.
- **Agent làm**: quan sát bug trên môi trường, điền field, quyết định
  severity/priority, xác nhận khi script hỏi.

### 6 subcommand

```bash
S=skills/log-bug/scripts
M="--manifest inputs/log_bug_manifest.yaml --profile configs/log_bug_project_profile.yaml"

python3 $S/log_bug_cli.py preflight   $M
python3 $S/log_bug_cli.py validate    $M --bug-file inputs/bugs.json
python3 $S/log_bug_cli.py render      $M --bug-file inputs/bugs.json
python3 $S/log_bug_cli.py merge-check $M --bug-file inputs/bugs.json
python3 $S/log_bug_cli.py create      $M --bug-file inputs/bugs.json --dry-run
python3 $S/log_bug_cli.py create      $M --bug-file inputs/bugs.json
python3 $S/log_bug_cli.py create      $M --bug-file inputs/bugs.json --no-merge
python3 $S/log_bug_cli.py registry    $M
```

## 5. Input — bug file JSON

Nhận 1 bug (object), một list bug, hoặc `{"bugs": [...]}`.

```json
{
  "bugs": [
    {
      "parent_ticket": "#1234",
      "screen": "Login",
      "item": "btn_submit",
      "summary": "Đăng nhập không thành công khi nhập sai mật khẩu",
      "bug_type": "logic",
      "tc_id": "TC002",
      "sheet_name": "Manual Test Cases",
      "preconditions": "Đã có account test hợp lệ",
      "steps_to_reproduce": ["Mở /login", "Nhập sai mật khẩu", "Bấm Đăng nhập"],
      "actual_result": "Màn hình trắng, không hiện message lỗi",
      "expected_result": "Hiện message 'Mật khẩu không đúng'",
      "evidence": "bug_evidence/login/actual_001.png",
      "design_reference": "figma/login-v2#error-state",
      "severity": "Major",
      "priority": "High",
      "status": "Open",
      "scope": "Frontend",
      "assignee": 42,
      "assignee_name": "Nguyễn Văn A",
      "start_date": "2026-08-25",
      "due_date": "2026-08-28"
    }
  ]
}
```

Field lặp lại cả đợt test (`device`, `os_version`, `browser`, `status`, `scope`,
`parent_ticket`, `sheet_name`) khai **một lần** ở `defaults` trong manifest —
giá trị khai trong từng bug luôn thắng default.

## 6. Field bắt buộc

| Field | Vì sao bắt buộc |
|---|---|
| `parent_ticket` | Cú pháp title yêu cầu ID ticket cha |
| `screen` | Tên màn hình / tính năng trong title |
| `summary` | Nội dung bug |
| `bug_type` | **rule 2** — mọi bug phải phân loại `ui` hoặc `logic` |
| `ui_subtype` | Bắt buộc khi `bug_type = ui` |
| `steps_to_reproduce` | Không tái hiện được thì dev không fix được |
| `actual_result` | |
| `expected_result` | |
| `severity` | `Critical` / `Major` / `Medium` / `Low` |
| `priority` | `High` / `Medium` / `Low` |

Thiếu bất kỳ field nào → **dừng, không tạo bug**, báo rõ thiếu gì.

Cảnh báo (không chặn): thiếu `evidence`, thiếu `tc_id`, thiếu `assignee`.

`ui_subtype` cho phép: `spelling` (chính tả) · `font` (phông chữ) ·
`font_size` (cỡ chữ) · `position` (vị trí hiển thị item) · `other`.

Mọi enum trên (`allowed_severities`, `allowed_priorities`, `allowed_statuses`,
`allowed_scopes`, `allowed_bug_types`, `allowed_ui_subtypes`) **đổi được ở config** —
hằng số trong code chỉ là fallback khi config không khai.
Bỏ trống `ui_subtype` thì skill **gợi ý** từ mô tả tiếng Việt ("sai chính tả" →
`spelling`, "xô lệch vị trí" → `position`) nhưng **không tự điền** — người chọn.

## 7. Format bug

### I. Title

```
[{parent_ticket}][{screen}] {summary}
```

Ví dụ: `[#1234][Login] Đăng nhập không thành công khi nhập sai mật khẩu`

Đổi được qua `bug_policy.bug_title_pattern`. Biến dùng được: `parent_ticket`,
`screen`, `summary`, `tc_id`, `module_name`. Dùng biến lạ → báo lỗi rõ, không
render ra title dở dang.

> Format này **khác** format của `execute-testcase`
> (`[TEST][module][TC_ID] summary`). Đã chốt: template này thắng.

### II. Description

Render theo đúng thứ tự — đọc từ trên xuống là tái hiện được bug:

```
Testcase ID          <Sheet_Name>_<ID>
Device               PC | Laptop (MAC) ...
OS Version           14.4.1
Browser              Chrome | Edge ...
Điều kiện tiền đề
Các bước tái hiện    (list → tự đánh số)
Kết quả thực tế      + Evidence
Kết quả mong đợi     + Design/Nghiệp vụ
```

### III. Label

`Priority` · `Severity` · `Loại bug` (UI/Logic + subtype) · `Assignee` ·
`Status` · `Link issue` (ticket cha) · `Scope` · `Due Date`

**Quyết định (2026-08-25):** `Severity`, `Scope`, `Device`, `OS Version`,
`Browser` **nhúng vào description**, không map sang custom field của tracker.
- **Được**: chạy ngay với cả 3 tracker, không cần biết custom field id thật.
- **Mất**: không filter / report theo Severity trên tracker.
- Muốn filter → đổi sang custom field và khai id trong config.

Field tracker không nhận native (vd `start_date` trên GitLab) tự động xuống mục
"Field tracker không nhận native" trong description → **không mất thông tin**.

## 8. Rule log bug

### Nguyên tắc chung

1. **Mọi bug đều phải được ghi nhận và log lên hệ thống.** Skill không bao giờ im
   lặng bỏ qua một bug — hoặc tạo, hoặc báo rõ lý do không tạo.
2. **Mọi bug đều phải phân loại UI hay logic.** `bug_type` không có giá trị mặc định.
3. **Bug độc lập với nhau, mỗi lỗi log 1 bug** — trừ 2 ngoại lệ UI ở mục 9.
4. **Không log bug trùng** — xem mục 10.

### Không được làm

- Không log bug cho lỗi môi trường / thiếu quyền / thiếu data / chưa deploy
- Không tự điền `bug_type`, `severity`, `priority` khi chưa rõ → hỏi user
- Không tạo bug khi `actual_result` trùng `expected_result` (không phải bug)
- Không gộp bug logic, kể cả khi trùng khít nhau
- Không tự gộp khi vượt ngưỡng Case B → phải hỏi user
- Không ghi credential vào description, report hay evidence
- Không log bug lên tracker production khi chỉ đang thử → dùng `--dry-run`
- Không tin `closed` trong registry mà không hỏi lại tracker (xem mục 10)

## 9. Rule gộp bug UI

Nguyên tắc chung là mỗi lỗi 1 bug. Nhưng log rời từng lỗi UI nhỏ thì mất quá
nhiều thời gian, nên cho phép gộp **đúng hai** trường hợp:

**Case A — cùng test object, nhiều item, cùng 1 loại bug.**
Cùng `screen` + cùng `ui_subtype` + trải trên **≥ 2 item khác nhau**.
VD: 3 chỗ sai chính tả trên màn hình Login (nút, label, tiêu đề) → 1 bug.

**Case B — cùng 1 item có 3 đến 5 lỗi nhỏ.**
Cùng `screen` + cùng `item` + số lỗi trong khoảng `[3, 5]`.
VD: nút Submit vừa sai chữ, vừa sai font, vừa lệch vị trí → 1 bug.

Ba điều được quyết định có chủ ý:

- **Case A bắt buộc trải trên ≥ 2 item khác nhau.** Rule gốc nói "bug xảy ra ở
  **nhiều item** nhưng cùng 1 loại bug". Nhiều lỗi cùng loại trên **cùng 1 item**
  là địa hạt Case B. Thiếu điều kiện này thì Case A ăn hết nhóm của Case B và
  ngưỡng 3-5 trở thành vô nghĩa.
- **Case A xét trước Case B** — cùng 1 loại lỗi trên nhiều item là nhóm sạch hơn,
  ít gây tranh cãi khi fix.
- **Cùng 1 item nhưng > 5 lỗi → KHÔNG tự gộp**, trả `needs_confirm` để hỏi user.
  Rule chỉ phủ 3-5; vượt ngưỡng đó có thể là màn hình làm sai hàng loạt, đáng một
  bug riêng chứ không phải một bug gộp.

**Bug logic không bao giờ được gộp**, kể cả khi `ui_merge.enabled = true`.

Bug gộp có thêm mục "Danh sách item bị lỗi" trong description — người fix thấy
đủ danh sách, không phải đoán gộp cái gì.

### `create` gộp theo mặc định

Số ticket `create` tạo ra **khớp đúng** kế hoạch của `merge-check` — không cần cờ gì.
Gộp là mặc định vì ngoại lệ gộp sinh ra chính để tiết kiệm thời gian; bắt phải nhớ
cờ thì quên cờ là lại ra ticket rác.

Nhóm nào `needs_confirm` (quá 5 lỗi/item) → `create` **exit 1 và không tạo gì**,
buộc hỏi user. Hai đường thoát:

```bash
python3 $S/log_bug_cli.py create $M --bug-file bugs.json --no-merge   # log riêng từng lỗi
```
hoặc đặt `ui_merge.enabled: false` ở config để tắt hẳn cho cả project.

Chạy `merge-check` trước để **xem** kế hoạch trước khi tạo.

## 10. Rule chống log bug trùng

Hai tầng, vì một tầng không đủ:

**Tầng 1 — registry local** `<bug_reports_root>/<module>/bug_registry.json`.
Nhanh, không cần mạng, bắt được cả bug vừa log 5 giây trước trong cùng run.

**Tầng 2 — search trên tracker.** Bắt được bug do **người khác log tay**, thứ mà
registry local không thể biết.

Tắt riêng từng tầng bằng `check_registry_before_create` /
`check_tracker_search_before_create` (vd chạy offline thì tắt tầng 2).
`duplicate_handling: warn_only` → vẫn tạo bug dù nghi trùng, nhưng ghi rõ cảnh báo
vào `warnings` thay vì skip im lặng.

**`parent_ticket` cố ý KHÔNG nằm trong dấu vân tay.** Hai bug trùng khít nội dung
nhưng khác ticket cha vẫn là **cùng một lỗi**, mà rule 4 nói không log trùng. Trường
hợp chính đáng cần ticket thứ hai là bug đã fix rồi tái xuất hiện — cái đó đã có
nhánh `create_regression` lo. Đưa `parent_ticket` vào sẽ làm mỗi vòng test dưới
ticket cha mới đều log lại y nguyên bộ bug cũ.

Dấu vân tay bug = hash của `screen` + `bug_type` + `ui_subtype` + `item` + `summary`,
đã chuẩn hoá casefold + bỏ dấu câu + gom khoảng trắng. **Giữ dấu tiếng Việt** —
"sai" và "sài" là hai thứ khác nhau.

| Tình huống | Hành động |
|---|---|
| Không tìm thấy bug trùng | `create_new` |
| Bug cùng dấu vân tay còn **open** | `skip_duplicate` — không tạo |
| Bug cùng dấu vân tay đã **closed** | `create_regression` — tạo mới, description mở đầu bằng `(!) Regression của <id>` |

Bug tái xuất hiện sau khi đã fix là thông tin quan trọng, **không được lặng đi**.

**Registry phải được refresh, không tin mù.** Entry ghi `closed: false` lúc tạo và
**không tự đổi** khi dev fix xong. Nên khi registry báo trùng, skill hỏi lại tracker
trạng thái hiện tại (`get_issue_status`) rồi mới quyết định. Thiếu bước này thì một
bug đã fix xong rồi tái xuất hiện sẽ bị skip **vĩnh viễn** — đúng thứ mà rule
regression cần bắt. Output có `status_source` cho biết quyết định dựa trên `tracker`
(đã hỏi lại) hay `registry` (không đọc được tracker → tin bản lưu).

API chỉ được gọi khi **thực sự có nghi vấn trùng** — bug mới không tốn thêm request.

Registry ghi atomic (`os.replace`) → crash giữa lúc ghi không để lại file nửa vời.

## 11. Bảo mật credential

- `api_key` / `token` / `api_token` / `password` **không được ghi plaintext** trong
  manifest hay profile.
- Chỉ ghi tên biến môi trường dạng `env:TEN_BIEN`:
  - `token: "env:GITLAB_TOKEN"`
  - `api_key: "env:REDMINE_API_KEY"`
  - `api_token: "env:JIRA_API_TOKEN"`
- Biến chưa set → **dừng ở preflight**, không thử gọi API với credential rỗng.
- Ghi **plaintext** vào `api_key`/`token`/`api_token`/`password` → **skill từ chối chạy**
  và báo đúng key nào sai. Giá trị thật không bị in ra output. Nếu key đó là key
  thật thì coi như đã lộ → revoke ngay.
- Bảng effective config luôn **mask** credential thành `***da-resolve-tu-env***`.
- Không commit manifest chứa credential vào git repo.

## 12. Workflow

### Phase 1 — Preflight
`log_bug_cli.py preflight`. Exit 1 → dừng theo lý do trong output.

Kiểm: `tracker.system` hợp lệ · đủ config bắt buộc · credential resolve được từ env
· tracker gọi được · **project khai trong config có thật và token đọc được** ·
**`priority_map` trỏ tới tên priority có thật trên tracker**.

Hai kiểm cuối là để một `project_path` gõ nhầm hay một tên priority sai không lộ ra
lúc **đang** tạo bug (HTTP 400/404 giữa chừng, sau khi vài ticket thật đã tạo).
Chỉ chặn khi **chắc chắn sai**; không đọc được (mất mạng, tracker không có khái niệm
priority như GitLab) thì ghi vào `warnings` và cho chạy tiếp — không đoán.

### Phase 2 — Thu thập bug
Agent điền bug file JSON từ kết quả test. Không đoán field còn thiếu — thiếu thì hỏi.
Field lặp lại cả đợt → khai ở `defaults` trong manifest.

### Phase 3 — Validate
`validate`. Exit 1 → sửa bug file, **không** tạo bug. Đọc cả `warnings`.

### Phase 4 — Xét gộp bug UI
`merge-check`. `needs_user_confirm = true` → **dừng hỏi user** trước khi gộp.

### Phase 5 — Thử khô
`create --dry-run`. Đọc lại title + description đã render. Dry-run **không** ghi
registry (bug thật chưa hề được tạo).

### Phase 6 — Tạo bug thật
`create`. Đọc `created` / `skipped` / `failed`. `failed` khác rỗng → exit 1, xử lý
rồi chạy lại; bug đã tạo thành công không bị tạo lại (registry đã chặn).

### Phase 7 — Ghi ngược lại test case
Có `Bug ID` / `Bug URL` → cập nhật vào file test case (xem `execute-testcase` mục 10).

## 13. Output

- **Chính**: bug trên tracker (title + description theo template)
- `<bug_reports_root>/<module>/bug_registry.json` — chống trùng cho lần sau
- Output JSON của mỗi lệnh (`created` / `skipped` / `failed` + đếm số)

Evidence để ở `<bug_evidence_root>/<module>/`, tham chiếu bằng đường dẫn trong
field `evidence`.

## 14. Quan hệ với execute-testcase

Đã chốt (2026-08-25): **hai skill độc lập.** `execute-testcase` giữ nguyên
`redmine_client.py` của nó; `/log-bug` là đường riêng cho luồng log bug tay và
cho tracker khác Redmine.

Đánh đổi đã biết: hai chỗ tạo bug → format bug có thể lệch nhau. `execute-testcase`
dùng title `[TEST][module][TC_ID]`, skill này dùng `[ticket cha][màn hình]`.
Muốn thống nhất → migrate `execute-testcase` sang gọi `scripts/` của skill này.

## 15. Tiêu chí hoàn tất

- Preflight pass, credential resolve từ env
- Mọi bug trong phạm vi đã validate, không còn `errors`
- Bug UI đã qua `merge-check`; `needs_confirm` đã được user quyết
- Bug được tạo trên tracker, có `Bug ID` + `Bug URL`
- Bug trùng đã bị skip đúng, không tạo ticket thứ hai
- Registry đã cập nhật
- Không có credential trong description / report / evidence

## 16. Nguyên tắc

- Ưu tiên bug **đủ để fix** hơn bug log nhanh
- Cấu hình mâu thuẫn hoặc thiếu → **dừng và báo**, không suy diễn
- Không chắc lỗi ứng dụng hay lỗi môi trường → **không log bug**, để `Pending` ở test case
- Không chắc có được gộp → **hỏi**, đừng tự gộp

## 17. Test

139 test, chạy không cần tracker thật (test regression tự dựng stub HTTP trên localhost rồi tự tắt):

```bash
cd skills/log-bug/tests && python3 -m pytest . -q
```

| File | Phủ |
|---|---|
| `test_bug_validator_rules.py` | Field bắt buộc, phân loại UI/logic, gợi ý subtype |
| `test_ui_bug_merge_rules.py` | Case A / Case B / overflow / bug logic không gộp |
| `test_dedup_and_template.py` | Dấu vân tay, 3 nhánh quyết định, render I/II/III |
| `test_config_and_adapters.py` | Merge config, resolve env, factory 3 adapter |
| `test_integration_cli_dry_run.py` | Chạy thật 6 subcommand ở dry-run + hợp đồng JSON khi input méo |
| `test_adapter_payloads.py` | Payload gửi lên từng tracker (mock HTTP), đường lỗi, không lọt credential |
| `test_integration_regression_cycle.py` | Chu trình log → dev fix → bug tái xuất hiện, qua HTTP thật |
| `test_apply_merge_and_config_fidelity.py` | Gộp mặc định khớp kế hoạch, enum đọc từ config, Ctrl+C không bị nuốt |
| `test_preflight_verification.py` | Bắt project sai / priority_map sai; lỗi mạng chỉ cảnh báo |
