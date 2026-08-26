---
name: estimate-test
description: "[personal] Estimate effort test (manhour/manday) cho từng chức năng theo luồng QA có AI hỗ trợ — 18 activity phủ cả công CHỈ ĐỊNH AI gen output (ticket, requirement, test case, bug log, test report) và công NGƯỜI làm (review, Q&A confirm PO, execute test, review bug AI log, verify bug, chốt report), cộng support (môi trường, test data, follow-up bug, regression) và rework. Chạy được NGAY khi có tài liệu nghiệp vụ (設計書/spec/ticket) — không cần chờ gen xong requirement hay test case — để lên plan cho team. Estimate theo 3 trục: độ phức tạp task × khối lượng công việc × level nhân sự. Xuất ra 1 Google Sheet riêng cho mỗi chức năng bằng cách duplicate từ master template được import từ file template_test_estimate.xlsx đi kèm skill. Triggers (VI): 'estimate test', 'ước lượng effort test', 'tính manday test', 'báo giá test'."
---

# Skill: estimate-test

## 1. Mục tiêu

- Ước lượng effort test cho **một chức năng** dựa trên artifact đã có (ticket, requirement package, bộ test case) thay vì đoán theo cảm nhận
- Bao quát **toàn bộ hoạt động test trong luồng có AI hỗ trợ**, không chỉ execute test
- Mọi con số phải suy ra được từ 3 trục: **độ phức tạp task**, **khối lượng công việc**, **level nhân sự**
- Chỉ ra rõ effort nào tăng vì requirement chưa ổn định, vì gán người non level, vì AI output còn phải rework
- Tạo 1 Google Sheet riêng cho mỗi chức năng bằng cách duplicate từ Google Sheet master template
- Hỗ trợ traceability từ dòng estimate về activity / test case / FR
- Ghi rõ giả định và điểm chưa rõ làm nên con số, kèm độ tin cậy — estimate không có giả định là estimate không review được

## 2. Phạm vi của skill

Skill này dùng để estimate effort test cho:
- Screen UI
- Module nghiệp vụ
- API function
- Batch / scheduler / event-driven process
- Change request
- Enhancement
- Reverse engineering từ source hiện có

**Ngoài phạm vi:** estimate effort dev, estimate automation test, phân bổ nhân sự cụ thể, dựng lịch / timeline (xem §11.4).

## 3. Đầu vào: TÀI LIỆU NGHIỆP VỤ là đủ

**Skill này estimate được ngay khi có tài liệu nghiệp vụ (`設計書` / spec / ticket).**
Đó là thời điểm cần con số — để lên plan, chia người, chốt lịch — **trước khi** QA chạy
`gen-requirement` hay `gen-testcase`.

> **Không được lấy requirement package hay bộ test case làm điều kiện để estimate.**
> Bản estimate tính cả `G2`/`A2` (gen + review requirement) và `G3`/`A3` (gen + review
> test case). Bắt chạy xong 2 việc đó rồi mới estimate = **estimate công việc vừa làm
> xong**, con số ra sau khi đã tiêu tiền, không lên plan được nữa.

### 3 tier đầu vào

| Tier | Có gì | Cách suy volume | Độ tin cậy |
|---|---|---|---|
| **1** | **Tài liệu nghiệp vụ gốc** — `外部設計書`, spec, ticket, 画面レイアウト | Đếm từ tài liệu → liệt kê TC (`estimation-model.md` §3.1.1 + §3.1.2) | **Trung bình** |
| 2 | + requirement package của `gen-requirement` | Đếm trực tiếp FR / BR / VR, liệt kê lại TC | Trung bình - Cao |
| 3 | + `testcases/<module>/testcase_draft.csv` | Đếm dòng | **Cao** |

**Tier 1 là đường chạy bình thường.** Tier 2 / 3 chỉ dùng để tinh chỉnh **nếu tình cờ đã
có sẵn** — không bao giờ là điều kiện chặn.

Không có cả tài liệu nghiệp vụ → **KHÔNG estimate**, dừng và báo thiếu input.

### Nguồn tier 2 / 3 (nếu có)

- `testcases/<module_name>/testcase_draft.csv` — volume test case chính xác nhất
- Google Sheet test case đã sinh cho module
- Requirement package: `functional_requirements.md` · `business_rules.md` · `validation_rules.md` · `impact_scope.md` · `assumptions_and_open_points.md` · `traceability_matrix.md`

