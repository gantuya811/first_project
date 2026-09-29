"""
MERRIGE ERP - Authentication Views
Views нимгэн байна: хүсэлтийг уншиж, Service Layer рүү дамжуулаад,
стандарт success_response буцаана. Бизнес логик энд байхгүй.
"""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.permissions import IsAdminRole, IsPasswordChanged
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    UserProfileSerializer,
    UserRegisterSerializer,
)
from apps.accounts.services import AuthService, UserService
from apps.shared.exceptions import БизнесАлдаа
from apps.shared.pagination import StandardResultsPagination
from apps.shared.responses import success_response
from apps.shared.throttling import LoginRateThrottle


class LoginView(APIView):
    """POST /api/v1/auth/login/ — Утасны дугаар, нууц үгээр нэвтэрч JWT авна."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = AuthService.authenticate(
            phone_number=serializer.validated_data["phone_number"],
            password=serializer.validated_data["password"],
        )
        tokens = AuthService.issue_tokens(user, request=request)

        return success_response(
            data={
                **tokens,
                "must_change_password": user.must_change_password,
                "user": UserProfileSerializer(user).data,
            },
            message="Амжилттай нэвтэрлээ.",
        )


class RefreshTokenView(APIView):
    """POST /api/v1/auth/refresh/ — Access токеныг refresh токеноор шинэчилнэ."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise БизнесАлдаа("Токен хүчингүй эсвэл хугацаа дууссан байна.") from exc

        return success_response(
            data=serializer.validated_data, message="Токен шинэчлэгдлээ."
        )


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — Refresh токеныг хүчингүй болгоно (blacklist)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError as exc:
            raise БизнесАлдаа(
                "Токен хүчингүй эсвэл аль хэдийн ашиглагдсан байна."
            ) from exc

        return success_response(message="Амжилттай гарлаа.")


class ChangePasswordView(APIView):
    """POST /api/v1/auth/change-password/ — Эхний нэвтрэлт болон энгийн
    нууц үг солиход ашиглагдана (IsPasswordChanged хоригийг тойрч ажиллана)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        AuthService.change_password(
            user=request.user,
            new_password=serializer.validated_data["new_password"],
        )

        return success_response(message="Нууц үг амжилттай солигдлоо.")


class MeView(APIView):
    """GET /api/v1/auth/me/ — Нэвтэрсэн хэрэглэгчийн өөрийн мэдээлэл."""

    def get(self, request):
        return success_response(data=UserProfileSerializer(request.user).data)


class RegisterView(APIView):
    """POST /api/v1/users/register/ — Шинэ Үндсэн/Гэрээт Борлуулагч
    бүртгүүлнэ. Админ баталгаажуулах хүртэл нэвтрэх боломжгүй."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = UserService.register(serializer.validated_data)

        return success_response(
            data=UserProfileSerializer(user).data,
            message=(
                "Бүртгэл амжилттай илгээгдлээ. Админ баталгаажуулсны дараа "
                "нэвтрэх боломжтой болно."
            ),
            status_code=status.HTTP_201_CREATED,
        )


class UserListView(APIView):
    """GET /api/v1/users/ — Эрхийн дагуу (RBAC) харагдах хэрэглэгчдийн жагсаалт."""

    def get(self, request):
        queryset = UserService.list_visible(request.user)
        paginator = StandardResultsPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = UserProfileSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class UserDetailView(APIView):
    """GET /api/v1/users/{uuid}/ — Нэг хэрэглэгчийн дэлгэрэнгүй (эрхийн дагуу)."""

    def get(self, request, user_uuid):
        user = UserService.get_visible(request.user, user_uuid)
        return success_response(data=UserProfileSerializer(user).data)


class UserApproveView(APIView):
    """POST /api/v1/users/{uuid}/approve/ — Админ хэрэглэгчийг баталгаажуулж,
    санамсаргүй анхны нууц үг үүсгэнэ (Админ хэрэглэгчид дамжуулна)."""

    permission_classes = [IsAuthenticated, IsPasswordChanged, IsAdminRole]

    def post(self, request, user_uuid):
        user, password = UserService.approve(user_uuid, approved_by=request.user)
        return success_response(
            data={
                "user": UserProfileSerializer(user).data,
                "generated_password": password,
            },
            message=(
                "Хэрэглэгч амжилттай баталгаажлаа. Дараах нэвтрэх нууц үгийг "
                "хэрэглэгчид дамжуулна уу."
            ),
        )


class UserDeactivateView(APIView):
    """POST /api/v1/users/{uuid}/deactivate/ — Админ хэрэглэгчийг идэвхгүй
    болгоно (Soft Delete Only дүрмийн дагуу, бодит устгал биш)."""

    permission_classes = [IsAuthenticated, IsPasswordChanged, IsAdminRole]

    def post(self, request, user_uuid):
        UserService.deactivate(user_uuid, actor=request.user)
        return success_response(message="Хэрэглэгчийг идэвхгүй болголоо.")
