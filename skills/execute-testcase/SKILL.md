---
name: execute-testcase
description: "Thực thi test cases cho từng chức năng trên môi trường test, cập nhật kết quả trực tiếp vào file test case hiện có, ghi Remark nếu chưa test được và log bug lên Redmine khi actual result khác expected result. Triggers (VI): 'execute test case', 'chạy test case', 'thực thi test', 'test trên UAT', 'log bug Redmine'."
---

# Skill: execute-testcase

## 1. Mục tiêu

- Sử dụng file test case hiện có của một chức năng làm đầu vào chính để thực thi kiểm thử
- Dùng thông tin môi trường test được cung cấp để đăng nhập hệ thống
- Thực hiện kiểm thử theo từng test case có trong worksheet mục tiêu
- Đối chiếu actual result với expected result để xác định kết quả test
- Cập nhật trực tiếp vào chính file test case hiện có các cột execution
- Nếu actual result khác expected result và được xác nhận là lỗi ứng dụng:
  - đánh `Fail`
  - log bug lên Redmine
- Lưu evidence và summary cho từng lần chạy

## 2. Phạm vi của skill

Skill này dùng để execute test case cho:
- Web application
- Chức năng UI có thể thao tác được qua browser
- Các test case có steps rõ ràng, có expected result xác định được
- Các test case có thể thao tác được bằng automation hoặc điều khiển browser có kiểm soát

Skill này không phù hợp hoặc chỉ phù hợp một phần cho:
- Test case cảm quan như UI đẹp/xấu
- Performance test chuyên sâu
- Security test chuyên sâu
- Compatibility đa trình duyệt phức tạp
- Test case cần OTP, captcha, email ngoài, ứng dụng bên thứ ba nếu chưa có support
- Test case quá mơ hồ, không đủ điều kiện để execute

## 2A. Nguồn cấu hình và thứ tự ưu tiên

Skill đọc cấu hình từ 3 nguồn. Khi cùng một key xuất hiện ở nhiều nguồn, áp dụng thứ tự ưu tiên sau (nguồn sau ghi đè nguồn trước):

1. `configs/test_execution_project_profile.yaml` — chuẩn chung của project (thấp nhất)
2. `inputs/test_execution_manifest.yaml` — cấu hình của lần chạy này (ghi đè profile)
3. Tham số truyền trực tiếp trên command line (cao nhất)

Quy tắc bắt buộc:
- Sau khi merge, skill phải in ra `execution_summary.md` bảng giá trị hiệu lực (effective config) cho các key có mặt ở nhiều nguồn: `result_policy`, `update_policy`, `execution_columns`, `definition_columns`, `redmine.enabled`, `bug_title_pattern`, `*_root`.
- Mọi rule trong tài liệu này khi nói "theo cấu hình" đều hiểu là **cấu hình sau merge**, không phải riêng profile hay riêng manifest.
- Nếu một key bắt buộc không có ở nguồn nào, dừng và ghi lý do vào summary; không tự suy diễn giá trị.

## 3. Input chính

Skill nhận các đầu vào sau:
- Module name / function name
- Test environment URL
- Username
- Password — **không đọc plaintext từ manifest**; xem rule bảo mật credential bên dưới
- Nguồn file test case hiện có
- Worksheet name
- Tên người thực hiện test
- Cấu hình Redmine để tạo bug khi cần
- Rule thực thi và mapping cột từ cấu hình sau merge (xem mục 2A)

### 3A. Rule bảo mật credential

- `password` và `redmine.api_key` **không được ghi plaintext** trong manifest hay profile.
- Trong file cấu hình chỉ ghi tên biến môi trường theo format `env:TEN_BIEN`, ví dụ:
  - `password: "env:TEST_PASSWORD"`
  - `api_key: "env:REDMINE_API_KEY"`
- Skill đọc giá trị thật từ environment variable tương ứng tại thời điểm chạy.
- Nếu biến môi trường chưa được set: dừng ở Phase 1, ghi lý do vào `execution_summary.md`, không thử login, không tạo bug.
- Không được echo/log/ghi vào evidence hay report bất kỳ giá trị credential nào.
- Không commit file manifest chứa credential vào git repo (xem `development-rules.md`).

## 4. Cách gọi skill

`/execute-testcase <module_name>`

Hoặc:

`/execute-testcase <module_name> --manifest ./inputs/test_execution_manifest.yaml`