## 4. Cách gọi skill

`/estimate-test <module_name>`

Hoặc:

`/estimate-test <module_name> --manifest ./inputs/estimate_source_manifest.yaml`

Hoặc:

`/estimate-test <module_name> --manifest ./inputs/estimate_source_manifest.yaml --profile ./configs/estimate_project_profile.yaml`

Ví dụ:
- `/estimate-test event_edit_schedule`
- `/estimate-test settlement_management --manifest ./inputs/estimate_source_manifest.yaml`

## 5. Input bắt buộc

| Biến | Mô tả |
|---|---|
| `$1` | Module name / function name |
| `MANIFEST_PATH` | File khai báo source đầu vào, mặc định `./inputs/estimate_source_manifest.yaml` |
| `PROFILE_PATH` | File cấu hình quy tắc dự án, mặc định `./configs/estimate_project_profile.yaml` |
| `OUTPUT_ROOT` | Thư mục output phụ, mặc định `estimates` |
| `EVIDENCE_ROOT` | Thư mục evidence, mặc định `evidence_estimate` |

## 5A. Quy tắc phạm vi: 1 module = 1 Google Sheet

Đây là quy tắc **cao nhất**, override mọi phần còn lại của skill khi có mâu thuẫn.

### 5A.1. Nguyên tắc

- **1 lần chạy chỉ estimate cho ĐÚNG 1 module**, xuất ra **đúng 1 Google Sheet**.
- **Cấm gộp nhiều module vào chung 1 Sheet**, cấm tạo nhiều Sheet trong một lần chạy.
- **Cấm estimate cho toàn bộ dự án** kể cả khi requirement hoặc 設計書 phủ nhiều module.
- Muốn làm nhiều module → chạy lại lệnh cho từng module.
- Output phụ chỉ ghi vào `<output_root>/<module_name>/` và `<evidence_root>/<module_name>/`. Cấm đụng folder module khác.

### 5A.2. Không có tên module trên dòng lệnh — LUÔN hiển thị danh sách rồi DỪNG hỏi

**Điều kiện kích hoạt:** chạy module discovery khi **argument `$1` trống** — **bất kể manifest ghi gì**.

- `run.module_name` trong manifest **KHÔNG được dùng** để chọn module chạy. Nó chỉ là ghi chép.
- Chỉ **bỏ qua** discovery khi người dùng gõ rõ tên module.
- Không được suy ra module từ: manifest, lần chạy trước, thư mục đã tồn tại trong `<output_root>`, Sheet đã tạo, hay ngữ cảnh hội thoại.

**Các bước:**

1. **Ưu tiên đọc module registry**: có `configs/module_registry.yaml` thì lấy danh sách từ đó. **Cấm** quét lại source khi registry đã có dữ liệu.
2. **Chỉ khi không có registry**, mới quét ở mức **khung**: thư mục trong `testcases/`, thư mục trong requirement output, mục lục / bảng FR của requirement doc. **Cấm** đọc chi tiết flow / business rule ở bước này.
3. Xuất **bảng danh sách chức năng** dạng Markdown:

   | # | module_name | Hệ thống | Màn hình / entry point | Có requirement? | Có test case? | Trạng thái |
   |---|---|---|---|---|---|---|

   - `Có requirement?` kiểm tra bằng sự tồn tại của `knowledge/<module_name>/functional_requirements.md`
   - `Có test case?` kiểm tra bằng `testcases/<module_name>/testcase_draft.csv`
   - `Trạng thái` lấy từ registry (`pending` / `req_done` / `tc_done` / `est_done` / `out_of_scope`)
4. **DỪNG hỏi người dùng chọn 1 chức năng** (nhận cả số thứ tự lẫn `module_name`). Không tự chọn, không tạo Sheet, không sinh file nào.
5. Sau khi người dùng chọn → chạy tiếp Phase 1 với đúng module đó.
6. Chạy xong → cập nhật `status` và `estimate_output` của module đó trong registry.

### 5A.3. Ranh giới nội dung estimate

- Chỉ estimate hoạt động test thuộc module đang chạy.
- Công việc của module khác **chỉ được** xuất hiện ở cột `Note` dạng điều kiện phụ thuộc, **không** tạo dòng estimate riêng.
- Phát hiện việc thuộc module khác cần estimate → ghi vào `open_points.md`, không tự mở rộng phạm vi.
- Naming Sheet phải chứa đúng `module_name` đang chạy theo `spreadsheet_name_pattern`.

