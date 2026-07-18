from django.contrib.auth import get_user_model

User = get_user_model()

def create_user_account_service(*, email: str, password: str):
    """
            BIKIN AKUN USER doang
    """

    user = User.objects.create_user(
        email=email,
        password=password
    ) # type: ignore

    return user

