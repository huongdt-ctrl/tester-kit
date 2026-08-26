# Estimation Model — test estimate cho luồng QA có AI hỗ trợ

> **Nguồn gốc bộ hệ số:** toàn bộ base rate và tham số trong file này được hiệu chỉnh
> từ đo đạc thật trên một dự án web tiếng Nhật (ticketing), tên màn hình và tên hệ thống
> đã được thay bằng nhãn generic. Dự án mới nên dùng bộ số này làm **điểm khởi đầu**,
> rồi tự calibrate lại sau vài sprint bằng chính phương pháp mô tả ở mục 6 và mục 7.

Tài liệu này là **nguồn duy nhất** của công thức và hệ số. Sửa hệ số ở đây (và ở
sheet `Rate Card` của file estimate) — **không** sửa vào `SKILL.md`.

Bảng số trong file này khớp 1-1 với `scripts/estimate_template_data.py`. Đổi số ở
một nơi thì phải đổi ở nơi kia rồi chạy lại `python3 scripts/build_estimate_template.py`.

## 1. Công thức

```
volume            = khối lượng theo đơn vị của activity
base_rate         = rate[activity][complexity]          # giờ của level Middle
level_factor      = factor[level]
level_check       = 1 + surcharge[activity]  nếu rank[level] < min_rank[activity]
                    1                        nếu đủ level
multiplier        = tích các yếu tố ở mục 5 (mặc định 1.00)

adjusted_h        = volume × base_rate × level_factor × multiplier × level_check
subtotal_h        = Σ adjusted_h
total_h           = subtotal_h × (1 + buffer_pct)
total_manday      = total_h / hours_per_manday
```

Estimate **không** tính số nhân sự và không tính duration — giai đoạn này chỉ chốt
**độ phức tạp**, **khối lượng** và **level người thực hiện**. Chia người và dựng
lịch là việc của bước planning.

Giờ họp / communication **không có dòng riêng** — nằm trong `buffer_pct`, vì giờ họp
không scale theo complexity cũng không scale theo level.

## 2. Trục 1 — Độ phức tạp task (S / M / L / XL)

Chấm bằng tiêu chí đếm được, không chấm bằng cảm nhận:

| Tiêu chí | S | M | L | XL |
|---|---|---|---|---|
| Số field / control trên màn hình | <= 5 | 6 - 15 | 16 - 30 | > 30 |
| Số validation rule | <= 3 | 4 - 10 | 11 - 20 | > 20 |
| Số alternate + exception flow | 0 - 1 | 2 - 3 | 4 - 6 | > 6 |
| Persist dữ liệu xuống DB | Không | 1 bảng | 2 - 3 bảng | > 3 bảng / có batch |
| Phụ thuộc module khác | Không | 1 module | 2 module | >= 3 module |
| Nhãn / message tiếng Nhật cần đối chiếu | Không | Ít | Nhiều | Toàn bộ màn hình |
| Số điểm mờ / `Cần xác nhận` trong tài liệu nguồn | 0 | 1 - 4 | 5 - 9 | >= 10 |

**Cả 7 tiêu chí đếm được thẳng từ tài liệu nghiệp vụ**, không cần requirement package —
đây là điều kiện để estimate chạy được ở thời điểm lên plan (mục 3.1). Ánh xạ sang
`外部設計書`:

| Tiêu chí | Đếm ở đâu trong `設計書` |
|---|---|
| Số field / control | `N_item` — số dòng `項目名` của `04_画面項目定義` |
| Số validation rule | `N_val` — số dòng có cột `バリデーション` không rỗng |
| Số alternate + exception flow | `N_flow` — nhánh điều kiện ở `05_処理内容` + số message ở `07_メッセージ一覧` |
| Persist dữ liệu xuống DB | `N_table` — số bảng ở `08_データベース` màn này ghi |
| Phụ thuộc module khác | số màn khác được tham chiếu ở `06_画面遷移` / `05_処理内容` |
| Nhãn / message tiếng Nhật | có `07_メッセージ一覧` cho màn này không, bao nhiêu dòng |
| Số điểm mờ | số chỗ phải hỏi lại trong block màn: ô trống, ghi chú mơ hồ, tham chiếu kiểu 「通常と同様」 phải đối chiếu màn khác |

> ⚠️ **KHÔNG lấy "`04_画面項目定義` rỗng" làm điểm mờ để đẩy complexity.** Chất lượng
> tài liệu nguồn đã được tính ở `A2b` + `R1` (mục 3.1.4); đưa vào complexity nữa là
> **đếm trùng** — đúng lỗi mà mục 5.1 đã phải vô hiệu 3 multiplier vì nó. Cụ thể: toàn
> bộ màn phía người dùng cuối trong tài liệu bản B đều có `04` rỗng, áp quy tắc đó thì `sample_module_g`
> (màn menu 2 mục, thực tế 18 TC / 1h) cũng bị chấm `XL`.

**Cách chấm:** đa số tiêu chí rơi vào cột nào thì lấy cột đó; hoà nhau → lấy cột cao hơn.
Ghi rõ các tiêu chí đã dùng vào `Note` của dòng estimate.

Module non-UI (API / batch / event): thay "số field trên màn hình" bằng "số tham số
payload / cột dữ liệu xử lý".

## 3. Trục 2 — Khối lượng công việc

18 activity, 4 nhóm:

- **G\*** — công **chỉ định AI gen** output: gom input, dựng manifest, viết prompt, chạy skill, chờ, đọc sơ output
- **A\*** — công **người làm**: đọc hiểu, review, execute, verify, chốt
- **S\*** — công **support** không giao được cho AI: môi trường, test data, follow-up bug, regression
- **R1** — **rework** khi output AI chưa đạt hoặc requirement đổi sau confirm

| # | Code | Hoạt động | Đơn vị | Cách lấy volume |
|---|---|---|---|---|
| 1 | G1 | Chuẩn bị input + chỉ định AI gen ticket task test | ticket | Số ticket cần gen |
| 2 | A1 | Review ticket task test AI gen | ticket | = volume G1 |
| 3 | G2 | Dựng manifest + chỉ định AI gen requirement | lần chạy | 1 lần / module; requirement đổi giữa chừng → cộng thêm |
| 4 | A2 | Đọc hiểu + review requirement AI tạo | requirement item | Đếm FR + BR + VR nếu đã có package; chưa có → `N_val + N_flow + số quy tắc nghiệp vụ` đọc từ `設計書` (3.1.1) |
| 5 | A2b | Q&A phân tích yêu cầu + confirm với PO | vòng Q&A | `qa_round_per_module` (1); **+1 nếu `04_画面項目定義` rỗng cho màn này** (3.1.4); có `open_points.md` rồi: >= 5 dòng → 2, >= 10 dòng → 3 |
| 6 | G3 | Chỉ định AI gen test case | lần chạy | 1 lần / module |
| 7 | A3 | Review test case AI gen + update | test case | Đếm `testcase_draft.csv` nếu có; chưa có → **liệt kê từ tài liệu nghiệp vụ** (3.1) |
| 8 | S1 | Setup môi trường test + account / quyền | môi trường | **Project-level** — tính 1 lần (mục 3.1) |
| 9 | S2 | Chuẩn bị test data | bộ data | **Project-level** nếu dùng chung; data riêng module → tính theo module |
| 10 | A4 | Execute test | test case | = volume A3 |
| 11 | G4 | Cung cấp evidence + chỉ định AI log bug | bug | `bugs_per_module` (1) — xem 3.1.5 |
| 12 | A4b | Review bug AI log (dedupe / severity / repro) | bug | = volume G4 |
| 13 | A5 | Verify bug | bug × round | = volume A4b × `retest_rounds` |
| 14 | S3 | Follow-up bug (reject / reopen / trao đổi dev) | bug | = volume A4b × `bug_followup_rate` |
| 15 | S4 | Regression test vùng ảnh hưởng | test case | = volume A4 × `regression_scope_rate` |
| 16 | R1 | Re-prompt + review lại (rework output AI / requirement đổi) | vòng rework | `rework_rounds` (1); **+1 nếu tài liệu nguồn mỏng** (3.1.4); AI `pilot` → 2, `mature` → 0.5 |
| 17 | G5 | Chỉ định AI gen test report | module | 1 / module |
| 18 | A6 | Review + chốt test report, cập nhật status ticket | module | 1 / module |

### 3.1. Dự báo khối lượng — ESTIMATE TỪ TÀI LIỆU NGHIỆP VỤ, KHÔNG chờ requirement / test case

**Estimate phải chạy được ngay khi có tài liệu nghiệp vụ (`設計書` / spec / ticket).**
Đó là thời điểm cần con số: để lên plan, chia người, chốt lịch — trước khi QA bắt đầu
bất cứ việc gì.

> **Vì sao bắt buộc phải như vậy:** bản estimate này tính cả `G2`/`A2` (gen + review
> requirement) và `G3`/`A3` (gen + review test case). Nếu phải chạy `gen-requirement`
> hay `gen-testcase` xong mới estimate được, thì đang **estimate công việc vừa làm xong**
> — con số ra sau khi đã tiêu tiền, không dùng để lên plan được nữa.

#### 3 tier đầu vào

| Tier | Có gì | Cách suy volume | Độ tin cậy |
|---|---|---|---|
| **1** | **Tài liệu nghiệp vụ gốc** (`設計書`, spec, ticket) | Đếm theo bảng 3.1.1 → liệt kê theo 3.1.2 | **Trung bình** |
| 2 | + requirement package | Đếm trực tiếp FR/BR/VR + liệt kê theo 3.1.2 | Trung bình - Cao |
| 3 | + `testcase_draft.csv` | Đếm dòng | **Cao** |

**Tier 1 là đường chạy bình thường.** Tier 2 / 3 chỉ để tinh chỉnh lại nếu tình cờ đã có.
**Cấm** yêu cầu tier cao hơn như điều kiện để estimate.

Không có cả tài liệu nghiệp vụ → **KHÔNG estimate**, dừng và báo thiếu input.

#### 3.1.1. Đếm gì trong tài liệu nghiệp vụ

Cấu trúc `外部設計書` của dự án tham chiếu (kiểm chứng trên 2 file `inputs/*.xlsx`):

| Sheet | Đếm | Ký hiệu | Dùng cho |
|---|---|---|---|
| `03_画面レイアウト` | số block `画面名`, số khối UI trong mỗi màn | `N_screen` · `N_block` | UI TC · phạm vi module |
| `04_画面項目定義` | số dòng `項目名` | **`N_item`** | Positive TC · tiêu chí complexity "số field/control" |
| `04_画面項目定義` | số dòng có cột `バリデーション` không rỗng | **`N_val`** | Form Validation TC · tiêu chí "số validation rule" |
| `04_画面項目定義` | số dòng có `Kiểu` là Textbox / Picker / Checkbox / Radio / Selectbox | `N_input` | Form Validation TC |
| `04_画面項目定義` | số `セクション` khác nhau | `N_sec` | UI TC |
| `05_処理内容` | số xử lý / nhánh điều kiện | `N_flow` | Positive + Negative TC |
| `06_画面遷移` | số điều hướng ra / vào màn | `N_nav` | Trigger/Navigation TC |
| `07_メッセージ一覧` | số message lỗi / cảnh báo của màn | `N_msg` | Negative TC |
| `08_データベース` | số bảng màn ghi xuống | `N_table` | tiêu chí complexity "persist DB" |

Số đếm thật của 2 file tài liệu nguồn (dùng làm mốc đối chiếu):

| Màn trong `04_画面項目定義` | `N_item` | `N_val` | `N_input` | `N_sec` |
|---|---|---|---|---|
| `Screen H` (form nhập lịch, nhiều validation) | 9 | 6 | 9 | 1 |
| `Screen I` (cấu hình loại chỗ / loại vé / giá, ít field) | 3 | 3 | 3 | 1 |
| `Screen F` (màn cấu hình nhiều tab) | 18 | 7 | 12 | 5 |
| `Screen J` (cấu hình số chỗ, hầu như chỉ hiển thị) | 4 | 0 | 1 | 1 |
| `Screen D` (danh sách quản lý) | 10 | 0 | 1 | 2 |
| `Screen E` (màn xử lý nghiệp vụ phức tạp) | 52 | 6 | 5 | 10 |
| `Screen A` (form tra cứu, nhiều điều kiện lọc) | 37 | 1 | 7 | 2 |
| `Screen K` (màn thiết lập danh sách chặn) | 9 | 2 | 2 | 3 |

#### 3.1.2. Dự báo số test case — LIỆT KÊ, cấm nhân hệ số

Mọi hệ số nhân đơn đều vỡ trên dữ liệu thật:

| Hệ số thử | Dải quan sát | Spread |
|---|---|---|
| TC / requirement item | 1.25 – 3.36 | 2.7× |
| TC / item màn hình | 1.76 – 3.60 | 2.0× |
| TC / dòng bảng `screen_specification.md` | 0.95 – 4.11 | 4.3× |
| TC / `N_item` của `04_画面項目定義` | 1.86 – 4.11 | 2.2× |

Không hệ số nào dưới 2×. Dự báo bằng cách nhân là **đoán có trang trí**.

Cách đúng: **liệt kê nhóm test case rồi cộng lại** — đúng cách một QA làm, chỉ dừng ở
mức đếm, không viết step / expected result.

| Phần tử đếm được | TC | Nhóm |
|---|---|---|
| Mỗi màn / entry point (`03_画面レイアウト`) | 1 | Trigger/Navigation |
| Mỗi điều hướng trong `06_画面遷移` | 1 | Trigger/Navigation |
| Mỗi `セクション` / khối UI | 1 | UI |
| Mỗi item hiển thị có nhãn / format / màu cố định phải đối chiếu | 1 | UI |
| Mỗi item trong `04_画面項目定義` không phải filter / trạng thái | 1 | Positive |
| Mỗi **điều kiện tìm kiếm / filter** | **3** | Positive (hợp lệ · rỗng · không khớp) |
| Mỗi **trạng thái dữ liệu** (`status` / `kbn`, đọc ở `08_データベース`) | **2** | Positive |
| Mỗi hành động ghi dữ liệu (tạo / sửa / xoá / huỷ) | 2 | Positive |
| Mỗi nhánh điều kiện trong `05_処理内容` | 1 | Positive |
| Mỗi dòng `バリデーション` gắn với field nhập liệu | 1 | Form Validation |
| Mỗi message trong `07_メッセージ一覧` | 1 | Negative |

**Hai thứ KHÔNG được đếm thành test case riêng** (rút ra từ lần kiểm tier-1 đầu tiên,
mục 6):

1. **Item ghi 「既存画面と同様に表示する」 / 「従来通り」 / "same as existing"** —
   là vùng regression của chức năng cũ, không phải hành vi mới. Gộp **toàn bộ** thành
   **1** test case, không tính 1 TC mỗi item. Trên `Screen C` riêng dòng này đã
   là 8 item.
2. **Nhãn trạng thái đã tính ở dòng "trạng thái dữ liệu"** thì **không** đếm lại ở dòng
   UI. Nhãn `Chưa xử lý` / `Trúng` / `Trượt` có màu + font riêng nhưng vẫn nằm trong test case
   của chính trạng thái đó.

**Rồi nhân `enum_correction` = 0.85.** Phép liệt kê đo được là **luôn thừa, chưa lần nào
thiếu**: navigator dự báo 20 / thật 18 (+11%), history_list dự báo 25 / thật 20 (+25%),
`Screen C` dự báo 42.5 / suy từ log 36 (+18% ở bậc `M`).

**Hai dòng đắt nhất là `filter` (3 TC) và `trạng thái dữ liệu` (2 TC)** — đây là chỗ giải
thích vì sao `sample_module_a` ra 69 TC còn `sample_module_g` chỉ 18.
Bằng chứng đếm thật: field `Từ khoá` sinh 6 TC, filter `Kết quả xử lý` sinh 6 TC, mỗi trạng
thái `Trúng` / `Chưa xử lý` / `Trượt` sinh 2 - 3 TC.

#### 3.1.3. Cross-check bắt buộc

Kết quả liệt kê phải rơi vào dải của loại màn tương ứng:

| Loại màn | TC / req item | Neo vào |
|---|---|---|
| Hiển thị / menu / list read-only, ít trạng thái | **1.25 - 1.50** | `sample_module_g` 1.50 · `sample_module_b` 1.25 |
| Tra cứu: filter + bảng kết quả + nhiều trạng thái | **~3.1** | `sample_module_a` 3.14 |
| Nhập liệu / edit form nhiều validation | **~3.4** | `sample_module_h` 3.36 |

Ở tier 1 chưa có số requirement item thật → suy tạm `req_item ≈ N_val + N_flow + số quy
tắc nghiệp vụ đọc được`, rồi đối chiếu. Lệch quá **40%** → **không tự chọn số nào**, ghi
1 dòng `Open point` nêu cả hai kết quả.

Chỉ khi **không đếm được gì** mới dùng `(FR + BR + VR) × tc_per_req_item` (**2.3**) kèm
`Open point` độ tin cậy `Thấp` — số để không tắc, không phải số để chốt giá.

#### 3.1.4. Chất lượng tài liệu nguồn — ảnh hưởng A2b và R1, KHÔNG ảnh hưởng số TC

Đo được trên 2 hệ thống của cùng một dự án:

| Tài liệu | `04_画面項目定義` | Hệ quả |
|---|---|---|
| Tài liệu thiết kế **bản A** (đầy đủ item) | đầy đủ `Kiểu` / `Giá trị mặc định` / `バリデーション` / `DB項目` | đếm thẳng được |
| Tài liệu thiết kế **bản B** (chỉ có block màn, thiếu dòng item) | **8 block màn, 0 dòng item** — bảng rỗng | phải dựng lại từ ảnh layout |

**Tài liệu mỏng KHÔNG có nghĩa ít việc.** `sample_module_g` có 0 dòng item trong
nguồn nhưng requirement package vẫn ra **12 item** và **18 test case** — toàn bộ phải
suy ngược từ ảnh layout và hỏi lại PO.

→ Tài liệu nguồn mỏng thì **cộng vào `A2b` (vòng Q&A) và `R1` (rework)**, không giảm số
TC. Cụ thể: `04_画面項目定義` rỗng cho màn đang estimate → `qa_round_per_module` +1 và
`rework_rounds` +1, ghi lý do vào `Note`.

#### 3.1.5. Số bug — đếm theo module, KHÔNG theo % test case

`bugs_per_module` = **1** (phase UI test), dùng cho `G4` · `A4b` · `A5` · `S3`.

Cách cũ (`TC × expected_defect_rate` 25%) sai nặng: `sample_module_a` 69 TC →
dự báo **17 bug**, thực tế **~1 bug / chức năng**. `expected_defect_rate` vẫn còn trong
`Rate Card` nhưng **tắt mặc định**; chỉ bật lại khi có dữ liệu defect thật của một phase
test sâu hơn (integration / regression).

