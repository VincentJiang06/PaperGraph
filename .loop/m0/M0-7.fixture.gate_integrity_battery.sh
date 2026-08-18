#!/usr/bin/env bash
# Deterministic red/green battery for the M0-7 gate_integrity design.
# Builds a throwaway repo, then asks: can a tampered gates/ (including a
# tampered gate_integrity.sh itself) be caught?
#   A. in-repo entry point  ./gates/gate_integrity.sh
#   B. out-of-repo pinned runner given ONE external 40-hex commit sha
# Fixed dates -> byte-stable output.
set -u
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
export GIT_AUTHOR_DATE='2020-01-01T00:00:00Z' GIT_COMMITTER_DATE='2020-01-01T00:00:00Z'
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT

cat > "$W/gate_integrity.sh" <<'GI'
#!/usr/bin/env bash
set -uo pipefail
REPO="${GI_REPO:-$(git rev-parse --show-toplevel 2>/dev/null)}"
LEDGER="$REPO/gates/BASELINE.ledger"; G=gates
die() { printf 'gate_integrity: RED: %s\n' "$1" >&2; exit 2; }
[ -n "$REPO" ] || die "not inside a git work tree"
if [ -n "${GI_BASE:-}" ]; then BASE="$GI_BASE"; else
  [ -f "$LEDGER" ] || die "no baseline ledger"
  prev=""; n=0
  while IFS='|' read -r commit chain; do
    n=$((n+1)); expect=$(printf '%s' "$prev" | shasum -a 256 | cut -d' ' -f1)
    [ "$chain" = "$expect" ] || die "ledger chain broken at line $n"
    prev="$prev$commit|$chain
"; BASE="$commit"
  done < "$LEDGER"
fi
[ -n "${BASE:-}" ] || die "no baseline"
git -C "$REPO" cat-file -e "$BASE^{commit}" 2>/dev/null || die "baseline $BASE not in repo"
if [ "${GI_HOISTED:-}" != "$BASE" ]; then
  PIN=$(mktemp -d); trap 'rm -rf "$PIN"' EXIT
  git -C "$REPO" archive "$BASE" "$G" | tar -x -C "$PIN" || die "cannot extract pinned $G"
  GI_HOISTED="$BASE" GI_BASE="$BASE" GI_REPO="$REPO" GI_PIN="$PIN" exec bash "$PIN/$G/gate_integrity.sh"
fi
PIN="${GI_PIN:?}"
d=$(git -C "$REPO" status --porcelain -- "$G"); [ -z "$d" ] || die "dirty $G/: $d"
git -C "$REPO" merge-base --is-ancestor "$BASE" HEAD || die "baseline not an ancestor of HEAD"
dg() { (cd "$1" && find "$G" -type f ! -name BASELINE.ledger -print0 | sort -z | xargs -0 shasum -a 256 | sed "s#  .*/#  #"); }
a=$(dg "$PIN"); b=$(dg "$REPO")
[ "$a" = "$b" ] || { echo "gate_integrity: RED: $G differs from pinned baseline" >&2; exit 3; }
echo "gate_integrity: OK"
GI

cat > "$W/run_pinned.sh" <<'RP'
#!/usr/bin/env bash
# Outside the repo. Only trusted input: $2 = 40-hex commit sha.
set -uo pipefail
REPO="$1"; BASE="$2"
PIN=$(mktemp -d); trap 'rm -rf "$PIN"' EXIT
git -C "$REPO" cat-file -e "$BASE^{commit}" 2>/dev/null || { echo "no such commit" >&2; exit 2; }
git -C "$REPO" archive "$BASE" gates | tar -x -C "$PIN" || exit 2
GI_BASE="$BASE" GI_HOISTED="$BASE" GI_REPO="$REPO" GI_PIN="$PIN" bash "$PIN/gates/gate_integrity.sh"
RP

git -c init.defaultBranch=main init -q "$W/repo"; cd "$W/repo" || exit 1
git config commit.gpgsign false
mkdir gates; echo 'process.exit(0)' > gates/check_contracts.mjs
cp "$W/gate_integrity.sh" gates/gate_integrity.sh; chmod +x gates/gate_integrity.sh
E0=$(printf '' | shasum -a 256 | cut -d' ' -f1); printf 'SEED|%s\n' "$E0" > gates/BASELINE.ledger
git add -A; git commit -qm v1; C1=$(git rev-parse HEAD)
printf 'SEED|%s\n%s|%s\n' "$E0" "$C1" "$(printf 'SEED|%s\n' "$E0" | shasum -a 256 | cut -d' ' -f1)" > gates/BASELINE.ledger
git add -A; git commit -qm baseline

say() { printf '%s -> exit %s\n' "$1" "$2"; }
./gates/gate_integrity.sh >/dev/null 2>&1; say "G1 clean / in-repo entry" $?
bash "$W/run_pinned.sh" "$W/repo" "$C1" >/dev/null 2>&1; say "G2 clean / pinned runner" $?

echo 'process.exit(0) // gutted' > gates/check_contracts.mjs
./gates/gate_integrity.sh >/dev/null 2>&1; say "R1 gate edited, uncommitted" $?
git commit -qam tamper1
./gates/gate_integrity.sh >/dev/null 2>&1; say "R2 gate edited, committed" $?

printf '#!/usr/bin/env bash\necho "gate_integrity: OK"\nexit 0\n' > gates/gate_integrity.sh
git commit -qam tamper2; CT=$(git rev-parse HEAD)
P=$(cat gates/BASELINE.ledger)
printf '%s\n%s|%s\n' "$P" "$CT" "$(printf '%s\n' "$P" | shasum -a 256 | cut -d' ' -f1)" > gates/BASELINE.ledger
git commit -qam "attacker appends its own baseline"
./gates/gate_integrity.sh >/dev/null 2>&1;                 say "R3 gate_integrity.sh itself replaced + ledger extended / in-repo entry" $?
bash "$W/run_pinned.sh" "$W/repo" "$C1" >/dev/null 2>&1;   say "R4 same tamper / pinned runner with EXTERNAL sha" $?
