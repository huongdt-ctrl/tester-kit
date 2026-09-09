---
name: bug-analyst
description: "Thu thap bug cua mot giai doan tu tracker (GitLab: mot trong cac label o bug_labels, mac dinh bug + Egg / Jira issuetype=Bug / Redmine tracker=Bug) theo khoang ngay, clone template QA TEM-ST03_02 (di kem skill: templates/template_bug_analysis.xlsx) roi do du lieu va phan tich vao dung cot, xuat ra file .xlsx dat ten theo giai doan. Tu gian dong khi vuot 37 bug va va lai cong thuc + 5 chart. Triggers (VI): 'phan tich bug', 'bug analysis', 'thong ke bug theo sprint', 'bao cao bug giai doan', 'gen file phan tich bug'."
---

# Skill: bug-analyst

## 1. Muc tieu

Bien danh sach bug rai rac tren tracker thanh **mot file phan tich bug cua mot
giai doan** dung template QA cua team (TEM-ST03_02), voi day du 7 bang thong ke
va 5 chart tu tinh.

Skill lo ba viec ma lam tay hay sai:
- **Loc bug cho dung giai doan** -- dung nhan/loai bug cua tung tracker, dung
  khoang ngay tao, co phan trang nen khong bo sot bug thu 101.
- **Do vao dung cot cua template** -- 12 cot, 5 dropdown, khong lech o.
- **Giu template con tinh duoc** -- vuot 37 bug thi phai chen dong VA keo theo
  cong thuc, dropdown, chart. Bo mot trong bon la file mo ra bi lech am tham.

## 2. Pham vi

Dung duoc cho:
- Bao cao phan tich bug cuoi sprint / cuoi giai doan / cuoi milestone
- Tong hop bug tu GitLab, Jira hoac Redmine (doi bang **mot dong** `tracker.system`)
- Lam lai file khi giai doan da chot them bug (chay lai voi `--overwrite`)

**Khong** dung cho:
- Log bug moi len tracker -> dung skill `log-bug`
- Chay test va ghi ket qua test case -> dung skill `execute-testcase`
- Bug ngoai khoang ngay cua giai doan (skill loc theo **ngay TAO** bug)

## 3. Tracker duoc ho tro

Ca ba deu goi API that, chi doc, khong ghi gi len tracker:

| System | API | Bug la gi | Loc ngay theo |
|---|---|---|---|
| `gitlab` | `GET /api/v4/projects/:id/issues`, header `PRIVATE-TOKEN` | issue co **mot trong** cac label o `tracker.bug_labels` (mac dinh `bug`; project NAL thuong dung `["bug", "Egg"]`) | `created_after` / `created_before` |
| `jira` | `GET /rest/api/2/search` (JQL), Basic auth | issue co **issuetype** `Bug` (`tracker.bug_issue_type`) | `created >=` / `created <=` |
| `redmine` | `GET /issues.json`, header `X-Redmine-API-Key` | issue co **tracker** `Bug` (`tracker.bug_tracker_name`) | `created_on=><from|to` |

Ghi chu ky thuat da chot:
- **Jira dung API v2**, giong skill `log-bug` -- v3 tra ve field dang ADF, khong
  dung chung duoc bo xu ly text.
- **GitLab khong co field priority cho issue** -> doc tu label dang
  `priority::High`. Khong co label do thi de **trong**, khong doan `Normal`
  (doan thi bang IV dep nhung sai).
- **Redmine loc theo `tracker_id` dang so**, khong loc theo ten -> skill tu tra
  id tu `/trackers.json` neu config chi khai ten.
- `system` mac dinh trong profile la **GitLab**; doi mot dong la sang jira/redmine.
- **Nhieu label bug tren GitLab = nhieu request.** GitLab loc `labels=bug,Egg` theo
  **AND** (issue phai co ca hai), khong co cu phap OR. Skill goi rieng tung label
  roi gop lai va khu trung theo `iid` -- issue dinh ca hai label chi dem **mot**
  lan. Doi lai: n label = n vong phan trang, chay lau gap n.
