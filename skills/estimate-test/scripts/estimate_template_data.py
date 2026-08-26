# Dữ liệu nguồn cho template test estimate (luồng QA có AI hỗ trợ).
# Tách khỏi builder để sửa hệ số mà không phải đọc code layout.
# Mọi giờ trong BASE_RATES là giờ của level Middle (baseline factor = 1.0).
#
# 3 nhóm code, xếp theo đúng thứ tự luồng làm việc:
#   G* — công chỉ định AI gen output (chuẩn bị input, viết prompt, chạy skill, chờ)
#   A* — công người làm: đọc hiểu, review, execute, verify, chốt
#   S* — công support không giao được cho AI (môi trường, test data, follow-up bug, regression)
#   R1 — rework khi output AI chưa đạt hoặc requirement đổi sau confirm

# code, tên activity, đơn vị, S, M, L, XL
#
# CALIBRATE 2026-08-18 — thay bộ DEFAULT ban đầu (sai ~15 lần ở cột XL).
# Neo vào 2 dữ kiện thật:
#   1. Phản hồi QA dự án tham chiếu: execute ~5 phút/test case là hợp lý; các hoạt động
#      khác (review requirement, review TC AI gen, Q&A) trước đó tính dư nhiều.
#   2. testcases/sample_module_h/testcase_draft.csv — 37 test case đếm thật.
# Bộ số cũ cho A4 = 0.70h/case ở cột XL (42 phút để execute 1 test case UI) —
# không bảo vệ được.
#
# CALIBRATE 2026-08-19 — lần đầu có LOG GIỜ THỰC TẾ theo activity (4 màn thật).
# Sửa G3 / A3 / A4; các activity khác giữ nguyên vì chưa có log.
#   Screen G     18 TC: gen+review TC 1.00h · test UI 2.00h
#   Screen B     20 TC: gen+review TC 1.00h · test UI 2.00h
#
# !! Giờ đo được là giờ của một bạn JUNIOR, không phải Middle. BASE_RATES là giờ
# Middle nên phải chia cho level_factor[Junior] = 1.3 trước khi nạp vào bảng.
# Bỏ bước này là nhét giờ Junior vào ô Middle → mọi estimate lệch lên 1.3 lần.
#   A4 Middle = 2.00h / 18TC / 1.3 = 0.0855 và 2.00h / 20TC / 1.3 = 0.0769 → 0.081
#   → 4.9 phút/case, khớp trực giác "execute ~5 phút/case" của QA (vốn nói về Middle).
# Chi tiết + phần chưa calibrate được (A5): references/estimation-model.md §6.
BASE_RATES = [
    ("G1", "Chuẩn bị input + chỉ định AI gen ticket task test", "ticket", 0.03, 0.05, 0.065, 0.08),
    ("A1", "Review ticket task test AI gen", "ticket", 0.03, 0.05, 0.065, 0.08),
    ("G2", "Dựng manifest + chỉ định AI gen requirement", "lần chạy", 0.08, 0.12, 0.16, 0.20),
    ("A2", "Đọc hiểu + review requirement AI tạo", "requirement item", 0.02, 0.025, 0.03, 0.04),
    ("A2b", "Q&A phân tích yêu cầu + confirm với PO", "vòng Q&A", 0.15, 0.25, 0.32, 0.40),
    ("G3", "Chỉ định AI gen test case", "lần chạy", 0.103, 0.155, 0.207, 0.258),
    ("A3", "Review test case AI gen + update", "test case", 0.026, 0.034, 0.043, 0.051),
    ("S1", "Setup môi trường test + account / quyền", "môi trường", 0.50, 1.00, 2.00, 3.00),
    ("S2", "Chuẩn bị test data", "bộ data", 0.50, 1.00, 1.50, 2.50),
    ("A4", "Execute test", "test case", 0.065, 0.081, 0.105, 0.130),
    ("G4", "Cung cấp evidence + chỉ định AI log bug", "bug", 0.015, 0.02, 0.025, 0.03),
    ("A4b", "Review bug AI log (dedupe / severity / repro)", "bug", 0.04, 0.05, 0.065, 0.08),
    ("A5", "Verify bug", "bug × round", 0.158, 0.190, 0.253, 0.317),
    ("S3", "Follow-up bug (reject / reopen / trao đổi dev)", "bug", 0.015, 0.02, 0.025, 0.03),
    ("S4", "Regression test vùng ảnh hưởng", "test case", 0.02, 0.025, 0.03, 0.04),
    ("R1", "Re-prompt + review lại (rework output AI / requirement đổi)", "vòng rework", 0.08, 0.12, 0.16, 0.20),
    ("G5", "Chỉ định AI gen test report", "module", 0.04, 0.06, 0.08, 0.10),
    ("A6", "Review + chốt test report, cập nhật status ticket", "module", 0.06, 0.09, 0.12, 0.15),
]

