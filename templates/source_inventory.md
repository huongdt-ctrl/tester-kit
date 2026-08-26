# Source Inventory: <module_name>

## Tổng quan
- Project Code: <project_code>
- Project Name: <project_name>
- Module Name: <module_name>
- Analysis Mode: <baseline | change_request | reverse_engineering>
- Output Language: Vietnamese
- Generated Date: <yyyy-mm-dd>
- Analyst: <name_or_team>

---

## Mục tiêu tài liệu
Tài liệu này liệt kê toàn bộ nguồn đã được xem xét để phân tích requirement cho module `<module_name>`, bao gồm nguồn chính, nguồn tham chiếu, nguồn không truy cập được và mức độ liên quan của từng nguồn.

---

## Danh sách nguồn

| Source ID | Type | Title | Location | Version | Status | Priority | Accessibility | Relevance | Module Refs | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| SRC-001 | requirement_doc | <title> | <path_or_url> | <version> | <approved> | <high> | <Accessible / Không truy cập được> | <high> | <module_name> | <notes> |
| SRC-002 | ticket | <title> | <path_or_url> |  | <approved> | <high> | <Accessible / Không truy cập được> | <medium> | <module_name> | <notes> |

---

## Phân loại nguồn

### Nguồn chính
- <Source ID> - <Lý do được xem là nguồn chính>
- <Source ID> - <Lý do>

### Nguồn tham chiếu
- <Source ID> - <Phạm vi tham chiếu>
- <Source ID> - <Phạm vi tham chiếu>

### Nguồn không truy cập được
- <Source ID> - <Lý do không truy cập được>
- <Source ID> - <Lý do>

### Nguồn ít liên quan
- <Source ID> - <Lý do ít liên quan>
- <Source ID> - <Lý do>

---

## Nhận xét về chất lượng nguồn
- Độ đầy đủ của nguồn: <Đầy đủ / Tương đối đầy đủ / Thiếu đáng kể>
- Nguồn có xung đột: <Có / Không>
- Nguồn cần xác nhận thêm: <Có / Không>
- Nhận xét chung:
  - <nhận xét 1>
  - <nhận xét 2>

---

## Rủi ro do thiếu nguồn
- <rủi ro 1>
- <rủi ro 2>
- Nếu không có rủi ro đáng kể, ghi: `Chưa ghi nhận rủi ro đáng kể từ chất lượng nguồn.`

---

## Kết luận sử dụng nguồn
- Nguồn ưu tiên cao nhất cho module này là: <Source ID / title>
- Nguồn dùng để xác nhận UI là: <Source ID / Cần xác nhận>
- Nguồn dùng để xác nhận business rule là: <Source ID / Cần xác nhận>
- Nguồn dùng để xác nhận impact scope là: <Source ID / Cần xác nhận>