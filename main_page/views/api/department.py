from django.contrib.auth.mixins import LoginRequiredMixin

from main_page.views.mixins import AdminRequiredMixin
from main_page.views.api.generic_endpoints import GetEndpoint
from main_page import models


class DepartmentEndpoint(AdminRequiredMixin, LoginRequiredMixin, GetEndpoint):
  model = models.Department
  
  fields = [
    'id',
    'name',
    'hospital',
    'config',
    'thining_factor',
    'thining_factor_change_date'
  ]

  def get(self, request, department_id=None):
    return super().get(request, obj_id=department_id)
