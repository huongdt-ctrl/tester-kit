---
name: gen-requirement
description: "[personal] Sinh bộ tài liệu requirement chuẩn hóa cho một module, screen hoặc function bằng cách phân tích nhiều nguồn đầu vào như requirement doc, ticket, figma, api spec, db schema, workflow diagram và các tài liệu liên quan."
---

# Skill: gen-requirement

Skill này dùng để sinh bộ tài liệu requirement chuẩn hóa cho một chức năng, màn hình hoặc module của bất kỳ dự án nào, dựa trên nhiều loại nguồn đầu vào khác nhau.

## 1. Mục tiêu

- Phân tích requirement từ nhiều nguồn đầu vào không đồng nhất
- Chuẩn hóa thông tin requirement theo cấu trúc dùng chung
- Sinh tài liệu self-contained để BA, Dev, QA có thể sử dụng trực tiếp
- Đảm bảo traceability từ nội dung sinh ra về đúng nguồn gốc
- Không suy diễn khi thiếu thông tin
- Ghi nhận rõ các điểm chưa chắc chắn hoặc cần xác nhận
- Đánh giá phạm vi ảnh hưởng sang các chức năng, màn hình, dữ liệu và luồng khác
- Tối ưu bộ output để đủ dùng nhưng không thừa file

## 2. Phạm vi áp dụng

Áp dụng cho:
- Web application
- Mobile application
- Admin portal
- Internal tool
- API module
- Batch / background process
- Feature enhancement
- New screen / new module
- Change request / bug fix có ảnh hưởng nghiệp vụ

## 3. Cách gọi skill

Invoked via:

`/gen-requirement <module_name>`

Hoặc:

`/gen-requirement <module_name> --manifest <source_manifest_path_or_url>`

Hoặc:

`/gen-requirement <module_name> --manifest <source_manifest_path_or_url> --project <project_code>`

Ví dụ:
- `/gen-requirement event_editing`
- `/gen-requirement lottery_management --manifest ./source_manifest.yaml`
- `/gen-requirement settlement_management --manifest https://example.com/source_manifest.yaml --project GL`

## 3A. Quy tắc phạm vi: 1 lần chạy = 1 module

Đây là quy tắc **cao nhất**, override mọi phần còn lại của skill khi có mâu thuẫn.

### 3A.1. Nguyên tắc

- **1 lần chạy chỉ xử lý ĐÚNG 1 module.** Cấm gộp nhiều module vào cùng một bộ output.
- **Cấm gen toàn bộ dự án** kể cả khi source (SRS, 設計書, ticket list) phủ nhiều module/màn hình. Source phủ rộng KHÔNG phải lý do để mở rộng phạm vi.
- Muốn làm nhiều module → chạy lại lệnh cho từng module, mỗi lần một `module_name`.
- Toàn bộ output chỉ được ghi vào `<output_root>/<module_name>/` và `<evidence_root>/<module_name>/`. **Cấm ghi hoặc ghi đè folder của module khác.**

### 3A.2. Không có tên module trên dòng lệnh — LUÔN hiển thị danh sách rồi DỪNG hỏi

**Điều kiện kích hoạt (quan trọng):** chạy module discovery khi **argument `$1` trống** — **bất kể manifest ghi gì**.

- `run.module_name` trong manifest **KHÔNG được dùng** để chọn module chạy. Nó chỉ là ghi chép, kể cả khi đang chứa một tên module hợp lệ.
- Chỉ **bỏ qua** discovery khi người dùng gõ rõ tên module: `/gen-requirement <module_name>`.
- Không được suy ra module từ: manifest, lần chạy trước, thư mục đã tồn tại trong `<output_root>`, hay ngữ cảnh hội thoại.

**Các bước:**

1. **Ưu tiên đọc module registry**: nếu tồn tại `configs/module_registry.yaml` (hoặc file registry do dự án khai báo) thì **lấy danh sách từ đó**.
   - **Cấm** quét lại source khi registry đã có dữ liệu — mục đích của registry là tránh đọc lại tài liệu lớn mỗi lần gọi.
2. **Chỉ khi không có registry**, mới quét ở mức **khung** của source ưu tiên cao nhất: mục lục, bảng danh sách chức năng, bảng FR, cột màn hình/画面, sitemap, menu tree.
   - **Cấm** trích xuất chi tiết flow, business rule, validation ở bước này.
   - **Cấm** đọc toàn văn source lớn chỉ để liệt kê module.
   - Source quá lớn (nhiều sheet/nhiều trăm trang) → chỉ đọc danh sách sheet/mục lục.
   - Sau khi dựng được danh sách, đề xuất người dùng lưu thành registry để lần sau không phải quét lại.