- `bug_labels` chi co o GitLab. Jira loc theo `bug_issue_type`, Redmine theo
  `bug_tracker_name`/`bug_tracker_id` -- moi ben mot gia tri, chua ho tro nhieu.

## 3b. Egg va bug la HAI LOAI KHAC NHAU -- khong duoc gop

Quy uoc cua team NAL:

| Nhan | Ai tim ra | Khi nao | Doc ra dieu gi |
|---|---|---|---|
| `Egg` | **Tester noi bo** | **Truoc** ban giao | Luoi test bat duoc bao nhieu, bat dung cho nguy hiem khong |
| `bug` | **Khach hang** | **Sau** ban giao | Bao nhieu loi LOT qua luoi test |

Hai con so nay tra loi hai cau hoi khac nhau, **gop vao mot file la mat ca hai**:
ty le lot loi (escape rate) = so bug / (so Egg + so bug). Gop lai thi mau so va tu
so nhap lam mot, khong con gi de do.

**Cach chay dung: hai lan, hai file.**

```bash
# Loi noi bo cua giai doan
python3 $S/bug_analyst_cli.py --profile $P --phase "Sprint 3 (Egg)" ... collect --out bug_analysis/egg.json

# Loi khach hang bao trong cung giai doan -- doi bug_labels trong profile thanh ["bug"]
python3 $S/bug_analyst_cli.py --profile $P --phase "Sprint 3 (bug KH)" ... collect --out bug_analysis/bug.json
```

Khai `bug_labels: ["bug", "Egg"]` chi dung khi ban that su muon **mot bang tong
tat ca defect** va da chap nhan mat phep do lot loi.

**Truoc khi ket luan "0 loi khach hang": kiem tra nhan do co TON TAI tren project
khong.** GitLab tra ve rong ca khi nhan khong ton tai lan khi that su khong co
issue nao -- hai truong hop khac han nhau ve y nghia:

```bash
curl -s -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://<host>/api/v4/projects/<path-url-encoded>/labels?per_page=100" \
  | python3 -c "import json,sys; print(sorted(l['name'] for l in json.load(sys.stdin)))"
```

Khong thay nhan trong danh sach => project chua ghi loai defect do o day, con so 0
la "khong co cho ghi", khong phai "khong co loi".

## 4. Cach goi

Ba buoc. Buoc 2 la viec cua agent, khong phai cua script.

```bash
S=~/.claude/skills/bug-analyst/scripts
P=configs/bug_analyst_project_profile.yaml

# 0. Kiem tra config truoc khi goi that
python3 $S/bug_analyst_cli.py --profile $P verify

# 1. Thu thap bug cua giai doan
python3 $S/bug_analyst_cli.py --profile $P \
    --phase "Sprint 3" --date-from 2026-08-01 --date-to 2026-08-31 \
    collect --out bug_analysis/collected_bugs.json

# 2. AGENT phan tich: dien severity / cause / root_cause vao file JSON tren

# 3. Xuat file Excel
python3 $S/bug_analyst_cli.py --profile $P \
    build --bugs-file bug_analysis/collected_bugs.json
```

Doi tracker: them `--system jira` (hoac sua `tracker.system` trong profile).

### Ten file output

Quy uoc da chot: **`<Giai đoạn>_Phân tích Bug_<YYYYMMDD-YYYYMMDD>.xlsx`**

vd `Sprint 3_Phân tích Bug_20260801-20260831.xlsx`.

## 5. Scripts di kem

Toan bo I/O xac dinh nam trong `scripts/`, agent **khong improvise** cac buoc nay:

