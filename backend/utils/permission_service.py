from django.contrib.auth.models import User

ALL_MODELS = {
    "finance": ["ledger", "category", "transaction", "account", "accounttype", "transfer"],
    "auth": ["group", "permission", "user"],
}

ALL_PERMISSIONS = {
    "group": ["view", "add", "change", "delete"],
    "permission": ["view", "add", "change", "delete"],
    "user": ["view", "add", "change", "delete"],
    "ledger": ["view", "add", "change", "delete"],
    "category": ["view", "add", "change", "delete"],
    "transaction": ["view", "add", "change", "delete"],
    "account": ["view", "add", "change", "delete"],
    "accounttype": ["view", "add", "change", "delete"],
    "transfer": ["view", "add", "change", "delete"],
}

APP_LABEL_MAP = {
    "user": "auth",
    "group": "auth",
    "permission": "auth",
    "ledger": "finance",
    "category": "finance",
    "transaction": "finance",
    "account": "finance",
    "accounttype": "finance",
    "transfer": "finance",
}


def get_user_permissions(user: User) -> dict:
    # 匿名用户无任何权限
    if user.is_anonymous:
        return {"modules": {}, "actions": {}}

    actions = {}
    for model, perms in ALL_PERMISSIONS.items():
        actions[model] = [action for action in perms if _has_perm(user, model, action)]

    modules = {
        module: [m for m in models_list if actions.get(m)]
        for module, models_list in ALL_MODELS.items()
    }

    return {"modules": modules, "actions": actions}


def _has_perm(user: User, model: str, action: str) -> bool:
    if user.is_superuser:
        return True
    return user.has_perm(f"{_get_app_label(model)}.{action}_{model}")


def _get_app_label(model: str) -> str:
    return APP_LABEL_MAP.get(model, "users")
