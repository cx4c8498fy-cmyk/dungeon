#!/bin/zsh
cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
  python3 game.py
else
  python game.py
fi

echo
echo "終了しました。Enterキーで閉じます。"
read -r
