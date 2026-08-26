---
name: gen-testcase
description: "[personal] Sinh manual test cases cho từng chức năng và xuất ra 1 Google Sheet riêng bằng cách duplicate từ master template được import từ file template_testcase.xlsx đi kèm skill."
---

# Skill: gen-testcase

## 1. Mục tiêu

- Sử dụng requirement package hoặc các requirement source liên quan làm đầu vào để thiết kế manual test cases
- Phân tích requirement ở mức phục vụ kiểm thử nhằm xác định test conditions, test coverage, test data và expected results
- Xác định các luồng chính, luồng phụ, ngoại lệ, business rules và validation rules cần được kiểm thử
- Thiết kế bộ manual test cases có độ bao phủ cao, đúng logic nghiệp vụ và độc lập
- Phân loại test case đúng nhóm và đúng thứ tự theo template chuẩn của công ty
- Tạo 1 Google Sheet riêng cho mỗi chức năng bằng cách duplicate từ Google Sheet master template
- Đổ dữ liệu test case vào đúng worksheet và đúng vùng dữ liệu của template
- Hỗ trợ traceability từ test case về FR / BR / VR / source
- Ghi rõ các điểm cần xác nhận nếu requirement chưa đủ rõ để thiết kế test case chính xác

## 2. Phạm vi của skill

Skill này dùng để sinh manual test cases cho:
- Screen UI
- Module nghiệp vụ
- API function
- Batch / scheduler / event-driven process
- Change request
- Enhancement
- Reverse engineering từ source hiện có

## 3. Dependency với bộ requirement

Skill này ưu tiên sử dụng output từ skill `gen-requirement` làm đầu vào chính, bao gồm:
- `functional_requirements.md`
- `business_rules.md`
- `validation_rules.md`
- `impact_scope.md`
- `assumptions_and_open_points.md`
- `traceability_matrix.md`

Nếu requirement package đã có sẵn:
- Skill không phân tích requirement lại ở mức tài liệu BA đầy đủ
- Skill chỉ phân tích ở mức phục vụ thiết kế test case

Nếu requirement package chưa có:
- Skill có thể dùng trực tiếp requirement doc, ticket, Figma, API spec, workflow và các source liên quan
- Mọi điểm chưa rõ phải được ghi vào `open_points.md`

## 4. Cách gọi skill

`/gen-testcase <module_name>`

Hoặc:

`/gen-testcase <module_name> --manifest ./inputs/testcase_source_manifest.yaml`

Hoặc:

`/gen-testcase <module_name> --manifest ./inputs/testcase_source_manifest.yaml --profile ./configs/testcase_project_profile.yaml`

Ví dụ:
- `/gen-testcase event_editing`
- `/gen-testcase settlement_management --manifest ./inputs/testcase_source_manifest.yaml`
- `/gen-testcase coupon_validation --manifest ./inputs/testcase_source_manifest.yaml --profile ./configs/testcase_project_profile.yaml`

## 5. Input bắt buộc

| Biến | Mô tả |
|---|---|
| `$1` | Module name / function name |
| `MANIFEST_PATH` | File khai báo source đầu vào |
| `PROFILE_PATH` | File cấu hình quy tắc dự án |
| `OUTPUT_ROOT` | Thư mục output phụ, mặc định `testcases` |
| `EVIDENCE_ROOT` | Thư mục evidence, mặc định `evidence_testcase` |

## 5A. Quy tắc phạm vi: 1 module = 1 Google Sheet

Đây là quy tắc **cao nhất**, override mọi phần còn lại của skill khi có mâu thuẫn.

### 5A.1. Nguyên tắc

- **1 lần chạy chỉ sinh test case cho ĐÚNG 1 module**, xuất ra **đúng 1 Google Sheet**.
- **Cấm gộp nhiều module vào chung 1 Sheet**, cấm tạo nhiều Sheet trong một lần chạy.
- **Cấm gen test case cho toàn bộ dự án** kể cả khi bộ requirement hoặc 設計書 phủ nhiều module.
- Muốn làm nhiều module → chạy lại lệnh cho từng module.
- Output phụ chỉ ghi vào `<output_root>/<module_name>/` và `<evidence_root>/<module_name>/`. Cấm đụng folder module khác.

### 5A.2. Không có tên module trên dòng lệnh — LUÔN hiển thị danh sách rồi DỪNG hỏi

