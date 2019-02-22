from django.contrib.auth.hashers import check_password
from .models import User


# Simple mysql database users
class SimpleBackend:
  def authenticate(self, request, username=None, password=None):
    if username and password:
      try:
        user = User.objects.get(username=username)

        if check_password(password, user.password):
          return user
      except User.DoesNotExist:
        pass

    return None

  def get_user(self, username):
    try:
      return User.objects.get(pk=username)
    except User.DoesNotExist:
      return None
