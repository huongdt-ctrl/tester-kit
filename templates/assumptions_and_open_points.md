# Assumptions and Open Points: <module_name>

## Tổng quan
- Project Code: <project_code>
- Project Name: <project_name>
- Module Name: <module_name>
- Mục tiêu tài liệu:
  - Ghi nhận các giả định hợp lý từ source
  - Ghi nhận các điểm còn thiếu, mâu thuẫn hoặc cần xác nhận

---

## Assumptions

### AS-01
- Nội dung:
  - <giả định>
- Lý do:
  - <vì sao hình thành giả định này>
- Ảnh hưởng nếu assumption sai:
  - <ảnh hưởng>
- Source References:
  - <SRC-xxx>
- Confidence:
  - <High / Medium / Low>

### AS-02
- Nội dung:
  - <giả định>
- Lý do:
  - <lý do>
- Ảnh hưởng nếu assumption sai:
  - <ảnh hưởng>
- Source References:
  - <SRC-xxx>
- Confidence:
  - <High / Medium / Low>

---

## Open Points

### OP-01
- Câu hỏi cần xác nhận:
  - <câu hỏi>
- Lý do chưa xác định được:
  - <thiếu source / xung đột nguồn / source không truy cập được / source không đủ chi tiết>
- Ảnh hưởng:
  - <ảnh hưởng tới FR / BR / VR / impact / dev / QA>
- Nguồn liên quan:
  - <SRC-xxx>
  - <SRC-yyy>
- Mức độ ưu tiên:
  - <High / Medium / Low>

### OP-02
- Câu hỏi cần xác nhận:
  - <câu hỏi>
- Lý do chưa xác định được:
  - <lý do>
- Ảnh hưởng:
  - <ảnh hưởng>
- Nguồn liên quan:
  - <SRC-xxx>
- Mức độ ưu tiên:
  - <High / Medium / Low>

---

## Nguồn xung đột cần follow-up

| Topic | Source A | Source B | Conflict Description | Recommended Action |
|---|---|---|---|---|
| <topic> | <SRC-001> | <SRC-002> | <mô tả xung đột> | <xác nhận với BA / PO / Dev> |
| <topic> | <SRC-003> | <SRC-004> | <mô tả xung đột> | <action> |

---

## Tổng hợp ưu tiên xác nhận

| Open Point | Priority | Owner Suggestion | Notes |
|---|---|---|---|
| OP-01 | High | <BA / PO / Dev / Design> | <notes> |
| OP-02 | Medium | <BA / PO / Dev / Design> | <notes> |

---

## Kết luận
- Số lượng assumption:
  - <count>
- Số lượng open point:
  - <count>
- Open point ưu tiên cao:
  - <OP-xx>
- Nếu không có assumption hoặc open point, ghi rõ:
  - `Chưa ghi nhận assumption hoặc open point đáng kể tại thời điểm phân tích.`