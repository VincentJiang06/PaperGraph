#!/usr/bin/env bash
# Deterministic: are git tags protected by the same server-side ref rules as branches?
# Self-contained; fixed dates so the output is byte-stable across runs.
set -u
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
export GIT_AUTHOR_DATE='2020-01-01T00:00:00Z' GIT_COMMITTER_DATE='2020-01-01T00:00:00Z'
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT; cd "$W" || exit 1
git init -q --bare r.git
git -c init.defaultBranch=main init -q w && cd w
git config commit.gpgsign false
echo a > f; git add -A; git commit -qm c1; C1=$(git rev-parse HEAD)
echo b > f; git add -A; git commit -qm c2; C2=$(git rev-parse HEAD)
git tag t1 "$C2"; git branch b1 "$C2"
git push -q "file://$W/r.git" main t1 b1
git --git-dir="$W/r.git" config receive.denyDeletes true
git --git-dir="$W/r.git" config receive.denyNonFastForwards true
echo "git: $(git --version | cut -d' ' -f3)"
echo "remote cfg: denyDeletes=$(git --git-dir="$W/r.git" config --get receive.denyDeletes) denyNonFastForwards=$(git --git-dir="$W/r.git" config --get receive.denyNonFastForwards)"
r() { # $1 label, rest = git args
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "$label: ACCEPTED"; else echo "$label: REJECTED"; fi
}
git tag -f t1 "$C1" >/dev/null 2>&1; git branch -f b1 "$C1" >/dev/null 2>&1
r "TAG    non-fast-forward force-update" git push --force "file://$W/r.git" t1
r "BRANCH non-fast-forward force-update" git push --force "file://$W/r.git" b1
r "TAG    delete"                        git push "file://$W/r.git" :refs/tags/t1
r "BRANCH delete"                        git push "file://$W/r.git" :refs/heads/b1
echo "-- reflog on the bare remote --"
git --git-dir="$W/r.git" config core.logAllRefUpdates true
git tag -f t2 "$C1" >/dev/null 2>&1; git push -q --force "file://$W/r.git" t2
git tag -f t2 "$C2" >/dev/null 2>&1; git push -q --force "file://$W/r.git" t2
echo "logAllRefUpdates=true  -> tag reflog entries: $(git --git-dir="$W/r.git" reflog refs/tags/t2 2>/dev/null | wc -l | tr -d ' ')"
git --git-dir="$W/r.git" config core.logAllRefUpdates always
git tag -f t3 "$C1" >/dev/null 2>&1; git push -q --force "file://$W/r.git" t3
git tag -f t3 "$C2" >/dev/null 2>&1; git push -q --force "file://$W/r.git" t3
echo "logAllRefUpdates=always -> tag reflog entries: $(git --git-dir="$W/r.git" reflog refs/tags/t3 2>/dev/null | wc -l | tr -d ' ')"