3. Xuất **bảng danh sách chức năng** dạng Markdown, hiển thị toàn bộ trong 1 bảng:

   | # | module_name | Hệ thống | Màn hình / entry point | FR liên quan | Trạng thái |
   |---|---|---|---|---|---|

   - `module_name` đặt theo `snake_case`, tiếng Anh, mô tả đúng phạm vi.
   - Gom theo màn hình / entry point (screen, API, batch), không gom theo hệ thống lớn.
   - Cột `Trạng thái` lấy từ registry (`pending` / `req_done` / `tc_done` / `out_of_scope`) để người dùng thấy ngay module nào đã làm.
4. **DỪNG lại và hỏi người dùng chọn 1 chức năng** (nhận cả số thứ tự lẫn `module_name`). Không tự chọn, không chạy tiếp, không sinh file nào ở bước này.
5. Sau khi người dùng chọn → chạy tiếp Phase 1 với đúng module đó.
6. Chạy xong → cập nhật `status` và `requirement_output` của module đó trong registry.

Nếu không có registry và source cũng không đủ để dựng danh sách → báo rõ thiếu gì và dừng, không đoán.

### 3A.3. Module scoping (bắt buộc trước khi phân tích)

Sau khi có `module_name`, trước khi trích xuất nội dung:

1. Xác định chính xác phần source thuộc phạm vi module: section, bảng, dòng FR, sheet, frame, màn hình.
2. Ghi lại phần **bị loại khỏi phạm vi** kèm lý do (thuộc module khác / ngoài scope / không liên quan).
3. Chỉ trích xuất nội dung trong phạm vi đã chốt.

### 3A.4. Ranh giới nội dung

- `FR`, `BR`, `VR` **chỉ được** mô tả hành vi thuộc module đang chạy.
- Chức năng của module khác **chỉ được** xuất hiện ở:
  - `impact_scope.md` (dạng upstream/downstream dependency), hoặc
  - `preconditions` của FR, hoặc
  - `dependencies.md` nếu có căn cứ.
- **Cấm** viết FR/BR/VR cho module khác dù source có sẵn thông tin.
- Nội dung liên quan module khác nhưng chưa đủ căn cứ → ghi `Cần xác nhận` trong `impact_scope.md`, không tự mở rộng.

## 4. Input

| Biến | Nguồn | Mô tả |
|---|---|---|
| `$1` | Command argument | Tên module / screen / function cần phân tích |
| `MANIFEST_PATH` | Optional argument | Đường dẫn local hoặc URL tới file source manifest |
| `PROJECT_CODE` | Optional argument | Mã dự án |
| `OUTPUT_LANGUAGE` | Optional config | Ngôn ngữ output, mặc định là Vietnamese |
| `PROJECT_PROFILE` | Optional config | File cấu hình riêng của dự án nếu có |
| `PROJECT_ROOT` | Optional runtime context | Root folder của dự án |
| `OUTPUT_ROOT` | Optional config | Folder output, mặc định là `knowledge` |
| `EVIDENCE_ROOT` | Optional config | Folder evidence, mặc định là `evidence` |

## 5. Điều kiện đầu vào

Skill kỳ vọng có ít nhất một trong các nguồn sau:
- Requirement document
- Ticket quản lý yêu cầu hoặc change request
- Figma hoặc screen design
- API spec
- DB schema / ERD
- Workflow diagram
- Meeting note / clarification note
- Existing screen capture
- UAT / testcase / QA artifact

Nếu không có đủ tài liệu:
- vẫn phân tích theo nguồn hiện có
- mọi điểm không xác định phải ghi là `Cần xác nhận`

## 6. Cấu trúc source manifest

Skill ưu tiên nhận đầu vào thông qua `source_manifest.yaml` hoặc `source_manifest.json`.

### Ví dụ `source_manifest.yaml`

```yaml
project_code: PRJ001
project_name: Sample Project
module_name: event_editing
output_language: vi
project_root: .
output_root: knowledge
evidence_root: evidence

sources:
  - id: SRC-001
    type: requirement_doc
    title: BRD v1.2
    location: /docs/BRD_v1.2.docx
    version: "1.2"
    status: approved
    priority: high
    notes: Tài liệu requirement chính

  - id: SRC-002
    type: ticket
    title: Redmine #2451
    location: https://redmine.example.com/issues/2451
    status: approved
    priority: high
    notes: Ticket change request đã được xác nhận

  - id: SRC-003
    type: figma
    title: Event Editing UI
    location: https://www.figma.com/file/xxxx
    status: confirmed
    priority: medium
    frames:
      - Event Edit
      - Confirm Dialog

  - id: SRC-004
    type: api_spec
    title: Event API
    location: /api/openapi.yaml
    status: reference
    priority: medium

  - id: SRC-005
    type: db_schema
    title: ERD
    location: /db/erd.pdf
    status: reference
    priority: low
```

