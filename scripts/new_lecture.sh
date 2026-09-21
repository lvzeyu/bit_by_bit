#!/usr/bin/env bash
# 用法: scripts/new_lecture.sh <NN> <short-name>
# 例:   scripts/new_lecture.sh 01 intro  ->  lectures/01_intro/
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "用法: $0 <NN> <short-name>" >&2
  exit 1
fi

root="$(cd "$(dirname "$0")/.." && pwd)"
dest="$root/lectures/${1}_${2}"

if [ -e "$dest" ]; then
  echo "已存在: $dest" >&2
  exit 1
fi

cp -R "$root/lectures/_template" "$dest"
sed -i.bak "s/第 NN 讲/第 $1 讲/" "$dest/README.md" && rm "$dest/README.md.bak"
echo "已创建 $dest"
