from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    ProfileDetailSerializer,
    ProfilePatchSerializer,
)
from .services import patch_user_service


class ProfileView(generics.RetrieveUpdateAPIView):

    permission_classes = [IsAuthenticated]

    # batesin request methods
    http_method_names = ["get", "patch"]

    # override
    def get_serializer_class(
        self,
    ):  # karena pake 2 serializers (satu buat patch, satu buat response)
        if self.request.method == "PATCH":
            return ProfilePatchSerializer
        return ProfileDetailSerializer

    def get_object(self):
        return self.request.user  # ambil object user yang lagi login

    def partial_update(self, request, *args, **kwargs):

        # ambil object user
        user = self.get_object()

        # validasi request
        serializer = self.get_serializer(user, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)

        # panggil service
        updated_user = patch_user_service(
            user=user, validated_data=serializer.validated_data
        )

        # panggil serializer untuk response
        response_serializer = ProfileDetailSerializer(updated_user)
        print(response_serializer.data)

        return Response(response_serializer.data)
