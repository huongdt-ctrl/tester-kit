#!/usr/bin/env bash
# Cai bo skill QA vao may + dung khung thu muc cho mot du an.
#
# Chay 2 viec tach bach:
#   1. Dang ky 8 skill vao ~/.claude/skills/  -> go /gen-testcase la dung duoc
#   2. Dung configs/ inputs/ trong du an dich -> skill co cho doc cau hinh
#
# KHONG BAO GIO ghi de file cau hinh da co: du an dang chay do dang ma bi
# reset config thi mat het thiet lap. File da ton tai se bi bo qua va bao ro.
set -euo pipefail

PACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_HOME="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
TARGET="${1:-}"
MODE="${QA_PACK_INSTALL_MODE:-symlink}"   # symlink | copy

SKILLS="bug-analyst create-test-schedule estimate-test execute-testcase gen-requirement gen-testcase gen-test-plan log-bug"

say()  { printf "  %s\n" "$*"; }
head_() { printf "\n== %s ==\n" "$*"; }

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  cat <<'USAGE'
Cach dung:
  ./install.sh                    # chi dang ky skill vao ~/.claude/skills
  ./install.sh /duong/dan/du-an   # dang ky skill + dung configs/ inputs/ cho du an do

Bien moi truong:
  QA_PACK_INSTALL_MODE=copy       # copy thay vi symlink (mac dinh: symlink)
  CLAUDE_SKILLS_DIR=/duong/dan    # doi cho cai skill (mac dinh: ~/.claude/skills)

symlink: sua trong pack la moi du an thay ngay -> hop khi tu phat trien pack
copy   : moi may mot ban doc lap  -> hop khi phat cho nguoi khac dung
USAGE
  exit 0
fi

# ---------- 1. Dang ky skill ----------
head_ "Cai skill vao $SKILLS_HOME (mode: $MODE)"
mkdir -p "$SKILLS_HOME"
for s in $SKILLS; do
  src="$PACK_DIR/skills/$s"
  dst="$SKILLS_HOME/$s"
  [ -d "$src" ] || { say "BO QUA $s (khong co trong pack)"; continue; }
  if [ -L "$dst" ]; then rm "$dst"
  elif [ -d "$dst" ]; then
    backup="$dst.backup-$(date +%y%m%d-%H%M%S)"
    mv "$dst" "$backup"; say "da co san -> chuyen cu sang $(basename "$backup")"
  fi
  if [ "$MODE" = "copy" ]; then cp -R "$src" "$dst"; else ln -s "$src" "$dst"; fi
  say "OK  $s"
done

# ---------- 2. Dung khung du an ----------
if [ -n "$TARGET" ]; then
  head_ "Dung khung du an tai $TARGET"
  [ -d "$TARGET" ] || { echo "  LOI: khong co thu muc $TARGET" >&2; exit 1; }
  created=0; skipped=0
  for sub in configs inputs templates; do
    mkdir -p "$TARGET/$sub"
    for f in "$PACK_DIR/$sub"/*; do
      [ -f "$f" ] || continue
      out="$TARGET/$sub/$(basename "$f")"
      if [ -e "$out" ]; then say "giu nguyen  $sub/$(basename "$f")"; skipped=$((skipped+1))
      else cp "$f" "$out"; say "tao         $sub/$(basename "$f")"; created=$((created+1)); fi
    done
  done
  # Thu muc output cac skill se ghi vao
  for d in knowledge testcases estimates schedules execution_reports execution_evidence bug_reports bug_evidence plans; do
    mkdir -p "$TARGET/$d"
  done
  say ""
  say "tao $created file cau hinh, giu nguyen $skipped file da co"
fi

head_ "Xong"
say "Kiem tra:  ls -la $SKILLS_HOME | grep -E 'gen-|log-bug|execute-|estimate-|create-test'"
if [ -n "$TARGET" ]; then
  say "Buoc tiep: sua $TARGET/configs/module_registry.yaml -> dien module that cua du an"
  say "           sua $TARGET/configs/*_project_profile.yaml -> dien project_code/name"
  say "           set bien moi truong credential (xem inputs/log_bug_manifest.yaml)"
fi
say "Mo Claude Code trong du an roi go /gen-requirement de bat dau."