# level, factor, rank, ghi chú
LEVELS = [
    ("Fresher", 1.6, 1, "Chưa đủ nền phản biện output AI → đọc lại nhiều vòng, dễ sót lỗi logic"),
    ("Junior", 1.3, 2, "Review được nhưng phải đối chiếu requirement từng dòng"),
    ("Middle", 1.0, 3, "Baseline của bảng base rate"),
    ("Senior", 0.8, 4, "Bắt sai lệch AI nhanh, quyết được điểm mờ, ít vòng lặp"),
]

# code, tên activity, min level, min rank, phụ phí senior review khi gán thấp hơn
MIN_LEVELS = [
    ("G1", "Chuẩn bị input + chỉ định AI gen ticket task test", "Fresher", 1, 0.00, 0),
    ("A1", "Review ticket task test AI gen", "Junior", 2, 0.20, 1),
    ("G2", "Dựng manifest + chỉ định AI gen requirement", "Middle", 3, 0.30, 0),
    ("A2", "Đọc hiểu + review requirement AI tạo", "Middle", 3, 0.30, 1),
    ("A2b", "Q&A phân tích yêu cầu + confirm với PO", "Middle", 3, 0.30, 1),
    ("G3", "Chỉ định AI gen test case", "Junior", 2, 0.20, 0),
    ("A3", "Review test case AI gen + update", "Junior", 2, 0.20, 1),
    ("S1", "Setup môi trường test + account / quyền", "Junior", 2, 0.20, 1),
    ("S2", "Chuẩn bị test data", "Junior", 2, 0.20, 1),
    ("A4", "Execute test", "Fresher", 1, 0.00, 1),
    ("G4", "Cung cấp evidence + chỉ định AI log bug", "Junior", 2, 0.20, 0),
    ("A4b", "Review bug AI log (dedupe / severity / repro)", "Junior", 2, 0.20, 1),
    ("A5", "Verify bug", "Fresher", 1, 0.00, 1),
    ("S3", "Follow-up bug (reject / reopen / trao đổi dev)", "Junior", 2, 0.20, 1),
    ("S4", "Regression test vùng ảnh hưởng", "Fresher", 1, 0.00, 1),
    ("R1", "Re-prompt + review lại (rework output AI / requirement đổi)", "Middle", 3, 0.30, 1),
    ("G5", "Chỉ định AI gen test report", "Fresher", 1, 0.00, 0),
    ("A6", "Review + chốt test report, cập nhật status ticket", "Middle", 3, 0.30, 1),
]

# yếu tố, giá trị, ghi chú
MULTIPLIERS = [
    ("module_type_new", 1.00, "Module làm mới"),
    ("module_type_modify", 0.85, "Sửa đổi / enhancement trên module đã có"),
    ("requirement_unstable", 1.00, "VÔ HIỆU 2026-08-18 — đếm trùng tiêu chí complexity 'Số dòng open_points.md'"),
    ("ui_japanese", 1.00, "VÔ HIỆU 2026-08-18 — đếm trùng tiêu chí complexity 'Nhãn / message tiếng Nhật'"),
    ("cross_module", 1.00, "VÔ HIỆU 2026-08-18 — đếm trùng tiêu chí complexity 'Phụ thuộc module khác'"),
    ("domain_first_time", 1.25, "Tester lần đầu làm nghiệp vụ này"),
    ("ai_output_maturity_pilot", 1.30, "Prompt/skill AI mới dùng, output còn nhiều rework"),
    ("ai_output_maturity_stable", 1.00, "Prompt/skill AI đã ổn định (mặc định)"),
    ("ai_output_maturity_mature", 0.90, "Output AI đã qua nhiều vòng tinh chỉnh, rework thấp"),
]