**Điều kiện kích hoạt (quan trọng):** chạy module discovery khi **argument `$1` trống** — **bất kể manifest ghi gì**.

- `run.module_name` trong manifest **KHÔNG được dùng** để chọn module chạy. Nó chỉ là ghi chép, kể cả khi đang chứa một tên module hợp lệ.
- Chỉ **bỏ qua** discovery khi người dùng gõ rõ tên module: `/gen-testcase <module_name>`.
- Không được suy ra module từ: manifest, lần chạy trước, thư mục đã tồn tại trong `<output_root>`, Sheet đã tạo, hay ngữ cảnh hội thoại.

**Các bước:**

1. **Ưu tiên đọc module registry**: nếu tồn tại `configs/module_registry.yaml` thì **lấy danh sách từ đó**. **Cấm** quét lại source khi registry đã có dữ liệu.
2. **Chỉ khi không có registry**, mới quét ở mức **khung**: danh sách thư mục trong `<output_root>` của bộ requirement đã sinh, mục lục / bảng FR / cột màn hình của requirement doc.
   - **Cấm** đọc chi tiết flow, business rule, validation ở bước này.
   - **Cấm** đọc toàn văn source lớn chỉ để liệt kê module.
3. Xuất **bảng danh sách chức năng** dạng Markdown, hiển thị toàn bộ trong 1 bảng:

   | # | module_name | Hệ thống | Màn hình / entry point | Có sẵn bộ requirement? | Trạng thái |
   |---|---|---|---|---|---|

   - Cột `Có sẵn bộ requirement?` kiểm tra bằng sự tồn tại của `knowledge/<module_name>/functional_requirements.md` (hoặc `requirement_output` trong registry).
   - Cột `Trạng thái` lấy từ registry (`pending` / `req_done` / `tc_done` / `out_of_scope`).
4. **DỪNG hỏi người dùng chọn 1 chức năng** (nhận cả số thứ tự lẫn `module_name`). Không tự chọn, không tạo Sheet, không sinh file nào.
5. Sau khi người dùng chọn → chạy tiếp Phase 1 với đúng module đó.
6. Chạy xong → cập nhật `status` và `testcase_output` của module đó trong registry.

### 5A.3. Ranh giới nội dung test case

- Test case **chỉ** cover FR/BR/VR thuộc module đang chạy.
- Chức năng của module khác **chỉ được** xuất hiện trong `Preconditions` hoặc `Test data` (dạng điều kiện đầu vào), **không** tạo test case riêng cho chúng.
- Phát hiện hành vi thuộc module khác cần test → ghi vào `open_points.md`, không tự sinh test case ngoài phạm vi.
- Naming Sheet phải chứa đúng `module_name` đang chạy theo `spreadsheet_name_pattern`.

## 6. Nguồn đầu vào hỗ trợ

Skill có thể dùng các nguồn sau:
- `functional_requirements.md`
- `business_rules.md`
- `validation_rules.md`
- `impact_scope.md`
- `assumptions_and_open_points.md`
- `traceability_matrix.md`
- Requirement document
- Ticket
- Figma
- API spec
- DB schema
- Workflow
- Meeting note
- Existing screen capture
- Existing test artifact
- Change request

## 7. Ưu tiên nguồn

Thứ tự ưu tiên khuyến nghị:
1. `functional_requirements.md`
2. `business_rules.md`
3. `validation_rules.md`
4. Requirement document đã approved
5. Approved ticket / change request
6. Confirmed Figma
7. API spec / DB schema
8. Workflow / screen capture
9. Meeting note / historical note

Nếu có xung đột:
- Ưu tiên nguồn cao hơn
- Nếu chưa đủ rõ, ghi vào `open_points.md`
- Không tự suy diễn nghiệp vụ

## 8. Excel / Google Sheet Template Policy

Template gốc của công ty đi kèm ngay trong skill này, tại:
- `<skill_dir>/templates/template_testcase.xlsx`

Trong đó `<skill_dir>` là thư mục chứa chính file `SKILL.md` này — hiện tại là
`~/.claude/skills/gen-testcase/`. KHÔNG dùng path tương đối `./templates/...` vì nó
resolve theo working directory của project đang mở, nên sẽ trỏ sai khi skill được
gọi từ project khác.

