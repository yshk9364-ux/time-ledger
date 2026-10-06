#!/bin/zsh
cd -- "${0:A:h}" || exit 1
export PATH="/opt/homebrew/opt/node@22/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
APP_URL='http://127.0.0.1:5173'
if /usr/bin/curl -fsS --max-time 2 "$APP_URL" | /usr/bin/grep -q '时间账户'; then
  /usr/bin/open "$APP_URL"
  exit 0
fi
if ! command -v node >/dev/null; then
  echo '未找到 Node.js，请先安装 Node.js 后再启动。'
  read '?按回车关闭'
  exit 1
fi
if [ ! -d node_modules ]; then
  npm install || { read '?依赖安装失败，按回车关闭'; exit 1; }
fi
(
  for attempt in {1..30}; do
    if /usr/bin/curl -fsS --max-time 1 "$APP_URL" | /usr/bin/grep -q '时间账户'; then
      /usr/bin/open "$APP_URL"
      exit 0
    fi
    /bin/sleep 1
  done
) &
echo '正在启动时间账户。网页会自动打开。使用期间请保留此终端窗口。'
echo '关闭服务请按 Control+C。'
npm run dev -- --port 5173 --strictPort
read '?服务已停止，按回车关闭'