# tham số, giá trị, number format, ghi chú
PARAMS = [
    ("bugs_per_module", 1, "0.0", "Số bug dự kiến / module — MẶC ĐỊNH dùng cho G4 / A4b / A5 / S3. "
     "Neo vào quan sát UI test 2026-08-20: ~1 bug / chức năng. Test sâu hơn (integration, "
     "regression) thì nâng số này, KHÔNG quay lại nhân % test case"),
    ("expected_defect_rate", 0.25, "0%", "KHÔNG dùng mặc định. Cách cũ: bug = số test case × tỷ lệ này. "
     "Đo thật cho thấy sai nặng: Screen A 69 TC → dự báo 17 bug, thực tế 1. Chỉ bật lại khi có "
     "dữ liệu defect thật của một phase test sâu"),
    ("retest_rounds", 2, "0", "Số vòng verify bug (A5)"),
    ("bug_followup_rate", 0.30, "0%", "Tỷ lệ bug bị reject / reopen phải follow-up (S3)"),
    ("regression_scope_rate", 0.30, "0%", "Tỷ lệ test case phải chạy lại khi regression (S4)"),
    ("rework_rounds", 1, "0", "Số vòng rework output AI (R1); AI pilot → 2, mature → 0.5"),
    ("qa_round_per_module", 1, "0", "Số vòng Q&A + confirm PO mặc định cho 1 module (A2b)"),
    ("buffer_pct", 0.15, "0%", "Buffer risk cộng vào tổng effort — đã bao gồm giờ họp / communication"),
    ("hours_per_manday", 8, "0", "Giờ làm việc / manday"),
    ("enum_correction", 0.85, "0.00", "Nhân vào kết quả LIỆT KÊ số test case từ requirement "
     "(estimation-model.md §3.1). Phép liệt kê đo được là luôn thừa: navigator +11%, history_list +25%"),
    ("tc_per_req_item", 2.3, "0.0", "CHỈ dùng khi không có cả requirement package (tier 3). "
     "Có requirement → LIỆT KÊ theo §3.1, cấm nhân hệ số này. "
     "Spread quan sát 1.25-3.36 (2.7 lần) → độ tin cậy THẤP, luôn kèm Open point"),
]

# tiêu chí, S, M, L, XL
COMPLEXITY_CRITERIA = [
    ("Số field / control trên màn hình", "<= 5", "6 - 15", "16 - 30", "> 30"),
    ("Số validation rule", "<= 3", "4 - 10", "11 - 20", "> 20"),
    ("Số alternate + exception flow", "0 - 1", "2 - 3", "4 - 6", "> 6"),
    ("Persist dữ liệu xuống DB", "Không", "1 bảng", "2 - 3 bảng", "> 3 bảng / có batch"),
    ("Phụ thuộc module khác", "Không", "1 module", "2 module", ">= 3 module"),
    ("Nhãn / message tiếng Nhật cần đối chiếu", "Không", "Ít", "Nhiều", "Toàn bộ màn hình"),
    ("Số dòng open_points.md", "0", "1 - 4", "5 - 9", ">= 10"),
    ("Cách chấm", "Đa số tiêu chí rơi vào cột nào thì lấy cột đó; hoà nhau → lấy cột cao hơn", "", "", ""),
]

