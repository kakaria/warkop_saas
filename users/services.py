
from django.db import transaction
from .models import User


def create_user_account_service(*, email: str, password: str):
    """
            BIKIN AKUN USER doang
    """

    user = User.objects.create_user(
        email=email,
        password=password
    ) # type: ignore

    return user

@transaction.atomic
def patch_user_service(user: User, validated_data: dict) -> User:

    new_full_name = validated_data.get("full_name")

    if not new_full_name:
        return user

    # apply perubahan
    for key, value in validated_data.items():
        setattr(user, key, value)

    # simpen ke database
    user.save(update_fields=list(validated_data.keys()))

    return user