Nguyên tắc vận hành:
- File Excel này là template nguồn của công ty
- Template nguồn cần được import lên Google Drive 1 lần để tạo Google Sheet master template
- Mỗi lần sinh test case cho một chức năng, skill phải tạo 1 file Google Sheet mới bằng cách duplicate từ Google Sheet master template
- Skill chỉ được ghi dữ liệu vào đúng worksheet cấu hình trong manifest
- Skill không được tự ý đổi tên cột, thêm cột hoặc đổi thứ tự cột nếu không có yêu cầu rõ ràng
- Skill phải preserve cấu trúc template thực tế nhiều nhất có thể
- Nếu template có nhiều sheet, chỉ ghi vào sheet được chỉ định
- Nếu chưa có `google_master_template_file_id`, cần ghi nhận là `Cần xác nhận` và dừng ở bước chuẩn bị output Google Sheet

## 9. Phân tích requirement phục vụ test design

Trước khi sinh test case, skill phải trích xuất:
- Tên chức năng
- Actor chính
- Mục tiêu chức năng
- Main Flow
- Alternate Flow
- Exception Flow
- Business Rules
- Validation Rules
- Điều kiện đặc biệt
- Dependency quan trọng
- Impact quan trọng tới khu vực liên quan
- Điểm chưa rõ ảnh hưởng tới test design

Nếu có điểm không rõ:
- không tự bịa
- ghi vào `open_points.md`

## 10. Nhóm test case bắt buộc và đúng thứ tự

Test case phải được sinh đúng thứ tự sau:

### 10.1. Common Test Cases
- Trigger/Navigation
- UI
- Form Validation

### 10.2. Functional Test Cases
- Positive
- Negative

### 10.3. Non-Functional Test Cases — CÓ ĐIỀU KIỆN

- Performance
- Security
- Usability
- Compatibility
- Reliability

**Nhóm này KHÔNG bắt buộc.** Chỉ sinh test case cho một nhóm con khi **requirement có mô tả rõ ràng, kiểm chứng được** cho đúng nhóm đó:

| Nhóm | Chỉ sinh khi requirement nêu rõ |
|---|---|
| Performance | Ngưỡng cụ thể (thời gian phản hồi, số bản ghi, số user đồng thời) |
| Security | Quy tắc phân quyền, thời gian timeout, ràng buộc truy cập cụ thể |
| Usability | Yêu cầu về vị trí / cách hiển thị thông báo, thao tác bắt buộc |
| Compatibility | Danh sách trình duyệt / thiết bị / OS được hỗ trợ |
| Reliability | Yêu cầu về khôi phục lỗi, toàn vẹn dữ liệu, xử lý gián đoạn |

- **Requirement không mô tả → KHÔNG sinh test case cho nhóm đó.** Ghi 1 dòng vào `open_points.md` nêu nhóm bị bỏ và lý do (không có nguồn).
- **Cấm** sinh case NFR với Expected Result kiểu `Cần xác nhận` ở phần cốt lõi (ngưỡng, danh sách hỗ trợ) — case không kiểm chứng được thì không có giá trị chạy.
- Ưu tiên hoàn thiện Common + Functional trước; NFR chỉ bổ sung khi có nguồn.

## 11. Kỹ thuật thiết kế test cần áp dụng

Khi phù hợp, test case nên phản ánh ít nhất một hoặc nhiều kỹ thuật:
- Boundary Value Analysis
- Equivalence Partitioning
- Decision Table
- State Transition
- Exploratory / Ad-hoc

Nếu template không có cột riêng cho design technique:
- Không thêm cột mới
- Thể hiện kỹ thuật qua dữ liệu test, bước test và expected result

## 12. Tiêu chí bắt buộc với từng test case

Mỗi test case phải đảm bảo:
- Bao phủ requirement quan trọng và edge cases
- Dễ đọc, ngắn gọn, rõ ràng
- Ưu tiên dùng test data dạng tham số hóa
- Độc lập với test case khác
- Có expected result rõ ràng, xác định được pass/fail
- Phản ánh đúng logic nghiệp vụ
- Có thể thực hiện thủ công
- **4 cột `Preconditions` / `Steps` / `Test data` / `Expected Result` phải tách dòng theo từng ý và đánh số thứ tự** theo §14.0
- **Số dòng `Expected Result` khớp 1-1 với số dòng `Steps`** — lệch numbering coi như test case chưa đạt
- **Nội dung viết bằng tiếng Anh**, giữ nguyên văn nhãn màn hình / field / message / tên bảng·cột DB (§13A)
- **So sánh viết bằng ký hiệu** `<` `<=` `>` `>=` `=` `!=`, không diễn đạt bằng lời (§14.0b)
- **Không có dữ liệu đầu vào → ô `Test data` để trống**, không ghi ký tự lấp chỗ (§14.0c)