## 6. Nguồn đầu vào hỗ trợ

`testcase_draft.csv` · test case Google Sheet · `functional_requirements.md` · `business_rules.md` · `validation_rules.md` · `impact_scope.md` · `assumptions_and_open_points.md` · `open_points.md` · requirement document · ticket · 設計書 · Figma · API spec · DB schema · workflow · meeting note · log effort dự án trước (nếu có).

## 7. Ưu tiên nguồn

1. `testcase_draft.csv` (volume test case)
2. `functional_requirements.md` / `business_rules.md` / `validation_rules.md` (volume requirement item)
3. `open_points.md` / `assumptions_and_open_points.md` (độ ổn định requirement → số vòng Q&A + multiplier)
4. `impact_scope.md` (cross-module multiplier)
5. Requirement document đã approved
6. Ticket / change request
7. Log effort dự án trước (calibrate base rate)

Xung đột giữa các nguồn → ưu tiên nguồn cao hơn; chưa đủ rõ → ghi `open_points.md`, **không tự suy diễn**.

## 8. Excel / Google Sheet Template Policy

Template estimate đi kèm ngay trong skill này, tại:
- `<skill_dir>/templates/template_test_estimate.xlsx`

`<skill_dir>` là thư mục chứa chính file `SKILL.md` này — hiện tại là `~/.claude/skills/estimate-test/`. **KHÔNG** dùng path tương đối `./templates/...` vì nó resolve theo working directory của project đang mở nên sẽ trỏ sai khi skill được gọi từ project khác.

Nguyên tắc vận hành:
- Template nguồn cần được import lên Google Drive 1 lần để tạo Google Sheet master template
- Mỗi lần estimate cho một chức năng, skill tạo 1 file Google Sheet mới bằng cách duplicate từ master template
- Skill chỉ ghi vào worksheet cấu hình trong profile, **preserve formula và format** của template
- **Cấm** ghi giá trị tĩnh lên ô đang chứa formula (`Activity name`, `Đơn vị`, `Base rate (h)`, `Level factor`, `Level check`, `Adjusted (h)`, toàn bộ sheet `Estimate Summary`) — người dùng phải tune được ở `Rate Card` và thấy tổng tự cập nhật
- Skill không tự đổi tên cột, thêm cột, đổi thứ tự cột nếu không có yêu cầu rõ ràng
- Chưa có `google_master_template_file_id` → ghi nhận `Cần xác nhận`, xuất đủ output phụ, **dừng ở bước tạo Google Sheet**
- Sửa layout template → sửa `scripts/estimate_template_data.py` rồi chạy `python3 scripts/build_estimate_template.py`, **không** sửa xlsx bằng tay

## 9. Phân tích phục vụ estimate

Trước khi tính, skill phải trích xuất:
- Tên chức năng, actor, mục tiêu
- Số field / control trên màn hình
- Số validation rule, số business rule
- Số alternate + exception flow
- Có persist DB không, mấy bảng
- Phụ thuộc / ảnh hưởng module khác
- Có nhãn / message tiếng Nhật cần đối chiếu nguyên văn không
- Số điểm mờ / `Cần xác nhận` trong tài liệu nguồn (độ ổn định requirement) — ở tier 2 trở lên thì đếm `open_points.md`
- **Chất lượng tài liệu nguồn**: block `04_画面項目定義` (hoặc tương đương) có dữ liệu hay rỗng
- Số ticket, số requirement item, số test case
- Ai chạy AI gen: QA tự chạy hay BA/dev chạy (`context.ai_driver`)
- Số môi trường / bộ test data cần dựng, đã có sẵn từ module trước chưa
- Số vòng rework dự kiến (theo độ chín prompt/skill AI)
- Module làm mới hay sửa đổi
- Độ chín của prompt/skill AI đang dùng

Thiếu thông tin → **không bịa**, ghi vào `open_points.md` + sheet `Assumptions & Risks` kèm độ tin cậy.

## 10. Bộ hoạt động bắt buộc — đủ 18 dòng, đúng thứ tự

4 nhóm: **G\*** công chỉ định AI gen · **A\*** công người làm · **S\*** support không giao được cho AI · **R1** rework.

