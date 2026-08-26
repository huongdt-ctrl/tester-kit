# ISTQB alignment — nội dung chuẩn cho từng mục của template

Neo theo ISTQB CTFL v4.0 (§5.1 Test Planning, §5.2 Risk Management, §5.3 Test Monitoring
& Control) và IEEE 829 Test Plan. Mục đích: bảo đảm test plan sinh ra **đủ nội dung chuẩn**,
không chỉ đúng ô Excel.

---

## 1. Bảng đối chiếu ISTQB ↔ sheet template

| Nội dung ISTQB yêu cầu trong test plan | Sheet · mục |
|---|---|
| Context of testing (project, product, stakeholders) | `01_Introduction` 1.2 Mục đích |
| Test plan identification / level | `01_Introduction` 1.1 Định danh |
| Glossary, viết tắt | `01_Introduction` 1.3 |
| Test basis (tài liệu cơ sở kiểm thử) | `01_Introduction` 1.4 References |
| Test objectives | `02_Scope test` 2.1 |
| Test items (view kỹ thuật) | `02_Scope test` 2.2 |
| Features to be tested (view USER) | `02_Scope test` 2.3 |
| Features not to be tested + lý do | `02_Scope test` 2.4 |
| Assumptions | `02_Scope test` 2.5 |
| Constraints | `02_Scope test` 2.6 |
| Test approach / strategy, deviation khỏi org strategy | `03_Test ApproachStrategy` 3.0 |
| Test techniques & mức chi tiết testware / tính năng | `03_Test ApproachStrategy` 3.1 |
| Test levels × test types | `03_Test ApproachStrategy` 3.2 (matrix) |
| Chi tiết từng test type (mục tiêu · kỹ thuật · exit · lưu ý) | `03_1_Test ApproachStr` |
| Roles, responsibilities, staffing, training needs | `04_Resources` |
| Test environment & tool requirements | `05_Test Environment` |
| Entry criteria / exit criteria (DoR · DoD) | `06_Criteria` 6.1 |
| Suspension & resumption criteria | `06_Criteria` 6.2 |
| Estimation + schedule + milestone | `07_Estimation & Schedule` |
| Testware / test deliverables | `08_Deliverables` |
| Product risk + project risk, mức độ, mitigation | `09_Risk management` |
| Traceability (test → test basis) | output phụ `testplan_traceability_matrix.md` |
| Test monitoring & control metrics | `06_Criteria` 6.1 (ngưỡng) + `07` (Status) |

**Không có mục nào của template được để trắng hoàn toàn.** Thiếu thông tin → ghi
`Cần xác nhận` + đẩy câu hỏi vào `open_points.md`, cấm bịa.

---

## 2. Định danh test plan (1.1)

Skill này sinh **Master Test Plan** cho toàn dự án. Ô `B6` phải ghi rõ:
- Cấp độ: `Master Test Plan`
- Phạm vi phủ: các test level nào (khớp matrix 3.2)
- Đối tượng: sản phẩm/hệ thống + version/release
- Vòng đời áp dụng: từ mốc nào đến mốc nào

---

## 3. Test level — chọn theo bằng chứng

| Level | Đưa vào matrix 3.2 khi |
|---|---|
| Unit | Dự án có yêu cầu/quy trình unit test, hoặc coverage target ở source |
| Intergration | Có ≥ 2 component/service/module tương tác, hoặc có API contract |
| System | Luôn có với sản phẩm có UI hoặc end-to-end business flow |
| Acceptance | Có UAT/khách hàng nghiệm thu, hoặc AC được định nghĩa rõ |

Level không có bằng chứng → **không tick `x`**, ghi lý do vào `open_points.md`.

---

## 4. Test type — điều kiện bắt buộc để đưa vào plan

Test type chỉ được đưa vào matrix 3.2 **và** fill nội dung ở `03_1` khi hội đủ điều kiện.
Không đủ → để nguyên `{...}` guidance của template + ghi `open_points.md`.

| Test type (`03_1`) | Điều kiện đưa vào plan |
|---|---|
| 3.1.1 Phân tích yêu cầu | **Luôn có** |
| 3.1.2 Review test cases | **Luôn có** |
| 3.2.1 Functional testing | **Luôn có** |
| 3.2.2 Business Cycle Testing | Nghiệp vụ có chu kỳ theo thời gian (tháng/quý/năm), batch định kỳ, đối soát |
| 3.2.3 User Interface Testing | Sản phẩm có UI |
| 3.2.4 Data & Database Integrity | Có DB schema / yêu cầu lưu trữ · migration · đối soát dữ liệu |
| 3.2.5.1 Performance Testing | Requirement nêu **ngưỡng response time / transaction rate cụ thể** |
| 3.2.5.2 Load Testing | Requirement nêu **số user/tps đồng thời cụ thể** |
| 3.2.5.3 Stress Testing | Requirement nêu **giới hạn tài nguyên** cần verify |
| 3.2.5.4 Volume Testing | Requirement nêu **khối lượng dữ liệu cụ thể** |
| 3.2.6 Security & Access Control | Có phân quyền theo role, xử lý dữ liệu cá nhân, thanh toán, authentication |
| 3.2.7 Failover & Recovery | Có yêu cầu HA/DR/backup-restore/RTO-RPO |
| 3.2.8 Configuration Testing | Có ma trận OS/browser/device phải hỗ trợ |
| 3.2.9 Installation Testing | Có gói cài đặt / deploy procedure người dùng tự chạy |
| 3.2.10 Regression Testing | **Luôn có** khi là enhancement / CR / có release ≥ 2 |

