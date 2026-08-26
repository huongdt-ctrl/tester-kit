# Impact Scope: <module_name>

## Tổng quan
- Project Code: <project_code>
- Project Name: <project_name>
- Module Name: <module_name>
- Mục tiêu tài liệu:
  - Đánh giá ảnh hưởng của module tới các chức năng, màn hình, dữ liệu và luồng khác
- Mức độ chắc chắn chung:
  - <High / Medium / Low>
- Lưu ý:
  - Nếu chưa đủ bằng chứng, phải ghi `Cần xác nhận`

---

## Impacted Functions / Screens

| Function/Screen | Impact Level | Description | Source Reference |
|---|---|---|---|
| <function_or_screen> | High | <mô tả ảnh hưởng> | <SRC-001 - Section x.x> |
| <function_or_screen> | Medium | <mô tả ảnh hưởng> | <SRC-xxx> |

---

## Upstream Dependencies

| Source Function/Screen | Data/Context Provided | Dependency Type | Source Reference |
|---|---|---|---|
| <source_function> | <data_or_context> | API / UI / Data / Event | <SRC-xxx> |
| <source_function> | <data_or_context> | API / UI / Data / Event | <SRC-xxx> |

---

## Downstream Dependencies

| Target Function/Screen | Consumed Data/Result | Dependency Type | Source Reference |
|---|---|---|---|
| <target_function> | <data_or_result> | API / UI / Data / Event | <SRC-xxx> |
| <target_function> | <data_or_result> | API / UI / Data / Event | <SRC-xxx> |

---

## Data Flow Impact

| Table/Field | Source | Target | Trigger/Event | Notes | Source Reference |
|---|---|---|---|---|---|
| <table.field> | <source_module> | <target_module> | <trigger> | <notes> | <SRC-xxx> |
| <table.field> | <source_module> | <target_module> | <trigger> | <notes> | <SRC-xxx> |

---

## Cross-Screen Dependency

| Screen/Tab | Dependency | Impact | Source Reference |
|---|---|---|---|
| <screen_or_tab> | <dependency_description> | <impact_description> | <SRC-xxx> |
| <screen_or_tab> | <dependency_description> | <impact_description> | <SRC-xxx> |

---

## Role / Permission Impact

| Role | Impact Description | Impact Level | Source Reference |
|---|---|---|---|
| <role> | <mô tả ảnh hưởng> | <High / Medium / Low> | <SRC-xxx> |
| <role> | <mô tả ảnh hưởng> | <High / Medium / Low> | <SRC-xxx> |

---

## Notification / Audit / Report Impact

| Area | Impact Description | Impact Level | Source Reference |
|---|---|---|---|
| Notification | <mô tả> | <High / Medium / Low> | <SRC-xxx> |
| Audit Log | <mô tả> | <High / Medium / Low> | <SRC-xxx> |
| Report / Export | <mô tả> | <High / Medium / Low> | <SRC-xxx> |

---

## Risk Assessment

| Risk ID | Risk | Likelihood | Impact | Mitigation | Source Reference |
|---|---|---|---|---|---|
| RK-01 | <rủi ro> | High | High | <biện pháp giảm thiểu> | <SRC-xxx> |
| RK-02 | <rủi ro> | Medium | High | <biện pháp giảm thiểu> | <SRC-xxx> |

---

## Kết luận đánh giá ảnh hưởng
- Ảnh hưởng chính:
  - <impact_1>
  - <impact_2>
- Khu vực cần regression test:
  - <area_1>
  - <area_2>
- Điểm cần xác nhận:
  - <open_point_1>
  - <open_point_2>