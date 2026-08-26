---
name: gen-test-plan
description: "[personal] Sinh Master Test Plan cho cả dự án theo chuẩn ISTQB (CTFL v4.0 §5 Test Management) + IEEE 829, xuất ra 1 Google Sheet duplicate từ master template import từ file template_testplan.xlsx (TEM-ST02-01) đi kèm skill. Phủ đủ 12 sheet: Cover, Introduction, Scope test, Test Approach/Strategy (+ guideline 15 test type), Resources, Test Environment, Criteria (entry/exit/suspension), Estimation & Schedule, Deliverables, Risk management. Chạy được ngay khi có tài liệu nghiệp vụ (設計書/spec/ticket/project plan) — không cần chờ xong requirement hay test case. Triggers (VI): 'gen test plan', 'tạo test plan', 'lập kế hoạch test', 'viết test plan', 'master test plan'."
---

# Skill: gen-test-plan

## 1. Mục tiêu

- Sinh **Master Test Plan cấp dự án** theo chuẩn ISTQB + IEEE 829, đúng template công ty `TEM-ST02-01`
- Phân tích nguồn đầu vào ở mức phục vụ **test planning** (không phải test design)
- Xác định: test objective, test scope (in/out), test basis, test level × test type, entry/exit/suspension criteria, resource, environment, estimation, deliverable, risk
- Tạo 1 Google Sheet riêng cho dự án bằng cách duplicate từ Google Sheet master template
- Đổ dữ liệu vào **đúng 12 sheet, đúng ô** của template, preserve format và formula
- Ghi rõ mọi điểm chưa đủ thông tin thành `Cần xác nhận` + `open_points.md`, tuyệt đối không bịa

## 2. Phạm vi của skill

Sinh Master Test Plan cho:
- Dự án phát triển mới
- Enhancement / change request theo release
- Dự án maintenance có chu kỳ regression
- Dự án migration / conversion

**KHÔNG** thuộc phạm vi skill này:
- Test case chi tiết → dùng `gen-testcase`
- Requirement package → dùng `gen-requirement`
- Bảng effort chi tiết theo activity → dùng `estimate-test`
- Test report / summary report

## 3. Dependency với các skill khác

| Skill | Vai trò với gen-test-plan |
|---|---|
| `gen-requirement` | Nguồn cho 2.1 · 2.2 · 2.3 · 2.5 · 2.6 · 1.4 References · risk sản phẩm |
| `estimate-test` | Nguồn số liệu effort cho sheet `07_Estimation & Schedule` |
| `gen-testcase` | Nguồn xác định testware thực tế cho 3.1 và `08_Deliverables` |

Chưa có output của các skill trên → skill vẫn chạy được, dùng trực tiếp 設計書 / spec / ticket /
project plan. Mọi suy luận thiếu căn cứ phải vào `open_points.md`.

## 4. Cách gọi skill

`/gen-test-plan <project_name>`

Hoặc:

`/gen-test-plan <project_name> --manifest ./inputs/testplan_source_manifest.yaml`

`/gen-test-plan <project_name> --manifest ./inputs/testplan_source_manifest.yaml --profile ./configs/testplan_project_profile.yaml`

Ví dụ:
- `/gen-test-plan <ten-du-an>`
- `/gen-test-plan <ten-du-an> --manifest ./inputs/testplan_source_manifest.yaml`

## 5. Input

| Biến | Mô tả | Default |
|---|---|---|
| `$1` | Project name | — (bắt buộc, xem §5A.2) |
| `MANIFEST_PATH` | File khai báo source đầu vào | `./inputs/testplan_source_manifest.yaml` |
| `PROFILE_PATH` | File cấu hình quy tắc dự án | `./configs/testplan_project_profile.yaml` |
| `OUTPUT_ROOT` | Thư mục output phụ | `testplans` |
| `EVIDENCE_ROOT` | Thư mục evidence | `evidence_testplan` |

Manifest tối thiểu:

```yaml
manifest_version: "1.0"
run:
  created_by: "<email-cua-ban>@nal.vn"
  reviewer: ""                     # ghi vào Cover!E10
  purpose: "Master Test Plan cấp dự án theo chuẩn ISTQB + IEEE 829"
project:
  project_code: "PRJ"
  project_name: "Sample Project"
  version: "1.0"                   # version test plan, ghi vào Cover!E6
  release_scope: ["Release 1"]
  output_language: "vi"
google:
  master_template_file_id: ""      # id Google Sheet master template (import 1 lần từ xlsx)
  master_template_source_file: "templates/template_testplan.xlsx"
  target_drive_folder_id: ""       # id folder Drive của dự án
  spreadsheet_name_pattern: "TEM-ST02-01_Test Plan_{project_name}_v{version}"
sources:
  - id: "SRC-DOC-01"
    type: "design_doc"          # design_doc | spec | ticket | project_plan | org_process | module_registry | requirement_package | testcase_output | estimate_output | test_environment | qna_log | figma | api_spec | db_schema
    path: "inputs/..."
    version: ""
    provides: ["test_basis", "feature_scope"]
    priority: 1
registry:
  path: "configs/module_registry.yaml"
  read_only: true                  # test plan chỉ ĐỌC registry, không cập nhật status
context:
  plan_level: "master"
  product_has_ui: true
  is_enhancement: false            # true => bắt buộc có Regression Testing
access_issues: []
```

## 5A. Quy tắc phạm vi: 1 lần chạy = 1 Master Test Plan = 1 Google Sheet

Quy tắc **cao nhất**, override mọi phần còn lại khi có mâu thuẫn.

### 5A.1. Nguyên tắc

- **1 lần chạy sinh ĐÚNG 1 Master Test Plan** cho **ĐÚNG 1 dự án**, xuất ra **đúng 1 Google Sheet**.
- Master Test Plan **phủ toàn bộ dự án và mọi test level** — đây là điểm **khác** `gen-testcase` (1 module = 1 Sheet). Không tách plan theo module, không tách theo test level.
- Cấm tạo nhiều Sheet trong một lần chạy. Cấm gộp 2 dự án vào 1 Sheet.
- Output phụ chỉ ghi vào `<output_root>/<project_name>/` và `<evidence_root>/<project_name>/`.

### 5A.2. Thiếu `project_name` — DỪNG hỏi, không tự suy

`$1` trống → **KHÔNG** tự suy project name từ manifest, tên workspace, tên folder, git remote hay
ngữ cảnh hội thoại. Các bước:

1. Đọc `configs/module_registry.yaml` (nếu có) và mục lục các source đã khai trong manifest — chỉ ở **mức khung**, cấm đọc chi tiết flow / business rule / validation.
2. Trình bày thông tin suy được: tên dự án ứng viên, danh sách module/chức năng phát hiện được, các release/milestone thấy trong source.
3. **DỪNG hỏi user xác nhận 3 thứ**: `project_name` · `version` · `release_scope`.
4. Có xác nhận → chạy tiếp Phase 1. Chưa có → không tạo Sheet, không sinh file nào.

### 5A.3. Ranh giới nội dung

- Sheet `02_Scope test` 2.3 liệt kê **toàn bộ** tính năng phải test của dự án; 2.4 liệt kê tính năng KHÔNG test **kèm lý do**.
- Tính năng của hệ thống khác / dự án khác chỉ được xuất hiện ở 2.6 (ràng buộc) hoặc `09_Risk management`, không đưa vào 2.3.
- Cấm chép nội dung test case chi tiết vào test plan. Test plan chỉ mô tả **phương pháp** (3.1) và **mức độ** (3.2).

## 6. Nguồn đầu vào hỗ trợ

設計書 · requirement document · spec · ticket · project plan · WBS · Figma · API spec · DB schema ·
workflow diagram · meeting note · Q&A log · requirement package của `gen-requirement` ·
test case Sheet của `gen-testcase` · estimate Sheet của `estimate-test` · log effort dự án trước ·
quy trình test của tổ chức.

## 7. Ưu tiên nguồn