| Script | Trach nhiem |
|---|---|
| `bug_analyst_cli.py` | Entry point duy nhat -- 3 subcommand. Output **luon** JSON, exit 0 ok / 1 loi, ke ca khi YAML sai cu phap hay template bi thay bang file rac |
| `adapters/` | 3 tracker, chi doc. Factory `build_adapter()` la cho duy nhat biet ten tracker cu the |
| `config_loader.py` | Merge profile < manifest < CLI; resolve credential `env:` |
| `bug_mapper.py` | Issue tho -> dong template. Parse `[ticket cha][man hinh] noi dung` |
| `template_layout.py` | **Nguon su that duy nhat ve toa do sheet.** Moi phep dich dong o day |
| `catalogue.py` | Doc danh muc Cause / Root cause tu sheet `Define`, bu nhung muc bang thong ke bo sot |
| `sheet_ops.py` | Chen dong + va lai 4 thu openpyxl khong tu va |
| `formula_writer.py` | Sinh lai toan bo cong thuc thong ke theo toa do moi |
| `workbook_builder.py` | Dieu phoi: clone -> chen dong -> do du lieu -> cong thuc -> chart |

## 6. Rang buoc THAT cua template (da do, khong phai phong doan)

Template `templates/template_bug_analysis.xlsx` (ban TEM-ST03_02), sheet `List bug`:

- Header o **dong 2**, 12 cot: `No. | Egg ID | Egg name | Screen name | Milestone |
  Title/Subject | Priority | Severity | Type | Cause catelogies | Root cause | Note`
- Vung data **chi 37 dong** (row 3..39). 7 bang thong ke + 5 chart nam duoi va
  **neo vao so dong tuyet doi**.
- Dropdown san co: Priority `Emergent/Urgent/High/Normal/Low`, Severity
  `Fatal/Critical/Major/Minor/Low`, Type `UI/Logic`, 22 Cause, 26 Root cause.
- Sheet `Define` giai thich tung ma bang tieng Viet -- **doc truoc khi phan loai**.

### Vuot 37 bug: bon thu phai va lai

Da do thuc te: `openpyxl.insert_rows()` day gia tri + style xuong dung cho nhung
**bo lai** ca bon thu duoi day. Bo qua bat ky muc nao = file mo ra bi lech am tham.

| Thu bi bo lai | Xu ly |
|---|---|
| Merged cell range | Unmerge het roi merge lai theo toa do moi; dong MOI chen duoc gop lai theo dung dong mau |
| Data validation `sqref` | Keo `G3:G39` -> `G3:G<data_end>` cho ca 5 cot |
| Chart series ref | Tro lai 5 chart, nhan dien chart bang ref goc chu khong bang thu tu `ws._charts` |
| Chart anchor | Dich anchor, khong thi chart de len bang khac |

Quy mo van hanh that cua project: **~200 bug moi giai doan** -> chen 163 dong vao
vung data, day moi bang thong ke va ca 5 chart xuong hon 160 dong. Da verify
end-to-end o dung muc nay (0.6s, ca 6 bang dem dung 200). Tran phan trang
(50 trang x 100 = 5000 bug) con rat xa, nhung neu co cham thi CLI bao co
`truncated` + warning chu khong im lang cat bot.

**Moi bang deu gian duoc**, khong chi vung data: bang II khi qua 12 man hinh,
bang III khi qua 5 milestone, bang VI **luon** len 22 dong (xem loi 5 duoi day).
`Layout(n_bugs, block_rows)` nhan so dong CAN CO cua tung bang va tu tinh het.

### Nam loi co san trong template -- da sua trong file clone

Template goc (khong bi sua) co nam loi that; file clone xuat ra **da sua het**,
va CLI liet ke o `chart_refs_fixed` / `catalogue_rows_added` de team doi chieu:

1. **Bang III (Milestone)** dem `$G$3:$G$39` -- do la cot **Priority**, khong
   phai Milestone (cot E). Phan tram cung chia cho TOTAL cua bang Priority.
2. **Bang VII (Root cause)**: `COUNTIF($K$3:$K$39,$A$126:$A$151)` -- tham so thu
   hai la ca dai o nen **moi dong tra ve cung mot so**.
