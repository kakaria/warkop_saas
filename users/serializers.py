from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class ProfileDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
        ]
        read_only_fields = ["id", "email"]


class ProfilePatchSerializer(serializers.ModelSerializer):

    full_name = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ["full_name"]