Khi các nguồn xung đột, lấy theo thứ tự giảm dần:
1. Project plan / hợp đồng / SOW đã chốt (scope, release, milestone, nhân sự)
2. Requirement package của `gen-requirement`
3. 設計書 / spec / API spec / DB schema
4. Ticket · Q&A log · meeting note (thông tin mới nhất theo thời gian)
5. Figma · workflow diagram
6. Source code (chỉ dùng khi reverse engineering)

Xung đột không tự giải quyết được → ghi cả 2 phiên bản vào `open_points.md`, ô tương ứng ghi
`Cần xác nhận`. **Cấm** tự chọn im lặng.

## 8. Excel / Google Sheet Template Policy

Template gốc của công ty đi kèm ngay trong skill này, tại:
- `<skill_dir>/templates/template_testplan.xlsx`

Trong đó `<skill_dir>` là thư mục chứa chính file `SKILL.md` này — hiện tại là
`~/.claude/skills/gen-test-plan/`. KHÔNG dùng path tương đối `./templates/...` vì nó resolve theo
working directory của project đang mở, nên sẽ trỏ sai khi skill được gọi từ project khác.

Nguyên tắc vận hành:
- File xlsx là template nguồn của công ty (`TEM-ST02-01`), **read-only**, cấm sửa
- Template nguồn cần được import lên Google Drive **1 lần** để tạo Google Sheet master template
- Mỗi lần sinh test plan, skill tạo 1 file Google Sheet mới bằng cách **duplicate** master template
- File mới đặt vào folder Drive của dự án theo `google.target_drive_folder_id`
- Tên file theo `google.spreadsheet_name_pattern`
- Chỉ ghi vào các ô khai trong `references/template-cell-map.md`
- **Cấm** đổi tên sheet, đổi tên cột, thêm/bớt/đổi thứ tự cột, xoá dòng, xoá formula
- Sheet `Table of content` giữ nguyên 100%
- Thiếu `master_template_file_id` **hoặc** `target_drive_folder_id` → ghi nhận `Cần xác nhận`, **vẫn xuất đủ output phụ**, dừng ở bước tạo Google Sheet và báo user cần cung cấp id nào

## 9. Phân tích nguồn phục vụ test planning

Trước khi ghi Sheet, phải trích xuất được:
- Sản phẩm / hệ thống đang test + version + release scope
- Mục tiêu chất lượng và mục tiêu testing
- Danh sách chức năng trong scope · ngoài scope + lý do
- Test basis: tài liệu nào là cơ sở kiểm thử, version nào
- Kiến trúc mức khung: có UI không, có API không, có DB không, có batch không, có tích hợp bên thứ ba không
- Yêu cầu phi chức năng **kèm ngưỡng số cụ thể** (nếu có)
- Ma trận OS / browser / device phải hỗ trợ
- Nhân sự: ai làm gì, level, site
- Môi trường: hardware, software, tool, infrastructure
- Mốc thời gian: release date, code freeze, test window
- Giả định · ràng buộc · rủi ro đã biết

Điểm không rõ → **không tự bịa**, ghi `open_points.md`.

## 10. Nội dung chuẩn theo ISTQB

**BẮT BUỘC đọc `references/istqb-alignment.md`** trước khi soạn nội dung. File đó quy định:
- Bảng đối chiếu nội dung ISTQB ↔ sheet template (§1) — mọi mục phải có nội dung
- Cách viết Định danh test plan (§2)
- Điều kiện chọn test level (§3) và test type (§4) — **có bằng chứng mới được đưa vào plan**
- Nội dung tối thiểu của entry/exit/suspension criteria kèm ngưỡng đo được (§5)
- Công thức mức độ rủi ro `Khả năng × Ảnh hưởng` và yêu cầu mitigation có chủ thể (§6)
- Nguồn số liệu estimation (§7)
- Yêu cầu traceability (§8)

## 11. Mapping ô theo template công ty

**BẮT BUỘC đọc `references/template-cell-map.md`** trước khi ghi bất kỳ ô nào. File đó chứa
anchor chính xác (`header_row`, `data_from`, `data_to`, cột) cho cả 12 sheet, cùng danh sách
formula bắt buộc giữ ở sheet `07_Estimation & Schedule`.