**BA/dev chạy AI thay QA** → G2 (và G1/G3 nếu tương ứng) để `Volume = 0`, ghi lý do vào `Note`.

### 3.2. Project-level vs module-level

- `S1` (môi trường + account/quyền) và `S2` (test data dùng chung) trả **1 lần cho cả dự án**.
- Đặt ở dòng có `Function = project_level`. Các module sau để `Volume = 0` + `Note` trỏ về dòng `project_level`.
- Data riêng của một module (file import đặc thù, bộ dữ liệu nghiệp vụ riêng) → vẫn tính `S2` theo module đó.

## 4. Trục 3 — Level nhân sự

`base_rate` là **giờ của Middle**. Level khác quy đổi qua factor.

> ⚠️ **Log giờ thực tế hầu như không phải giờ Middle.** Trước khi nạp một con số đo
> được vào bảng base rate, **chia cho `level_factor` của người đã làm**. Bộ số
> 2026-08-19 suýt sai đúng chỗ này: dữ liệu là giờ của một bạn **Junior**, nhét thẳng
> vào ô Middle thì mọi estimate lệch lên **1.3 lần**.

### 4.1. Activity KHÔNG nhạy level — nhóm G*

`G1` `G2` `G3` `G4` `G5` dùng **`level_factor` cứng = 1.00 ở mọi level.**

Phần lớn giờ của nhóm G* là **gom input, chạy skill và chờ output** — Fresher hay
Senior bấm chạy thì AI vẫn mất từng ấy thời gian. Chỉ nhóm `A*` (đọc hiểu, review,
execute, verify) và `S*` / `R1` mới scale theo level.

Cột `Level factor` trong template tự trả `1.00` cho các dòng này, điều khiển bằng cột
**`Nhạy level? (1/0)`** ở bảng 3 của `Rate Card`.

**`level_check` vẫn áp bình thường cho nhóm G*** — gán người dưới mức tối thiểu của
`G2` vẫn cộng phụ phí senior review. Chi phí *chạy* không đổi theo level, nhưng chi phí
*sai* thì có.

| Level | Factor | Rank | Vì sao |
|---|---|---|---|

| Fresher | 1.6 | 1 | Chưa đủ nền phản biện output AI → đọc lại nhiều vòng, dễ sót lỗi logic |
| Junior | 1.3 | 2 | Review được nhưng phải đối chiếu requirement từng dòng |
| Middle | 1.0 | 3 | Baseline |
| Senior | 0.8 | 4 | Bắt sai lệch AI nhanh, quyết được điểm mờ, ít vòng lặp |

**Đã được QA xác nhận định tính (2026-08-20): giữ nguyên bộ factor này.** Cơ chế QA nêu:
level thấp chậm hơn **ở các hoạt động review** — đọc requirement, review test case AI gen,
review bug log — vì phải đối chiếu từng dòng thay vì bắt sai lệch bằng kinh nghiệm.

Vẫn **chưa có điểm đo định lượng** nào: cả 4 log đều từ một bạn Junior nên không có cặp
so sánh giữa 2 level. Độ tin cậy `Thấp` cho giá trị tuyệt đối, `Trung bình` cho hướng
và cho việc nhóm `A*` chịu ảnh hưởng level còn nhóm `G*` thì không.

### Level tối thiểu theo activity

| Level tối thiểu | Activity | Gán thấp hơn → phụ phí |
|---|---|---|
| **Middle** | G2 · A2 · A2b · R1 · A6 | +30% |
| Junior | A1 · G3 · A3 · S1 · S2 · G4 · A4b · S3 | +20% |
| Fresher | G1 · A4 · A5 · S4 · G5 | — |

Nhóm Middle là chỗ sai là sai cả chuỗi: hiểu sai requirement (G2/A2/A2b), quyết sai
hướng rework (R1), chốt report sai (A6). Không cho Fresher/Junior đứng một mình mà
không có senior review.

## 5. Multiplier

Nhân dồn khi có nhiều yếu tố cùng đúng:

| Yếu tố | Giá trị | Áp dụng khi |
|---|---|---|
| `module_type_new` | 1.00 | Module làm mới |
| `module_type_modify` | 0.85 | Sửa đổi / enhancement trên module đã có |
| `domain_first_time` | 1.25 | Tester lần đầu làm nghiệp vụ này |
| `ai_output_maturity_pilot` | 1.30 | Prompt/skill AI mới dùng, output còn nhiều rework |
| `ai_output_maturity_stable` | 1.00 | Prompt/skill AI đã ổn định (mặc định) |
| `ai_output_maturity_mature` | 0.90 | Output AI đã qua nhiều vòng tinh chỉnh |

### 5.1. Ba multiplier đã bị vô hiệu — chống đếm trùng (2026-08-18)

| Yếu tố | Giá trị cũ | Trùng với tiêu chí complexity nào ở §2 |
|---|---|---|
| `requirement_unstable` | 1.20 | "Số dòng `open_points.md`" |
| `ui_japanese` | 1.10 | "Nhãn / message tiếng Nhật cần đối chiếu" |
| `cross_module` | 1.15 | "Phụ thuộc module khác" |

Cả 3 yếu tố này **đã** được dùng để chấm bậc complexity ở §2; áp thêm multiplier là
nhân dồn cùng một yếu tố hai lần. Ví dụ thật: `sample_module_l` có 10
open point → tiêu chí 7 đẩy complexity lên `XL`, rồi `requirement_unstable` lại nhân
tiếp 1.20. Ba yếu tố cộng lại tạo hệ số 1.518 chồng lên bậc `XL` — riêng lỗi này thổi
estimate lên ~1.5 lần.

Giá trị hiện tại của cả 3 = `1.00` (giữ dòng trong `Rate Card` để còn dấu vết, không xoá).
**Chỉ bật lại** nếu đồng thời bỏ tiêu chí tương ứng khỏi bảng §2 — nếu không, lỗi tái diễn.

## 6. Base rate — giờ / đơn vị, tính cho Middle

