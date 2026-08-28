# Template cell map — `TEM-ST02-01_Template Test Plan.xlsx`

Anchor chính xác của từng vùng ghi dữ liệu. Đo trực tiếp từ file
`<skill_dir>/templates/template_testplan.xlsx`.

## Bẫy của template — ĐỌC TRƯỚC KHI GHI

6 khiếm khuyết **có sẵn trong file template công ty** (`md5 db3fca98`), đo trực tiếp bằng
`openpyxl` ngày 2026-08-28. B1–B3 làm file xuất ra nhìn như bảng vỡ dù nội dung đúng;
B4–B6 gây sai dữ liệu hoặc lỗi runtime.

### B1. Template chỉ merge ~5 dòng đầu mỗi bảng

Các dòng sau chỉ có border, **không có merge** → Excel hiện đường kẻ dọc **bên trong** ô
`C:E` / `F:L` / `M:O`, nhìn lệch hẳn so với các dòng trên. Số dòng thực có merge:

| Bảng | Vùng data | Số dòng CÓ merge |
|---|---|---|
| `02_Scope test` 2.6 | 63–75 | 5/13 |
| `01_Introduction` 1.4 | 46–60 | 5/15 |
| `05_Test Environment` 5.3 | 32–45 | 5/14 |
| `06_Criteria` 6.2 | 18–30 | 5/13 |
| `02_Scope test` 2.4 · 2.5 · `05` 5.1 · 5.2 | — | 5/7 |
| `01_Introduction` 1.3 · `02` 2.2 · 2.3 · `03` 3.1 · `04` 4.1 · `06` 6.1 | — | thiếu đúng dòng cuối |
| `08_Deliverables` | 7–15 | 0/9 — bảng này **vốn không merge**, đúng thiết kế |

→ Ghi xong mỗi bảng phải gọi `normalize_row_merges(ws, first_data_row, n)` để nhân bản mẫu
merge của dòng data đầu ra mọi dòng đã ghi.

### B2. Mọi dòng để mặc định 12.75pt

Bật wrap text mà không chỉnh chiều cao thì nội dung bị cắt (đo được 87 dòng ở lần chạy đầu).
→ Gọi `autofit_rows(ws, rows)` cuối cùng. Ô nằm trong **merge dọc** phải chia đều phần chiều cao
còn thiếu cho cả block, không đặt cho 1 dòng.

### B3. Ô văn bản dài không nhất quán về merge ngang

`B10:W11`, `B27:W27`, `B62:W62` (`02`), `B3:X17` (`03`), `B22:R22` (`04`) **có** merge, nhưng
`B6`/`B10` (`01`), `B6` (`02`), `B6` (`04`), `B7`/`B19`/`B30` (`05`), `B5`/`B15` (`06`) thì **không**.
Ô không merge + wrap text → chữ bị ép vào bề rộng 1 cột (~8 ký tự), một đoạn 600 ký tự thành ~80 dòng.

→ Gọi `ensure_narrative_merge(ws, addr, end_col)` trước khi ghi. Cột kết thúc theo từng sheet:
`01`→`R` · `02`→`W` · `03`→`X` · `04`→`R` · `05`→`V` · `06`→`Y` (lấy theo merge template đã dùng sẵn).

### B4. Sheet 07 — cột G/H sai number format

`G5`/`H5` là `0.00` nhưng `G6:H19` lại là `yyyy/mm/dd`. Ghi effort `2.58` vào `G6` thì Excel hiển thị
`1900/01/02 13:55`. → Sau khi ghi, gọi `sync_number_format(ws, col, rows, ref_row=5)`.

### B5. Sheet 07 — formula chỉ có ở dòng 5 và dòng 20

Không phải mọi dòng 5–19. Khi verify formula `S`/`AB`/`AC`, chỉ check **dòng có data** + dòng `Total` 20.

### B6. Sheet 07 — cột A và B merge theo block

`A5:A19` (Release ghi **1 lần** ở `A5`) · `B5:B7` · `B8:B10` · `B11:B15` · `B16:B18`
(Function cấp I theo block). Bố cục dòng data phải khớp block merge, không thì ghi vào `MergedCell`
sẽ ném `AttributeError: read-only` → mọi ô trong vùng merge phải ghi qua `anchor(ws, addr)`.

