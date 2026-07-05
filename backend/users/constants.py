from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "管理员"
    USER = "user", "用户"
