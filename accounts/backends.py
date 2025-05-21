from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                # Only allow login if user is verified
                if user.is_verified:
                    return user
                return None  # User exists but isn't verified
        except User.DoesNotExist:
            return None
        return None