> **openpyxl 3.1.5**: `ws.insert_rows()` **không** dịch merged range, row height và data validation.
> Phải dùng `scripts/xlsx_row_ops.py:insert_rows_keep_merges()`, cấm gọi thẳng.
> Mọi ô nằm trong vùng merge phải ghi qua `anchor()`.
>
> Ghi xong **bắt buộc** chạy `scripts/verify_testplan.py` — 10 mục verify của Phase 7 đã được script hoá, exit code khác 0 là cấm bàn giao.

---

**Quy tắc chung khi ghi:**
- `header_row` = dòng chứa tên cột. **Cấm sửa** dòng này.
- `data_from` = dòng đầu tiên được ghi data.
- `data_to` = dòng cuối của vùng data có sẵn format (dòng ngay trước heading mục kế tiếp ở cột `A`).
- Data nhiều hơn `data_to - data_from + 1` dòng → **insert row** ngay trước `data_to`, copy format từ dòng liền trên. Cấm ghi tràn qua heading mục kế tiếp.
- Data ít hơn vùng có sẵn → **để trống** các dòng còn lại, cấm xoá dòng, cấm ghi `—` / `N/A`.
- Ô guidance dạng `{...}` → **ghi đè bằng nội dung thật**. Ô guidance của mục không áp dụng → **để nguyên `{...}`** (xem §Quy tắc mục không áp dụng trong SKILL.md).
- Cột `No` đánh số dạng `1.0`, `2.0`, `3.0`… theo đúng format sẵn của template.

---

## Sheet `Cover`

| Field | Cell |
|---|---|
| Documemt Name | `E6` |
| Project Name | `E7` |
| Created Date | `E8` |
| Created by | `E9` |
| Reviewer/Approver | `E10` |

**Lịch sử thay đổi** — `header_row` 15 · `data_from` 16 · `data_to` 26 (`C27` = `Annotation:`)

| Cột | Header |
|---|---|
| `C` | No |
| `D` | Ngày hiệu lực |
| `F` | Version |
| `G` | Mục thay đổi |
| `J` | *A,D,M (A=Add · D=Delete · M=Modify) |
| `K` | Mô tả thông tin thay đổi |
| `O` | Thông tin tham khảo |

---

## Sheet `Table of content`
**KHÔNG ghi.** Sheet mục lục tĩnh, giữ nguyên 100%.

---

## Sheet `01_Introduction`

| Mục | Heading cell | Ô ghi nội dung |
|---|---|---|
| 1.1 Định danh | `A4` | `B6` |
| 1.2 Mục đích | `A8` | `B10` |
| 1.3 Định nghĩa, từ viết tắt | `A12` | bảng, xem dưới |
| 1.4 References | `A41` | bảng, xem dưới |

**1.3 Định nghĩa / từ viết tắt** — `header_row` 16 · `data_from` 17 · `data_to` 40
`B`=No · `C`=Thuật ngữ/Từ viết tắt · `F`=Mô tả · `M`=Ghi chú

**1.4 References** — `header_row` 45 · `data_from` 46 · `data_to` 60
`B`=No · `C`=Tên tài liệu · `F`=Mô tả · `M`=Link · `P`=Version

---

## Sheet `02_Scope test`

| Mục | Heading | Guidance cell | Bảng |
|---|---|---|---|
| 2.1 Mục tiêu testing | `A4` | `B6` | — (ghi text vào `B6`) |
| 2.2 Test items | `A8` | `B10` | header 13 · data 14–24 |
| 2.3 Các tính năng PHẢI test | `A25` | `B27` | header 29 · data 30–35 |
| 2.4 Các tính năng KHÔNG phải test | `A36` | `B38` | header 40 · data 41–47 |
| 2.5 Giả định | `A48` | `B49` | header 51 · data 52–58 |
| 2.6 Sự ràng buộc | `A59` | `B60` | header 62 · data 63–75 |

Cột của cả 5 bảng: `B`=No · `C`=<tên mục> · `F`=Mô tả · `M`=Ghi chú

Bảng 2.4 **bắt buộc** ghi lý do không test vào cột `F` (Mô tả).

---

## Sheet `03_Test ApproachStrategy`

| Mục | Heading | Vùng ghi |
|---|---|---|
| 3.0 Test strategy (narrative) | `A2` | `B3` |
| 3.1 Loại test case, cách thức test | `A18` | bảng header 20 · data 21–24 |
| 3.2 Test levels/Test stages | `A25` | matrix header 29–30 · data 31–36 |

