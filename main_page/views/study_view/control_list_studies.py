# Python standard Library
from logging import getLogger


# Third party packages
from django.views.generic import TemplateView
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest


# Clairvoyance packages
from constants import GFR_LOGGER_NAME
from main_page.libs import server_config
from main_page.models import User, Department, GFRStudy, StudyStatus

logger = getLogger(GFR_LOGGER_NAME)

class ControlListView(LoginRequiredMixin, TemplateView):
  template_name = "main_page/control_list_studies.html"

  def get(self, request: WSGIRequest) -> HttpResponse:
    """
    List all studies that shall be send to Pacs
    """
    user: User = request.user

    studies = [study for study in GFRStudy.objects.filter(
      Department=user.department,
      StudyStatus=StudyStatus.CONTROL
    )]

    context = {
      "title"               : server_config.SERVER_NAME,
      "version"             : server_config.SERVER_VERSION,
      "registered_studies"  : studies
    }

    return render(request, self.template_name, context)
