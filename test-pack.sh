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

SKILLS="create-test-schedule estimate-test execute-testcase gen-requirement gen-testcase gen-test-plan log-bug"

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
head_ "4. Khong lot du lieu khach hang / credential"
leak() {  # $1 = mo ta, $2 = regex
  n=$(grep -rEl "$2" "$PACK_DIR" --exclude-dir=.git --exclude="test-pack.sh" 2>/dev/null | wc -l | tr -d ' ')
  [ "$n" = "0" ] && ok "khong co $1" || { bad "LOT $1 trong $n file"; grep -rEl "$2" "$PACK_DIR" --exclude-dir=.git --exclude="test-pack.sh" 2>/dev/null | sed "s|$PACK_DIR/|    |"; }
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