Hoặc:

`/execute-testcase <module_name> --manifest ./inputs/test_execution_manifest.yaml --profile ./configs/test_execution_project_profile.yaml`

Ví dụ:
- `/execute-testcase event_editing`
- `/execute-testcase settlement_management --manifest ./inputs/test_execution_manifest.yaml`
- `/execute-testcase coupon_validation --manifest ./inputs/test_execution_manifest.yaml --profile ./configs/test_execution_project_profile.yaml`

## 4A. Scripts đi kèm skill

Toàn bộ I/O xác định (deterministic) nằm trong `scripts/`, agent **không tự improvise** các bước này:

| Script | Trách nhiệm |
|---|---|
| `execute_testcase_cli.py` | Entry point duy nhất — 4 subcommand `preflight`, `load-cases`, `write-result`, `log-bug`. Mọi output là JSON, exit 0 khi ok / 1 khi lỗi |
| `config_loader.py` | Merge profile + manifest theo mục 2A, resolve `env:` credential (mục 3A), cổng an toàn môi trường (mục 13A) |
| `column_mapper.py` | Map header thực tế → cột logic bằng alias; chặn thiếu cột filter (mục 6A) |
| `case_filter.py` | 5 bước lọc của Phase 3 + trail số case sau từng bước |
| `sheet_io.py` | Đọc/ghi test case in-place; route theo `source_type`; `assert_writable()` chặn ghi vào definition column |
| `excel_worksheet.py` | Backend `.xlsx` local (openpyxl) với cùng interface như gspread worksheet |
| `redmine_client.py` | Tạo bug + quyết định trùng bug (mục 12A) |
| `target_resolver.py` | Chốt file đích cho cả run: `in_place` / `backup_then_update` / `clone_then_write` |
| `result_validator.py` | Chặn ghi kết quả thiếu Remark / Actual (mục 9A, 9B) |

Phân công rõ:
- **Script làm**: đọc/ghi Sheet, merge config, lọc case, gọi Redmine, validate rule.
- **Agent làm**: điều khiển browser qua skill `chrome-devtools` / `browser-automation`, quan sát actual result, quyết định Pass/Fail/Pending, viết summary.

Hai nguồn test case, chọn bằng `testcase_source.source_type`:
- `google_sheet` — cần service account (xem dưới)
- `excel` — file `.xlsx` local qua `testcase_source.local_excel_path`; chạy được ngay không cần credential, dùng cho thử nghiệm và cho project không dùng Google Sheet

Cả hai đi qua cùng một đường code (`read_cases` / `write_result`), nên rule bảo vệ cột definition áp dụng giống nhau.

File nháp 5 case để thử: `tests/fixtures/sample_testcases_event_editing.xlsx` (sinh lại bằng `tests/fixtures/build_sample_testcases.py`). **Không ghi trực tiếp vào fixture** — copy ra chỗ khác rồi trỏ `local_excel_path` vào bản copy.

Auth Google Sheet: service account JSON, đường dẫn lấy từ `GOOGLE_APPLICATION_CREDENTIALS` hoặc `testcase_source.service_account_json`. Không dùng MCP Google Drive vì cần OAuth tương tác và không có API ghi theo range để bảo vệ cột definition.

Ví dụ luồng gọi:

```bash
S=skills/execute-testcase/scripts
python3 $S/execute_testcase_cli.py preflight   --manifest inputs/test_execution_manifest.yaml --profile configs/test_execution_project_profile.yaml
python3 $S/execute_testcase_cli.py load-cases  --manifest ... --profile ...
# agent execute case qua browser, roi ghi ket qua tung dong:
python3 $S/execute_testcase_cli.py write-result --manifest ... --profile ... \
    --row 7 --status Fail --remark "Actual khác Expected: ..." --actual "..." --tested-by "Huong"
python3 $S/execute_testcase_cli.py log-bug     --manifest ... --profile ... \
    --tc-id TC002 --summary "..." --expected "..." --actual "..." --existing-bug-id 1234
```

`preflight` trả exit code 1 kèm `production_risk_reasons` khi môi trường nghi là production — **phải dừng hỏi user**, không tự chạy tiếp.

## 5. Nguồn đầu vào hỗ trợ

