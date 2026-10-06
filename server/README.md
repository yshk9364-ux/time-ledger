# 在线账户后端

Python 3.12 标准库 HTTP API + SQLite，通过 Nginx 反向代理，只监听 127.0.0.1:5187。不开放注册，首次初始化建立 admin 用户。

环境变量：

- `LEDGER_DB`：SQLite 路径，默认 `/var/lib/time-ledger/ledger.sqlite3`。
- `ADMIN_PASSWORD`：仅首次初始化必需；从环境安全传入，数据库有用户后不再读取。不要将实际密码写入 Git。
- `PORT`：默认 5187。
- `COOKIE_SECURE`：默认 1；只有本地 HTTP 测试才设为 0。

密码以随机盐 + PBKDF2-HMAC-SHA256（600000 次）存储；会话随机 token，服务器只存 token 的 SHA256 摘要。Cookie 为 HttpOnly、Secure、SameSite=Strict，期限七天。密码修改撤销所有旧会话。错误登录 5 次后按来源 IP 限制一分钟。

保存包含 revision，SQLite BEGIN IMMEDIATE 内校验并递增。过时设备得到 409，无条件覆盖不被允许。每个用户独立账本。

## 部署

1. `npm ci && npm run build`，静态 dist 放在 `/var/www/time-ledger/`。
2. `server/app.py` 放在 `/opt/time-ledger/server/app.py`。
3. 新建系统用户 time-ledger，数据目录 `/var/lib/time-ledger` 仅由此用户访问。
4. 通过环境设置首次密码后运行 `app.setup()`，再移除初始化环境变量。不要把密码放进 systemd 文件。
5. 安装 `time-ledger.service`，systemctl enable --now。只写数据目录、禁止权限提升。
6. Nginx HTTPS：`/time-ledger/api/` proxy_pass `http://127.0.0.1:5187/`，传递 `Host $host`、`X-Real-IP $remote_addr`、`X-Forwarded-Proto $scheme`。设置 client_max_body_size 2m。HTTP 跳转到 HTTPS。
7. `/time-ledger/` alias 静态目录。无第三方字体、分析或远程数据库。

用可信域名证书；也可以使用 [Let's Encrypt IP 证书](https://letsencrypt.org/2026/03/11/shorter-certs-certbot)，要求 Certbot 5.4+、shortlived profile、配置自动续期与 Nginx reload hook。IP HTTPS 虚拟主机应作为 443 default_server，兼容不发送 IP SNI 的客户端；域名虚拟主机继续按自己的 SNI 匹配。

## 备份、恢复

把 backup.py 放在 `/opt/time-ledger/server/`，安装 time-ledger-backup.service/.timer。每日在 `/var/backups/time-ledger/` 生成一致性快照，保留最近 14 份，目录 0700、文件 0600，不通过网页访问。

恢复：停止 time-ledger 服务，备份当前数据库，选定快照替换 `/var/lib/time-ledger/ledger.sqlite3`，设 owner 为 time-ledger、权限0600，再启动。快照包含账号与会话，恢复后可在数据库清空 sessions 强制重新登录。

## 测试

```sh
python3 -m unittest discover -s server -p 'test_*.py'
```

测试使用临时数据库与测试密码，与生产 admin 独立。覆盖未登录访问、错误密码、退出会话、持久化与版本冲突。
