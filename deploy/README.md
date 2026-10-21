# 部署说明（personal_finance）

## 运行结构

```
浏览器 → 宝塔 nginx（站点 xph.silyahuukou.cn）
        ├─ /personal_finance/         → 静态文件（/www/wwwroot/xph.silyahuukou.cn/personal_finance）
        └─ /personal_finance/api/     → 127.0.0.1:8013（gunicorn, 用户 www）
                                            └─ SQLite: backend/db.sqlite3
```

- **不再使用宝塔的「Python 项目」**。面板只负责站点、反向代理和证书。
- Python 环境与依赖由 `uv` 独占管理（`pyproject.toml` + `uv.lock`），面板不会再往 venv 里装 uvicorn/daphne/uwsgi。
- 进程由 systemd 托管：单元文件 `deploy/personal-finance.service`。

## 一次部署

本地：

```bash
git add -A && git commit -m "..." && git push
```

服务器：

```bash
ssh xph@82.156.209.232
cd /opt/personal_finance/personal_finance
./deploy.sh
```

`deploy.sh` 会按顺序做：`git pull` → 生成 `backend/.env.production` → `uv sync --frozen` →
修正权限 → `migrate` → 构建前端 → 重启服务。

## 日志

| 来源 | 位置 | 轮转 |
|---|---|---|
| gunicorn 访问/错误日志 | `journalctl -u personal-finance` | journald 自动 |
| Django 应用日志 | `backend/logs/app.log` | 按天，保留 30 天 |
| Django 错误日志 | `backend/logs/error.log` | 按天，保留 90 天 |
| Django SQL 日志 | `backend/logs/sql.log` | 按天，保留 7 天 |

常用：

```bash
journalctl -u personal-finance -f          # 实时
journalctl -u personal-finance --since today
systemctl status personal-finance
```

## 权限约定（不要随意改）

- 服务以 `www` 运行，但代码目录归部署用户（`xph`）所有。
- `backend/` 目录需要 `xph:www 775`：SQLite 会在数据库旁边创建 journal 文件，`www` 必须能写这个目录。
- `backend/db.sqlite3`、`backend/logs/`、`backend/media/` 归 `www`。
- `.venv` 的解释器必须在 `www` 可读的位置。**不要用 root 或 `/home/xph` 下的 Python 建 venv**——
  `deploy.sh` 固定 `UV_PYTHON_INSTALL_DIR=/opt/uv-python` 就是这个原因。

## 常见操作

```bash
sudo systemctl restart personal-finance    # 只重启进程
sudo systemctl stop personal-finance       # 停止
journalctl -u personal-finance -n 100      # 最近 100 行
ss -ltnp | grep 8013                       # 确认只在 127.0.0.1 监听
```

## 回滚

```bash
cd /opt/personal_finance/personal_finance
git log --oneline -5
git reset --hard <commit>
sudo systemctl restart personal-finance
```

若 systemd 方案整体失败，仍可在宝塔里重新创建 Python 项目（端口 8013、gunicorn、`config.wsgi:application`），
但记得它会把 uvicorn/daphne/uwsgi 重新装进 venv。