Không được dùng các câu:
- `tương tự test case trên`
- `như case trước`
- `same as above`

## 13. Mapping cột theo template công ty

Skill phải map dữ liệu vào template công ty theo header thực tế của file template.

Bộ cột logic tối thiểu phải hỗ trợ:
1. Classification 1
2. Classification 2
3. Classification 3
4. TC ID
5. Title
6. Priority
7. Preconditions
8. Steps
9. Test data
10. Expected Result

Nếu header trong template khác nhẹ về cách viết:
- Dùng header alias trong `testcase_project_profile.yaml`
- Không sửa header thật của template

## 13A. Ngôn ngữ output của test case

- **Nội dung 10 cột test case viết bằng TIẾNG ANH.** Áp dụng cho `Test subject` / `Title`, `Preconditions`, `Steps`, `Test data`, `Expected Result` và các giá trị `Classification` mang tính mô tả.
- **Giữ NGUYÊN VĂN, không dịch** các định danh sau — tester phải đối chiếu đúng chữ hiển thị trên màn hình / trong DB:
  - Tên màn hình, tab, section (VD: `基本情報編集`, `スケジュール`, `公開日程設定`)
  - Nhãn field, checkbox, button (VD: `公開期間 (開始日時)`, `事前登録`, `Apply`, `Cancel`)
  - Nội dung message hiển thị cho người dùng
  - Tên bảng · cột DB, tên API endpoint, tên tham số (VD: `GL_SALES_TERM.reserve_st_date`, `sales_kbn`)
  - Tên tham số hoá trong `Test data` (VD: `<valid_start_datetime>`)
- Cách viết: câu tiếng Anh bao quanh định danh gốc.
  - **Đúng**: `Tick 事前登録 checkbox and leave 公開期間 (開始日時) empty`
  - **Sai**: `Tick the first lottery round checkbox` (đã dịch nhãn → tester không dò được trên UI)
- Cần chú thích nghĩa cho định danh khó → mở ngoặc sau lần xuất hiện đầu tiên trong cùng ô: `事前登録 (1st lottery round)`. Không lặp lại chú thích ở các dòng sau.
- **Output phụ** (`testcase_generation_summary.md`, `testcase_traceability_matrix.md`, `open_points.md`) **KHÔNG** áp rule này — vẫn theo `project.output_language` trong manifest.

## 14. Quy tắc nội dung từng cột

### 14.0. Quy tắc format đa dòng (BẮT BUỘC cho 4 cột nội dung)

Áp dụng cho **`Preconditions`**, **`Steps`**, **`Test data`**, **`Expected Result`**:

- **Mỗi ý = 1 dòng riêng.** Cấm dồn nhiều ý vào cùng 1 dòng bằng dấu `;` hay `,`.
- **Mỗi dòng phải có số thứ tự** dạng `1.` `2.` `3.` ở đầu dòng.
- **Xuống dòng thật trong cùng 1 ô** (ký tự `\n` trong cell). **KHÔNG** tách thành nhiều row, **KHÔNG** tạo thêm cột.
- **Cấm** dùng bullet `-`, `•`, `*` thay cho số.
- Một ý chỉ có 1 dòng → vẫn phải đánh số `1.`.
- **Ngoại lệ duy nhất**: ô `Test data` của case không có dữ liệu đầu vào → **để trống hoàn toàn** (§14.0c).

#### Quy tắc mapping Steps ↔ Expected Result

- **Số dòng của `Expected Result` = số dòng của `Steps`**, khớp 1-1, cùng thứ tự.
- Dòng `n` của `Expected Result` là kết quả mong đợi của **đúng** dòng `n` trong `Steps`.
- Step không có kết quả quan sát được rõ ràng → **vẫn giữ dòng tương ứng**, ghi kết quả trung gian (VD: `2. Màn hình chuyển sang tab "Chi tiết", chưa có thông báo lỗi`). **Cấm** bỏ trống hoặc bỏ số để numbering bị lệch.
- Một step sinh nhiều kết quả cần verify → tách thành `2.1`, `2.2`, `2.3` **nằm dưới số `2`**, không đẩy sang số `3` (giữ nguyên mapping với step 2).

