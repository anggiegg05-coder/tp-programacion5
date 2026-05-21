from rest_framework import generics, permissions
from django.contrib.auth import get_user_model

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response

from .serializers import RegisterSerializer, UserProfileSerializer

User = get_user_model()


# =========================
# REGISTER
# =========================
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# =========================
# LOGIN (JWT)
# =========================
class LoginView(TokenObtainPairView):
    """
    Devuelve access + refresh token
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        return Response({
            "access": response.data["access"],
            "refresh": response.data["refresh"],
        })


# =========================
# PROFILE (USER LOGUEADO)
# =========================
class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user