#!/usr/bin/env bash
# Kiem tra pack con dung duoc khong -- chay truoc khi tag phien ban moi.
#
# Kiem 5 dieu, deu la cai tung hong that:
#   1. Cai vao mot du an TRONG thi chay duoc          (tieu chi "clone ve la chay")
#   2. Cai lai KHONG ghi de cau hinh nguoi dung da sua
#   3. Test suite cua cac skill co script van pass
#   4. Khong lot du lieu khach hang / credential vao pack
#   5. Moi skill co SKILL.md hop le (co frontmatter name + description)
set -uo pipefail

PACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SANDBOX="$(mktemp -d)"
trap 'rm -rf "$SANDBOX"' EXIT

PASS=0; FAIL=0
ok()   { printf "  PASS  %s\n" "$*"; PASS=$((PASS+1)); }
bad()  { printf "  FAIL  %s\n" "$*"; FAIL=$((FAIL+1)); }
head_() { printf "\n== %s ==\n" "$*"; }

SKILLS="bug-analyst create-test-schedule estimate-test execute-testcase gen-requirement gen-testcase gen-test-plan log-bug"

# Cai gi LA noi dung phat di -> phai duoc quet du lieu khach hang.
SCAN_TARGETS="skills configs inputs templates README.md requirements.txt install.sh"
# Cai gi la tooling -> khong quet. Danh sach nay PHAI ngan va on dinh; khong chac
# thi de vao SCAN_TARGETS cho an toan.
SCAN_IGNORE=".git .github .gitignore test-pack.sh"

# ---------- 1. Cai vao du an trong ----------
head_ "1. Cai vao du an trong"
mkdir -p "$SANDBOX/home" "$SANDBOX/duan"
if CLAUDE_SKILLS_DIR="$SANDBOX/home" "$PACK_DIR/install.sh" "$SANDBOX/duan" >"$SANDBOX/install.log" 2>&1; then
  ok "install.sh chay xong"
else
  bad "install.sh loi -- xem $SANDBOX/install.log"; cat "$SANDBOX/install.log"
fi
for s in $SKILLS; do
  [ -e "$SANDBOX/home/$s/SKILL.md" ] && ok "dang ky $s" || bad "thieu $s/SKILL.md sau khi cai"
done
[ -f "$SANDBOX/duan/configs/module_registry.yaml" ] && ok "sinh configs/" || bad "khong sinh configs/"
[ -f "$SANDBOX/duan/inputs/log_bug_manifest.yaml" ]  && ok "sinh inputs/"  || bad "khong sinh inputs/"

# Tung mac loi: xoa ca thu muc templates/ vi thay .xlsx bi trung trong skill,
# keo theo mat 8 template .md ma 4 skill dang tham chieu. Chan lai bang cach
# doi chieu THUC TE: moi ten template duoc SKILL.md nhac den phai ton tai.
head_ "1b. Template ma skill tham chieu phai co that"
missing=0
for name in $(grep -rhoE "(business_rules|functional_requirements|validation_rules|traceability_matrix|impact_scope|source_inventory|assumptions_and_open_points)" "$PACK_DIR"/skills/*/SKILL.md 2>/dev/null | sort -u); do
  if [ -f "$PACK_DIR/templates/$name.md" ]; then ok "co templates/$name.md"
  else bad "THIEU templates/$name.md (skill dang tham chieu)"; missing=$((missing+1)); fi
done
[ -f "$PACK_DIR/templates/excel_testcase_schema.yaml" ] && ok "co templates/excel_testcase_schema.yaml" || bad "THIEU templates/excel_testcase_schema.yaml"
for x in $(find "$PACK_DIR/skills" -name "*.xlsx" -not -path "*/fixtures/*" 2>/dev/null); do
  ok "template xlsx nam trong skill: $(basename "$x")"
done
[ -d "$SANDBOX/duan/templates" ] && ok "install sinh templates/ cho du an" || bad "install KHONG sinh templates/"

# ---------- 2. Cai lai khong ghi de ----------
head_ "2. Cai lai khong ghi de cau hinh da sua"
echo "# nguoi dung tu sua" >> "$SANDBOX/duan/configs/module_registry.yaml"
CLAUDE_SKILLS_DIR="$SANDBOX/home" "$PACK_DIR/install.sh" "$SANDBOX/duan" >/dev/null 2>&1
if grep -q "nguoi dung tu sua" "$SANDBOX/duan/configs/module_registry.yaml"; then
  ok "sua cua nguoi dung con nguyen"
else
  bad "cai lan 2 DA GHI DE cau hinh nguoi dung"
fi

# ---------- 3. Test suite cua skill ----------
head_ "3. Test suite cua cac skill"
for s in $SKILLS; do
  d="$PACK_DIR/skills/$s/tests"
  [ -d "$d" ] || continue
  out=$(cd "$d" && python3 -m pytest . -q 2>&1 | tail -1)
  case "$out" in
    *failed*|*error*) bad "$s: $out" ;;
    *passed*)         ok  "$s: $out" ;;
    *)                bad "$s: khong chay duoc pytest ($out)" ;;
  esac
done

# ---------- 4. Khong lot du lieu khach ----------
# Chan diem mu cua allowlist TRUOC khi quet.
#
# Allowlist an hon --exclude voi file tooling, nhung doi lai co diem mu: them
# thu muc NOI DUNG moi ma quen khai thi no khong duoc quet, va khong ai biet.
# "Nho khai" la loai luat nguoi ta quen -- chinh minh da quen 2 lan trong 1 buoi.
# Nen khong dua vao tri nho: doi chieu top-level thuc te, thieu khai la FAIL.
head_ "4a. Allowlist quet co phu het noi dung khong"
uncovered=0
for entry in $(ls -A "$PACK_DIR"); do
  case " $SCAN_TARGETS $SCAN_IGNORE " in
    *" $entry "*) ;;
    *) bad "'$entry' chua khai o SCAN_TARGETS lan SCAN_IGNORE -> dang bi quet BO QUA"
       uncovered=$((uncovered+1)) ;;
  esac
done
[ "$uncovered" = "0" ] && ok "moi thu muc/file top-level da duoc khai" \
  || bad "$uncovered muc chua khai -- them vao SCAN_TARGETS (neu la noi dung) hoac SCAN_IGNORE (neu la tooling)"

head_ "4. Khong lot du lieu khach hang / credential"
# Chi quet NOI DUNG duoc phat di, khong quet ca cay.
#
# Da vap 2 lan vi quet ca cay roi dap them --exclude: chinh test-pack.sh chua
# regex "gettii" nen tu bat minh, roi .github/workflows/ci.yml cung vay. Cu
# them exclude thi lan sau co file tooling moi lai vap tiep.
# Liet ke tuong minh cai gi LA noi dung -> file tooling them vao khong lam nhieu.
scan_paths() {
  for t in $SCAN_TARGETS; do
    [ -e "$PACK_DIR/$t" ] && printf "%s\n" "$PACK_DIR/$t"
  done
}

leak() {  # $1 = mo ta, $2 = regex
  hits=$(scan_paths | xargs grep -rEl "$2" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$hits" = "0" ]; then
    ok "khong co $1"
  else
    bad "LOT $1 trong $hits file"
    scan_paths | xargs grep -rEl "$2" 2>/dev/null | sed "s|$PACK_DIR/|    |"
  fi
}
leak "ten du an cu (gettii)"      "gettii|GETTII"
leak "URL git noi bo"             "git\.nal\.vn|nal/tt3"
leak "email ca nhan"              "huongdt@|ngocttb@"
leak "token that"                 "glpat-|ghp_|xox[baprs]-"

# ---------- 5. SKILL.md hop le ----------
head_ "5. SKILL.md hop le"
for s in $SKILLS; do
  f="$PACK_DIR/skills/$s/SKILL.md"
  if [ ! -f "$f" ]; then bad "$s: khong co SKILL.md"; continue; fi
  if python3 - "$f" <<'PY'
import re, sys, yaml
t = open(sys.argv[1], encoding="utf-8").read()
m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
assert m, "khong co frontmatter"
fm = yaml.safe_load(m.group(1))
assert fm.get("name"), "frontmatter thieu name"
assert fm.get("description"), "frontmatter thieu description"
PY
  then ok "$s: frontmatter hop le"
  else bad "$s: SKILL.md sai frontmatter"
  fi
done

# ---------- Ket qua ----------
head_ "Ket qua"
printf "  %d pass, %d fail\n\n" "$PASS" "$FAIL"
[ "$FAIL" = "0" ] || exit 1
