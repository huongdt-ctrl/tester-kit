# Validation Rules: <module_name>

## Tổng quan
- Project Code: <project_code>
- Project Name: <project_name>
- Module Name: <module_name>
- Phạm vi validation:
  - <UI input / API payload / state validation / business validation>
- Ghi chú:
  - Nếu module là non-UI và không có nguồn tương ứng, ghi: `Validation rules chi tiết: Cần xác nhận`

---

## Danh sách Validation Rule

### VR-01 - <Tên validation>
- Field / Input / Control Name:
  - <field_name>
- Rule Type:
  - <Required / Format / Length / Range / State / Permission / Uniqueness / Other>
- Rule Description:
  - <mô tả rule>
- Boundary Values:
  - <min / max / allowed range / Cần xác nhận>
- Equivalence Classes:
  - <valid_class>
  - <invalid_class>
- Error Behavior:
  - <cách hệ thống phản hồi>
- Error Message:
  - <message hoặc Cần xác nhận>
- Trigger Timing:
  - <on_change / on_blur / on_submit / before_save / server_side>
- Source References:
  - <SRC-001 - Section x.x>
  - <SRC-003 - Frame Validation Error State>
- Confidence:
  - <High / Medium / Low>
- Note:
  - <ghi chú>

---

### VR-02 - <Tên validation>
- Field / Input / Control Name:
  - <field_name>
- Rule Type:
  - <type>
- Rule Description:
  - <mô tả>
- Boundary Values:
  - <value>
- Equivalence Classes:
  - <class>
- Error Behavior:
  - <behavior>
- Error Message:
  - <message>
- Trigger Timing:
  - <timing>
- Source References:
  - <SRC-xxx>
- Confidence:
  - <High / Medium / Low>
- Note:
  - <ghi chú>

---

## Tổng hợp Validation theo field

| Field / Input | Validation Rules | Ghi chú |
|---|---|---|
| <field_1> | VR-01, VR-02 | <notes> |
| <field_2> | VR-03 | <notes> |

---

## Tổng hợp Validation theo loại

### Required
- VR-xx
- VR-xx

### Format
- VR-xx
- VR-xx

### Length / Range
- VR-xx
- VR-xx

### State / Permission
- VR-xx
- VR-xx

---

## Điểm cần xác nhận
- <open point 1>
- <open point 2>
- Nếu không có, ghi: `Chưa ghi nhận điểm cần xác nhận bổ sung trong phạm vi Validation Rules.`