Quy tắc chống lệch mapping:
- Trước khi ghi 1 bảng, **verify header thật** ở `header_row` khớp mô tả trong cell map. Lệch → dừng, báo user template đã đổi, cấm ghi mò.
- Data vượt vùng có sẵn → insert row trước `data_to`, copy format từ dòng liền trên.
- Data ít hơn vùng có sẵn → để trống dòng còn lại, cấm xoá dòng.

## 12. Ngôn ngữ output

- **Nội dung test plan viết bằng TIẾNG VIỆT**, khớp với heading và guidance tiếng Việt của template.
- **Giữ NGUYÊN VĂN, không dịch** các định danh sau:
  - Tên màn hình · tab · section (vd `基本情報編集`, `公開日程設定`)
  - Nhãn field · button · message hiển thị
  - Tên bảng · cột DB, API endpoint, tham số (vd `GL_SALES_TERM.reserve_st_date`)
  - Tên môi trường · server · tool · branch (vd `stg-01`, `Robot Framework`)
  - Tên test type / test level theo template (`Functional Test`, `Intergration`, `Acceptance`) — giữ đúng chữ template, kể cả typo có sẵn
- Cần chú thích định danh khó → mở ngoặc **lần xuất hiện đầu tiên** trong cùng ô: `事前登録 (vòng xổ số thứ nhất)`.
- Output phụ (`.md`) theo `project.output_language` trong manifest, default `vi`.

## 13. Quy tắc nội dung chung

### 13.1. Format nhiều dòng
- Ô có nhiều ý → **1 ý / 1 dòng, đánh số `1.` `2.` `3.`**, dùng ký tự xuống dòng thật trong ô (`\n`), **bật wrap text**.
- Cấm dồn nhiều ý vào 1 dòng. Cấm tách 1 ý thành nhiều row.

### 13.2. Ngưỡng và so sánh
- Mọi ngưỡng dùng **ký hiệu + đủ 2 vế**: `pass rate >= 95%`, `Critical bug = 0`, `response time <= 2s`.
- Cấm diễn đạt bằng lời: "hầu hết pass", "không còn bug nghiêm trọng", "phản hồi nhanh".

### 13.3. Thiếu thông tin
- Ô bắt buộc mà thiếu thông tin → ghi đúng chuỗi `Cần xác nhận` + 1 dòng nêu thiếu gì.
- Đồng thời **bắt buộc** thêm 1 entry vào `open_points.md`.
- Cấm ghi `N/A` / `—` / `TBD` / để trắng cho ô bắt buộc.

### 13.4. Ngày tháng và số
- Ngày: `YYYY-MM-DD`. Effort: giờ (`h`), số thập phân 1 chữ số.
- Cấm ngày tương đối ("tuần sau", "cuối sprint") — quy về ngày tuyệt đối, không suy được thì `Cần xác nhận`.

## 14. Quy tắc mục / test type không áp dụng

- Sheet `03_1_Test ApproachStr`: test type **có** trong matrix 3.2 → fill 4 ô (`Mục tiêu` · `Kỹ thuật/Cách thức` · `Tiêu chí hoàn thành` · `Các cân nhắc/lưu ý`) bằng nội dung riêng của dự án, ghi đè guidance `{...}`.
- Test type **không** trong matrix 3.2 → **để nguyên guidance `{...}`**, cấm xoá, cấm ghi `Không áp dụng`. Đã-fill = trong scope, còn-`{...}` = ngoài scope; đây là quy ước tự mô tả.
- `08_Deliverables`: deliverable không bàn giao → giữ dòng, cột `F` (Status) = `Không áp dụng`, cột `E` để trống.
- `09_Risk management`: rủi ro catalog không áp dụng → cột `Q` (Tình trạng) = `Không áp dụng`, cột `R` ghi lý do.
- Danh sách test type đã fill vs để nguyên **bắt buộc** liệt kê trong `testplan_generation_summary.md`.