### 14.0b. Dùng ký hiệu so sánh, không diễn đạt bằng lời

Mọi quan hệ so sánh giữa 2 giá trị / 2 mốc thời gian phải viết bằng **ký hiệu**: `<` `<=` `>` `>=` `=` `!=`.

- Áp dụng cho: `Title` / `Test subject`, `Preconditions`, `Steps`, `Test data`, `Expected Result`.
- **Cấm** diễn đạt quan hệ bằng lời: "không sớm hơn", "sau khi", "trước", "vượt quá", "nằm trong quá khứ", "bằng đúng", "lớn hơn"…
- Viết dạng biểu thức đầy đủ **vế trái — ký hiệu — vế phải**, dùng đúng tên field gốc ở cả 2 vế.
- Ký hiệu phải phản ánh **đúng độ chặt** của ràng buộc trong requirement — `<` và `<=` là 2 case biên khác nhau, không được dùng lẫn.
- Ràng buộc kép viết nối: `情報公開日 <= 公開開始日時 < 公演開始日時`.

| Sai (diễn đạt bằng lời) | Đúng (ký hiệu) |
|---|---|
| `第3期間終了日時 không sớm hơn 公開開始日時` | `第3期間終了日時 >= 公開開始日時` |
| `公開開始日時 lớn hơn 公開終了日時` | `公開開始日時 > 公開終了日時` |
| `公開終了日時 bằng đúng 公演開始日時` | `公開終了日時 = 公演開始日時` |
| `公開終了日時 vượt quá 公演開始日時` | `公開終了日時 > 公演開始日時` |
| `公開開始日時 nằm trong quá khứ` | `公開開始日時 < 現在日時` |
| `第2期間開始日時 sau khi 第1期間終了日時` | `第2期間開始日時 > 第1期間終了日時` |

Trong `Expected Result`, khi nêu lý do chặn/cho phép thì trích thẳng ràng buộc dạng ký hiệu:
`System blocks saving — constraint is 公開開始日時 < 公開終了日時`.

### 14.0c. Ô Test data rỗng

- Test case **không có dữ liệu đầu vào** (case thuần điều hướng, thuần quan sát UI) → **để trống hoàn toàn ô `Test data`**.
- **Cấm** ghi ký tự lấp chỗ: `—`, `-`, `N/A`, `None`, `Không áp dụng`, `Không có`.
- Không chắc case có cần test data hay không → xem lại `Steps`: có giá trị nào người test phải nhập / chọn / truyền vào không. Không có → để trống.

#### Quy tắc đánh số của Preconditions / Test data

- `Preconditions` và `Test data` đánh số **độc lập**, **KHÔNG** map theo số của `Steps` — vì đây là điều kiện / dữ liệu đầu vào, không phải hành động tuần tự.

#### Ví dụ mẫu 1 test case

| Cột | Nội dung trong ô |
|---|---|
| TC ID | `TC005` |
| Title | `Account is locked when failed login count >= lock threshold` |
| Preconditions | `1. User <active_user> exists with status = active`<br>`2. Account lock threshold = 3 failed attempts`<br>`3. Failed login counter of <active_user> = 0` |
| Steps | `1. Open the Login screen`<br>`2. Enter <active_user> and <invalid_password>, then click "ログイン"`<br>`3. Repeat step 2 two more times (total failed attempts = 3)`<br>`4. Enter <active_user> and <valid_password>, then click "ログイン"` |
| Test data | `1. <active_user> = user01@example.com`<br>`2. <valid_password> = Abc@12345`<br>`3. <invalid_password> = Wrong@000` |
| Expected Result | `1. Login screen shows Email field, Password field and "ログイン" button`<br>`2. Authentication fails; failed login counter = 1`<br>`3.1. Failed login counter = 3 >= lock threshold, so the account is locked`<br>`3.2. Lock notification message is displayed`<br>`4. Login still fails although password = <valid_password>; lock notification message is displayed` |