## 7. Các loại source được hỗ trợ

| Type | Mô tả |
|---|---|
| `requirement_doc` | BRD, SRS, spec doc, DOCX, PDF, MD |
| `ticket` | Redmine, Jira, Backlog, Azure DevOps item |
| `figma` | File hoặc frame link dùng để xác định UI/UX |
| `api_spec` | OpenAPI, Swagger, Postman collection |
| `db_schema` | ERD, DDL doc, schema document |
| `workflow` | draw.io, PNG, Visio, BPMN |
| `meeting_note` | MOM, clarification log, decision note |
| `screen_capture` | Ảnh màn hình hiện tại hoặc ảnh evidence |
| `test_artifact` | testcase, UAT note, QA checklist |
| `change_request` | CR document hoặc enhancement request |
| `policy_doc` | quy định nghiệp vụ, vận hành, compliance |
| `config_doc` | tài liệu config, feature flag, parameter |

## 8. Quy tắc ưu tiên nguồn

Khi nhiều nguồn có nội dung mâu thuẫn, áp dụng thứ tự ưu tiên sau:

1. Tài liệu requirement đã approved hoặc signed-off
2. Bản requirement mới nhất đã approved
3. Change request / ticket đã approved
4. Figma đã được confirm
5. API spec / DB schema / config doc
6. Workflow diagram / screen capture / test artifact
7. Tài liệu cũ, historical note, thông tin tham khảo

Nếu vẫn không thể kết luận chắc chắn:
- ghi là `Cần xác nhận`
- mô tả conflict rõ ràng trong `assumptions_and_open_points.md`
- lưu đầy đủ mapping nguồn trong `traceability_matrix.md`

## 9. Nguyên tắc phân tích

- Chỉ ghi nhận điều có bằng chứng từ source
- Không tự bịa business rule, workflow, validation, dependency hoặc API
- Tách biệt rõ:
  - thông tin quan sát trực tiếp từ source
  - thông tin tổng hợp từ nhiều source
  - thông tin chưa xác định
- Nếu source không truy cập được:
  - ghi nhận là access issue
  - không suy đoán nội dung từ tiêu đề source
- Nếu source là URL cần authentication:
  - ghi nhận trạng thái `Không truy cập được`
  - tiếp tục xử lý các source còn lại
- Nếu có nhiều phiên bản của cùng một tài liệu:
  - ưu tiên bản mới nhất đã approved
  - nếu không rõ trạng thái approved thì ghi `Cần xác nhận`
- Nếu source chỉ mô tả UI nhưng không có rule nghiệp vụ:
  - không tự suy ra business rule nếu không có bằng chứng

## 10. Bối cảnh môi trường

- Working directory: current workspace
- Project root: resolved at runtime hoặc từ manifest
- Output root: `<output_root>/<module_name>/`
- Evidence root: `<evidence_root>/<module_name>/`

Nếu manifest không chỉ định:
- `output_root = knowledge`
- `evidence_root = evidence`

## 11. Cấu trúc folder output

Kết quả phải được lưu theo cấu trúc sau:

```text
<output_root>/<module_name>/
├─ source_inventory.md
├─ functional_requirements.md
├─ business_rules.md
├─ validation_rules.md
├─ impact_scope.md
├─ assumptions_and_open_points.md
├─ traceability_matrix.md
├─ dependencies.md              # optional
├─ screen_specification.md      # optional
├─ workflows.md                 # optional
├─ screen_analysis.md           # optional
└─ change_summary.md            # optional

<evidence_root>/<module_name>/
├─ source_snapshots/
├─ extraction_notes/
└─ access_issues/
```

### Quy tắc folder output

- Các file requirement output phải nằm trực tiếp trong `<output_root>/<module_name>/`
- Không bắt buộc tách thêm folder con như `requirements/`, `business_rules/`, `traceability/`
- Evidence không lưu chung với output requirement
- Chỉ tạo file optional khi có đủ căn cứ
- Không tạo file rỗng chỉ để đủ bộ

## 12. Tạo thư mục

Tạo các thư mục sau nếu chưa tồn tại:

