from django.contrib.auth.mixins import LoginRequiredMixin

from main_page.views.api.generic_endpoints import GetEndpoint
from main_page.views.mixins import AdminRequiredMixin
from main_page import models


class UserEndpoint(AdminRequiredMixin, LoginRequiredMixin, GetEndpoint):
  def __init__(self):
    super().__init__(models.User, fields={
      'id',
      'username',
      'department',
      'user_group'      
    })

  def get(self, request, user_id=None):
    return super().get(request, obj_id=user_id)