3. **Chart VI va VII** tro `$B$105:$B$121` / `$B$126:$B$151`, nhung so lieu hai
   bang do nam o **cot D** -> ca hai chart ve ra rong.
4. **Chart II** bo qua dong dau tien cua bang (`$A$44` thay vi `$A$43`), **chart V**
   lay ca dong header (`$A$87` thay vi `$A$88`).
5. **Bang VI thieu 5 muc danh muc**: sheet `Define` khai **22** cause nhung bang VI
   chi liet ke **17** -- thieu `REQ1.4 Other`, `COD1.6 Other`, `TES1.3 Other`,
   `DEP1.3 Other`, `OTH Other`. Bug xep vao 5 muc do **khong duoc dem vao dau ca**,
   va TOTAL cua bang VI im lang nho hon so bug.

Loi thu 5 duoc sua bang cach **noi bang VI len du 22 dong** (dung chinh co che
gian dong o tren): 5 dong moi duoc gop o `A:C` giong cac dong san co, co COUNTIF
rieng, va TOTAL doi thanh `SUM` het 22 dong. CLI bao chinh xac nhung muc da them
o `catalogue_rows_added`. Bang VII (Root cause) doi chieu ra **du ca 26 muc** nen
khong phai noi them.

Danh muc doc tu sheet **`Define`**, khong doc tu dropdown: nhan trong dropdown
noi bang dau phay nhung ban than mot so nhan co dau phay ben trong
(`SKI1.1 ... Requirement Definition, Basic Design`) -> tach theo dau phay la tach sai.

`uncounted` trong output JSON gio chi con bao gia tri **khong nam trong ca danh
muc** (vd go tay sai ma) -- do la loi du lieu that, khong phai khoang trong template.

### Chuan hoa gia tri truoc khi ghi (bat buoc)

Nhan cua bang thong ke duoc sinh tu chinh du lieu bug, nen hai ben phai khop theo
**dung luat so sanh cua Excel COUNTIF**: no **bo qua hoa/thuong** nhung **KHONG bo
qua dau cach**. Skill vi the:

- **Cat dau cach dau/cuoi moi gia tri chu khi ghi vao vung data.** Ghi `"Sprint 3 "`
  trong khi nhan la `"Sprint 3"` -> COUNTIF truot, bug do bien mat khoi thong ke.
- **Gop nhan bang dong khong phan biet hoa/thuong**, giu cach viet gap dau tien.
  De `"G10"` va `"g10"` thanh hai dong nhan thi moi dong dem ca hai -> TOTAL dem doi
  (do that: 4 bug ra TOTAL 7).

## 7. Ranh gioi may / nguoi

Script chi dien nhung o **suy ra duoc** tu tracker:

| Cot | Nguon |
|---|---|
| `No.` | Thu tu |
| `Egg ID` | **ID ticket bug** |
| `Egg name` | **Ten bug** (phan noi dung sau 2 ngoac cua title) |
| `Screen name` | Parse `[ticket cha][man hinh]` tu title; khong co -> `All screen` |
| `Milestone` | Milestone / fixVersion / fixed_version cua tracker; khong co -> ten giai doan |
| `Title/Subject` | Title day du |
| `Priority` | Map ten priority cua tracker -> 5 gia tri dropdown |
| `Type` | Label `ui`/`logic`; khong co label thi doan tu title |
| `Note` | Link ticket |

Ba o **de TRONG cho agent phan tich** -- `Severity`, `Cause catelogies`,
`Root cause`. Doan bua vao day thi bang V/VI/VII dep nhung sai.

Ca **bang Issue / Action** o duoi cung cung do agent viet 100% -- co luat rieng
o muc **7b**, doc truoc khi viet.

`build` **tu chan** khi ba o do con trong; muon xuat ban thieu phai noi ro
`--allow-incomplete`.