```bash
mkdir -p <output_root>/<module_name>
mkdir -p <evidence_root>/<module_name>/source_snapshots
mkdir -p <evidence_root>/<module_name>/extraction_notes
mkdir -p <evidence_root>/<module_name>/access_issues
```

## 13. Output structure final

### 13.1. File bắt buộc

Skill luôn phải sinh 7 file sau:

1. `<output_root>/<module_name>/source_inventory.md`
2. `<output_root>/<module_name>/functional_requirements.md`
3. `<output_root>/<module_name>/business_rules.md`
4. `<output_root>/<module_name>/validation_rules.md`
5. `<output_root>/<module_name>/impact_scope.md`
6. `<output_root>/<module_name>/assumptions_and_open_points.md`
7. `<output_root>/<module_name>/traceability_matrix.md`

### 13.2. File optional theo điều kiện

Chỉ sinh khi có đủ căn cứ từ source:

1. `<output_root>/<module_name>/dependencies.md`
2. `<output_root>/<module_name>/screen_specification.md`
3. `<output_root>/<module_name>/workflows.md`
4. `<output_root>/<module_name>/screen_analysis.md`
5. `<output_root>/<module_name>/change_summary.md`

## 14. Quy tắc sinh file

### 14.1. File bắt buộc

- Luôn phải tạo
- Nếu thiếu dữ liệu, vẫn tạo file nhưng ghi rõ `Cần xác nhận`
- Không được bỏ qua file bắt buộc chỉ vì source không đủ chi tiết

### 14.2. File optional

Chỉ tạo khi có đủ bằng chứng hoặc căn cứ hợp lý từ source.

#### `dependencies.md`
Sinh khi có ít nhất một trong các dấu hiệu sau:
- Có API endpoint rõ ràng
- Có external system integration
- Có auth / session / config dependency
- Có batch / queue / event / scheduler dependency
- Có shared service hoặc DB dependency đáng kể

#### `screen_specification.md`
Sinh khi:
- Có UI screen cụ thể trong requirement doc, figma hoặc screen capture
- Có đủ thông tin về menu path, layout, action, popup, filter, grid hoặc form

#### `workflows.md`
Sinh khi:
- Có workflow diagram
- Có flow nhiều bước, nhiều actor, decision point hoặc exception flow rõ ràng

#### `screen_analysis.md`
Sinh khi:
- Cần reverse từ màn hình hiện tại
- Có screenshot / figma / existing UI evidence
- Cần bóc tách UI component nhưng source chưa có screen spec chính thức

#### `change_summary.md`
Sinh khi:
- Đây là change request
- Có current behavior và expected behavior
- Có delta impact hoặc enhancement scope

Nếu không đủ căn cứ cho file optional:
- không tạo file
- ghi nhận vào `assumptions_and_open_points.md` nếu thông tin đó đáng lẽ quan trọng nhưng đang thiếu

## 15. Workflow thực thi

### Phase 1 — Nạp cấu hình và kiểm tra nguồn

1. Nhận `module_name`
   - Thiếu `module_name` hoặc là placeholder → chạy **module discovery** theo §3A.2, DỪNG hỏi người dùng chọn, không đi tiếp Phase 2
2. Nạp `source_manifest`
3. Xác định `project_root`, `output_root`, `evidence_root`
4. Kiểm tra từng source:
   - có tồn tại hay không
   - có truy cập được hay không
   - có liên quan tới `module_name` hay không
4b. **Module scoping** theo §3A.3: chốt phần source thuộc phạm vi module + ghi rõ phần bị loại và lý do
5. Chuẩn hóa danh sách source:
   - source chính
   - source tham chiếu
   - source không truy cập được
   - source ít liên quan
6. Sinh file `source_inventory.md`

### Phase 2 — Phân loại và chuẩn hóa thông tin nguồn

Với mỗi source:
- xác định loại source
- trích xuất thông tin liên quan tới module đang xử lý
- chuẩn hóa tên chức năng, actor, field, trạng thái, entity
- xác định mức độ tin cậy của nội dung
- đánh dấu nội dung mơ hồ hoặc mâu thuẫn

Phân loại thông tin thành 3 nhóm:
- **Observed**: đọc được trực tiếp từ nguồn
- **Synthesized**: tổng hợp từ nhiều nguồn nhưng không mâu thuẫn
- **Unresolved**: chưa đủ căn cứ hoặc có xung đột

### Phase 3 — Phân tích requirement

Thu thập và cấu trúc các nhóm thông tin sau:

- Tên chức năng / screen / module
- Mục tiêu nghiệp vụ
- Actor chính và actor liên quan
- Phạm vi sử dụng
- Main flow
- Alternate flow
- Exception flow
- Business rules
- Validation rules
- Permission / role scope
- Preconditions
- Postconditions
- Data entities
- State transition nếu có
- External integration nếu có
- Session / authentication dependency nếu có
- Configuration dependency nếu có
- Impact scope
- Assumptions
- Open points

### Phase 4 — Đánh giá ảnh hưởng

Bắt buộc đánh giá ảnh hưởng của module sang các thành phần khác theo các góc nhìn sau:

- Chức năng / màn hình bị ảnh hưởng trực tiếp
- Upstream dependency
- Downstream dependency
- Shared API
- Shared DB table / field
- Shared entity
- Shared config
- Shared workflow
- Cross-screen / cross-tab dependency
- Notification / audit / report impact
- Role / permission impact
- Regression risk

Nếu có dấu hiệu ảnh hưởng nhưng chưa đủ bằng chứng:
- vẫn ghi vào `impact_scope.md`
- đánh dấu `Cần xác nhận`

### Phase 5 — Lập traceability

Với mỗi item được sinh ra, bắt buộc ghi nhận:
- Item ID
- Item type
- Source ID
- Source reference
- Confidence
- Conflict note nếu có

`Source reference` có thể là:
- page number
- section title
- table title
- figure
- frame name
- ticket ID
- comment link
- endpoint path
- DB table name

### Phase 6 — Sinh 7 file bắt buộc

Sinh đầy đủ các file sau:
1. `source_inventory.md`
2. `functional_requirements.md`
3. `business_rules.md`
4. `validation_rules.md`
5. `impact_scope.md`
6. `assumptions_and_open_points.md`
7. `traceability_matrix.md`

### Phase 7 — Xác định và sinh file optional

Phân tích source để quyết định có sinh thêm hay không:
- `dependencies.md`
- `screen_specification.md`
- `workflows.md`
- `screen_analysis.md`
- `change_summary.md`

Chỉ sinh file nếu có bằng chứng phù hợp.

### Phase 8 — Kiểm tra chất lượng trước khi hoàn tất

Trước khi finalize, bắt buộc kiểm tra:
- Không có nội dung bịa thêm
- Mỗi FR/BR/VR quan trọng đều có ít nhất 1 source reference
- Mọi điểm thiếu thông tin đều ghi `Cần xác nhận`
- Thuật ngữ được dùng nhất quán
- Các conflict được ghi riêng
- `impact_scope.md` phải có mặt trong mọi lần chạy
- `traceability_matrix.md` phải cover toàn bộ item quan trọng
- Không sinh file optional rỗng chỉ để đủ bộ
- Tài liệu độc lập, đọc riêng vẫn hiểu được

## 16. Quy chuẩn đặt ID

Sử dụng format ID thống nhất:

| Loại | Format |
|---|---|
| Functional Requirement | `FR-01`, `FR-02` |
| Business Rule | `BR-01`, `BR-02` |
| Validation Rule | `VR-01`, `VR-02` |
| Assumption | `AS-01`, `AS-02` |
| Open Point | `OP-01`, `OP-02` |
| Risk | `RK-01`, `RK-02` |
| Dependency | `DP-01`, `DP-02` |
| Workflow | `WF-01`, `WF-02` |

Nếu dự án cần prefix riêng, có thể dùng:
- `EVT-FR-01`
- `LOT-BR-01`

## 17. Yêu cầu nội dung từng file bắt buộc

### 17.1. `source_inventory.md`

Mục tiêu:
- Liệt kê toàn bộ source đã được dùng hoặc không dùng
- Minh bạch tình trạng truy cập và mức độ liên quan

Cấu trúc khuyến nghị:

```markdown
# Source Inventory: <module_name>

## Tổng quan
- Project: <project_code>
- Module: <module_name>
- Output language: Vietnamese

## Phạm vi module (bắt buộc)
- Module đang xử lý:
- Phần source thuộc phạm vi: <section / bảng / dòng FR / sheet / màn hình>
- Phần bị loại khỏi phạm vi + lý do:
| Phần bị loại | Thuộc module nào | Lý do loại |
|---|---|---|

## Danh sách nguồn
| Source ID | Type | Title | Location | Version | Status | Priority | Accessibility | Relevance | Notes |
|---|---|---|---|---|---|---|---|---|---|

## Nhận xét
- Nguồn chính:
- Nguồn tham chiếu:
- Nguồn không truy cập được:
- Nguồn thiếu thông tin chi tiết:
```

### 17.2. `functional_requirements.md`

Mục tiêu:
- Liệt kê requirement nghiệp vụ theo cấu trúc đánh số