Skill có thể dùng:
- Google Sheet test case đã được sinh trước đó
- Excel test case hiện có nếu có cơ chế đọc/ghi phù hợp
- Requirement package để hiểu thêm expected behavior nếu cần clarification
- Redmine issue/task của chức năng
- Test data note hoặc execution note
- Tài khoản test và môi trường test

## 6. Cột tối thiểu cần có trong file test case

Skill phải map được tối thiểu các cột sau từ header thực tế:
- TC ID
- Title
- Preconditions
- Steps
- Test data
- Expected Result
- Test result
- Test date
- Tested by
- Remark

Nếu `case_filter` trong cấu hình có dùng filter theo phân loại hoặc độ ưu tiên, thì các cột sau cũng là **bắt buộc phải map được**:
- Priority — bắt buộc khi `include_priorities` hoặc `exclude_priorities` không rỗng
- Classification 1 — bắt buộc khi `include_classification_1` hoặc `exclude_classification_1` không rỗng

Nếu template có thêm cột:
- Bug ID
- Bug URL
- Actual Result
- Evidence Link

thì skill có thể ghi thêm nếu cấu hình cho phép.

### 6A. Rule khi cột dùng để filter không tồn tại

Nếu một cột được `case_filter` tham chiếu mà không map được từ header thực tế:
- **Không** được im lặng trả về 0 test case.
- Dừng Phase 3, ghi vào `execution_summary.md`: `Thiếu cột filter: <tên cột> — filter <tên filter> không áp dụng được`.
- Chỉ chạy tiếp khi user xác nhận bỏ filter đó; khi bỏ, phải ghi rõ trong summary là filter nào đã bị bỏ.

Nếu sau khi áp toàn bộ filter mà tập test case rỗng:
- Ghi rõ vào summary số case ở từng bước lọc (tổng → sau `execution_mode` → sau status filter → sau `case_filter`) để phân biệt "không có case thoả" với "map cột sai".

## 7. Rule thực thi từng test case

Với mỗi test case:
1. Đọc preconditions
2. Chuẩn bị dữ liệu nếu có thể
3. Thực hiện steps
4. Thu actual result
5. So sánh với expected result
6. Ghi kết quả vào đúng dòng tương ứng trong file test case hiện có

## 8. Rule mapping Test result

### Pass
- Actual result khớp expected result

### Fail
- Actual result khác expected result
- Và đã xác nhận không phải do blocker môi trường hoặc thiếu dữ liệu
- Bắt buộc ghi `Actual Result` (nếu template có cột này) **và** `Remark` theo format `Actual khác Expected: <mô tả ngắn>`
- Chỉ ghi một trong hai là chưa đủ; đây là rule chặt hơn mức `fail_cases_have_actual_result_or_remark` trong `review_policy`

### N/A
- Test case không áp dụng cho môi trường hoặc cấu hình hiện tại

### Untested
- Test case chưa được chạy

### Pending
- Không thể hoàn tất execution do blocker
- Ví dụ:
  - môi trường lỗi
  - tài khoản không đủ quyền
  - thiếu test data
  - chức năng chưa deploy
  - phụ thuộc ngoài chưa sẵn sàng
  - test case không đủ rõ để execute

## 9. Rule bắt buộc cho Remark

Remark là bắt buộc trong **hai** trường hợp: case không test được, và case `Fail`.

### 9A. Case không test được

Nếu test case không test được:
- `Test result` phải là `Pending` hoặc `Untested` theo rule của profile
- `Remark` bắt buộc ghi theo format:
  - `Chưa test được: <lý do cụ thể>`

Ví dụ:
- `Chưa test được: môi trường test đang lỗi 500`
- `Chưa test được: tài khoản test không có quyền Admin Event`
- `Chưa test được: chưa có dữ liệu event ở trạng thái Published`
- `Chưa test được: chức năng chưa được deploy lên UAT`

Không được để trống `Remark` nếu case không test được.

### 9B. Case Fail

Nếu test case `Fail`:
- `Remark` bắt buộc ghi theo format `Actual khác Expected: <mô tả ngắn>`
- Và bắt buộc ghi `Actual Result` nếu template có cột này

Ví dụ:
- `Actual khác Expected: hệ thống cho lưu event với ngày kết thúc trước ngày bắt đầu`
- `Actual khác Expected: không hiện message lỗi khi bỏ trống trường bắt buộc`

Prefix của cả hai trường hợp lấy từ cấu hình sau merge (`not_testable_remark_prefix`, `fail_remark_prefix`), không hard-code trong skill.