Lưu ý ở ví dụ trên:
- `Steps` có 4 dòng → `Expected Result` có đúng 4 nhóm số `1.` `2.` `3.` `4.`; step 3 sinh 2 kết quả nên tách `3.1` / `3.2` chứ không đẩy thành `4.`.
- Nội dung tiếng Anh nhưng nhãn button `ログイン` giữ nguyên văn (§13A).
- Quan hệ so sánh viết bằng ký hiệu `>=`, `=` chứ không diễn đạt bằng lời (§14.0b).

### Classification 1
Một trong các giá trị:
- `Common Test Cases`
- `Functional Test Cases`
- `Non-Functional Test Cases`

### Classification 2
Ví dụ:
- `Trigger/Navigation`
- `UI`
- `Form Validation`
- `Positive`
- `Negative`
- `Performance`
- `Security`
- `Usability`
- `Compatibility`
- `Reliability`

### Classification 3
- Tên field
- Tên item màn hình
- Tên function nhỏ
- Tên endpoint
- Tên process
- Nếu không có thì dùng `General`

### TC ID
- Theo format tăng dần: `TC001`, `TC002`, ...
- Không trùng lặp trong cùng module

### Title
- Ngắn gọn
- Dễ hiểu
- Phân biệt được với các case khác

### Priority
- `High`
- `Medium`
- `Low`

### Preconditions
- Chỉ ghi điều kiện thực sự cần trước khi test
- Không nhắc lại steps
- **Mỗi điều kiện 1 dòng, đánh số `1.` `2.` `3.`** theo §14.0
- Đánh số độc lập, không map với `Steps`

### Steps
- Viết theo từng bước rõ ràng
- Mỗi case độc lập
- **Mỗi bước 1 dòng, đánh số `1.` `2.` `3.`** theo §14.0
- Mỗi dòng chỉ chứa **1 hành động** — hành động ghép (nhập + bấm) chỉ được gộp khi cùng phục vụ 1 kết quả kiểm chứng
- Số dòng ở đây quyết định numbering của `Expected Result`

### Test data
- Ưu tiên dữ liệu tham số hóa
- **Mỗi mục dữ liệu 1 dòng, đánh số `1.` `2.` `3.`** theo §14.0
- Đánh số độc lập, không map với `Steps`
- Ghi dạng `<tên_tham_số> = giá trị` khi đã xác định được giá trị cụ thể
- **Case không có dữ liệu đầu vào → để trống hoàn toàn ô**; cấm `—` / `N/A` / `Không áp dụng` (§14.0c)
- Ví dụ:
  - `<valid_name>`
  - `<empty_required_field>`
  - `<max_length_255>`
  - `<invalid_special_characters>`
  - `<expired_session_user>`

### Expected Result
- Có kết quả mong đợi rõ ràng
- Xác định được pass/fail
- Đúng logic nghiệp vụ và validation
- **Mỗi kết quả 1 dòng, đánh số `1.` `2.` `3.`** theo §14.0
- **Số dòng phải map 1-1 với `Steps`**: dòng `n` là kết quả của bước `n`
- 1 bước sinh nhiều kết quả → tách `n.1`, `n.2` dưới cùng số `n`, không nhảy sang số kế tiếp

## 15. Workflow thực thi

### Phase 1 — Nạp cấu hình và source
- Đọc `module_name`
  - Thiếu hoặc là placeholder → chạy **module discovery** theo §5A.2, DỪNG hỏi người dùng chọn, không đi tiếp Phase 2
- **Module scoping** theo §5A.3: chốt phạm vi FR/BR/VR thuộc module, ghi rõ phần bị loại và lý do
- Đọc manifest
- Đọc profile
- Kiểm tra template local tại `<skill_dir>/templates/template_testcase.xlsx` (xem §8)
- Kiểm tra `google_master_template_file_id`
- Kiểm tra source requirement liên quan
- Ghi nhận access issue nếu có

### Phase 2 — Phân tích requirement cho test design
- Trích xuất function name
- Actor
- Goal
- Main flow
- Alternate / exception flow
- Business rules
- Validation rules
- Open points có ảnh hưởng tới test design

### Phase 3 — Lập test inventory
- Liệt kê vùng cần test
- Mapping field / action / role / state / integration / impact
- Xác định coverage mục tiêu

### Phase 4 — Thiết kế test cases
Sinh test case theo đúng thứ tự:
1. Common Test Cases
2. Functional Test Cases
3. Non-Functional Test Cases

