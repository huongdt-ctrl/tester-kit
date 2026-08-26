# Traceability Matrix: <module_name>

## Tổng quan
- Project Code: <project_code>
- Project Name: <project_name>
- Module Name: <module_name>
- Mục tiêu tài liệu:
  - Truy vết toàn bộ item quan trọng về nguồn gốc
  - Hỗ trợ review, audit, QA coverage và impact analysis

---

## Traceability Matrix

| Item ID | Item Type | Description | Source ID | Source Reference | Confidence | Conflict Note | Status |
|---|---|---|---|---|---|---|---|
| FR-01 | Functional Requirement | <mô tả ngắn> | SRC-001 | Section 3.2 | High |  | Confirmed |
| BR-01 | Business Rule | <mô tả ngắn> | SRC-001 | Section 5.1 | High |  | Confirmed |
| VR-01 | Validation Rule | <mô tả ngắn> | SRC-003 | Frame Validation Error State | Medium |  | Draft |
| RK-01 | Risk | <mô tả ngắn> | SRC-006 | ERD page 2 | Medium |  | Draft |
| OP-01 | Open Point | <mô tả ngắn> | SRC-002 | Ticket #2451 comment 3 | Low | Xung đột với SRC-001 | Need Confirmation |

---

## Mapping theo loại item

### Functional Requirements
| Item ID | Source ID | Source Reference | Status |
|---|---|---|---|
| FR-01 | SRC-001 | Section 3.2 | Confirmed |
| FR-02 | SRC-002 | Ticket #2451 | Draft |

### Business Rules
| Item ID | Source ID | Source Reference | Status |
|---|---|---|---|
| BR-01 | SRC-001 | Section 5.1 | Confirmed |
| BR-02 | SRC-008 | MOM 2026-08-03 | Draft |

### Validation Rules
| Item ID | Source ID | Source Reference | Status |
|---|---|---|---|
| VR-01 | SRC-003 | Frame Validation Error State | Draft |
| VR-02 | SRC-001 | Section 5.4 | Confirmed |

### Risks / Open Points
| Item ID | Source ID | Source Reference | Status |
|---|---|---|---|
| RK-01 | SRC-006 | ERD page 2 | Draft |
| OP-01 | SRC-002 | Ticket #2451 | Need Confirmation |

---

## Nguồn chưa được trace đầy đủ
- <Source ID> - <lý do>
- <Source ID> - <lý do>
- Nếu không có, ghi: `Tất cả item quan trọng đã được trace về source tương ứng.`

---

## Nhận xét
- Mức độ traceability tổng thể:
  - <Đầy đủ / Tương đối đầy đủ / Cần bổ sung>
- Item thiếu source rõ ràng:
  - <item_id hoặc Không có>
- Item có conflict:
  - <item_id hoặc Không có>