| # | Code | Hoạt động | Đơn vị | S | M | L | XL | XL quy ra phút |
|---|---|---|---|---|---|---|---|---|
| 1 | G1 | Chuẩn bị input + chỉ định AI gen ticket task test | ticket | 0.03 | 0.05 | 0.065 | 0.08 | 4.8 /ticket |
| 2 | A1 | Review ticket task test AI gen | ticket | 0.03 | 0.05 | 0.065 | 0.08 | 4.8 /ticket |
| 3 | G2 | Dựng manifest + chỉ định AI gen requirement | lần chạy | 0.08 | 0.12 | 0.16 | 0.20 | 12 /lần |
| 4 | A2 | Đọc hiểu + review requirement AI tạo | requirement item | 0.02 | 0.025 | 0.03 | 0.04 | 2.4 /item |
| 5 | A2b | Q&A phân tích yêu cầu + confirm với PO | vòng Q&A | 0.15 | 0.25 | 0.32 | 0.40 | 24 /vòng |
| 6 | G3 | Chỉ định AI gen test case | lần chạy | 0.103 | 0.155 | 0.207 | 0.258 | 15.5 /lần |
| 7 | A3 | Review test case AI gen + update | test case | 0.026 | 0.034 | 0.043 | 0.051 | 3.1 /case |
| 8 | S1 | Setup môi trường test + account / quyền | môi trường | 0.50 | 1.00 | 2.00 | 3.00 | 180 /môi trường |
| 9 | S2 | Chuẩn bị test data | bộ data | 0.50 | 1.00 | 1.50 | 2.50 | 150 /bộ |
| 10 | A4 | Execute test | test case | 0.065 | 0.081 | 0.105 | 0.130 | **7.8 /case** |
| 11 | G4 | Cung cấp evidence + chỉ định AI log bug | bug | 0.015 | 0.02 | 0.025 | 0.03 | 1.8 /bug |
| 12 | A4b | Review bug AI log (dedupe / severity / repro) | bug | 0.04 | 0.05 | 0.065 | 0.08 | 4.8 /bug |
| 13 | A5 | Verify bug | bug × round | 0.158 | 0.190 | 0.253 | 0.317 | 19 /bug×round |
| 14 | S3 | Follow-up bug (reject / reopen / trao đổi dev) | bug | 0.015 | 0.02 | 0.025 | 0.03 | 1.8 /bug |
| 15 | S4 | Regression test vùng ảnh hưởng | test case | 0.02 | 0.025 | 0.03 | 0.04 | 2.4 /case |
| 16 | R1 | Re-prompt + review lại (rework AI / requirement đổi) | vòng rework | 0.08 | 0.12 | 0.16 | 0.20 | 12 /vòng |
| 17 | G5 | Chỉ định AI gen test report | module | 0.04 | 0.06 | 0.08 | 0.10 | 6 /module |
| 18 | A6 | Review + chốt test report, cập nhật status ticket | module | 0.06 | 0.09 | 0.12 | 0.15 | 9 /module |

Tham số phái sinh: **`bugs_per_module` 1** (mục 3.1.5) · `retest_rounds` 2 · `bug_followup_rate` 30% ·
`regression_scope_rate` 30% · `rework_rounds` 1 · `qa_round_per_module` 1 ·
`buffer_pct` 15% · `hours_per_manday` 8 · `tc_per_req_item` **2.3** (chỉ tier 3, mục 3.1) ·
`enum_correction` **0.85** (hiệu chỉnh phép liệt kê TC, mục 3.1).

### CALIBRATE 2026-08-19 — G3 / A3 / A4, lần đầu có log giờ thực tế

Điểm dữ liệu đầu tiên có **giờ thực tế ghi theo từng activity**. Nguồn: log effort QA
dự án tham chiếu, 4 màn, **người thực hiện level `Junior`**.

| Màn | module_name | TC thật | Hoạt động | Giờ thực (Junior) |
|---|---|---|---|---|
| Screen G (menu 2 mục) | `sample_module_g` | 18 | gen + review TC (G3+A3) | 1.00 |
| Screen G (menu 2 mục) | `sample_module_g` | 18 | test UI (A4) | 2.00 |
| Screen B (danh sách lịch sử) | `sample_module_b` | 20 | gen + review TC (G3+A3) | 1.00 |
| Screen B (danh sách lịch sử) | `sample_module_b` | 20 | test UI (A4) | 2.00 |
| Screen C (màn chi tiết, nhiều trạng thái) | `sample_module_c` | *chưa có CSV* | gen + review TC (G3+A3) | 1.75 |
| Screen A (form tra cứu, nhiều filter) | `sample_module_a` | 69 | verify bug (A5) | 0.25 |

Cả 4 màn chấm complexity `M`, multiplier 1.00.

#### Bước bắt buộc: quy giờ Junior về giờ Middle

`BASE_RATES` là **giờ Middle**. Log là **giờ Junior** (`level_factor` 1.3) → phải chia
1.3 trước khi nạp. Riêng `G3` thuộc nhóm không nhạy level (mục 4.1) nên factor = 1.00,
không chia.

**A4** — chia trực tiếp:

| Màn | Giờ Junior / TC | ÷ 1.3 → giờ Middle |
|---|---|---|
| Screen G | 2.00 / 18 = 0.1111 | **0.0855** |
| Screen B | 2.00 / 20 = 0.1000 | **0.0769** |

trung bình → `A4` bậc `M` = **0.081 h/case = 4.9 phút**.

> Con số này **khớp với trực giác "execute ~5 phút/case"** mà QA đưa ra từ 2026-08-18 —
> trực giác đó vốn nói về người làm bình thường (Middle), lần calibrate trước lại gán
> nhầm nó vào cột `XL`.

**G3 + A3** — log gộp chung 1 con số nên phải giải hệ, với `G3` phẳng và `A3` × 1.3:

```
G3_M + 1.3 × A3_M × TC = 1.00
```

Hai điểm 18 TC và 20 TC đều cho vế phải = 1.00 (số đã làm tròn) → hệ suy biến, không
tách được `G3` khỏi `A3`. Giữ nguyên tỷ lệ của bộ cũ và giải cho hệ số chung `k`:

| Màn | Phương trình | k |
|---|---|---|
| Screen G | `0.09k + 1.3 × 0.02k × 18 = 1.00` | 1.792 |
| Screen B | `0.09k + 1.3 × 0.02k × 20 = 1.00` | 1.639 |

trung bình `k` = **1.716** → `G3` bậc `M` = **0.155**, `A3` bậc `M` = **0.034**.

#### Bộ số chốt