# function, code, complexity, volume (số hoặc formula), level, multiplier, note
# Dòng mẫu bám đúng thứ tự BASE_RATES; volume phái sinh viết bằng formula để đổi
# tham số ở Rate Card là tự cập nhật. Row thực tế bắt đầu từ 4 (E10 = volume A3...).
SAMPLE_ROWS = [
    ("sample_module", "G1", "M", 1, "Junior", 1.00, "1 ticket task test cần AI gen"),
    ("sample_module", "A1", "M", 1, "Junior", 1.00, "Review ticket AI gen"),
    ("sample_module", "G2", "M", 1, "Middle", 1.00, "1 lần chạy /gen-requirement (gồm dựng manifest)"),
    ("sample_module", "A2", "M", 12, "Middle", 1.00, "12 requirement item = FR + BR + VR"),
    ("sample_module", "A2b", "M", "=qa_round_per_module", "Middle", 1.00, "Q&A + confirm PO"),
    ("sample_module", "G3", "M", 1, "Junior", 1.00, "1 lần chạy /gen-testcase"),
    ("sample_module", "A3", "M", 20, "Junior", 1.00, "20 test case AI gen"),
    ("project_level", "S1", "M", 1, "Junior", 1.00, "Project-level: chỉ tính 1 lần, module sau để Volume = 0"),
    ("project_level", "S2", "M", 1, "Junior", 1.00, "Project-level nếu dùng chung bộ data"),
    ("sample_module", "A4", "M", "=E10", "Junior", 1.00, "Execute = số TC ở dòng A3"),
    ("sample_module", "G4", "M", "=bugs_per_module", "Junior", 1.00, "Bug dự kiến / module (UI test)"),
    ("sample_module", "A4b", "M", "=E14", "Junior", 1.00, "Review đúng số bug AI đã log"),
    ("sample_module", "A5", "M", "=E15*retest_rounds", "Junior", 1.00, "Verify bug × số vòng retest"),
    ("sample_module", "S3", "M", "=E15*bug_followup_rate", "Junior", 1.00, "Bug bị reject / reopen"),
    ("sample_module", "S4", "M", "=E13*regression_scope_rate", "Junior", 1.00, "Regression vùng ảnh hưởng"),
    ("sample_module", "R1", "M", "=rework_rounds", "Middle", 1.00, "Rework output AI / requirement đổi"),
    ("sample_module", "G5", "M", 1, "Junior", 1.00, "Chỉ định AI gen test report"),
    ("sample_module", "A6", "M", 1, "Middle", 1.00, "Chốt report + cập nhật status ticket"),
]

# loại, nội dung, ảnh hưởng tới estimate, độ tin cậy, nguồn
ASSUMPTION_ROWS = [
    ("Assumption", "Base rate là giờ của level Middle; level khác quy đổi qua Level factor",
     "Toàn bộ cột Adjusted (h)", "Cao", "Rate Card mục 1 + 2"),
    ("Assumption", "Base rate calibrate 2026-08-18 từ 1 điểm dữ liệu (phản hồi QA: execute ~5 phút/case) "
     "+ 37 TC đếm thật của sample_module_h — CHƯA có log giờ thực tế theo từng activity",
     "Sai tỷ lệ tổng effort nếu team nhanh/chậm hơn mốc này", "Thấp", "references/estimation-model.md §6"),
    ("Assumption", "QA tự chạy skill AI → có tính G1..G5; nếu BA/dev chạy thì để Volume = 0",
     "Toàn bộ nhóm G", "Trung bình", "manifest: context.ai_driver"),
    ("Assumption", "Giờ họp / communication nằm trong buffer 15%, không có dòng riêng",
     "buffer_pct", "Trung bình", "Rate Card mục 5"),
    ("Assumption", "S1 / S2 là project-level — chỉ tính 1 lần ở Function = project_level",
     "Không nhân lặp theo từng module", "Cao", "SKILL.md §10.2"),
    ("Assumption", "Bug dự kiến = bugs_per_module (1 bug / chức năng, phase UI test); "
     "follow-up = bug × bug_followup_rate",
     "Volume G4 / A4b / A5 / S3", "Trung bình", "Rate Card mục 5"),
    ("Open point", "Chưa có testcase_draft.csv → volume TC suy từ (FR+BR+VR) × tc_per_req_item",
     "Volume A3 / A4 → kéo theo G4 / A4b / A5 / S3 / S4", "Thấp", "references/estimation-model.md §3"),
    ("Risk", "Multiplier requirement_unstable / ui_japanese / cross_module đã bị VÔ HIỆU (=1.00) vì "
     "đếm trùng với tiêu chí chấm complexity — không tự bật lại nếu chưa bỏ tiêu chí tương ứng ở mục 6",
     "Tránh nhân dồn 2 lần cùng 1 yếu tố", "Cao", "Rate Card mục 4 + mục 6"),
    ("Risk", "Gán level thấp hơn mức tối thiểu của activity → cộng phụ phí senior review",
     "Cột Level check tự nhận hệ số > 1", "Cao", "Rate Card mục 3"),
    ("Risk", "Requirement chưa ổn định (open_points >= 5) → vòng Q&A và rework nhiều hơn 1",
     "Volume A2b và R1 tăng", "Trung bình", "open_points.md của module"),
    ("Risk", "Prompt/skill AI còn ở mức pilot → rework_rounds = 2 và multiplier 1.30",
     "Volume R1 + toàn bộ multiplier", "Trung bình", "manifest: context.ai_output_maturity"),
]