### Phase 5 — Gán priority
Ưu tiên `High` cho:
- Main flow
- Validation critical
- Permission
- Security
- Data integrity
- State transition critical
- Dependency impact lớn

### Phase 6 — Lập traceability
Map từng test case về:
- FR
- BR
- VR
- Source ID
- Source reference

### Phase 7 — Tạo Google Sheet output
- Duplicate từ `google_master_template_file_id`
- **Đúng 1 Sheet cho đúng 1 module** — cấm tạo nhiều Sheet hoặc gộp module (§5A.1)
- Đổi tên file theo naming convention
- Ghi data test case vào worksheet đúng cấu hình
- Preserve format template ở mức tối đa
- **Ghi ký tự xuống dòng thật trong ô** cho 4 cột `Preconditions` / `Steps` / `Test data` / `Expected Result` (§14.0) — dùng `\n` trong giá trị cell, không tách thành nhiều row
- **Bật wrap text** cho 4 cột này để nội dung nhiều dòng hiển thị đầy đủ
- Không thêm / bớt / đổi thứ tự cột khi áp dụng format đa dòng
- **Verify trước khi kết thúc Phase 7**: với mỗi row, số dòng `Expected Result` khớp số dòng `Steps`; lệch → sửa lại test case, không xuất Sheet lỗi

### Phase 8 — Xuất output phụ
- Xuất `testcase_generation_summary.md`
- Xuất `testcase_traceability_matrix.md`
- Xuất `open_points.md`

## 16. Quy tắc coverage tối thiểu

### 16.1. Bắt buộc — luôn phải có
- Navigation / trigger
- UI cơ bản nếu là module có UI
- Validation theo field
- Positive flow
- Negative flow
- Boundary cases
- Invalid input cases
- **Data persistence theo từng trường** (§16A)

### 16.2. Có điều kiện — chỉ khi requirement mô tả rõ
- Authorization / permission — cần mô tả phân quyền theo vai trò
- Security / session timeout — cần mô tả quy tắc truy cập, thời gian timeout
- Performance / Compatibility / Usability / Reliability — theo bảng điều kiện ở §10.3
- Impact / dependency-related cases — chỉ khi có dấu hiệu ảnh hưởng rõ trong `impact_scope.md`

Hạng mục ở §16.2 không có nguồn → **không sinh case**, ghi vào `open_points.md`.

## 16A. Test case lưu dữ liệu xuống DB (BẮT BUỘC)

Bộ test case phải có nhóm case kiểm chứng **dữ liệu được lưu đúng xuống database**.

### 16A.1. Nguyên tắc

- **Mỗi trường được persist = 1 test case ĐỘC LẬP.** Cấm gộp nhiều trường vào 1 case.
- Case nằm ở `Classification 1` = `Functional Test Cases`, `Classification 2` = `Positive`.
- `Classification 3` = **tên field trên màn hình** (VD: `公開期間 (開始日時)`).
- Expected Result phải nêu **đúng bảng · đúng cột · đúng giá trị**, dạng `<TABLE>.<column> = <value>`.
- Verify bằng cách mở lại màn hình **hoặc** query DB — ghi rõ cách verify trong `Steps`.

### 16A.2. Mỗi case cần cover

1. Giá trị hợp lệ được ghi đúng cột.
2. Giá trị hiển thị lại đúng khi mở lại màn hình (round-trip).
3. Các cột phụ thuộc trường đó (flag, kbn, timestamp) nhận đúng giá trị, nếu requirement có mô tả.

### 16A.3. Ví dụ

| Cột | Nội dung |
|---|---|
| Classification 3 | `公開期間 (開始日時)` |
| Title | `公開期間 (開始日時) is persisted to GL_SALES_TERM.reserve_st_date` |
| Steps | `1. Tick 事前登録 checkbox`<br>`2. Set 公開期間 (開始日時) = <valid_start_datetime>`<br>`3. Save the screen`<br>`4. Query GL_SALES_TERM where sales_kbn = 4`<br>`5. Reopen the スケジュール tab` |
| Expected Result | `1. 事前登録 checkbox is checked`<br>`2. The field shows <valid_start_datetime>`<br>`3. Save completes without error`<br>`4. GL_SALES_TERM.reserve_st_date = <valid_start_datetime>`<br>`5. 公開期間 (開始日時) = <valid_start_datetime>` |

### 16A.4. Khi thiếu thông tin mapping

