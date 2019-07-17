from django.contrib.auth.mixins import LoginRequiredMixin

from main_page.views.api.generic_endpoints import GetEndpoint
from main_page.views.mixins import AdminRequiredMixin
from main_page import models


class ConfigEndpoint(AdminRequiredMixin, LoginRequiredMixin, GetEndpoint):
  model = models.Config

  fields=[
    'id',
    'ris_aet',
    'ris_ip',
    'ris_port',
    'ris_calling',
    'pacs_aet',
    'pacs_ip',
    'pacs_port',
    'pacs_calling'
  ]
  
  def get(self, request, config_id=None):
    return super().get(request, obj_id=config_id)