Mỗi FR nên có:
- ID
- Tên requirement
- Mô tả
- Actor
- Trigger
- Preconditions
- Main flow
- Alternate flow
- Postconditions
- Related screen / API / entity
- Priority nếu xác định được
- Related modules nếu xác định được
- Source references
- Confidence
- Note nếu cần xác nhận

Cấu trúc khuyến nghị:

```markdown
# Functional Requirements: <module_name>

## Tổng quan
- Mục tiêu nghiệp vụ:
- Actor chính:
- Phạm vi:

## Danh sách Functional Requirement

### FR-01 - <Tên requirement>
- Actor:
- Trigger:
- Preconditions:
- Mô tả:
- Main flow:
- Alternate flow:
- Postconditions:
- Related screen / API / entity:
- Related modules:
- Priority:
- Source references:
- Confidence:
- Note:
```

### 17.3. `business_rules.md`

Mục tiêu:
- Liệt kê toàn bộ quy tắc nghiệp vụ

Mỗi BR nên có:
- ID
- Rule description
- Trigger condition
- Expected behavior
- Exception nếu có
- Affected entity / screen / process
- Test impact
- Related modules nếu xác định được
- Source references
- Confidence

Cấu trúc khuyến nghị:

```markdown
# Business Rules: <module_name>

## Danh sách Business Rule

### BR-01 - <Tên rule>
- Rule description:
- Trigger condition:
- Expected behavior:
- Exception:
- Affected entity / screen / process:
- Related modules:
- Test impact:
- Source references:
- Confidence:
```

### 17.4. `validation_rules.md`

Mục tiêu:
- Chuẩn hóa các rule kiểm tra input, trạng thái và UI

Mỗi VR nên có:
- ID
- Field / input / control name
- Rule type
- Rule description
- Boundary values
- Equivalence classes
- Error behavior
- Error message nếu xác định được
- Trigger timing
- Source references
- Confidence

Nếu module là non-UI:
- vẫn tạo file
- ghi rõ `Validation rules chi tiết: Cần xác nhận` nếu không có nguồn tương ứng

Cấu trúc khuyến nghị:

```markdown
# Validation Rules: <module_name>

## Danh sách Validation Rule

### VR-01 - <Tên validation>
- Field / input / control name:
- Rule type:
- Rule description:
- Boundary values:
- Equivalence classes:
- Error behavior:
- Error message:
- Trigger timing:
- Source references:
- Confidence:
```

### 17.5. `impact_scope.md`

Mục tiêu:
- Đánh giá ảnh hưởng của module tới các chức năng, màn hình, dữ liệu và luồng khác

Đây là file bắt buộc trong mọi lần chạy.

Nội dung tối thiểu phải có:
- Impacted Functions / Screens
- Upstream Dependencies
- Downstream Dependencies
- Data Flow Impact
- Cross-Screen Dependency
- Risk Assessment

Cấu trúc bắt buộc:

```markdown
# Impact Scope: <module_name>

## Impacted Functions / Screens
| Function/Screen | Impact Level | Description | Source Reference |
|---|---|---|---|

## Upstream Dependencies
| Source Function/Screen | Data/Context Provided | Dependency Type | Source Reference |
|---|---|---|---|

## Downstream Dependencies
| Target Function/Screen | Consumed Data/Result | Dependency Type | Source Reference |
|---|---|---|---|

## Data Flow Impact
| Table/Field | Source | Target | Trigger/Event | Notes | Source Reference |
|---|---|---|---|---|---|

## Cross-Screen Dependency
| Screen/Tab | Dependency | Impact | Source Reference |
|---|---|---|---|

## Risk Assessment
| Risk ID | Risk | Likelihood | Impact | Mitigation | Source Reference |
|---|---|---|---|---|---|
```

Nếu không xác định được đầy đủ:
- vẫn phải tạo các section trên
- nội dung chưa rõ phải ghi `Cần xác nhận`

### 17.6. `assumptions_and_open_points.md`

Mục tiêu:
- Ghi lại các giả định và các điểm cần confirm

Bao gồm 2 phần rõ ràng:

#### Assumptions
Chỉ ghi assumption khi:
- được suy ra hợp lý từ source có thật
- không mâu thuẫn với nguồn nào khác

Mỗi assumption cần có:
- ID
- Nội dung
- Lý do hình thành
- Ảnh hưởng nếu assumption sai
- Source references

#### Open Points
Mỗi open point cần có:
- ID
- Câu hỏi cần xác nhận
- Vì sao chưa xác định được
- Source conflict / missing source / inaccessible source
- Mức độ ảnh hưởng
- Nguồn liên quan

