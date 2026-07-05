# Personal Finance App

**Generated:** 2026-06-22
**Stack:** Django 6.0 / DRF 3.14+ / Vue 3.5 / Naive UI 2.44 / TypeScript 6.0

## OVERVIEW

Django + Vue monorepo for personal/family financial record-keeping. Backend provides DRF API with JWT auth; frontend is a Vue 3 SPA with Naive UI. Designed for single-user deployment (SaaS-style, per-user data isolation).

## STRUCTURE

```
personal_finance/
├── backend/           # Django project
│   ├── config/        # Django settings, urls, wsgi, pagination
│   ├── finance/       # Core domain: Ledger, Category, Transaction
│   ├── users/         # Auth endpoints + user/group/permission CRUD
│   ├── utils/         # Shared utilities (NOT a Django app)
│   ├── test/          # Standalone test file
│   ├── manage.py      # CLI entry
│   ├── pyproject.toml # Python deps (uv)
│   └── db.sqlite3     # Dev database
├── frontend/          # Vue 3 SPA
│   ├── src/
│   │   ├── api/       # API client (auth, finance, shared types)
│   │   ├── axios/     # Axios config + interceptors
│   │   ├── stores/    # Pinia state (auth)
│   │   ├── router/    # Vue Router + navigation guard
│   │   ├── pages/     # Route components (auth, finance, users)
│   │   └── components/# Reusable components
│   ├── vite.config.ts
│   ├── package.json   # pnpm
│   └── index.html
└── docs/              # design.md, todolist.md, usage-guide.md
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Core data models | `backend/finance/models.py` | Ledger, Category, Transaction |
| API endpoints (finance) | `backend/finance/views.py` | ViewSets: CRUD + summary/daily-summary/batch/recalculate |
| API endpoints (auth) | `backend/users/views.py` | Login, logout, register, me, user/group/perm CRUD |
| URL routing | `backend/config/urls.py` | Routes `/api/finance/` and `/api/` + drf-spectacular |
| Computed field logic | `backend/finance/signals.py` | post_save/post_delete handlers |
| Error codes | `backend/utils/code_enum.py` | OK=0, auth 1001-1004, perm 2001, domain 3001-3003, amount 4001 |
| Unified response helpers | `backend/utils/response.py` | `success_response()`/`error_response()` |
| Custom permissions | `backend/utils/permissions.py` | `ViewModelPermissions` (GET→view) |
| DRF config | `backend/config/settings.py` | REST_FRAMEWORK dict: renderer, auth, pagination, exception handler |
| Frontend pages | `frontend/src/pages/` | Login, Dashboard, Ledgers, Categories, Transactions, Users/Groups/Permissions |
| Frontend API calls | `frontend/src/api/` | auth/, finance/ + shared types |
| Frontend router | `frontend/src/router/index.ts` | Auth guard, lazy-loaded routes |
| Auth store | `frontend/src/stores/auth.ts` | Pinia + localStorage persist |
| Axios setup | `frontend/src/axios/axios.ts` | BaseURL, Bearer token, auto-refresh, error toasts |
| System design | `docs/design.md` | Full model/architecture docs |
| Design decisions | `docs/todolist.md` | Anti-patterns, abandoned approaches |

## CONVENTIONS

Unless otherwise stated, standard Django / DRF / Vue / TypeScript conventions apply. Listed below are deviations or project-specific rules.

### Backend (Python)

- **Project config package** is `config/` (not `backend/` or project-name)
- **Python >=3.13**, managed via `uv` (`pyproject.toml` + `uv.lock`)
- **Unified JSON response** — `UnifiedJSONRenderer` wraps ALL 2xx into `{success, code, message, data}`
- **Business errors** use `BusinessException(code, message, http_status)` — never bare `ValidationError` or `APIException`
- **Global exception handler** in `utils.exception_handler.custom_exception_handler`: maps BusinessException → code, DRF errors → mapped codes, 500 fallback
- **Pagination** via `ElementPlusPagination`: `?page=1&size=20` max 500, returns `{total, items, page, size}`
- **Error codes** defined in `CodeEnum` (utils/code_enum.py)
- **JWT auth** via `djangorestframework-simplejwt`: access 60min, refresh 7d, rotated
- **Permissions**: `IsAuthenticated` globally + `ViewModelPermissions` (adds `view` perm check for GET)
- **Row-level isolation** via `get_queryset()` override — blacklist approach (`not superuser → filter`)
- **Computed fields** (`Category.actual_amount`, `Ledger.balance`) maintained via Django signals, NOT in save()
- **Signals** track old FK values via `pre_save` and recalculate both old and new paths on change
- **Model cascades**: `on_delete=PROTECT` everywhere (no cascade deletes)
- **Locale**: `zh-hans`, timezone `Asia/Shanghai`
- **CORS**: configurable via env, default `localhost:5174,127.0.0.1:5175`
- **Type checking**: Pyright with `reportAttributeAccessIssue=false` (Django runtime metaclass methods)
- **No admin.py** — intentionally no Django admin (Vue-only frontend)
- **No ASGI** — WSGI only (pure REST API)

### Frontend (TypeScript / Vue)

- **Package manager**: pnpm
- **Build**: Vite 8, dev server port 5174, `@/` alias → `./src/`
- **TypeScript 6.0** strict mode with `noUncheckedIndexedAccess`
- **UI**: Naive UI 2.44 (zhCN locale), `@vicons/ionicons5` for icons
- **State**: Pinia 3.0 with `pinia-plugin-persistedstate`
- **Router**: Vue Router 5, WebHistory, auth guard checks JWT in localStorage
- **API client**: Axios with baseURL from `VITE_API_BASE_URL`, Bearer token via interceptor, auto-refresh on 401, error toasts via Naive UI
- **Token storage**: `access_token` and `refresh_token` in localStorage
- **Auth store persistence**: key `finance-auth`, persists only `username`
- **No linter/formatter configured** — neither ESLint nor Prettier

## ANTI-PATTERNS (THIS PROJECT)

| Rule | Category | Source |
|------|----------|--------|
| **No Django admin** — Vue-only frontend | Architecture | `AGENTS.md` |
| **`amount` cannot be zero** — enforced in `save()` and serializer | Domain | `finance/models.py` |
| **Category must link ≥1 ledger** — `full_clean` enforces | Domain | `finance/models.py` |
| **`is_complete` not for locking** — filtering only | Domain | `docs/design.md` |
| **Don't use `balance` for monthly queries** — cumulative across all time | Domain | `docs/todolist.md` |
| **Don't pick one of real-time vs cached** — both serve different needs | Design | `docs/todolist.md` |
| **No NaiveUI heatmap** — component doesn't exist, use ECharts | UI | `docs/todolist.md` |
| **Blacklist isolation, not whitelist** — filter by user in `get_queryset()` | Security | `AGENTS.md` |
| **Category validator checks ledger ownership** — can't use others' ledgers | Security | `finance/serializers.py` |
| **Protect before deleting** — check sub-records exist | API | `finance/views.py` |

## COMMANDS

```bash
# Backend (from backend/)
python manage.py runserver                    # Dev server (127.0.0.1:8000)
python manage.py makemigrations                # Create migrations
python manage.py migrate                       # Apply migrations
python manage.py seed_data                     # Seed demo data

# Frontend (from frontend/)
pnpm dev                                       # Dev server (0.0.0.0:5174)
pnpm build                                     # Type-check + build
pnpm type-check                                # vue-tsc type check only
```

## NOTES

- `db.sqlite3` committed but in `.gitignore` — pre-existing artifact
- `frontend/dist/` committed — pre-existing build output
- `frontend/src/composables/`, `assets/`, `api/users/` are empty (stubs)
- `backend/users/migrations/` has `__init__.py` but no migrations yet
- `backend/test/test.py` — standalone, outside Django test discovery
- No Docker setup yet
- Frontend `.env.production` has empty `VITE_API_BASE_URL` — must be filled for deployment