| # | Code | Hoạt động | Đơn vị khối lượng |
|---|---|---|---|
| 1 | G1 | Chuẩn bị input + chỉ định AI gen ticket task test | ticket |
| 2 | A1 | Review ticket task test AI gen | ticket |
| 3 | G2 | Dựng manifest + chỉ định AI gen requirement | lần chạy |
| 4 | A2 | Đọc hiểu + review requirement AI tạo | requirement item |
| 5 | A2b | Q&A phân tích yêu cầu + confirm với PO | vòng Q&A |
| 6 | G3 | Chỉ định AI gen test case | lần chạy |
| 7 | A3 | Review test case AI gen + update | test case |
| 8 | S1 | Setup môi trường test + account / quyền | môi trường |
| 9 | S2 | Chuẩn bị test data | bộ data |
| 10 | A4 | Execute test | test case |
| 11 | G4 | Cung cấp evidence + chỉ định AI log bug | bug |
| 12 | A4b | Review bug AI log (dedupe / severity / repro) | bug |
| 13 | A5 | Verify bug | bug × round |
| 14 | S3 | Follow-up bug (reject / reopen / trao đổi dev) | bug |
| 15 | S4 | Regression test vùng ảnh hưởng | test case |
| 16 | R1 | Re-prompt + review lại (rework output AI / requirement đổi) | vòng rework |
| 17 | G5 | Chỉ định AI gen test report | module |
| 18 | A6 | Review + chốt test report, cập nhật status ticket | module |

- **Mọi module đều phải có đủ 18 dòng.** Activity không áp dụng → vẫn giữ dòng, `Volume = 0`, ghi lý do vào `Note`. **Cấm** xoá dòng làm mất dấu vết "đã xét, không áp dụng".
- Một module có nhiều màn hình / nhiều nhóm chức năng cần tách → được phép nhiều dòng cùng một code, phân biệt bằng cột `Function`.
- **Giờ họp / communication không có dòng riêng** — nằm trong `buffer_pct` vì không scale theo complexity cũng không scale theo level. Dự án họp nhiều bất thường → nâng `buffer_pct` ở `Rate Card`, không thêm activity.

### 10.1. Ai chạy AI

- QA tự chạy skill AI → tính đủ G1 → G5.
- BA / dev chạy rồi QA chỉ nhận output → activity G tương ứng để `Volume = 0`, `Note` ghi rõ ai chạy.
- Lấy từ `context.ai_driver` trong manifest; không khai → mặc định QA tự chạy và ghi 1 dòng `Assumption` vào `Assumptions & Risks`.

### 10.2. Project-level vs module-level

- `S1` (môi trường + account/quyền) và `S2` (test data dùng chung) trả **1 lần cho cả dự án** → đặt ở dòng có `Function = project_level`.
- Module sau để `Volume = 0` + `Note` trỏ về dòng `project_level`. **Cấm** nhân lặp chi phí setup theo từng module.
- Test data riêng của một module (file import đặc thù, bộ dữ liệu nghiệp vụ riêng) → vẫn tính `S2` theo module đó.

## 11. Mô hình estimate — 3 trục

Công thức, bảng hệ số và cách calibrate nằm ở **`references/estimation-model.md`**. Skill phải đọc file đó trước khi tính. Tóm tắt:

```
adjusted_h = volume × base_rate[activity][complexity] × level_factor[level]
             × multiplier × level_check
total_h    = Σ adjusted_h × (1 + buffer_pct)
```

### 11.1. Độ phức tạp task
S / M / L / XL, chấm bằng bảng tiêu chí đếm được ở `estimation-model.md` §2 và ở sheet `Rate Card` mục 6. **Cấm** chấm bằng cảm nhận; phải ghi tiêu chí đã dùng vào `Note`.

### 11.2. Khối lượng công việc
Đếm theo bảng `estimation-model.md` §3. Số đếm phải **truy được về nguồn** (tên file + cách đếm) ghi ở `Note` hoặc `estimate_traceability_matrix.md`.

### 11.3. Level nhân sự
`Fresher` / `Junior` / `Middle` / `Senior`. **Base rate là giờ của Middle.**