- Không xác định được field ↔ bảng · cột → **ghi vào `open_points.md`**, KHÔNG đoán tên bảng/cột.
- Vẫn sinh case round-trip qua UI (nhập → lưu → mở lại) vì không phụ thuộc tên cột.
- Module không persist dữ liệu (màn hình chỉ hiển thị) → bỏ nhóm này, ghi rõ lý do trong `testcase_generation_summary.md`.

## 17. Quy tắc với module non-UI

Nếu module là API, batch, event hoặc scheduler:
- `Classification 3` có thể là endpoint, payload field, event name hoặc process name
- Không bắt buộc có UI cases nếu không liên quan
- Vẫn phải có Positive, Negative và data persistence theo từng trường (§16A)
- Security / Reliability chỉ sinh khi requirement mô tả rõ, theo bảng điều kiện §10.3

## 18. Quy tắc với requirement chưa rõ

Nếu requirement thiếu:
- không tự suy diễn
- ghi vào `open_points.md`
- vẫn sinh test cases cho phần đã xác định được
- không viết expected result khẳng định sai logic

## 19. Output bắt buộc

### Output chính
- 01 Google Spreadsheet riêng cho mỗi chức năng
- File được tạo bằng cách duplicate từ Google Sheet master template
- File chứa 01 worksheet chính để nhập manual test cases

### Output phụ
- `<output_root>/<module_name>/testcase_generation_summary.md`
- `<output_root>/<module_name>/testcase_traceability_matrix.md`
- `<output_root>/<module_name>/open_points.md`

### Evidence
- `<evidence_root>/<module_name>/source_snapshots/`
- `<evidence_root>/<module_name>/analysis_notes/`
- `<evidence_root>/<module_name>/access_issues/`

## 20. Tiêu chí hoàn tất

Skill hoàn tất khi:
- Đã phân tích requirement ở mức phục vụ test design
- Đã tạo 1 file Google Sheet riêng cho module
- Đã ghi test case vào đúng worksheet của template
- Classification đúng thứ tự
- TC ID tăng dần, không trùng
- Có traceability cho test case quan trọng
- Có open points nếu requirement chưa rõ
- Không có nội dung bịa

## 21. Rules

- Không bịa nghiệp vụ
- Không tạo test case trùng ý nghĩa
- Không để test case phụ thuộc nhau
- Không đổi template công ty nếu không có yêu cầu rõ ràng
- Không thêm cột ngoài template nếu chưa được phép
- Ưu tiên độ đúng và khả năng review hơn số lượng
- **1 module = 1 Google Sheet.** Cấm gộp module, cấm gen toàn bộ dự án dù source phủ rộng (§5A)
- **Không có tên module trên dòng lệnh → LUÔN hiển thị bảng danh sách chức năng rồi DỪNG hỏi**, bất kể manifest ghi gì; `run.module_name` không được dùng để chọn module (§5A.2)
- Chức năng module khác chỉ nằm ở `Preconditions` / `Test data`, không tạo test case riêng (§5A.3)
- **`Preconditions` / `Steps` / `Test data` / `Expected Result` luôn tách dòng theo từng ý + đánh số thứ tự; cấm dồn nhiều ý vào 1 dòng, cấm dùng bullet thay số (§14.0)**
- **Numbering `Expected Result` phải map 1-1 với `Steps`**; step nhiều kết quả → `n.1` / `n.2`, không nhảy số (§14.0)
- **Nội dung test case viết bằng tiếng Anh**; nhãn màn hình / field / button / message / tên bảng·cột DB giữ nguyên văn, không dịch (§13A)
- **Mọi so sánh dùng ký hiệu** `<` `<=` `>` `>=` `=` `!=` với đủ vế trái · vế phải; cấm "không sớm hơn", "sau khi", "vượt quá"… (§14.0b)
- **Non-Functional chỉ sinh khi requirement mô tả rõ**; không nguồn → không sinh case, ghi `open_points.md`; cấm case NFR có ngưỡng `Cần xác nhận` (§10.3)
- **Case không có dữ liệu đầu vào → ô `Test data` để trống hoàn toàn**; cấm `—` / `N/A` / `Không áp dụng` (§14.0c)
- **Bắt buộc có case lưu DB theo từng trường**, mỗi trường 1 case độc lập, Expected Result nêu đúng `<TABLE>.<column> = <value>` (§16A)