**Cấm** đưa test type NFR vào plan với ngưỡng `Cần xác nhận` — không có số thì không có test type.

---

## 5. Entry / Exit criteria (6.1) — nội dung tối thiểu

**Exit criteria (Tiêu chí hoàn thành)** phải bao gồm, mỗi tiêu chí kèm ngưỡng đo được:
1. Test execution: `% test case đã execute = 100%`
2. Pass rate: `% test case pass >= <ngưỡng>`
3. Defect: `Critical = 0` · `High = 0` · `Medium <= <n>` (nêu rõ số)
4. Coverage: `% requirement được cover bởi test case = 100%` (qua RTM)
5. Deliverable: toàn bộ testware ở `08_Deliverables` đã bàn giao
6. Bug còn mở đều đã có quyết định (fix sau / accept risk) từ người có thẩm quyền

**Cấm** tiêu chí không đo được: "chất lượng tốt", "test đầy đủ", "khách hàng hài lòng".

**Suspension criteria (6.2)** tối thiểu:
- Build không pass smoke test / CIT
- Blocker chặn `>= <n>%` test case không execute được
- Môi trường test down `>= <thời gian>`
- Requirement thay đổi lớn giữa chu kỳ test
Mỗi tiêu chí **bắt buộc** có `Điều kiện bắt đầu lại` tương ứng ở cột `M`.

---

## 6. Risk management (09) — công thức mức độ

Phân biệt rõ 2 loại, ghi vào cột `C` (Loại rủi ro):
- **Product risk**: rủi ro chất lượng sản phẩm (chức năng sai, performance kém, mất dữ liệu, lỗ hổng bảo mật)
- **Project risk**: rủi ro tiến trình (nhân sự, môi trường, tiến độ, giao tiếp, tài liệu)

`Mức độ` (cột `P`) = `Khả năng xảy ra × Mức ảnh hưởng`, mỗi trục thang `Cao / Trung bình / Thấp`:

| | Ảnh hưởng Thấp | Ảnh hưởng TB | Ảnh hưởng Cao |
|---|---|---|---|
| **Khả năng Cao** | Trung bình | Cao | Cao |
| **Khả năng TB** | Thấp | Trung bình | Cao |
| **Khả năng Thấp** | Thấp | Thấp | Trung bình |

Ghi vào `P` theo dạng `Cao (KN: Cao × AH: TB)` để review được cách suy ra.

`Tình trạng` (cột `Q`): `Mở` / `Đang giảm thiểu` / `Đã đóng` / `Chấp nhận`.

`Biện pháp giảm thiểu` (cột `R`) phải là **hành động cụ thể có chủ thể**, không phải nguyện vọng.
- Đúng: `Chốt Q&A với PO trong 2 ngày đầu sprint; QA lead theo dõi bảng Q&A hằng ngày`
- Sai: `Trao đổi thường xuyên hơn`

Rủi ro mức `Cao` **bắt buộc** kéo theo tác động thấy được trong plan: tăng độ chi tiết testware ở
3.1, thêm test type ở 3.2, hoặc thêm effort ở sheet 07. Không thấy tác động → ghi `open_points.md`.

---

## 7. Estimation (07) — nguồn số liệu

Ưu tiên nguồn theo thứ tự:
1. Output skill `estimate-test` cho các chức năng của dự án (nếu có) → map trực tiếp vào `G`/`L`/`S`
2. Log effort dự án tương tự trước đó (metrics-based)
3. Expert-based, ghi rõ giả định vào `02_Scope test` 2.5

Bắt buộc:
- Effort chỉ điền cột `Plan` (`G` `L` `S`), cột `Actual` (`H` `M` `T`) để trống
- Mọi dòng data giữ đủ 3 formula (`S`, `AB`, `AC`) theo `template-cell-map.md`
- Cột `A` (Release) không được trống — dự án 1 release thì ghi `Release 1`
- Số liệu suy ra từ `estimate-test` → ghi nguồn vào `AD` (Comment), vd `estimate-test v1, 2026-08-20`

---

## 8. Traceability (output phụ)

`testplan_traceability_matrix.md` map 2 chiều:
- Mỗi tính năng ở `02_Scope test` 2.3 → source ID / tài liệu ở `01_Introduction` 1.4
- Mỗi tính năng ở 2.3 → phương pháp test ở 3.1 → test level/type ở 3.2

Tính năng ở 2.3 mà không truy được về source, hoặc không có phương pháp test ở 3.1 → là **lỗi plan**,
phải sửa trước khi kết thúc.
