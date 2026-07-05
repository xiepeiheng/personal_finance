# Account + Transfer 实现计划

## 背景

当前系统是纯损益视角（收入/支出），无法区分"消费支出"和"资产转移"（如银行卡入金到证券账户）。引入 Account（资金容器）和 Transfer（账户间转账）后：
- **Transaction** = 真正的收入/支出，影响损益面板
- **Transfer** = 账户间资金搬运，不影响损益面板

## Git 前置操作

- 项目尚未初始化 git，根目录即 monorepo 根
- 初始化：`git init`，创建 `.gitignore`，`git commit -m "save: pre-account-transfer snapshot"`
- `.gitignore` 忽略：`__pycache__/`, `*.pyc`, `db.sqlite3`, `logs/`, `.env.development`, `.venv/`, `node_modules/`, `dist/`, `.idea/`, `.ruff_cache/`, `.codegraph/`

## 步骤

### 1. 后端数据模型

#### 1.1 新增 `Account`（`finance/models.py`）

| 字段 | 类型 | 说明 |
|------|------|------|
| name | CharField(50) | "招商银行储蓄卡7258" |
| account_type | CharField(20, choices) | bank/securities/cash/credit/alipay |
| initial_balance | DecimalField(11,2) | 默认 0 |
| current_balance | DecimalField(11,2) | 计算字段，Signal 维护 |
| user | FK→User, PROTECT | 行级隔离 |
| remarks | CharField(200), blank | |
| created_at | DateTimeField, auto | |
| updated_at | DateTimeField, auto | |

#### 1.2 新增 `Transfer`（`finance/models.py`）

| 字段 | 类型 | 说明 |
|------|------|------|
| from_account | FK→Account, PROTECT | 钱从哪来 |
| to_account | FK→Account, PROTECT | 钱去哪 |
| amount | DecimalField(11,2) | 正数 |
| trade_time | DateField | |
| note | CharField(200), blank | |
| user | FK→User, PROTECT | 行级隔离 |
| created_at/updated_at | DateTimeField, auto | |

Meta 约束：`CheckConstraint(from_account != to_account)` 防止自转账。

#### 1.3 修改 `Transaction`

新增：`account = FK→Account (null=True, blank=True, on_delete=PROTECT)`

### 2. Signal 扩展（`finance/signals.py`）

- `Transfer.post_save` / `post_delete` → 重新计算 from_account 和 to_account 的 current_balance
- `Transaction.post_save` / `post_delete` → 如果 account 不为 null，重新计算 account.current_balance
- 扩展现有 Transaction signal：通过 `pre_save` 追踪旧 account 值，account 变更时重算新旧两个账户
- `Account.current_balance = initial_balance + SUM(转入) - SUM(转出) + SUM(关联Transaction金额)`

### 3. 错误码（`utils/code_enum.py`）

- `ACCOUNT_NOT_FOUND = (3004, "账户不存在")`
- `TRANSFER_SAME_ACCOUNT = (3005, "转账的源账户和目标账户不能相同")`

### 4. 后端 API

#### 4.1 `AccountViewSet`（`finance/views.py`）

- ModelViewSet，IsAuthenticated + ViewModelPermissions
- get_queryset：行级隔离
- perform_destroy：检查有关联 Transaction/Transfer 则拒绝
- 筛选：`?account_type=bank`

#### 4.2 `TransferViewSet`

- ModelViewSet，同上权限
- 筛选：`?from_account=` / `?to_account=` / `?date_from=` / `?date_to=`

#### 4.3 修改序列化器

- 新增 `AccountSerializer`, `TransferSerializer`
- `TransactionSerializer` / `TransactionCreateSerializer`：增加可空 `account` 字段

#### 4.4 路由（`config/urls.py`）

```
/api/finance/accounts/   → AccountViewSet
/api/finance/transfers/  → TransferViewSet
```

#### 4.5 现有端点不变

`/summary` 和 `/daily-summary` 不需要改动——它们只统计 Transaction，Transfer 天然排除在外。

### 5. 种子数据命令

新建 `finance/management/commands/seed_accounts.py`：
- 创建 "招商银行储蓄卡7258"（bank）
- 创建 "投资账户"（securities）
- 将所有 `account__isnull=True` 的 Transaction 关联到招商银行卡

### 6. 前端 API 层

- `frontend/src/api/finance/type.ts`：新增 `Account`、`Transfer`、`AccountType` 类型
- `frontend/src/api/finance/account-api.ts`：新增，标准 CRUD
- `frontend/src/api/finance/transfer-api.ts`：新增，标准 CRUD
- `frontend/src/api/finance/index.ts`：导出新模块

### 7. 前端页面

#### 7.1 `Accounts.vue`（`pages/finance/`）

NaiveUI DataTable，标准 CRUD，显示余额，支持按 account_type 筛选。

#### 7.2 `Transfers.vue`（`pages/finance/`）

NaiveUI DataTable，CRUD，筛选（来源/目标账户、日期范围）。

### 8. 修改现有页面/组件

- `Dashboard.vue`：新增 "账户余额" 卡片行，显示所有账户 current_balance
- `TransactionForm.vue`：增加可空的账户选择下拉
- `MainLayout.vue`：侧边栏增加 "账户管理"、"转账记录" 菜单项
- `router/index.ts`：新增 `/accounts`、`/transfers` 懒加载路由

## 涉及文件

| 文件 | 操作 |
|------|------|
| `.gitignore` | 新增 |
| `backend/finance/models.py` | 修改 |
| `backend/finance/signals.py` | 修改 |
| `backend/finance/views.py` | 修改 |
| `backend/finance/serializers.py` | 修改 |
| `backend/config/urls.py` | 修改 |
| `backend/utils/code_enum.py` | 修改 |
| `backend/finance/management/commands/seed_accounts.py` | 新增 |
| `frontend/src/api/finance/type.ts` | 修改 |
| `frontend/src/api/finance/account-api.ts` | 新增 |
| `frontend/src/api/finance/transfer-api.ts` | 新增 |
| `frontend/src/api/finance/index.ts` | 修改 |
| `frontend/src/pages/finance/Accounts.vue` | 新增 |
| `frontend/src/pages/finance/Transfers.vue` | 新增 |
| `frontend/src/pages/Dashboard.vue` | 修改 |
| `frontend/src/components/TransactionForm.vue` | 修改 |
| `frontend/src/pages/MainLayout.vue` | 修改 |
| `frontend/src/router/index.ts` | 修改 |

共 18 个文件（7 新增，11 修改）。

## 验证清单

- [ ] `python manage.py makemigrations` 生成 migration，无错误
- [ ] `python manage.py migrate` 执行成功
- [ ] `python manage.py seed_accounts` 创建两个账户并关联历史数据
- [ ] `/api/finance/accounts/` GET/POST/PUT/DELETE 正常
- [ ] `/api/finance/transfers/` GET/POST/PUT/DELETE 正常
- [ ] `/api/finance/transactions/` 返回的 Transaction 包含 account 字段
- [ ] `/api/finance/transactions/summary/` 金额不受 Transfer 影响
- [ ] 添加 Transfer 后，相关两个 Account 的 current_balance 自动更新
- [ ] Transaction account 变更后，新旧账户余额自动重算
- [ ] 前端 `pnpm type-check` 通过
- [ ] 前端 `pnpm build` 通过
- [ ] 面板新增账户余额卡片，数据正确
- [ ] 转账页面 CRUD 正常
- [ ] 账户页面 CRUD 正常
- [ ] 导航菜单新增两项
