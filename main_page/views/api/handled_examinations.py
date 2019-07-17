from django.contrib.auth.mixins import LoginRequiredMixin

from main_page.views.mixins import AdminRequiredMixin
from main_page.views.api.generic_endpoints import GetEndpoint
from main_page import models


class HandledExaminationsEndpoint(AdminRequiredMixin, LoginRequiredMixin, GetEndpoint):
  model = models.HandledExaminations

  fields = [
    'accession_number'
  ]

  def get(self, request, handled_id=None):
    return super().get(request, obj_id=handled_id)