**3.1** — `B`=Tên tính năng · `F`=Phương pháp test
Giá trị `F` hợp lệ: `Full test case` · `Full check list` · `Free test`.

**3.2 matrix** — `B29`=Type off tests · `F29`=Stage of test
Cột stage: `F`=Unit · `G`=Intergration · `I`=System · `J`=Acceptance
Data rows 31–36: `B`=tên test type, các cột stage ghi `x` nếu áp dụng, để trống nếu không.
Cần > 6 test type → insert row trước 36.

---

## Sheet `03_1_Test ApproachStr`

Sheet guideline chuẩn cho từng test type. **Layout cố định** — mỗi test type có 4 ô nội dung
ở cột `F`, label ở cột `B`.

| Test type | Heading row | Mục tiêu | Kỹ thuật/Cách thức | Tiêu chí hoàn thành | Cân nhắc/lưu ý |
|---|---|---|---|---|---|
| 3.1 Static testing | 2 | — | — | — | — |
| 3.1.1 Phân tích yêu cầu | 5 | `F7` | `F8` | `F13` | `F15` |
| 3.1.2 Review test cases | 17 | `F21` | `F22` | `F39` | `F41` |
| 3.2 Dynamic testing | 44 | — | — | — | — |
| 3.2.1 Functional testing | 45 | `F50` | `F51` | `F55` | `F56` |
| 3.2.2 Business Cycle Testing | 58 | `F62` | `F63` | `F69` | `F70` |
| 3.2.3 User Interface Testing | 72 | `F75` | `F79` | `F81` | `F83` |
| 3.2.4 Data and Database Integrity Testing | 85 | `F89` | `F90` | `F93` | `F96` |
| 3.2.5 Performance Profiling (nhóm) | 99 | — | — | — | — |
| 3.2.5.1 Performance Testing | 104 | `F108` | `F110` | `F113` | `F115` |
| 3.2.5.2 Load Testing | 121 | `F127` | `F129` | `F131` | `F133` |
| 3.2.5.3 Stress Testing | 136 | `F142` | `F147` | `F151` | `F153` |
| 3.2.5.4 Volume Testing | 157 | `F162` | `F165` | `F169` | `F171` |
| 3.2.6 Security and Access Control Testing | 173 | dò label cột `B` trong 173–190 |
| 3.2.7 Failover and Recovery Testing | 191 | dò label cột `B` trong 191–218 |
| 3.2.8 Configuration Testing | 219 | dò label cột `B` trong 219–232 |
| 3.2.9 Installation Testing | 233 | dò label cột `B` trong 233–248 |
| 3.2.10 Regression test Testing | 249 | dò label cột `B` trong 249–hết |

Với 3.2.6–3.2.10: **dò runtime** ô cột `B` khớp `Mục tiêu:` / `Kỹ thuật/Cách thức thực hiện:` /
`Tiêu chí hoàn thành:` / `Các cân nhắc/lưu ý đặc biệt:` trong khoảng row của mục, ghi vào ô cột `F`
cùng dòng. Cấm hardcode row cho nhóm này.

---

## Sheet `04_Resources`

| Mục | Heading | Vùng ghi |
|---|---|---|
| 4.1 Human resource | `A4` | guidance `B6` · header 8 · data 9–19 |
| 4.2 Staffing and Training Resources | `A20` | `B22` |

**4.1** cột: `B`=Name/Email/Mobile (3 dòng 1 người) · `D`=Role · `F`=Trách nhiệm · `I`=Site
Mỗi người chiếm **3 dòng liền**: dòng 1 `B`=tên + `D`=role + `I`=site, dòng 2 `B`=email, dòng 3 `B`=mobile.
Cột `F` ghi 1 trách nhiệm / dòng, tối đa 3 dòng / người. > 4 người → insert theo block 3 dòng.

---

## Sheet `05_Test Environment`

| Mục | Heading | Guidance | header_row | data |
|---|---|---|---|---|
| 5.1 Hardware | `A5` | `B7` | 9 | 10–16 |
| 5.2 Software | `A17` | `B19` | 21 | 22–28 |
| 5.3 Infrastructure | `A29` | `B30` | 31 | 32–45 |

