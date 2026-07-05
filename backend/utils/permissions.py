from rest_framework.permissions import DjangoModelPermissions


class ViewModelPermissions(DjangoModelPermissions):
    """DjangoModelPermissions 默认 GET 不检查 view 权限，此类补上。"""
    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }
