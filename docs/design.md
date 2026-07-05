# 财务应用设计

## 基本设计

### 技术栈

- **后端**：Django + Django REST Framework + djangorestframework-simplejwt（仅提供 API）
- **前端**：Vue（前后端分离）
- **数据库**：SQLite（初期）→ PostgreSQL（规模扩大后）
- **鉴权**：JWT + Django 内置 `auth` 应用

### 项目结构

Monorepo 方式组织：

```
/personal_finance
├── /backend          # Django 项目
│   └── /finance      # Finance 应用（模型、视图、序列化器）
├── /frontend        # Vue 项目
└── /docs            # 文档
```

### 部署模式

目标定位：`SaaS` 模式，但实际上系统为一个组织（典型场景：一个家庭）部署使用。

### 用户管理

- 使用 Django 内置 `auth` 应用进行用户和权限管理
- 自注册默认关闭，通过 `UserViewSet.register` 注册时自动加入 `UserRole.USER` 组

---

## 设计理念

### 核心概念

- **Transaction（交易记录）**：最小的原子数据，每笔收入或支出
- **Category（消费计划）**：关联到具体消费计划，如"日常三餐计划"、"出游计划"
- **Ledger（账本）**：分类聚合容器，按维度组织

### 为什么这样设计

个人财务的两个核心视角：
1. **时间维度** - 看某一时间段（如 2025 年）内的所有收支
2. **事件维度** - 看某一专项（如三餐、出游、投资）的收支

通过两种 Ledger 和 Category 的双向关联，实现灵活的账本组织，同时避免 Ledger 数量爆炸。

---

## 模型设计

### `Ledger`（账本/维度集合）

Ledger 既是"账本"也是"维度分类工具"，通过 `ledger_type` 区分两种角色：

| 字段名称 | 字段含义 | 类型 | 属性 | 备注 |
| -------- | -------- | ---- | ---- | ---- |
| id | / | 自增主键 | / | |
| ledger_type | 账本类型 | `varchar(20)` | 必填 | `time`=时间维度，`category`=分类维度 |
| name | 名称 | `varchar(20)` | 必填 | 如"2025年收支总账"、"日常三餐" |
| user | 所属用户 | `FK auth.User` | 必填 | 创建者 |
| balance | 余额 | `DecimalField(max_digits=11, decimal_places=2)` | 必填 | 由子记录汇总得出 |
| is_complete | 是否完成 | `BooleanField` | `default=False` | 用于筛选，不用于锁定 |
| remarks | 备注 | `varchar(200)` | 可空 | |
| created_at | 创建时间 | `DateTimeField` | auto | |
| updated_at | 更新时间 | `DateTimeField` | auto | |

**ledger_type 说明**：
- `time`：时间维度账本，如"2025年收支总账"、"2024年总账"
- `category`：分类维度账本，如"日常三餐"、"出游计划"、"投资账本"

### `Category`（消费计划）

消费计划，属于一个或两个 Ledger：

| 字段名称 | 字段含义 | 类型 | 属性 | 备注 |
| -------- | -------- | ---- | ---- | ---- |
| id | / | 自增主键 | / | |
| time_ledger | 关联时间账本 | `FK finance.Ledger` | 可空 | 关联到时间维度 Ledger |
| category_ledger | 关联分类账本 | `FK finance.Ledger` | 可空 | 关联到分类维度 Ledger |
| name | 名称 | `varchar(100)` | 必填 | 如"2025年三餐"、"春节出游" |
| budget | 预算金额 | `DecimalField(max_digits=11, decimal_places=2)` | 必填 | 负数=支出计划，正数=收入计划 |
| actual_amount | 实际金额 | `DecimalField(max_digits=11, decimal_places=2)` | 必填 | 由子记录汇总得出 |
| is_complete | 是否完成 | `BooleanField` | `default=False` | 用于筛选，不用于锁定 |
| star | 满意度 | `PositiveIntegerField` | `default=0` | 可选值：0-5 |
| remarks | 备注 | `varchar(200)` | 可空 | |
| created_at | 创建时间 | `DateTimeField` | auto | |
| updated_at | 更新时间 | `DateTimeField` | auto | |

**关联规则**：
- 至少关联一个 Ledger（time_ledger 或 category_ledger）
- 可以同时关联两个 Ledger
- 不允许两个都为空

### `Transaction`（交易记录）

单条收入或支出记录。

| 字段名称 | 字段含义 | 类型 | 属性 | 备注 |
| -------- | -------- | ---- | ---- | ---- |
| id | / | 自增主键 | / | 可作为订单编号使用 |
| category | 所属分类 | `FK finance.Category` | 必填 | |
| trade_time | 交易日期 | `DateField` | 必填 | |
| partner | 交易对象 | `varchar(100)` | 必填 | 如"美团"、"超市" |
| amount | 金额 | `DecimalField(max_digits=11, decimal_places=2)` | 必填 | 负数=流出（支出），正数=流入（收入），不得为零 |
| star | 满意度 | `PositiveIntegerField` | `default=0` | 可选值：0-5 |
| channel | 交易渠道 | `varchar(100)` | 可空 | 如"现金"、"招商信用卡" |
| detail | 交易细节 | `varchar(100)` | 可空 | |
| ticket_file | 凭据 | `FileField` | 可空 | 消费小票、转账截图等 |
| remarks | 备注 | `varchar(200)` | 可空 | |

---

## 计算字段维护

`Category.actual_amount` 和 `Ledger.balance` 由子记录汇总得出，通过 **Django Signals** 自动维护：

- `post_save`：创建/更新 `Transaction` 时触发
- `post_delete`：删除 `Transaction` 时触发

```python
# signals.py
@receiver(post_save, sender=Transaction)
def update_amounts_on_save(sender, instance, **kwargs):
    instance.category.recalculate()
    # 如果关联了 time_ledger，更新其 balance
    if instance.category.time_ledger:
        instance.category.time_ledger.recalculate()
    # 如果关联了 category_ledger，更新其 balance
    if instance.category.category_ledger:
        instance.category.category_ledger.recalculate()

@receiver(post_delete, sender=Transaction)
def update_amounts_on_delete(sender, instance, **kwargs):
    instance.category.recalculate()
    if instance.category.time_ledger:
        instance.category.time_ledger.recalculate()
    if instance.category.category_ledger:
        instance.category.category_ledger.recalculate()
```

`Model.recalculate()` 方法只负责 SUM 计算：

```python
class Category(Model):
    def recalculate(self):
        total = self.transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        self.actual_amount = total
        self.save(update_fields=['actual_amount', 'updated_at'])

class Ledger(Model):
    def recalculate(self):
        if self.ledger_type == "time":
            total = self.time_categories.aggregate(Sum('actual_amount'))['actual_amount__sum'] or 0
        else:
            total = self.category_categories.aggregate(Sum('actual_amount'))['actual_amount__sum'] or 0
        self.balance = total
        self.save(update_fields=['balance', 'updated_at'])
```

**注意**：两个维度的 balance 各自独立计算，不会相加。各看各的维度。

---

## 权限设计

### 行级数据隔离

在 `ViewSet.get_queryset()` 中实现过滤：

```python
# Ledger: 直接过滤 user
def get_queryset(self):
    queryset = super().get_queryset()
    if not self.request.user.is_superuser:
        queryset = queryset.filter(user=self.request.user)
    return queryset

# Category: 过滤关联 Ledger 属于该用户的记录
def get_queryset(self):
    queryset = super().get_queryset()
    if not self.request.user.is_superuser:
        queryset = queryset.filter(
            Q(time_ledger__user=self.request.user) |
            Q(category_ledger__user=self.request.user)
        )
    return queryset

# Transaction: 通过 category 链式过滤
def get_queryset(self):
    queryset = super().get_queryset()
    if not self.request.user.is_superuser:
        queryset = queryset.filter(
            Q(category__time_ledger__user=self.request.user) |
            Q(category__category_ledger__user=self.request.user)
        )
    return queryset
```

| 用户类型 | 行为 |
| -------- | ---- |
| 普通用户 | 属于 `UserRole.USER` 组，只能操作自己的记录 |
| 超级管理员 | `is_superuser=True`，不受限制，可操作所有记录 |

### 登录返回权限结构

登录成功后返回 JWT token + 权限信息：

```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "permissions": {
    "modules": {
      "auth": ["user", "group"],
      "finance": ["transaction", "category", "ledger"]
    },
    "actions": {
      "user": ["view", "add", "change", "delete"],
      "group": ["view", "add", "change", "delete"],
      "transaction": ["view", "add", "change", "delete"],
      "category": ["view", "add", "change", "delete"],
      "ledger": ["view", "add", "change", "delete"]
    }
  }
}
```

- `modules`：用户能访问的应用及其下的模型名称列表
- `actions`：每个模型的具体操作权限

## 分页

全局分页器 `ElementPlusPagination` 定义于 `backend/config/pagination.py`。

返回格式：

```json
{
    "total": 28,
    "items": [...],
    "page": 1,
    "size": 20
}
```

查询参数：`?page=1&size=100`。默认值：page=1, size=20, max_page_size=500。

可通过视图类 `pagination_class` 属性覆盖。

---

## 功能示例

### 典型 Ledger 结构

```
时间维度 Ledger:
├── 2025年收支总账
│   ├── 2025年三餐
│   ├── 2025年服饰美容
│   ├── 2025年住房水电
│   ├── 2025年出行
│   └── 2025年工资收入
│
└── 2024年收支总账
    ├── 2024年三餐
    └── ...

分类维度 Ledger:
├── 日常三餐
│   ├── 2025年三餐
│   └── 2024年三餐
│
├── 出游计划
│   ├── 2025年春节出游
│   └── 2024年国庆出游
│
├── 投资账本
│   ├── 基金投资
│   └── 股票投资
│
└── 收入计划
    ├── 工资收入
    └── 奖金收入
```

### 使用场景

| 场景 | 操作 |
|------|------|
| 看 2025 年总收支 | 查询 `ledger_type=time` 的 "2025年收支总账" |
| 看三餐历年趋势 | 查询 `ledger_type=category` 的 "日常三餐" 及其所有 Category |
| 新增一笔三餐消费 | Transaction → Category "2025年三餐" |
| 看某次出游的所有支出 | 查询分类维度 Ledger "出游计划" 下的 Category |

---
