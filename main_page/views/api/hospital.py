from django.contrib.auth.mixins import LoginRequiredMixin

from main_page.views.mixins import AdminRequiredMixin
from main_page.views.api.generic_endpoints import GetEndpoint
from main_page import models


class HospitalEndpoint(AdminRequiredMixin, LoginRequiredMixin, GetEndpoint):
  def __init__(self):
    super().__init__(models.Hospital, fields={
      'id',
      'name',
      'short_name',
      'address'
    })

  def get(self, request, hospital_id=None):
    return super().get(request, obj_id=hospital_id)
