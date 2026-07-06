# Personal Finance

个人/家庭财务记账系统。基于 Django + DRF + Vue 3 的 monorepo。

## 设计理念

### 核心概念

| 概念 | 模型 | 说明 |
|------|------|------|
| 账本 | `Ledger` | 分类聚合容器，分**时间维度**（"2025总账"）和**分类维度**（"日常三餐"）两种 |
| 消费计划 | `Category` | 关联 1~2 个账本，含预算和实际金额 |
| 交易记录 | `Transaction` | 单笔收入/支出，必属一个分类和一个账户 |
| 账户 | `Account` | 资金存放容器（银行卡、证券户、信用卡等） |
| 转账 | `Transfer` | 账户间资金调拨，**不计入收支面板** |
| 账户类型 | `AccountType` | 可自定义的账户分类（银行/证券/现金/信用卡/支付宝等） |

### 核心区分

- **Transaction** = 真正的收入或支出，影响月度损益
- **Transfer** = 钱在账户间搬家（如银行卡入金到证券账户），不影响损益
- **Account** 的 `current_balance` 由 `initial_balance + 转入 - 转出 + 关联 Transaction 金额` 自动计算

### 行级数据隔离

多用户 SaaS 架构，每个用户只能看到自己的数据。超级管理员可查看全部。

### 计算字段维护

所有聚合字段（`Category.actual_amount`、`Ledger.balance`、`Account.current_balance`）通过 Django signals 自动维护，不在 ViewSet 代码中手动更新。提供 `/api/finance/ledgers/recalculate/` 接口用于全量重算。

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Django 6.0 / DRF 3.14+ / SimpleJWT / drf-spectacular |
| 前端 | Vue 3.5 / TypeScript 6.0 / Naive UI 2.44 / Pinia |
| 数据库 | SQLite（开发） |
| 包管理 | uv（Python）/ pnpm（Node） |

## 项目结构

```
personal_finance/
├── backend/
│   ├── config/          # Django 配置、分页、路由
│   ├── finance/         # 核心业务：模型、视图、序列化器、信号
│   ├── users/           # 认证：登录/登出/注册，用户/组/权限 CRUD
│   ├── utils/           # 共享工具：响应格式、异常处理、权限
│   ├── manage.py
│   └── start.sh         # 一键启动（清理日志 + 启动服务）
├── frontend/
│   └── src/
│       ├── api/         # API 客户端（按模块拆分）
│       ├── axios/       # Axios 实例 + 拦截器 + Token 刷新
│       ├── stores/      # Pinia 状态（auth）
│       ├── router/      # Vue Router + 导航守卫
│       ├── pages/       # 页面组件
│       └── components/  # 可复用组件
└── docs/                # 设计文档
```

## 快速开始

### 后端

```bash
cd backend

# 复制环境变量
cp .env.example .env.development

# 安装依赖
uv sync

# 数据库迁移
uv run python manage.py migrate

# 创建种子数据（用户、账本、分类、示例交易）
uv run python manage.py seed_data

# 创建初始账户 + 关联历史交易
uv run python manage.py seed_accounts

# 启动（自动清理旧日志）
./start.sh
```

### 前端

```bash
cd frontend

pnpm install
pnpm dev     # http://localhost:5174
```

### 默认账号

执行 `seed_data` 后会自动创建：

| 用户 | 密码 | 角色 |
|------|------|------|
| admin | admin | 超级管理员 |
| user1 | pass1234 | 普通用户 |

> **提示**：部署到服务器前，请删除这些默认账号或修改密码。生产环境建议通过系统注册功能或管理员手动创建用户。

## API 概览

| 路径 | 说明 |
|------|------|
| `POST /api/login/` | 登录，返回 JWT + 权限信息 |
| `/api/finance/ledgers/` | 账本 CRUD |
| `/api/finance/categories/` | 分类 CRUD |
| `/api/finance/transactions/` | 交易 CRUD + 批量 + summary/daily-summary |
| `/api/finance/accounts/` | 账户 CRUD |
| `/api/finance/transfers/` | 转账 CRUD |
| `/api/finance/account-types/` | 账户类型 CRUD |
| `/api/finance/ledgers/recalculate/` | 全量重算 |
| `/api/docs/` | Swagger 文档 |

所有响应为统一格式：`{success, code, message, data}`。

## 部署

1. 前端构建：`cd frontend && pnpm build` → 产物在 `dist/`
2. Nginx 配置参考 `docs/usage-guide.md`
3. 后端用 Gunicorn/uWSGI 运行，WSGI 入口：`config/wsgi.py`

## License

MIT