Cấu trúc khuyến nghị:

```markdown
# Assumptions and Open Points: <module_name>

## Assumptions

### AS-01
- Nội dung:
- Lý do:
- Ảnh hưởng nếu assumption sai:
- Source references:

## Open Points

### OP-01
- Câu hỏi cần xác nhận:
- Lý do chưa xác định được:
- Ảnh hưởng:
- Nguồn liên quan:
```

### 17.7. `traceability_matrix.md`

Mục tiêu:
- Truy vết toàn bộ item quan trọng về nguồn gốc

Cấu trúc khuyến nghị:

```markdown
# Traceability Matrix: <module_name>

| Item ID | Item Type | Description | Source ID | Source Reference | Confidence | Conflict Note | Status |
|---|---|---|---|---|---|---|---|
| FR-01 | Functional Requirement | ... | SRC-001 | Section 3.2 | High |  | Confirmed |
```

File này phải cover tối thiểu:
- toàn bộ FR
- toàn bộ BR
- toàn bộ VR
- risk quan trọng nếu có
- open point quan trọng nếu có source liên quan

## 18. Yêu cầu nội dung từng file optional

### 18.1. `dependencies.md`

Chỉ sinh khi có đủ căn cứ.

Bao gồm:
- Backend APIs
- Method
- Endpoint
- Purpose
- Request / response dependency nếu xác định được
- External systems
- Shared services
- Config items
- Session management
- Authentication / authorization
- Database dependency
- Batch / event / queue dependency
- Source references

### 18.2. `screen_specification.md`

Chỉ sinh khi có UI screen cụ thể.

Bao gồm:
- Tổng quan màn hình
- Target system
- Actor / target user
- Menu path
- Business context
- UI layout
- Buttons / actions
- Search & filter
- Data display
- Popup / dialog
- Behavior notes
- Permissions
- Preconditions
- Postconditions
- Source references

Nếu module không có UI:
- không sinh file này

### 18.3. `workflows.md`

Chỉ sinh khi có flow rõ ràng.

Mỗi WF nên có:
- ID
- Workflow name
- Goal
- Actor
- Preconditions
- Steps
- Decision points
- Alternate flow
- Exception flow
- Postconditions
- Related FR / BR
- Source references

### 18.4. `screen_analysis.md`

Chỉ sinh khi có nhu cầu reverse hoặc phân tích hiện trạng UI.

Bao gồm:
- Screen / module summary
- Main UI components
- Key input fields
- Validation summary
- Permissions summary
- System behavior
- State behavior nếu có
- Source references

### 18.5. `change_summary.md`

Chỉ sinh khi là change request hoặc enhancement.

Bao gồm:
- Change overview
- Current behavior
- Expected behavior
- Delta summary
- Impact summary
- Risk summary
- Related source references

Nếu không đủ thông tin về current behavior:
- ghi `Current behavior: Cần xác nhận`

## 19. Mẫu phân loại confidence

Sử dụng 3 mức:
- `High`: được nêu rõ, trực tiếp, không mâu thuẫn
- `Medium`: được tổng hợp từ nhiều nguồn tương thích
- `Low`: có dấu hiệu nhưng chưa đủ chắc chắn

Nếu `Low` và ảnh hưởng nghiệp vụ đáng kể:
- bắt buộc thêm vào `Open Points`

## 20. Quy tắc viết nội dung

- Tất cả phần giải thích phải viết bằng tiếng Việt
- Giữ nguyên tiếng Anh với:
  - file name
  - API endpoint
  - database table
  - column name
  - enum value
  - variable name
  - source title
  - URL
- Dùng Markdown
- Viết rõ ràng, độc lập, không phụ thuộc ngữ cảnh hội thoại
- Không ghi các câu phỏng đoán kiểu:
  - "có thể hệ thống sẽ..."
  - "nhiều khả năng..."
  - "ước tính..."
- Thay vào đó phải dùng:
  - `Cần xác nhận`
  - hoặc mô tả rõ dữ liệu nào đang thiếu

## 21. Quy tắc xử lý thiếu dữ liệu

Nếu thiếu thông tin:
- không tự bổ sung
- ghi `Cần xác nhận`
- nêu rõ thiếu ở đâu:
  - thiếu source
  - source không truy cập được
  - source mâu thuẫn
  - source không đủ chi tiết

Ví dụ:
- `Menu path: Cần xác nhận`
- `Validation message: Cần xác nhận`
- `Related API endpoint: Cần xác nhận`
- `Impacted downstream screen: Cần xác nhận`