## 15. Workflow thực thi

### Phase 1 — Nạp cấu hình và source
- Đọc `project_name`; trống → chạy §5A.2, DỪNG hỏi, không đi tiếp
- Đọc manifest, profile
- Đọc `references/template-cell-map.md` và `references/istqb-alignment.md`
- Kiểm tra template local `<skill_dir>/templates/template_testplan.xlsx`
- Kiểm tra `google.master_template_file_id` và `google.target_drive_folder_id`
- Kiểm tra truy cập từng source, ghi access issue vào `<evidence_root>/<project_name>/access_issues/`

### Phase 2 — Phân tích nguồn cho test planning
Trích xuất đủ 12 nhóm thông tin ở §9. Ghi note vào `<evidence_root>/<project_name>/analysis_notes/`.

### Phase 3 — Chốt scope
- Lập danh sách tính năng PHẢI test (view USER) + tính năng KHÔNG test + lý do
- Lập danh sách test items (view kỹ thuật)
- Chốt giả định, ràng buộc
- Map từng tính năng về source ID → dữ liệu cho traceability matrix

### Phase 4 — Chốt strategy
- Viết narrative test strategy (3.0) khớp cấp Master Test Plan
- Gán phương pháp test cho từng tính năng (3.1): `Full test case` / `Full check list` / `Free test`, nêu căn cứ (effort · rủi ro · AC)
- Dựng matrix test level × test type (3.2) theo điều kiện §3–§4 của `istqb-alignment.md`
- Fill `03_1` cho các test type đã chọn (§14)

### Phase 5 — Chốt resource · environment · criteria
- 04: nhân sự, role, trách nhiệm, site, kế hoạch training
- 05: hardware · software · infrastructure kèm số lượng và thời gian sử dụng
- 06: exit criteria + suspension/resumption criteria, **mọi tiêu chí có ngưỡng đo được** (§5 `istqb-alignment.md`)

### Phase 6 — Estimation · deliverables · risk
- 07: đổ effort theo §7 `istqb-alignment.md`, giữ đủ formula, `Actual`/`Status` để trống
- 08: chốt danh mục testware bàn giao + ngôn ngữ + ngày
- 09: điền mức độ theo công thức `Khả năng × Ảnh hưởng`, mitigation có chủ thể; rủi ro `Cao` phải thấy tác động ngược lại vào 3.1/3.2/07

### Phase 7 — Tạo Google Sheet output
- Duplicate từ `google.master_template_file_id` vào folder `google.target_drive_folder_id`
- **Đúng 1 Sheet cho đúng 1 dự án** (§5A.1)
- Đổi tên theo `spreadsheet_name_pattern`
- Ghi data theo `template-cell-map.md`; verify header trước mỗi bảng (§11)
- Bật wrap text cho mọi ô nội dung nhiều dòng
- **Verify trước khi kết thúc Phase 7**:
  1. 12 sheet đủ, tên sheet không đổi
  2. Không sheet nào (trừ `Table of content`) còn trắng hoàn toàn
  3. Sheet 07 còn đủ formula `S` · `AB` · `AC` mọi dòng data + dòng `Total` row 20
  4. Mọi tính năng ở 2.3 đều có phương pháp test ở 3.1
  5. Mọi test type tick `x` ở 3.2 đều đã fill nội dung ở `03_1`
  6. Mọi tiêu chí ở 6.1 · 6.2 đều có ngưỡng dạng ký hiệu
  7. Mọi rủi ro có `Mức độ` + `Tình trạng` + `Biện pháp`
  Lệch bất kỳ mục nào → sửa, cấm xuất Sheet lỗi

### Phase 8 — Xuất output phụ
- `testplan_generation_summary.md`
- `testplan_traceability_matrix.md`
- `open_points.md`

## 16. Output bắt buộc

### Output chính
- 01 Google Spreadsheet Master Test Plan cho dự án, duplicate từ master template, nằm trong folder Drive của dự án

