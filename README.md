# qa-ai-pack

Bộ 7 skill Claude Code phủ trọn vòng đời QA — từ đọc tài liệu nghiệp vụ tới log bug lên tracker.
Đóng gói từ một dự án thật để dùng lại cho mọi dự án khác.

## Cài

```bash
git clone <url-repo> qa-ai-pack
cd qa-ai-pack
./install.sh /duong/dan/toi/du-an-cua-ban
```

Xong 2 việc: đăng ký 7 skill vào `~/.claude/skills/`, và dựng `configs/` + `inputs/` trong dự án đích.

Chạy lại lúc nào cũng được — **file cấu hình đã có sẽ không bị ghi đè**.

```bash
./install.sh                              # chỉ đăng ký skill, không đụng dự án nào
QA_PACK_INSTALL_MODE=copy ./install.sh …  # copy thay vì symlink (phát cho người khác)
```

## 7 skill

| Lệnh | Làm gì | Output |
|---|---|---|
| `/gen-requirement` | Đọc 設計書/spec/ticket → bộ requirement chuẩn hoá | `knowledge/<module>/` |
| `/gen-testcase` | Sinh manual test case | Google Sheet |
| `/gen-test-plan` | Master Test Plan theo ISTQB + IEEE 829 | Google Sheet 12 sheet |
| `/estimate-test` | Ước lượng manhour/manday, 18 activity | Google Sheet |
| `/create-test-schedule` | Lịch test cho tester, theo dõi actual vs estimate | `.xlsx` |
| `/execute-testcase` | Chạy test trên môi trường, ghi kết quả vào chính file test case | cập nhật in-place |
| `/log-bug` | Log bug lên **Redmine / GitLab / Jira** theo template QA | issue trên tracker |

Thứ tự thường dùng:

```
gen-requirement → gen-testcase → estimate-test → create-test-schedule
                                      ↓
                            execute-testcase → log-bug
```

## Sau khi cài, phải điền 3 thứ

**1. `configs/module_registry.yaml`** — sổ cái nối cả 7 skill. Liệt kê module của dự án;
mỗi module đi qua requirement → test case → estimate, trạng thái ghi ngay tại đây.
Quy ước hạt: **1 màn hình = 1 module**.

**2. `configs/*_project_profile.yaml`** — `project_code`, `project_name`, và chuẩn riêng của dự án
(cột test case, mức severity, tracker…).

**3. Biến môi trường cho credential** — pack **không bao giờ** nhận credential ghi thẳng trong file:

```bash
export GITLAB_TOKEN=...        # hoặc REDMINE_API_KEY / JIRA_API_TOKEN
export TEST_PASSWORD=...       # tài khoản môi trường test
```

Trong YAML chỉ ghi tên biến: `token: "env:GITLAB_TOKEN"`. Ghi thẳng giá trị → skill **từ chối chạy**.

## Cấu hình gộp theo 3 tầng

```
configs/<skill>_project_profile.yaml   chuẩn chung dự án      (ưu tiên thấp nhất)
inputs/<skill>_manifest.yaml           cấu hình lần chạy này  (ghi đè profile)
tham số dòng lệnh                                             (ưu tiên cao nhất)
```

Thiếu key bắt buộc → skill **dừng và báo**, không tự suy diễn.

## Test

```bash
cd skills/log-bug/tests           && python3 -m pytest . -q   # 139 test
cd skills/execute-testcase/tests  && python3 -m pytest . -q   # 63 test
```

Chạy được offline, không cần tracker thật (test regression tự dựng stub HTTP rồi tự tắt).

## Nguyên tắc chung của cả bộ

- **Không đoán.** Cấu hình thiếu hoặc mâu thuẫn → dừng và báo.
- **Không bịa dữ liệu.** Không đánh Pass khi chưa quan sát được kết quả thật.
- **Không log bug cho lỗi môi trường.** Đó là `Pending` ở test case, không phải bug ứng dụng.
- **Credential chỉ qua biến môi trường**, không bao giờ vào report/evidence/description.
- **Không sửa cột định nghĩa test case gốc** — skill chỉ ghi vào cột execution.

## Yêu cầu

- Python 3.9+, `pyyaml`, `requests`, `openpyxl`
- Google Sheet (tuỳ chọn): service account JSON, trỏ qua `GOOGLE_APPLICATION_CREDENTIALS`

## Đang còn nợ

- `execute-testcase` và `log-bug` có `config_loader.py` riêng, gần giống nhau. Chưa gộp vì
  hai bản đã lệch nhau (bản của log-bug chặn credential plaintext, trả 3 giá trị).
  Gộp sau khi dùng thật vài dự án, biết rõ cái gì thực sự chung.
- `gen-requirement` và `gen-testcase` mới chỉ có SKILL.md, chưa có script — logic nằm hết trong
  prompt, agent tự thực thi.
