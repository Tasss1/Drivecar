from rest_framework_simplejwt.tokens import AccessToken

class CustomAccessToken(AccessToken):
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token['role'] = 'admin' if user.is_staff or user.is_superuser else 'user'
        return token