**Nhóm `G*` (G1 · G2 · G3 · G4 · G5) dùng `Level factor` cứng = 1.00** — giờ chỉ định AI gen phần lớn là chạy skill + chờ output, không đổi theo level (`estimation-model.md` §4.1). `level_check` vẫn áp bình thường. Gán level thấp hơn mức tối thiểu của activity → cột `Level check` tự cộng phụ phí senior review và skill **bắt buộc** ghi 1 dòng `Level warning` vào `Assumptions & Risks`.

### 11.4. Không estimate số người và timeline
Output **không có** cột số nhân sự / duration / ngày bắt đầu-kết thúc. Người dùng hỏi timeline → trả lời bằng manday theo level và nói rõ việc chia người thuộc bước planning.

## 12. Tiêu chí bắt buộc với từng dòng estimate

Mỗi dòng phải:
- Có `Function`, `Activity`, `Complexity`, `Volume`, `Level` — thiếu 1 trong 5 thì dòng đó không hợp lệ
- Có `Volume` truy được về nguồn đếm, không phải số tự nghĩ
- Có `Note` nêu căn cứ chấm complexity và/hoặc cách đếm volume
- Để nguyên formula ở các cột tính (§8)
- `Multiplier` = tích các yếu tố ở `estimation-model.md` §5, mặc định `1.00`; khác `1.00` thì **bắt buộc** ghi lý do vào `Note`

Cấm các cách ghi: `tương tự dòng trên`, `như module trước`, `same as above`, `~`, `N/A` ở cột `Volume`.

## 13. Mapping cột theo template

Sheet `Estimate Detail` — bộ cột logic tối thiểu:

1. Function
2. Activity (code)
3. Activity name *(formula)*
4. Complexity
5. Volume
6. Đơn vị *(formula)*
7. Base rate (h) *(formula)*
8. Level
9. Level factor *(formula)*
10. Multiplier
11. Level check *(formula)*
12. Adjusted (h) *(formula)*
13. Note

Header trong template khác nhẹ về cách viết → dùng `template_header_aliases` trong `estimate_project_profile.yaml`, **không** sửa header thật của template.

## 13A. Ngôn ngữ output

- Nội dung sheet estimate viết theo `project.output_language` trong manifest (mặc định `vi`).
- **Giữ NGUYÊN VĂN, không dịch**: tên màn hình / field / message tiếng Nhật, tên bảng · cột DB, tên API endpoint, tên module, mã ticket.
- Tên activity, level, complexity giữ đúng giá trị trong `Rate Card` — đây là khoá `VLOOKUP`, dịch là công thức vỡ.

## 14. Quy tắc nội dung từng cột

### Function
Tên chức năng / màn hình / nhóm việc trong module. Snake_case theo `module_name_style`.

### Activity
Đúng 1 trong **18** code ở §10: `G1` `A1` `G2` `A2` `A2b` `G3` `A3` `S1` `S2` `A4` `G4` `A4b` `A5` `S3` `S4` `R1` `G5` `A6`. Có dropdown trong template.

**Cả 18 code đều phải xuất hiện** (§10) — kể cả nhóm `G*` (chỉ định AI gen) và `S*` (support). Không áp dụng → giữ dòng, `Volume = 0`, ghi lý do vào `Note`.

### Complexity
Đúng 1 trong `S` `M` `L` `XL`. Chấm theo §11.1.

### Volume
- Số, không âm. Không áp dụng → `0` kèm lý do ở `Note`
- A4b, A5 nên để nguyên formula phái sinh (`= volume A4 × expected_defect_rate`, `= volume A4b × retest_rounds`) để đổi tham số là tự cập nhật

### Level
Đúng 1 trong `Fresher` `Junior` `Middle` `Senior`. Chưa chốt người → gán `Middle` (baseline) và ghi `Assumption`.

### Multiplier
Số thập phân, mặc định `1.00`. Nhiều yếu tố → nhân dồn, ghi rõ từng yếu tố ở `Note`.

### Note
Ghi: căn cứ chấm complexity · cách đếm volume + tên file nguồn · lý do multiplier khác 1.00 · lý do volume = 0.

## 15. Workflow thực thi

### Phase 1 — Nạp cấu hình và source
- Đọc `module_name`; thiếu hoặc là placeholder → **module discovery** theo §5A.2, DỪNG hỏi, không đi tiếp
- Đọc manifest, đọc profile, đọc `references/estimation-model.md`
- Kiểm tra template local `<skill_dir>/templates/template_test_estimate.xlsx` (§8)
- Kiểm tra `google_master_template_file_id`
- **Xác định tier đầu vào (§3)**: có `testcase_draft.csv`? có requirement package? nếu không → tier 1, chạy bằng tài liệu nghiệp vụ. **Không dừng chờ tier cao hơn**
- Mở tài liệu nghiệp vụ, khoanh block thuộc đúng module đang chạy
- Ghi nhận access issue nếu có

### Phase 2 — Đếm dữ kiện từ tài liệu nghiệp vụ
Theo §9 và `estimation-model.md` §3.1.1. Với `外部設計書` đếm 8 con số: `N_screen` · `N_block` · `N_item` · `N_val` · `N_input` · `N_sec` · `N_flow` · `N_nav` · `N_msg` · `N_table`.

Ghi lại **con số đếm được kèm nguồn** (tên sheet + dòng), chưa tính giờ.

**Kiểm chất lượng tài liệu nguồn:** block `04_画面項目定義` rỗng cho màn này → `qa_round_per_module` +1 và `rework_rounds` +1, ghi lý do vào `Note` (`estimation-model.md` §3.1.4). Tài liệu mỏng **không** làm giảm số test case.

### Phase 2b — Dự báo số test case (bỏ qua nếu đã có `testcase_draft.csv`)

Bắt buộc ở tier 1 và tier 2. Theo `estimation-model.md` §3.1.2:

1. **Liệt kê** nhóm test case từ các con số ở Phase 2 — chỉ đếm, **không** viết step / expected result. **Cấm nhân hệ số**: mọi hệ số đơn đo được đều có spread >= 2 lần.
2. Cộng theo 5 nhóm: `Trigger/Navigation` · `UI` · `Positive` · `Negative` · `Form Validation`.
3. **Nhân `enum_correction` = 0.85** — phép liệt kê đo được là luôn thừa (+11% và +25% trên 2 module đã kiểm).
4. **Cross-check** với dải `TC / requirement item` theo loại màn (`estimation-model.md` §3.1.3). Lệch > 40% → **không tự chọn**, ghi `Open point` nêu cả hai con số.
5. Ghi vào `Assumptions & Risks` 1 dòng `Assumption`: bảng liệt kê theo nhóm + tổng trước/sau hiệu chỉnh + kết quả cross-check.

Số TC dự báo này là volume của `A3` / `A4` / `S4`. Volume `G4` / `A4b` / `A5` / `S3` lấy từ `bugs_per_module`, **không** suy từ số test case (`estimation-model.md` §3.1.5).

### Phase 3 — Chấm độ phức tạp
Áp bảng tiêu chí §11.1 cho từng `Function`. Ghi tiêu chí đã dùng. Hoà nhau → lấy mức cao hơn.

### Phase 4 — Xác định khối lượng cho đủ 18 activity
Theo bảng `estimation-model.md` §3. Volume test case lấy từ Phase 2b (dự báo) hoặc từ `testcase_draft.csv` (đếm).

### Phase 5 — Gán level + multiplier
- Gán level **theo từng dòng activity** (1 module có thể Junior test + Middle confirm PO)
- **Nhóm `G*` không nhạy level** — `Level factor` tự trả `1.00` (`estimation-model.md` §4.1). Không sửa tay cột này
- Chưa chốt người → `Middle` + ghi `Assumption`
- Level thấp hơn mức tối thiểu → ghi `Level warning` vào `Assumptions & Risks`
- Áp multiplier theo §5 của `estimation-model.md`, ghi lý do

### Phase 6 — Traceability
Map từng dòng estimate về: activity code · nguồn đếm volume (file + cách đếm) · FR / BR / VR liên quan · TC ID range (nếu có) · căn cứ chấm complexity.

### Phase 7 — Tạo Google Sheet output
- Duplicate từ `google_master_template_file_id`
- **Đúng 1 Sheet cho đúng 1 module** (§5A.1)
- Đổi tên file theo `spreadsheet_name_pattern`
- Ghi dữ liệu vào `Estimate Detail` (chỉ các cột nhập tay) và `Assumptions & Risks`
- **Không** ghi vào `Estimate Summary` và các ô formula — để công thức tự tính
- Sửa tham số dự án (defect rate, retest rounds, buffer, giờ/manday) ở `Rate Card`, không hard-code vào dòng estimate
- **Verify trước khi kết thúc Phase 7**: đủ 18 activity · không dòng nào thiếu 5 field bắt buộc · `Estimate Summary` ra số khác 0 · tổng theo level = tổng theo activity

