# Business Rules: <module_name>

## Tổng quan
- Project Code: <project_code>
- Project Name: <project_name>
- Module Name: <module_name>
- Mục tiêu tài liệu:
  - Liệt kê các quy tắc nghiệp vụ áp dụng cho module
  - Làm rõ điều kiện, hành vi mong đợi và ảnh hưởng kiểm thử

---

## Danh sách Business Rule

### BR-01 - <Tên rule>
- Rule Description:
  - <mô tả rule>
- Trigger Condition:
  - <điều kiện kích hoạt>
- Expected Behavior:
  - <hành vi mong đợi>
- Exception:
  - <ngoại lệ hoặc Cần xác nhận>
- Affected Entity / Screen / Process:
  - <entity_or_screen_or_process>
- Related Modules:
  - <related_module_1>
  - <related_module_2>
- Test Impact:
  - <ảnh hưởng tới test case / regression / negative case>
- Source References:
  - <SRC-001 - Section x.x>
  - <SRC-002 - Ticket #xxxx>
- Confidence:
  - <High / Medium / Low>
- Note:
  - <ghi chú>

---

### BR-02 - <Tên rule>
- Rule Description:
  - <mô tả rule>
- Trigger Condition:
  - <điều kiện>
- Expected Behavior:
  - <hành vi>
- Exception:
  - <ngoại lệ>
- Affected Entity / Screen / Process:
  - <entity_or_screen_or_process>
- Related Modules:
  - <related_module>
- Test Impact:
  - <ảnh hưởng kiểm thử>
- Source References:
  - <SRC-xxx>
- Confidence:
  - <High / Medium / Low>
- Note:
  - <ghi chú>

---

## Tổng hợp Business Rule theo nhóm

### Nhóm trạng thái
- BR-xx
- BR-xx

### Nhóm quyền hạn
- BR-xx
- BR-xx

### Nhóm dữ liệu
- BR-xx
- BR-xx

### Nhóm quy trình
- BR-xx
- BR-xx

---

## Mapping với Functional Requirements

| Business Rule | Related FR | Ghi chú |
|---|---|---|
| BR-01 | FR-01, FR-03 | <notes> |
| BR-02 | FR-02 | <notes> |

---

## Điểm cần xác nhận
- <open point 1>
- <open point 2>
- Nếu không có, ghi: `Chưa ghi nhận điểm cần xác nhận bổ sung trong phạm vi Business Rules.`