| Code | Bộ cũ (S/M/L/XL) | Bộ mới (S/M/L/XL) | M quy ra phút (Middle) |
|---|---|---|---|
| G3 | 0.06 / 0.09 / 0.12 / 0.15 | **0.103 / 0.155 / 0.207 / 0.258** | 5.4 → **9.3** /lần chạy |
| A3 | 0.015 / 0.02 / 0.025 / 0.03 | **0.026 / 0.034 / 0.043 / 0.051** | 1.2 → **2.0** /case |
| A4 | 0.04 / 0.05 / 0.065 / 0.08 | **0.065 / 0.081 / 0.105 / 0.130** | 3.0 → **4.9** /case |

15 activity còn lại **không đụng vào** — chưa có log giờ.

Kiểm ngược, quy lại về giờ Junior để so với log gốc:

| Màn | G3+A3 dự báo | thực | A4 dự báo | thực |
|---|---|---|---|---|
| Screen G (18 TC) | 0.951h | 1.00 | 1.895h | 2.00 |
| Screen B (20 TC) | 1.039h | 1.00 | 2.106h | 2.00 |

#### Bổ sung 2026-08-20 — A5 verify bug, và số bug tính theo module

QA chốt: phase UI test hiện tại **~1 bug / chức năng**. Có mẫu số thì tính được A5.

| | Giá trị |
|---|---|
| Giờ log (Junior) | 0.25h |
| Số bug | 1 |
| Số vòng verify đã chạy | **1** *(QA xác nhận 2026-08-20)* |
| → giờ Middle / bug-round | `0.25 / 1.3 / 1` = **0.192** → chốt **0.19** |

`A5` bậc `M`: **0.03 → 0.190** (1.8 phút → **11.4 phút / bug-round**). Rate cũ coi verify
1 bug chỉ mất 1.8 phút — không đủ để mở ticket, dựng lại precondition, chạy lại repro,
đối chiếu và cập nhật trạng thái.

**Cảnh báo còn lại:** `0.25h` nhiều khả năng là **đơn vị log nhỏ nhất** (15 phút) → đây
là **cận trên**, effort thật có thể thấp hơn. Số vòng verify đã được xác nhận là 1 nên
không còn nhập nhằng ×2.

`retest_rounds` = 2 vẫn **chưa đo** — đó là giả định "bug fail 1 lần rồi mới pass".

**Số bug: bỏ cách nhân % test case.** `expected_defect_rate` 25% dự báo
`sample_module_a` (69 TC) có **17 bug**; thực tế ~**1**. Sai 17 lần, và sai
theo hướng thổi phồng đúng 4 dòng cuối luồng (`G4` `A4b` `A5` `S3`). Thay bằng
`bugs_per_module` = 1 (mục 3.1.5).

Hiệu ứng gộp trên `sample_module_a`, quy về giờ Junior:

| | Bộ cũ | Bộ mới | Thực đo |
|---|---|---|---|
| Volume A5 | 69 × 25% × 2 = 34.5 | 1 × 2 = 2 | — |
| Giờ A5 | 34.5 × 0.03 × 1.3 = **1.35h** | 2 × 0.19 × 1.3 = **0.49h** | 0.25h *(mới 1 vòng)* |

#### Kiểm chứng tier-1 đầu tiên — `sample_module_c` (2026-08-20)

Lần đầu chạy estimate **thuần từ `設計書`**, không có requirement package, không có
`testcase_draft.csv`. Nguồn: tài liệu thiết kế **bản B** sheet `03_画面レイアウト` dòng 659 - 997
(4 trạng thái `Chưa xử lý` / `Trúng (chưa thanh toán)` / `Trúng (đã thanh toán)` / `Trượt` + huỷ đơn + dialog xác
nhận + 2 nhánh phương thức thanh toán). Sheet `04_画面項目定義` **rỗng**.

Liệt kê ra **59 điểm thô** → sau 2 quy tắc loại trừ ở 3.1.2 còn **50** → × 0.85 = **42.5 TC**.

Đối chiếu với log thật `1.75h` (Junior, gen + review test case):

| Bậc complexity | Dự báo với 42.5 TC | TC suy ngược từ 1.75h | Lệch |
|---|---|---|---|
| `M` | 2.03h | **36** | **+16%** |
| `L` | 2.58h | 28 | +48% |
| `XL` | 3.08h | 23 | +76% |

**Chỉ bậc `M` khớp.** Nhưng chấm complexity cho màn này bằng bảng mục 2 lại ra `L`
(field `L` · validation `S` · flow `XL` · persist `M` · phụ thuộc module `XL` · nhãn JP
`L` · điểm mờ `L`).

Hai khả năng, **một điểm dữ liệu không tách được**:

| Khả năng | Hệ quả nếu đúng |
|---|---|
| **(a)** Phép liệt kê vẫn thừa trên màn nhiều nội dung | Cần thêm quy tắc gộp; `enum_correction` phải giảm theo kích thước màn |
| **(b)** Thang `S`/`M`/`L`/`XL` của base rate quá dốc | Cả 3 log trước đều bậc `M` → **chưa bậc nào ngoài `M` được đo**. Tỷ lệ 0.75/1/1.25/1.5 là suy luận thuần |

Khả năng **(b) đáng ngờ hơn**: bậc `M` khớp ở cả 3 module đã log, và nhảy sang `L` chỉ
đổi bậc một nấc đã đẩy sai số từ +16% lên +48%.

**Chưa sửa thang complexity** — sửa theo 1 điểm là đổi một suy luận này lấy một suy luận
khác. Đây là việc đo ưu tiên số 1 (mục dưới).

**Một lỗi đã sửa nhờ lần chạy này:** quy tắc "`04_画面項目定義` rỗng → điểm mờ `>= 10`"
(thêm 2026-08-20) đẩy **mọi** màn phía người dùng cuối lên `XL`, kể cả `sample_module_g`
vốn là menu 2 mục. Đó là đếm trùng với `A2b`/`R1` — đã gỡ khỏi mục 2.

#### Ba điều bộ số này CHƯA giải quyết được