## 10. Rule cập nhật kết quả vào file test case

Sau khi execute từng test case, skill phải cập nhật trực tiếp vào chính file test case hiện có:
- `Test result`
- `Test date`
- `Tested by`

Nếu không test được:
- cập nhật thêm `Remark`

Nếu profile cho phép ghi thêm:
- `Actual Result`

Nếu fail và bug được tạo:
- cập nhật thêm `Remark`
- và nếu template hỗ trợ, cập nhật:
  - `Bug ID`
  - `Bug URL`

## 11. Rule log bug lên Redmine

Chỉ log bug khi:
- Test case đã được execute thực sự
- Expected result rõ ràng
- Actual result khác expected result
- Không phải lỗi môi trường, dữ liệu hoặc quyền truy cập chưa đúng

Không log bug khi:
- dòng test case đó đã có `Bug ID` hoặc `Bug URL` từ lần chạy trước và bug vẫn còn open — xem rule chống trùng bên dưới
- môi trường down
- login fail do credential sai
- thiếu data
- thiếu quyền account
- chưa deploy
- expected result mơ hồ

Các trường hợp trên phải:
- đặt `Pending` hoặc `Untested` theo rule
- ghi `Remark` là `Chưa test được: <lý do>`

## 12. Format bug Redmine

### Bug title
`[TEST][<module_name>][<TC_ID>] <short failure summary>`

### 12A. Rule chống tạo bug trùng

Trước khi tạo bug cho một case `Fail`, bắt buộc kiểm tra theo thứ tự:
1. Đọc `Bug ID` / `Bug URL` của đúng dòng test case đó trong file test case.
2. Nếu đã có giá trị:
   - Query Redmine để lấy trạng thái issue đó.
   - Issue còn open → **không tạo bug mới**; giữ nguyên `Bug ID`/`Bug URL`, cập nhật `Remark` ghi rõ `Fail lặp lại — bug đã tồn tại`, và ghi vào `redmine_bug_mapping.md`.
   - Issue đã closed/rejected → tạo bug mới, ghi thêm vào description dòng `Regression của <bug_id_cũ>`.
3. Nếu cột `Bug ID`/`Bug URL` không tồn tại trong template, tra `redmine_bug_mapping.md` của các lần chạy trước theo cặp `module_name` + `TC ID` trước khi tạo mới.
4. Khi `duplicate_bug_handling` trong cấu hình là `warn_only`: vẫn tạo bug nhưng phải ghi cảnh báo trùng vào `redmine_bug_mapping.md`; không được im lặng.

### Bug description tối thiểu
- Module name
- TC ID
- Test case title
- Environment URL
- Preconditions
- Steps executed
- Test data
- Expected result
- Actual result
- Tested by
- Test date
- Evidence path hoặc screenshot path

## 13. Workflow thực thi

### Phase 1 — Nạp cấu hình

Chạy `execute_testcase_cli.py preflight`; exit code 1 thì dừng theo lý do trong output.

- Đọc module_name
- Đọc execution manifest
- Đọc execution profile
- Kiểm tra testcase source
- Kiểm tra mapping cột
- Kiểm tra thông tin môi trường test
- Kiểm tra cấu hình Redmine
- Kiểm tra chế độ update in-place
- Resolve credential từ environment variable theo mục 3A; thiếu biến thì dừng tại đây
- In bảng effective config theo mục 2A
- **Kiểm tra an toàn môi trường** theo mục 13A

### 13A. Cổng an toàn môi trường (bắt buộc trước Phase 2)

Skill sẽ login và thao tác UI có thể làm thay đổi dữ liệu, nên trước khi mở browser phải:

- Đối chiếu `environment.name` và `environment.base_url` với danh sách môi trường được phép chạy trong cấu hình.
- **Dừng và hỏi user xác nhận** nếu `base_url` khớp bất kỳ dấu hiệu production: không chứa `uat`/`stg`/`staging`/`dev`/`test`/`local`, hoặc `environment.name` là `PROD`/`PRODUCTION`, hoặc host là domain chính của khách hàng.
- Không bao giờ tự ý chạy trên production kể cả khi manifest ghi như vậy.
- Với mọi bước trong `Steps` có tính phá huỷ dữ liệu (xoá, huỷ, hoàn tiền, gửi thông báo ra ngoài), phải xác nhận đang ở môi trường test trước khi thực hiện; nếu không xác nhận được thì đặt `Pending` với Remark `Chưa test được: bước có rủi ro dữ liệu, chưa xác nhận được môi trường an toàn`.