Cột cả 3 bảng: `B`=No · `C`=Tên thiết bị / Tên công cụ · `F`=Mô tả · `N`=Version/OS version · `Q`=Số lượng · `T`=Thời gian sử dụng (Tháng)

---

## Sheet `06_Criteria`

**6.1 Tiêu chí hoàn thành** — heading `A4` · guidance `B5` · header 7 · data 8–13
`B`=No · `C`=Criteria · `F`=Mô tả · `M`=Status · `O`=Ghi chú

**6.2 Tiêu chí tạm dừng và điều kiện bắt đầu lại** — heading `A14` · guidance `B15` · header 17 · data 18–30
`B`=No · `C`=Criteria · `F`=Mô tả · `M`=Điều kiện bắt đầu lại · `T`=Status · `V`=Ghi chú

---

## Sheet `07_Estimation & Schedule`

Header 3 tầng: row 2 (nhóm) · row 3 (cột con) · row 4 (browser cho nhóm Testing).
`data_from` 5 · `data_to` 19 · row 20 = dòng `Total` (**cấm ghi đè**, chỉ giữ formula).

| Cột | Nội dung |
|---|---|
| `A` | Release |
| `B` | Function (cấp I) |
| `C` | Function (cấp II) |
| `D` | PIC |
| `E`·`F`·`G`·`H`·`I` | Study requirement: Start · End · Plan Effort (h) · Actual effort (h) · Status |
| `J`·`K`·`L`·`M`·`N` | Create testcase: Start · End · Plan Effort (h) · Actual effort (h) · Status |
| `O`·`P` | Build code: Plan date · Status |
| `Q`·`R`·`S`·`T`·`U` | Execute: Start · End · Plan Effort (h) · Actual effort (h) · Status |
| `V`…`AA` | Testing (h) chia theo browser/thiết bị: Chrome · IE11 · Firefox · IE9 · IE10 · … |
| `AB` | Total Plan Effort (h) |
| `AC` | Total Actual Effort (h) |
| `AD` | Comment |

**Formula bắt buộc giữ** (ghi lại cho mọi dòng data mới, không hardcode số):
- `S<r>` = `=sum(V<r>:AA<r>)`
- `AB<r>` = `=sum(G<r>,L<r>,S<r>)`
- `AC<r>` = `=Sum(H<r>,M<r>,T<r>)`
- Row 20: `=sum(X5:X19)` cho từng cột `G H L M S T V W X Y Z AA AB AC`

Cột `Actual effort` (`H`, `M`, `T`) và mọi `Status` → **để trống** khi tạo plan (điền lúc execute).
Row 4 (`V4`…`AA4`) đổi theo browser/device thật của dự án; không dùng → để trống cột đó.

---

## Sheet `08_Deliverables`

`header_row` 6 · `data_from` 7 · `data_to` 15 (9 dòng đã prefill)
`B`=No · `C`=Deliverables · `D`=Language · `E`=Delivered Date · `F`=Status

Danh mục prefill: Test plan · Test cases · Test scenarios · RTM · Execution test reports ·
Test incident report · Summary test reports · Release notes · Defect log.
Deliverable không bàn giao → **giữ dòng**, `F` = `Không áp dụng`, `E` để trống.

---

## Sheet `09_Risk management`

Guidance `B2` · tiêu đề `B8` · `header_row` 10 · `data_from` 11 · `data_to` 26 (prefill catalog)

| Cột | Header |
|---|---|
| `B` | No (số nhóm rủi ro) |
| `C` | Loại rủi ro (nhóm) |
| `E` | No (số thứ tự trong nhóm) |
| `F` | Rủi ro |
| `H` | Mô tả |
| `P` | Mức độ |
| `Q` | Tình trạng |
| `R` | Biện pháp giảm thiểu rủi ro |

Catalog prefill (giữ nguyên, chỉ điền `P`/`Q`/`R`):
- `1.0 Vấn đề từ phía khách hàng`: 1.0 Giao tiếp · 2.0 Yêu cầu · 3.0 Yêu cầu bị thay đổi · 4.0 Lịch trình bị thay đổi
- `2.0 Vấn đề từ phía tổ chức`: 1.0 Con người · 2.0 Vấn đề kỹ thuật · 3.0 Làm việc nhóm

Rủi ro mới ngoài catalog → insert row trong đúng nhóm, hoặc thêm nhóm mới sau row 26.