**1. Không tách được chi phí cố định / chi phí theo test case của G3+A3.**
18 TC → 1.00h và 20 TC → 1.00h: số TC lệch 11% mà giờ làm tròn bằng nhau, khớp cả
"gần như toàn bộ là chi phí cố định" lẫn "tuyến tính ~2 phút/TC". Đang **giữ dạng tuyến
tính** vì ít xáo trộn model nhất. Cần 1 module **>= 40 TC** để phân định.
`sample_module_c` (1.75h) gợi ý dạng tuyến tính còn đứng được: nếu bậc `L`,
`0.207 + 1.3 × 0.043 × TC = 1.75` → **TC ≈ 27**, hợp với mô tả registry (màn nhiều trạng
thái nhất phía người dùng cuối). **Chưa xác nhận** vì màn này chưa có `testcase_draft.csv`.

**2. `level_factor` chưa có điểm đo nào.**
Cả 4 log đều từ một bạn Junior → không có cặp so sánh giữa 2 level. Dải hiện tại
(1.6 → 0.8) là suy luận, và phản hồi định tính cho thấy nó **rộng quá** (mục 4).

**3. `A5` dựa trên đúng 1 điểm đo, và là cận trên.**
Mẫu số đã rõ (1 bug × 1 vòng) nhưng `0.25h` là đơn vị log nhỏ nhất. Cần log tiếp 1 module
có **>= 3 bug** để biết rate thật nằm ở đâu trong khoảng `(0, 0.19]`. `retest_rounds` = 2
cũng chưa có điểm đo nào.

**4. `bugs_per_module` = 1 chỉ đúng cho phase UI test.**
Test sâu hơn (integration, regression, luồng nghiệp vụ đầu-cuối) chắc chắn ra nhiều bug
hơn. Khi sang phase đó phải đo lại — **không** quay về nhân % test case, vì đó là cách
đã chứng minh sai 17 lần.

### Cơ sở của bộ số — CALIBRATE 2026-08-18

Bộ số này **thay bộ DEFAULT ban đầu**, vốn sai khoảng **15 lần** ở cột XL. Hai nguồn neo:

1. **Phản hồi QA dự án tham chiếu (2026-08-18)** — execute ~5 phút/test case là hợp lý; các
   hoạt động còn lại trước đó tính dư nhiều; 18 test case thì tổng phải rõ ràng dưới 1 ngày.
2. **`testcases/sample_module_h/testcase_draft.csv`** — 37 test case đếm thật, cho
   hệ số `tc_per_req_item`.

Bộ cũ sai ở đâu (giữ lại để không lặp lại):

| Hoạt động | Rate cũ (XL) | Quy ra | Vô lý ở chỗ |
|---|---|---|---|
| A4 execute | 0.70 | 42 phút/case | Execute 1 test case trên màn web không mất 42 phút |
| A2 review requirement | 0.70 | 42 phút/item | Đọc 1 mục FR/BR/VR không mất 42 phút |
| A3 review TC AI gen | 0.40 | 24 phút/case | Review case AI đã sinh sẵn, không phải tự viết |
| A2b Q&A | 4.00 | 4h/vòng | Giờ **chờ** PO trả lời không phải effort của QA |

Nguyên tắc giữ nguyên từ bộ cũ:

- Review 1 test case AI gen nhanh hơn tự viết nhiều, nhưng **không miễn phí** — vẫn phải
  đối chiếu requirement, sửa expected result, bỏ case trùng.
- **G4 tính theo bug, không theo test case** — chỉ case fail mới phải gom evidence.
- Verify bug (A5) rẻ vì đã có repro sẵn.
- **S1/S2 giữ nguyên bậc giờ** — dựng môi trường và bộ data thật sự tốn hàng giờ; đây
  là chi phí **project-level trả 1 lần**, môi trường đã sẵn thì để `Volume = 0`, KHÔNG
  hạ rate để bù.

### Độ tin cậy hiện tại — cập nhật 2026-08-19

Không còn đồng hạng cho cả bảng. Chia theo activity:

| Hạng mục | Độ tin cậy | Neo vào |
|---|---|---|
| **A4** execute | **Trung bình** | 2 log giờ thực, 2 module, cùng bậc `M`, lệch nhau 10%, đã quy về Middle |
| **G3 + A3** (tổng) | **Trung bình** | 2 log giờ thực; nhưng **cách chia** giữa G3 và A3 chỉ là giả định (mục trên, điểm 1) |
| **A3 riêng lẻ** | **Thấp** | Chưa tách được khỏi G3 |
| Dự báo TC bằng liệt kê (mục 3.1) | **Trung bình** | Kiểm trên 2 module: thừa 11% và 25%, luôn thừa chứ chưa lần nào thiếu |
| `tc_per_req_item` (tier 3) | **Thấp** | Spread 2.7 lần |
| **`level_factor`** (1.6 / 1.3 / 1.0 / 0.8) | **Thấp** | **Chưa có điểm đo nào** — cả 4 log đều từ một bạn Junior |
| Nhóm G* phẳng theo level | **Trung bình** | Phản hồi trực tiếp của QA: giờ gen TC như nhau ở mọi level |
| **A5** verify bug | **Thấp** | 1 log giờ **không kèm số bug** → không tính được rate |
| `expected_defect_rate` · `retest_rounds` | **Thấp** | Chưa đo; dữ kiện 2026-08-19 cho thấy tổ hợp 3 tham số này đang thổi A5 lên ~5.4 lần |
| **A2b** Q&A · **R1** rework | **Thấp** | Chưa có log; A2b phụ thuộc số open point PO phải quyết, R1 phụ thuộc độ chín prompt |
| 11 activity còn lại | **Thấp** | Chưa có log giờ nào |

- **Cao** cho: tỷ lệ tương đối giữa các activity, và cho việc bộ DEFAULT ban đầu sai.
- Bậc S/M/L/XL trong mỗi dòng vẫn là **tỷ lệ suy ra**, chưa bậc nào được đo riêng —
  cả 4 điểm dữ liệu 2026-08-19 đều rơi vào bậc `M`.

### Việc đo kế tiếp — xếp theo giá trị thu được

1. **Log 1 module bậc `L` hoặc `XL`** → tách được khả năng (a) và (b) ở mục kiểm chứng
   tier-1 trên. Cả 4 log hiện có đều bậc `M`, nên **thang complexity chưa có điểm đo nào**
   — đây là suy luận lớn nhất còn sót trong model.
2. **Ghi số TC thật của `sample_module_c`** sau khi gen → xác nhận ngay con
   số 36 suy ngược, chốt luôn khả năng (a) hay (b).
3. **Log cùng 1 activity ở 2 level khác nhau** (vd 2 bạn cùng execute 2 màn tương đương)
   → lần đầu đo được `level_factor`, hiện chưa có điểm nào.
