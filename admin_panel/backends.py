from django.contrib.auth.backends import ModelBackend
from core.models import Usuario


class EmailBackend(ModelBackend):
    """Custom authentication backend that allows login with email or username."""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try email first
            user = Usuario.objects.get(email=username)
        except Usuario.DoesNotExist:
            try:
                # Fall back to username
                user = Usuario.objects.get(username=username)
            except Usuario.DoesNotExist:
                return None
        
        if user.check_password(password):
            return user
        return None