### Phase 8 — Xuất output phụ
- `estimate_summary.md` — tổng manhour/manday, breakdown theo activity và theo level, giả định chính
- `estimate_traceability_matrix.md`
- `open_points.md`

## 16. Quy tắc coverage tối thiểu

### 16.1. Bắt buộc
- Đủ 18 dòng activity theo bảng §10 (G1 → A6), gồm cả nhóm G (chỉ định AI gen) và nhóm S (support)
- Mọi dòng có complexity chấm theo tiêu chí đếm được
- Mọi dòng có volume truy được về nguồn (tên sheet + dòng trong tài liệu nghiệp vụ, hoặc tên file requirement / test case)
- Buffer risk được tính
- Sheet `Assumptions & Risks` có ít nhất: cơ sở base rate, cách suy bug count, mọi `Open point` ảnh hưởng volume

### 16.2. Có điều kiện
- Multiplier `domain_first_time` (1.25) — chỉ khi người thực hiện lần đầu làm nghiệp vụ này
- Multiplier `module_type_modify` (0.85) — chỉ khi sửa đổi / enhancement trên module đã có
- Multiplier `ai_output_maturity_pilot` (1.30) / `_mature` (0.90) — theo độ chín prompt/skill AI; mặc định `_stable` (1.00)
- Vòng Q&A > 1 — khi tài liệu nguồn mỏng (`04_画面項目定義` rỗng) hoặc số open point vượt ngưỡng ở `estimation-model.md` §3
- Vòng rework > 1 — khi tài liệu nguồn mỏng (`estimation-model.md` §3.1.4)

**Ba multiplier `requirement_unstable` · `cross_module` · `ui_japanese` đã bị vô hiệu (= 1.00)** — cả 3 yếu tố này đã được dùng để chấm bậc complexity ở §11.1, áp thêm multiplier là **đếm trùng** (`estimation-model.md` §5.1). Dòng vẫn còn trong `Rate Card` để giữ dấu vết; **cấm** tự bật lại.

Hạng mục §16.2 không có nguồn → **không áp multiplier**, ghi 1 dòng vào `open_points.md`.

## 17. Quy tắc với module non-UI

Module là API, batch, event hoặc scheduler:
- `Function` dùng endpoint / process / event name
- Tiêu chí complexity: thay "số field trên màn hình" bằng "số tham số payload / cột dữ liệu xử lý"
- A1, A2, A2b, A3, A4b, A5 giữ nguyên; A4 vẫn tính (execute qua tool / query DB)
- Có batch xử lý > 3 bảng → mức `XL` theo tiêu chí persist DB

## 18. Quy tắc với requirement chưa rõ

- Không tự suy diễn để "cho có số"
- Ghi vào `open_points.md` + `Assumptions & Risks` kèm **độ tin cậy** và **ảnh hưởng tới estimate**
- Vẫn estimate phần đã xác định được, phần chưa rõ để `Volume = 0` + `Note` nêu rõ "chưa estimate được, chờ xác nhận"
- **Cấm** đưa ra tổng manday mà không kèm danh sách giả định

## 19. Output bắt buộc

### Output chính
- 01 Google Spreadsheet riêng cho mỗi chức năng, duplicate từ master template
- 04 worksheet: `Rate Card` · `Estimate Detail` · `Estimate Summary` · `Assumptions & Risks`

### Output phụ
- `<output_root>/<module_name>/estimate_summary.md`
- `<output_root>/<module_name>/estimate_traceability_matrix.md`
- `<output_root>/<module_name>/open_points.md`

### Evidence
- `<evidence_root>/<module_name>/source_snapshots/`
- `<evidence_root>/<module_name>/analysis_notes/`
- `<evidence_root>/<module_name>/access_issues/`

## 20. Tiêu chí hoàn tất

- Đã trích xuất dữ kiện estimate từ nguồn thật, không đoán
- Đã tạo 1 Google Sheet riêng cho module (hoặc ghi `Cần xác nhận` khi thiếu master template id)
- Đủ 18 dòng activity, đúng thứ tự
- Mọi dòng có đủ `Function` / `Activity` / `Complexity` / `Volume` / `Level`
- Formula ở các cột tính còn nguyên, `Estimate Summary` ra số
- Tổng theo level = tổng theo activity
- Có traceability cho mọi dòng estimate
- Có `Assumptions & Risks` kèm độ tin cậy
- Có `open_points.md` nếu requirement chưa rõ
- Không có nội dung bịa

