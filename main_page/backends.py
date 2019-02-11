from django.contrib.auth.hashers import check_password
from .models import User


# Simple mysql database users
class SimpleBackend:
  def authenticate(self, request, username=None, password=None):
    pass

  def get_user(self, username):
    pass