## 22. Quy tắc xử lý conflict

Khi có conflict:
1. So sánh thứ tự ưu tiên nguồn
2. Chọn nguồn ưu tiên cao hơn nếu đủ rõ
3. Nếu không đủ rõ:
   - ghi cả hai cách hiểu
   - tạo `Open Point`
   - đánh `Confidence = Low` hoặc `Medium`
4. Không được âm thầm chọn một phương án mà không có giải thích

## 23. Quy tắc xác định impact scope

Khi đánh giá impact trong `impact_scope.md`, cần xem xét tối thiểu:
- Shared entity
- Shared screen/tab
- Shared API
- Shared DB table
- Shared config
- Shared workflow
- Trigger / event downstream
- Permission / role change
- Data lifecycle impact
- Audit / notification impact
- Report / export impact
- Search/filter/listing impact
- Status transition impact

Nếu có dấu hiệu ảnh hưởng nhưng chưa đủ bằng chứng:
- vẫn ghi vào `impact_scope.md`
- đánh dấu `Cần xác nhận`

## 24. Quy tắc với non-UI function

Nếu chức năng không phải màn hình:
- vẫn phải tạo 7 file bắt buộc
- không bắt buộc tạo `screen_specification.md`
- không bắt buộc tạo `screen_analysis.md`
- `functional_requirements.md` và `impact_scope.md` phải mô tả theo entry point như:
  - API
  - batch
  - scheduler
  - event
  - queue
  - background processor

## 25. Quy tắc với change request

Nếu source thể hiện đây là change request:
- vẫn tạo đủ 7 file bắt buộc
- cân nhắc sinh thêm `change_summary.md`
- trong FR và impact cần cố gắng phân biệt:
  - current behavior
  - expected behavior
- nếu không đủ thông tin về current behavior:
  - ghi `Current behavior: Cần xác nhận`

## 26. Output tiêu chuẩn tối thiểu

Một lần chạy thành công phải tạo được tối thiểu 7 file bắt buộc:
- `source_inventory.md`
- `functional_requirements.md`
- `business_rules.md`
- `validation_rules.md`
- `impact_scope.md`
- `assumptions_and_open_points.md`
- `traceability_matrix.md`

File optional chỉ tạo khi có đủ căn cứ.

## 27. Mẫu quyết định khi không đủ thông tin

Ưu tiên cách trình bày sau:

- **Đã xác định**: thông tin có bằng chứng rõ
- **Tổng hợp từ nhiều nguồn**: thông tin hợp nhất từ nhiều source
- **Cần xác nhận**: chưa đủ căn cứ
- **Xung đột nguồn**: các source đưa ra thông tin khác nhau

## 28. Tiêu chí hoàn tất

Skill được xem là hoàn tất khi:
- đã đọc và phân loại source
- đã sinh 7 file bắt buộc
- đã có `impact_scope.md`
- đã có `traceability_matrix.md`
- đã liệt kê assumptions và open points
- không có nội dung không truy xuất được về source
- không sinh file optional rỗng hoặc không cần thiết

## 29. Kết quả mong đợi

Khi skill chạy xong, người đọc phải có thể:
- hiểu module đang làm gì
- biết actor nào sử dụng
- biết flow chính và flow ngoại lệ nếu có
- biết business rules và validation rules
- biết phạm vi ảnh hưởng tới chức năng khác
- biết chính xác nội dung lấy từ nguồn nào
- biết phần nào còn cần confirm
- không bị ngợp bởi quá nhiều file không cần thiết

## 30. Rules

- Tất cả phần giải thích phải viết bằng tiếng Việt
- Không được bịa requirement, business rule, validation rule, flow, permission, dependency hoặc impact
- Mọi nội dung quan trọng phải có traceability
- `impact_scope.md` là file bắt buộc
- Nếu không xác định được thì ghi `Cần xác nhận`
- Mỗi tài liệu phải self-contained
- Ưu tiên tính đúng, khả năng review và khả năng audit hơn là cố gắng lấp đầy nội dung
- **1 lần chạy = 1 module.** Cấm gộp nhiều module, cấm gen toàn bộ dự án dù source phủ rộng (§3A)
- **Không có tên module trên dòng lệnh → LUÔN hiển thị bảng danh sách chức năng rồi DỪNG hỏi**, bất kể manifest ghi gì; `run.module_name` không được dùng để chọn module (§3A.2)
- Nội dung của module khác chỉ được nằm ở `impact_scope.md` / `preconditions` / `dependencies.md`, không được viết thành FR/BR/VR (§3A.4)