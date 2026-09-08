---
name: bug-analyst
description: "Thu thap bug cua mot giai doan tu tracker (GitLab label=bug / Jira issuetype=Bug / Redmine tracker=Bug) theo khoang ngay, clone template QA TEM-ST03_02 (di kem skill: templates/template_bug_analysis.xlsx) roi do du lieu va phan tich vao dung cot, xuat ra file .xlsx dat ten theo giai doan. Tu gian dong khi vuot 37 bug va va lai cong thuc + 5 chart. Triggers (VI): 'phan tich bug', 'bug analysis', 'thong ke bug theo sprint', 'bao cao bug giai doan', 'gen file phan tich bug'."
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
| `gitlab` | `GET /api/v4/projects/:id/issues`, header `PRIVATE-TOKEN` | issue co **label** `bug` (`tracker.bug_label`) | `created_after` / `created_before` |
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

50 test, khong cham mang (HTTP duoc mock). Phu: quy mo that 200 bug, phep dich
dong khi vuot suc chua,
va lai chart/dropdown/merge, nam loi cua template, bu danh muc bang VI va dem
duoc bug xep vao muc vua bu, mo phong lai COUNTIF de bat cong thuc tro nham cot,
filter cua ca 3 tracker, phan trang, hop dong "luon tra JSON" cua CLI, vi tri bang
Issue/Action sau khi dich dong, va hai regression ve chuan hoa gia tri (lech
hoa/thuong, lech dau cach) -- mo phong dung luat COUNTIF de bat lai duoc bug goc.
