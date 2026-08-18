#!/usr/bin/env bash
# 把仓库里的 profile 源装到 ~/.dsh/profiles/academic-research/
#
# 仓库是唯一真值源；~/.dsh 下那份是**产物**。因此本脚本只单向覆盖，
# 绝不从 ~/.dsh 往回读——否则「运行中配置漂移」（cordis.patch.yml 热重载）
# 会悄悄回流进仓库。
#
# 〔R6-12 之后新增的第二件事〕本脚本此前只 cp 两个文件，于是 packages/dsh-academic-fetch
# 那条把自己插进配置树的 `insert` **没有任何脚本会安装它**——审计实测
# `--dump-config` 355 行里 `academic-fetch` 命中 0，M1 的交付件在 DSH 里根本不存在。
# 现在：打包 → 落 vendor → 写 file: 依赖 → npm install → 由 gates/check_profile.mjs
# 断言 `tool-academic-fetch` 真的出现在 dump 里。**装没装上，由 dump 说了算。**
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
REPO="$(dirname "$SRC")"
DSH_ROOT="${DSH_HOME:-$HOME/.dsh}"
DEST="$DSH_ROOT/profiles/academic-research"
VENDOR="$DEST/.dsh-vendor"
mkdir -p "$VENDOR"

# ① 打包本地 bundle（内容寻址意义上的产物：版本号变了才会换文件名）
PKG_DIR="$REPO/packages/dsh-academic-fetch"
TGZ_NAME="$(cd "$PKG_DIR" && npm pack --pack-destination "$VENDOR" --silent | tail -1)"
echo "已打包 → $VENDOR/$TGZ_NAME"

# ② 写 profile 清单，把 __DEST__ 占位替换成真实路径
sed "s#__DEST__#$DEST#g" "$SRC/package.json" > "$DEST/package.json"
cp "$SRC/cordis.patch.yml" "$DEST/"

# ③ 安装依赖（离线即可：依赖就是本地那个 tgz）
#
# 〔实测踩到的静默失败，必须写下来〕版本号不变时 npm 认为 `file:…0.1.0.tgz`
# 与已装的那份是同一个依赖，**直接跳过安装**——源码改了、装上去的还是旧的，
# 而 install.sh 照样打印「已安装」。我第一次就是这么拿到一个假绿的：
# 源里有 `output: anchorOutput`，跑起来的那份没有。
# 因此：先删掉旧副本与 npm 缓存条目，装完再**逐字节比对**源与产物。
#
# 〔第二个静默失败，同一次实测里踩到的〕给 npm 传 `--cache <本地目录>` 时，
# 它**退出码 0 而什么都没装**。删 node_modules 那一行是强制重装的手段；
# 退出码不是安装成功的证据——④ 的哈希比对才是。
# 锁文件也要删：它把**旧 tgz 的 integrity 哈希**钉住了，于是重新打包出来的
# 同名 tgz 会被当成「已经装过的那一个」。$DEST 整体是产物，锁文件在这里没有
# 「可复现构建」的意义——真值源是仓库，不是它。
rm -rf "$DEST/node_modules/dsh-academic-fetch" "$DEST/package-lock.json"
( cd "$DEST" && npm install --no-audit --no-fund --silent )

# ④ 安装校验：产物必须逐字节等于源。装没装上不靠 npm 的退出码，靠哈希。
SRC_H="$(shasum -a 256 "$PKG_DIR/lib/index.js" | cut -d' ' -f1)"
DST_H="$(shasum -a 256 "$DEST/node_modules/dsh-academic-fetch/lib/index.js" | cut -d' ' -f1)"
if [ "$SRC_H" != "$DST_H" ]; then
  echo "FAIL  安装产物与源不一致（npm 跳过了安装？）" >&2
  echo "      源   $SRC_H" >&2
  echo "      产物 $DST_H" >&2
  exit 1
fi

echo "已安装 → $DEST  （lib/index.js 哈希一致 ${SRC_H:0:12}…）"
echo "校验:  node $REPO/gates/check_profile.mjs"