### Phase 2 — Kết nối môi trường test
- Điều khiển browser qua skill `chrome-devtools` (Puppeteer) hoặc `browser-automation`; **không tự viết browser driver mới**
- Mở test URL
- Login bằng username/password đã resolve từ env
- Xác nhận đăng nhập thành công
- Nếu login fail:
  - dừng execution nếu policy yêu cầu
  - ghi execution summary
  - không tự log bug ứng dụng

### Phase 3 — Nạp test cases

Chạy `execute_testcase_cli.py load-cases` — script đã thực hiện đúng 5 bước lọc dưới đây và trả `filter_trail`.

- Đọc worksheet mục tiêu
- Chọn test cases theo thứ tự lọc bắt buộc dưới đây
- Ghi số lượng case còn lại sau từng bước lọc vào `execution_summary.md`

**Thứ tự áp filter (bắt buộc theo đúng trình tự):**

1. `execution_mode` quyết định tập gốc:
   - `baseline` — lấy toàn bộ case trong worksheet
   - `rerun_failed` — chỉ lấy case đang có `Test result` là `Fail`
   - `selected_cases` — chỉ lấy case có TC ID nằm trong `case_filter.include_tc_ids`; nếu `include_tc_ids` rỗng thì **dừng và báo lỗi cấu hình**, không được hiểu thành "chạy hết"
2. `execute_only_statuses` lọc tiếp theo `Test result` hiện tại. Bỏ qua bước này khi `execution_mode` là `rerun_failed` (mode đã ngụ ý status) hoặc `selected_cases` (user chỉ định tường minh).
3. `case_filter.include_tc_ids` / `exclude_tc_ids` — `exclude` luôn thắng `include`.
4. `case_filter.include_classification_1` / `exclude_classification_1`.
5. `case_filter.include_priorities` / `exclude_priorities`.

Danh sách rỗng nghĩa là **không áp filter đó**, không phải "loại hết".

### Phase 4 — Execute từng test case
- Thao tác UI qua `chrome-devtools` / `browser-automation`; chụp screenshot theo `capture_screenshot_on_*`
- Chuẩn bị preconditions nếu có thể
- Thực hiện steps
- So sánh actual với expected
- Xác định status
- Điền kết quả vào dòng tương ứng

### Phase 5 — Log bug nếu cần

Chạy `execute_testcase_cli.py log-bug` (đã bao gồm dedup mục 12A); `action` trả về là `create_new` / `reuse_open` / `create_regression`.

- Với test case `Fail` hợp lệ:
  - tạo Redmine bug
  - lấy bug id / url
  - ghi lại vào file test case nếu có cột tương ứng
  - nếu không có cột thì ghi vào summary / mapping file

### Phase 6 — Xuất output phụ
- execution_summary.md
- failed_cases.md
- redmine_bug_mapping.md
- environment_issues.md

## 14. Rule phân loại nguyên nhân khi không test được

Nếu không test được, skill phải xác định một trong các nhóm sau:
- Environment issue
- Access / permission issue
- Test data unavailable
- Deployment not ready
- Dependency unavailable
- Ambiguous test case
- Manual-only step not executable

Và ghi vào Remark:
- `Chưa test được: <root cause>`

## 15. Rule không được làm

- Không đánh `Pass` nếu chưa xác minh actual result
- Không đánh `Fail` nếu chưa loại trừ blocker môi trường
- Không log bug Redmine cho lỗi môi trường
- Không xóa lịch sử kết quả cũ nếu `update_policy.overwrite_existing_result` trong **cấu hình sau merge** (mục 2A) không bật; key này nằm ở manifest, profile không định nghĩa nó
- Không suy diễn expected result khi test case mơ hồ
- Không bịa actual result khi chưa thực sự quan sát được trên môi trường
- Không log bug sai bản chất (lỗi môi trường/dữ liệu/quyền ghi thành bug ứng dụng)
- Không ghi credential vào report, evidence hoặc bug description
- Không sửa nội dung định nghĩa gốc của test case
- Không sửa nhầm các cột ngoài execution columns

## 16. Output bắt buộc