4. **Log G3 và A3 tách riêng** trên 1 module **>= 40 TC** → phân định chi phí cố định
   / chi phí theo case.
5. **Log thêm số bug** trên 1 module có **>= 3 bug** → siết `A5` và `retest_rounds`.
6. Log A2 / A2b / R1 → 3 activity đầu luồng, hiện chưa có số nào.

### Cách calibrate

1. Chạy 1 module thật, ghi giờ thực tế **theo từng activity** vào `Assumptions & Risks`
   — kèm **mẫu số** theo mục 7. Log không có mẫu số **không dùng calibrate được**.
2. `factor_thực = giờ_thực / giờ_estimate` cho từng activity.
3. Sau 2 - 3 module, nhân base rate của activity đó với trung bình `factor_thực`.
4. **Chỉ sửa activity có log.** Activity không có log giữ nguyên — sửa "cho đồng bộ"
   là quay lại lỗi đoán số của bộ DEFAULT ban đầu.
5. Giữ nguyên tỷ lệ S/M/L/XL của activity đó, trừ khi log rơi vào nhiều bậc khác nhau.
6. Sửa `scripts/estimate_template_data.py` + bảng ở mục 6, cập nhật ví dụ regression
   ở mục 8, rồi chạy lại `python3 scripts/build_estimate_template.py`.

## 7. Log effort thực tế — mẫu số bắt buộc

Giờ thực tế chỉ calibrate được khi biết **chia cho cái gì**. Log
`verify bug màn Screen A (0.25h)` là ví dụ thật của một log **không dùng được**:
không biết verify bao nhiêu bug thì không suy ra được giờ / bug-round (xem mục 6,
CALIBRATE 2026-08-19, điểm 2).

Mỗi dòng log phải có đủ 5 mục: **module · activity code · giờ thực · mẫu số + giá trị
· bậc complexity**.

| Activity | Mẫu số bắt buộc ghi kèm |
|---|---|
| G1 · A1 | số ticket |
| G2 | số lần chạy gen requirement |
| A2 | số requirement item (FR + BR + VR) |
| A2b | số vòng Q&A |
| G3 | số lần chạy gen test case |
| A3 · A4 · S4 | **số test case** |
| S1 · S2 | số môi trường / số bộ data |
| G4 · A4b · S3 | **số bug** |
| A5 | **số bug × số vòng verify** — ghi riêng 2 số, không gộp |
| R1 | số vòng rework |
| G5 · A6 | số module |

**Gộp nhiều activity vào 1 con số thì phải nói rõ gộp những code nào.** Log
`gen + review test case 1h` gộp G3 + A3 — dùng được để calibrate **tổng** G3+A3, nhưng
**không** tách được từng cái. Tách được ngay từ lúc log thì tốt hơn nhiều.

Nơi ghi: sheet `Assumptions & Risks` của chính module đó, loại `Actual`, cột nguồn ghi
ngày log.

## 8. Ví dụ kiểm chứng (regression check khi sửa layout / hệ số)

`sample_module` complexity `M`, module mới, AI `stable`, multiplier 1.00; S1/S2 ở
`Function = project_level`; bug theo `bugs_per_module` = 1. Chú ý nhóm **G\*** có
`Level factor` = 1.00 dù level là `Junior` (mục 4.1):

| Code | Volume | Level | base × factor × check | Adjusted (h) |
|---|---|---|---|---|
| G1 | 1 | Junior | 0.050 × **1.0** × 1 | 0.0500 |
| A1 | 1 | Junior | 0.050 × 1.3 × 1 | 0.0650 |
| G2 | 1 | Middle | 0.120 × 1.0 × 1 | 0.1200 |
| A2 | 12 | Middle | 0.025 × 1.0 × 1 | 0.3000 |
| A2b | 1 | Middle | 0.250 × 1.0 × 1 | 0.2500 |
| G3 | 1 | Junior | 0.155 × **1.0** × 1 | 0.1550 |
| A3 | 20 | Junior | 0.034 × 1.3 × 1 | 0.8840 |
| S1 | 1 | Junior | 1.000 × 1.3 × 1 | 1.3000 |
| S2 | 1 | Junior | 1.000 × 1.3 × 1 | 1.3000 |
| A4 | 20 | Junior | 0.081 × 1.3 × 1 | 2.1060 |
| G4 | 1 | Junior | 0.020 × **1.0** × 1 | 0.0200 |
| A4b | 1 | Junior | 0.050 × 1.3 × 1 | 0.0650 |
| A5 | 2 | Junior | 0.190 × 1.3 × 1 | 0.4940 |
| S3 | 0.3 | Junior | 0.020 × 1.3 × 1 | 0.0078 |
| S4 | 6 | Junior | 0.025 × 1.3 × 1 | 0.1950 |
| R1 | 1 | Middle | 0.120 × 1.0 × 1 | 0.1200 |
| G5 | 1 | Junior | 0.060 × **1.0** × 1 | 0.0600 |
| A6 | 1 | Middle | 0.090 × 1.0 × 1 | 0.0900 |

Volume phái sinh: `G4` = `bugs_per_module` 1 · `A4b` = `G4` · `A5` = `A4b` ×
`retest_rounds` 2 · `S3` = `A4b` × `bug_followup_rate` 0.3 · `S4` = `A4` ×
`regression_scope_rate` 0.3.

Subtotal `7.5818h` → buffer 15% `1.1373h` → **total `8.7191h` = `1.09` manday**.

- Theo level: Junior `6.7018h` · Middle `0.8800h` · Fresher `0` · Senior `0`
- Theo function: `sample_module` `4.9818h` · `project_level` `2.6000h`
- Kiểm tra bất biến: **tổng theo level = tổng theo activity = tổng theo function**

Đổi level dòng A2 sang `Fresher` → `level_check` = 1.3 (thiếu 2 bậc so với Middle),
`adjusted_h` = 12 × 0.025 × 1.6 × 1.3 = **0.6240h**.

Đổi level dòng **G3** sang `Fresher` → `Level factor` vẫn **1.00** (không nhạy level),
nhưng `level_check` = 1.2 (dưới mức tối thiểu `Junior`) → `adjusted_h` = 1 × 0.155 × 1.0
× 1.2 = **0.1860h**.

Bộ số trên đã recalc bằng engine formula sau khi calibrate **2026-08-20**, khớp 0.0000
sai lệch.