### Output phụ
- `<output_root>/<project_name>/testplan_generation_summary.md` — nguồn đã dùng · test level & test type đã chọn + căn cứ · test type để nguyên guidance · số liệu effort và nguồn · link Sheet
- `<output_root>/<project_name>/testplan_traceability_matrix.md` — tính năng (2.3) ↔ source ID (1.4) ↔ phương pháp test (3.1) ↔ test level/type (3.2)
- `<output_root>/<project_name>/open_points.md`

Format bắt buộc mỗi entry `open_points.md`:

```markdown
### OP-01 — <câu hỏi cần chốt>
- Ảnh hưởng tới: <sheet · mục · ô>
- Khuyến nghị: <phương án nên chọn>
- Hệ quả nếu chọn sai: <tác động cụ thể lên plan / effort / chất lượng>
- Độ tin cậy: Cao | Trung bình | Thấp
```

### Evidence
- `<evidence_root>/<project_name>/source_snapshots/`
- `<evidence_root>/<project_name>/analysis_notes/`
- `<evidence_root>/<project_name>/access_issues/`

## 17. Tiêu chí hoàn tất

- Đã phân tích nguồn ở mức phục vụ test planning (§9)
- Đã tạo đúng 1 Google Sheet cho dự án (hoặc ghi `Cần xác nhận` khi thiếu Drive id, kèm đủ output phụ)
- 12 sheet đúng tên, đúng cột, đúng formula; không sheet nào bị trắng
- Test level · test type đều có bằng chứng, không có NFR với ngưỡng `Cần xác nhận`
- Entry/exit/suspension criteria đều đo được
- Mọi rủi ro có mức độ suy ra được + mitigation có chủ thể
- Traceability đầy đủ, mọi tính năng ở 2.3 truy được về source và có phương pháp test
- Có `open_points.md` đúng format khi còn điểm chưa rõ
- Không có nội dung bịa

## 18. Rules

- Không bịa nghiệp vụ, không bịa ngưỡng, không bịa nhân sự · môi trường · ngày tháng
- Không sửa template công ty: cấm đổi tên sheet/cột, thêm/bớt/đổi thứ tự cột, xoá dòng, xoá formula (§8)
- **1 lần chạy = 1 Master Test Plan = 1 Google Sheet.** Master plan phủ toàn dự án và mọi test level — khác `gen-testcase` (1 module = 1 Sheet) (§5A.1)
- **Thiếu `project_name` → DỪNG hỏi user xác nhận `project_name` · `version` · `release_scope`**, cấm tự suy từ manifest / tên folder / git remote (§5A.2)
- **Verify header thật trước khi ghi mỗi bảng**; lệch cell map → dừng và báo, cấm ghi mò (§11)
- **Nội dung tiếng Việt**; tên màn hình · field · message · bảng·cột DB · API · tool · test type theo template giữ nguyên văn (§12)
- **Mọi ngưỡng dùng ký hiệu** `<` `<=` `>` `>=` `=` `!=` với đủ 2 vế; cấm "hầu hết", "không còn bug nghiêm trọng" (§13.2)
- **Ô bắt buộc thiếu thông tin → `Cần xác nhận` + entry trong `open_points.md`**; cấm `N/A` / `—` / `TBD` / để trắng (§13.3)
- **Test level · test type chỉ vào plan khi có bằng chứng**; NFR không có ngưỡng số → không đưa vào, ghi `open_points.md` (§4 `istqb-alignment.md`)
- **Test type ngoài scope → để nguyên guidance `{...}` ở `03_1`**, cấm xoá, cấm ghi `Không áp dụng` (§14)
- **Sheet 07 chỉ điền cột Plan**; `Actual effort` và mọi `Status` để trống, giữ nguyên formula và dòng `Total` (§`template-cell-map.md`)
- **Rủi ro mức `Cao` phải có tác động thấy được** vào 3.1 / 3.2 / sheet 07; không có → ghi `open_points.md` (§6 `istqb-alignment.md`)
- Nguồn xung đột → ghi cả 2 phiên bản vào `open_points.md`, cấm tự chọn im lặng (§7)
- Ưu tiên độ đúng và khả năng review hơn độ dài nội dung
