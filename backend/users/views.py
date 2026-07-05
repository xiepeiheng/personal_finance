from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from utils.permissions import ViewModelPermissions
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from utils import success_response, CodeEnum, BusinessException
from utils.permission_service import get_user_permissions
from .serializers import (
    UserCreateSerializer,
    UserRegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    GroupSerializer,
    PermissionSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    permission_classes = [IsAuthenticated, ViewModelPermissions]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        return UserSerializer

    @action(detail=True, methods=["post"], url_path="set-password")
    def set_password(self, request, pk=None):
        user = self.get_object()
        password = request.data.get("password")
        if not password or len(password) < 8:
            raise BusinessException(
                code=CodeEnum.PARAM_ERROR.code,
                message="密码长度至少8位",
                http_status=400,
            )
        user.set_password(password)
        user.save(update_fields=["password"])
        return success_response(message="密码已更新")

    @action(detail=False, methods=["post"], permission_classes=[])
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return success_response(
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "permissions": get_user_permissions(user),
            }
        )


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by("id")
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, ViewModelPermissions]


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Permission.objects.all().order_by("id")
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, ViewModelPermissions]
    pagination_class = None


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            raise BusinessException(
                code=CodeEnum.PARAM_ERROR.code,
                message="用户名和密码必填",
                http_status=400,
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise BusinessException(
                code=CodeEnum.USER_NOT_LOGIN.code,
                message="用户名或密码错误",
                http_status=401,
            )

        if not user.check_password(password):
            raise BusinessException(
                code=CodeEnum.USER_NOT_LOGIN.code,
                message="用户名或密码错误",
                http_status=401,
            )

        if not user.is_active:
            raise BusinessException(
                code=CodeEnum.USER_DISABLED.code,
                message="账号已停用",
                http_status=403,
            )

        refresh = RefreshToken.for_user(user)

        return success_response(
            data={
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "permissions": get_user_permissions(user),
            }
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return success_response(
            data={
                **serializer.data,
                "permissions": get_user_permissions(request.user),
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return success_response(message="已退出登录")


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            raise BusinessException(
                code=CodeEnum.PARAM_ERROR.code,
                message="旧密码和新密码均必填",
                http_status=400,
            )

        if not request.user.check_password(old_password):
            raise BusinessException(
                code=CodeEnum.PARAM_ERROR.code,
                message="旧密码错误",
                http_status=400,
            )

        if len(new_password) < 8:
            raise BusinessException(
                code=CodeEnum.PARAM_ERROR.code,
                message="新密码长度至少8位",
                http_status=400,
            )

        request.user.set_password(new_password)
        request.user.save()

        return success_response(message="密码已更新")
