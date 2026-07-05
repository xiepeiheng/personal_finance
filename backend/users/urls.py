from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    LogoutView,
    MeView,
    ChangePasswordView,
    UserViewSet,
    GroupViewSet,
    PermissionViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet)
router.register("groups", GroupViewSet)
router.register("permissions", PermissionViewSet)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

urlpatterns += router.urls