`build` cung **tu chan khi 0 bug**: gan nhu luon la loc sai (nham label/loai bug,
nham khoang ngay, nham project) chu hiem khi la giai doan sach that. Giai doan
that su khong co bug thi them `--allow-empty`.

Canh bao `uncounted` so nhan **khong phan biet hoa/thuong**, dung luat COUNTIF:
go `major` thay vi `Major` thi Excel VAN dem dung, nen khong bao dong gia --
neu bao gia, agent se di "sua" mot gia tri von dang dung.

Khi phan tich, giu dung ranh gioi khai niem:
- **Severity** = muc tac dong len nguoi dung. **Priority** = thu tu can fix.
  Hai cai khac nhau, khong copy o nay sang o kia.
- **Cause catelogies** = sai o **KHAU** nao (requirement / design / code / test / deploy).
- **Root cause** = **TAI SAO** khau do sai (process / skill / discipline).

## 7b. Bang Issue / Action -- bon luat

Bang duoi cung (`No. | Issue | Action | Status | PIC`, 12 dong) do **agent viet
tay**, script chi do vao o. Day la phan bi doc nhieu nhat trong ca file va cung
bi viet do nhat: liet ke cam nhan roi ghi "Dev A, B, C fix" thi bang nay khong
theo doi duoc gi.

### Luat 1 -- Issue phai la VAN DE, khong phai khoang trong du lieu

Ba cau hoi gac cong. Truot **mot** cau la **bo dong do**, khong co ngoai le:

1. **Co so neo tu chinh du lieu bug vua thu khong?** Issue phai chi ra duoc
   cot / con so dua ra nhan dinh (vd `12/45 bug o Cause = COD1.1`,
   `8 bug o man Đăng nhập`). Khong neo duoc vao so nao -> cam nhan, khong phai issue.
2. **Co phai chi la "khong co du lieu" khong?** `0 bug nhan bug` khi **khach hang
   chua test** la **trang thai tien do**, KHONG phai issue -- cho ghi la muc 3b
   (kiem tra nhan co ton tai) hoac cot Note, KHONG phai bang nay. Tuong tu:
   "chua co milestone", "chua co Severity" khi giai doan chua chay xong.
3. **Giai doan sau lam khac di duoc khong?** Khong dan tới viec lam khac di
   duoc -> bo.

**12 dong la du cho 3-6 issue that.** Dien cho het 12 dong bang issue mo la lam
loang bang: nguoi doc khong biet cai nao dang thuc su phai xu ly.

### Luat 2 -- Action phai KIEM CHUNG duoc

Moi action bat buoc du **bon phan**. Thieu mot phan la action chua viet xong:

| Phan | Sai | Dung |
|---|---|---|
| **Ai** | "Dev A, B, C", "team dev", "QA" | ten that + role: `Nam (BE)`, `Linh (QA)` |
| **Lam gi** | "fix cho ky", "chu y hon", "review lai" | dong tu + doi tuong DO DUOC: `thêm 6 test case biên cho màn Thanh toán` |
| **Khi nao** | (bo trong) | moc cu the: `trước 2026-09-20` hoac `trước khi mở Sprint 4` |
| **Bang chung** | (bo trong) | artifact mo ra kiem duoc: `link MR`, `checklist review có người thứ hai ký`, `số bug Cause=COD1.1 sprint sau ≤ 4` |

**Phep thu truoc khi ghi:** doc action roi tu hoi *"ba tuan nua toi mo cai gi ra
de biet viec nay da lam?"*. Khong tra loi duoc -> viet lai. "Da nhac team",
"da luu y" KHONG phai bang chung; commit / MR / file test case / con so do lai
sprint sau thi la.

### Luat 3 -- Action phai treo khoi case, dung o goc DU AN

Bug trong file nay chi la **nhung cho DA BI SOI**. Sua dung 5 ticket da log thi
5 cho do thanh 5 cho sach nhat du an, con cho cung kieu chua ai test van y nguyen
-- ky sau lai log lai dung loai loi do. Vi the moi action di **ba tang, moi tang
mot dong**:

| Tang | Cau hoi phai tra loi | Vi du |
|---|---|---|
| **1. Chan ngay** | cai da bat duoc, sua o dau | `FE bo hardcode màu/font-size ở 4 màn #61 #64 #67 #95 — bằng chứng: link MR, trước 15/09` |
| **2. Quet tuong tu** | **con cho nao CUNG KIEU ma chua ai test?** Phai neu **mau so TOAN DU AN**, khong phai mau so trong lo bug | `grep hardcode hex/px trên cả 30 module trong scope, không chỉ 4 màn đã có Egg — bằng chứng: danh sách file còn hardcode, trước 17/09` |
| **3. Chan tai phat** | **lan sau con sinh ra duoc nua khong?** Sua vao quy trinh / cong cu / DoD, kem so do | `thêm lint rule chặn hex trong style mới — bằng chứng: CI fail khi commit hardcode; đo cuối Sprint 7: Egg IMP3 ≤ 2 (kỳ này 6)` |

**Phep thu:** bit het so ticket trong action ma action **van con nghia** -> da treo
khoi case. Con doc ra "sua #61, #64" la van case by case.

**Mau so phai la mau so du an.** Issue neu so trong lo bug (`6/15 Egg`); action
neu **pham vi quet toan du an** (`30 module trong scope`, `moi màn có input ngày`,
`moi quan hệ xoá cha-con`). Thieu ve nay thi action chi va dung phan da lo ra.

**Nhung KHONG suy rong bua.** Quet theo **cung CO CHE sinh loi**, khong phai cung
chu de: #99/#116 la co che "xoa cha nhung con con tham chieu" -> quet moi cap
cha-con co chuc nang xoa; KHONG phai "review lai toan bo màn seat". Action rong
den muc khong ai biet bat dau tu dau thi cung vo dung nhu action chi va 1 ticket.

### Luat 4 -- Moi y mot dong, co danh so

KHONG viet van lien mach trong o:

- **Issue**: 1-2 dong. Dong dau neu van de + so neo. Khong ke lai qua trinh.
- **Action**: danh so `1.` `2.` `3.` -- **dung ba tang cua Luat 3**, moi tang mot
  so. Qua 4 so -> tach thanh 2 issue rieng (dung nhoi tang 2 va 3 vao cung mot so).
- **Trong moi so, moi Y lai mot dong rieng.** Dong chinh = VIEC. Bang chung,
  han, so do -> **y con**, moi cai mot dong, CLI tu thut vao `\u2022`. Nhoi
  "viec + bang chung + han" vao cung mot dong thi doc phai do mat tim dau la
  vat, va dong do dai gap 2-3 lan be rong cot nen Excel wrap tuy y giua cau.
- **Tieu chi la MOT DONG MOT Y, khong phai dem ky tu.** Do that: o `Issue`
  (merge B:D) chua ~36 ky tu mot dong hien thi, o `Action` (merge E:I) ~82 --
  moi cau du nghia deu dai hon the, va wrap la binh thuong vi skill da tinh
  height theo so dong sau wrap. **Dau hieu phai tach**: mot dong ngon tu 3 dong
  hien thi tro len -> gan nhu chac chan dong do dang gom nhieu y, day bot xuong
  y con (`Cặp cần rà: ...`, `4 nhóm: ...`) chu dung de nguyen mot cau dai.
- Truyen vao JSON: `issue` / `action` nhan **list**; phan tu la **string** (mot
  dong) hoac **list cua string** (`[dong chinh, y con, y con...]`). CLI tu danh
  so + thut y con. String co `\n` san cung duoc; da tu danh so hoac gach dau
  dong thi CLI giu nguyen, khong danh so lan hai.

```json
{"issues": [
  {"issue": "12/45 bug có Cause = COD1.1 (code sai logic), tập trung ở màn Thanh toán",
   "action": [["Chặn ngay: Nam (BE) bổ sung unit test cho 3 hàm tính phí màn Thanh toán",
               "Bằng chứng: link MR",
               "Hạn: 2026-09-20"],
              ["Quét tương tự: rà mọi màn có tính toán tiền trong 30 module scope",
               "Bằng chứng: danh sách hàm chưa có UT",
               "Hạn: 2026-09-24"],
              ["Chặn tái phát: DoD task BE thêm điều kiện “hàm tính tiền phải có UT”",
               "Bằng chứng: CI báo coverage",
               "Đo cuối Sprint 4: tỉ lệ bug COD1.1 ≤ 15% (kỳ này 27%)"]],
   "status": "Open", "pic": "Nam"}
]}
```

Ba dong tren doc theo dung thu tu **tang 1 / tang 2 / tang 3** cua Luat 3. Khong
bat buoc ghi chu tien to "Chan ngay:" / "Quet tuong tu:" -- nhung ghi vao thi
nguoi doc biet ngay action da du ba tang hay con thieu.

**Do that, khong phai phong doan:** o `B`/`E` cua bang nay la **merged cell +
wrap_text**, va Excel **KHONG tu gian chieu cao dong da merge** -> text nhieu
dong bi che mat neu khong set height. Skill tu set `row_dimensions[row].height`;
**dung** go tay newline vao file da xuat roi mong Excel tu gian.

Chieu cao tinh theo **so dong SAU KHI WRAP**, khong phai so dong logic: be rong
o lay bang **tong ca vung merge** (B:D ~37 ky tu, E:I ~82), roi moi dong logic
dem `ceil(do_dai / be_rong)` dong hien thi. Do that: dong action 150-200 ky tu
an 2-3 dong -> tinh theo dong logic la dat height thieu mot nua, text bi che
im lang.

Template can GIUA o `Issue` (`horizontal=center`) -- hop voi nhan ngan nhung doan
van dai thi lech mep hai ben. Skill doi rieng field `horizontal` sang `left`,
**giu nguyen** `vertical=center` + `wrap_text`: gan `Alignment` moi tay la mat
wrap_text, mat wrap_text la text tran ngang qua o ben canh.

**Tran 12 dong la cung** (row 155..166 theo toa do goc): duoi 166 khong con o nao
co border / merge / wrap. Truyen hon 12 issue thi CLI ghi 12 dong dau va bao phan
bo o `issues_dropped`, khong tran im lang xuong vung trang. Output JSON cua
`build` co `issues_written` / `issues_dropped` / `issue_slots` de doi chieu.

## 8. Bao mat credential

Giong `log-bug` va `execute-testcase`: `token` / `api_key` / `api_token`
**khong bao gio** ghi plaintext trong file config -- chi ghi `env:TEN_BIEN`.

- Ghi plaintext -> CLI **dung ngay**, khong goi tracker.
- Thieu bien env -> CLI **dung ngay**, khong goi API voi credential rong.
- Credential **luon bi mask** trong moi output JSON.

## 9. Test

```bash
cd ~/.claude/skills/bug-analyst && python3 -m unittest discover -s tests
```

66 test, khong cham mang (HTTP duoc mock). Phu: quy mo that 200 bug, phep dich
dong khi vuot suc chua,
va lai chart/dropdown/merge, nam loi cua template, bu danh muc bang VI va dem
duoc bug xep vao muc vua bu, mo phong lai COUNTIF de bat cong thuc tro nham cot,
filter cua ca 3 tracker, phan trang, hop dong "luon tra JSON" cua CLI, vi tri bang
Issue/Action sau khi dich dong, dinh dang o Issue/Action (danh so, y con
xuong dong, chieu cao dong merged tinh sau wrap, can le trai, tran 12 dong), va hai regression ve chuan hoa gia tri (lech hoa/thuong,
lech dau cach) -- mo phong dung luat COUNTIF de bat lai duoc bug goc.