### Output chính
- File test case hiện có được cập nhật trực tiếp các cột execution
- Không tạo file test case mới với cấu trúc tự định nghĩa để lưu kết quả execution; chỉ được ghi vào chính file test case hoặc bản clone/backup y nguyên của nó
- Các cột được phép cập nhật:
  - Test result
  - Test date
  - Tested by
  - Remark
  - Actual Result nếu có
  - Bug ID nếu có
  - Bug URL nếu có

### Output phụ
- `<execution_reports>/<module_name>/execution_summary.md`
- `<execution_reports>/<module_name>/failed_cases.md`
- `<execution_reports>/<module_name>/redmine_bug_mapping.md`
- `<execution_reports>/<module_name>/environment_issues.md`

### Evidence
- `<execution_evidence>/<module_name>/screenshots/`
- `<execution_evidence>/<module_name>/logs/`
- `<execution_evidence>/<module_name>/page_states/`

## 16A. Chính sách cập nhật file test case hiện có

**Skill KHÔNG BAO GIỜ tự định nghĩa file kết quả mới.** Đích ghi luôn là chính file test case, hoặc một bản clone y nguyên của nó — mọi cột, mọi dòng, mọi định dạng giữ đúng vị trí QA đã viết.

Ba mode, chọn bằng `update_policy.mode`:

| Mode | Ghi vào đâu | File gốc |
|---|---|---|
| `in_place` (default) | chính file test case | bị cập nhật |
| `backup_then_update` | chính file test case | bị cập nhật, có bản backup cạnh đó |
| `clone_then_write` | bản clone của file test case | **không sửa một ô nào** |

Với `clone_then_write`:
- Excel → clone thành `<tên gốc>__executed_<module>_<timestamp>.xlsx`
- Google Sheet → copy cả spreadsheet (giữ permission), ghi vào bản copy

Quyết định đã chốt (2026-08-24) — đừng đổi ngược mà không thống nhất lại:
- **Default vẫn là `in_place`.** Team chọn không đổi default sang `clone_then_write`; ai muốn giữ file gốc nguyên thì set mode ở manifest của run đó.
- **Bản clone đặt chung thư mục với file gốc**, không gom vào thư mục riêng — ưu tiên dễ tìm hơn là thư mục gọn.
- **Google Sheet clone giữ permission gốc** (`copy_permissions=True`) để QA lead mở được ngay, không phải xin quyền.

Đích được chốt **một lần cho cả run** và lưu ở `<execution_runtime_root>/<module_name>/target.json`. Nếu không nhớ đích, mỗi case sẽ sinh một bản clone riêng và kết quả bị rải ra N file. Bắt đầu run mới → `write-result --reset-target`.

- File test case hiện có là nguồn input và cũng là đích output chính
- Skill phải cập nhật in-place vào đúng worksheet mục tiêu (hoặc vào bản clone khi mode là `clone_then_write`)
- Skill không được sửa các cột định nghĩa test case gốc như:
  - TC ID
  - Title
  - Preconditions
  - Steps
  - Test data
  - Expected Result
  - Classification
- Skill chỉ được cập nhật các cột execution theo cấu hình
- Nếu profile bật backup trước khi ghi:
  - tạo bản backup trước khi update
- Nếu profile không bật backup:
  - ghi trực tiếp vào file hiện có

## 17. Tiêu chí hoàn tất

Skill hoàn tất khi:
- Đã login được môi trường test hoặc ghi rõ lý do không login được
- Đã xử lý toàn bộ test case trong phạm vi run
- Đã cập nhật kết quả vào file test case hiện có
- Các case không test được đều có Remark
- Các case `Fail` hợp lệ đã được log bug Redmine
- Đã xuất đầy đủ execution summary và evidence
- Đã ghi bảng effective config vào `execution_summary.md` (mục 2A)
- Các case `Fail` đều có cả `Actual Result` và `Remark` (mục 9B)
- Không tạo bug trùng cho case đã có bug open (mục 12A)
- Credential được resolve từ environment variable, không xuất hiện trong report/evidence

## 18. Nguyên tắc

- Ưu tiên tính chính xác của execution hơn tốc độ
- Khi cấu hình mâu thuẫn hoặc thiếu, dừng và báo — không suy diễn
- Khi không chắc một case Fail là lỗi ứng dụng hay lỗi môi trường, đặt `Pending` chứ không đặt `Fail`