from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            return super().get_user(validated_token)
        except AuthenticationFailed:
            raise AuthenticationFailed(
                "Given token not valid for any token type",
                code="token_not_valid",
            )