## 21. Rules

- Không bịa số. Volume không có nguồn đếm → không được điền
- Không chấm complexity bằng cảm nhận — phải bám bảng tiêu chí (§11.1)
- **1 module = 1 Google Sheet.** Cấm gộp module, cấm estimate toàn dự án (§5A)
- **Không có tên module trên dòng lệnh → LUÔN hiển thị bảng danh sách chức năng rồi DỪNG hỏi**, bất kể manifest ghi gì (§5A.2)
- **Đủ 18 dòng activity G1 → A6**; không áp dụng thì `Volume = 0` + lý do, cấm xoá dòng (§10)
- **Công chỉ định AI gen (G1–G5) phải được tính**, không được coi là miễn phí; BA/dev chạy thay thì `Volume = 0` + ghi rõ ai chạy (§10.1)
- **S1 / S2 là project-level** — đặt ở `Function = project_level`, cấm nhân lặp theo từng module (§10.2)
- **Không thêm activity cho giờ họp** — đã nằm trong `buffer_pct` (§10)
- **Base rate là giờ của Middle**; level khác quy đổi qua `Level factor`, cấm sửa base rate để "bù" level (§11.3)
- **Gán level dưới mức tối thiểu của activity → phải cộng phụ phí senior review** và ghi `Level warning` (§11.3)
- **Cấm ghi giá trị tĩnh lên ô formula** và cấm ghi tay vào `Estimate Summary` (§8)
- **Cấm thêm cột số nhân sự / duration / timeline** vào bản estimate (§11.4)
- Tham số dự án (defect rate, retest rounds, buffer, giờ/manday) chỉ sửa ở `Rate Card`, không hard-code
- **Cấm đưa tổng manday mà không kèm giả định + độ tin cậy** (§18)
- **Có tài liệu nghiệp vụ là estimate được** — tier 1 (§3). **Cấm** đòi requirement package hoặc bộ test case như điều kiện; đó là estimate công việc vừa làm xong, vô nghĩa cho việc lên plan
- **Cấm nhân hệ số để suy số test case** — liệt kê theo `estimation-model.md` §3.1.2. Mọi hệ số đơn đo được đều có spread >= 2 lần
- **Số bug lấy từ `bugs_per_module`** (1 cho phase UI test), **không** nhân % test case — cách cũ sai 17 lần trên `lottery_application_inquiry` (`estimation-model.md` §3.1.5)
- **Tài liệu nguồn mỏng thì cộng `A2b` + `R1`, KHÔNG giảm số test case** — bằng chứng: `buyer_navigator_menu` có 0 dòng item trong nguồn nhưng vẫn ra 12 requirement item + 18 test case (`estimation-model.md` §3.1.4)
- **Nhóm `G*` không nhạy level** — `Level factor` = 1.00 ở mọi level; `level_check` vẫn áp (§11.3)
- **Log giờ thực tế phải quy về giờ Middle trước khi nạp base rate** — chia cho `level_factor` của người đã làm. Bỏ bước này là mọi estimate lệch theo level của người được log (`estimation-model.md` §4)
- **Log effort thực tế phải kèm mẫu số** (số test case / số bug / số bug × số vòng...) theo `estimation-model.md` §7. Nhận log không có mẫu số → **không** sửa hệ số, ghi 1 `Open point` hỏi lại mẫu số
- Calibrate → **chỉ sửa activity có log**, giữ nguyên activity chưa đo (`estimation-model.md` §6 "Cách calibrate")
- **Độ tin cậy khác nhau theo hạng mục** — bảng ở `estimation-model.md` §6 "Độ tin cậy hiện tại". `A4` và tổng `G3+A3` có log giờ thực (Trung bình); `level_factor` và 15 activity còn lại chưa có điểm đo nào (Thấp). Báo cáo **phải nói rõ** phần nào dựa trên số đo, phần nào còn là suy luận
- Sửa hệ số → sửa `scripts/estimate_template_data.py` + `references/estimation-model.md` rồi chạy lại builder; **không** sửa xlsx bằng tay (§8)
