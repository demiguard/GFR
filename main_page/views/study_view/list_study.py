from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest

from typing import Type

from main_page.libs.query_wrappers import ris_query_wrapper as ris
from main_page.libs import server_config
from main_page import models
from main_page import log_util

logger = log_util.get_logger(__name__)


class ListStudiesView(LoginRequiredMixin, TemplateView):
  """
  Lists all registered studies in RIS
  """
  template_name = "main_page/list_studies.html"

  def get(self, request: WSGIRequest) -> HttpResponse:
    # Fetch all registered studies
    curr_department = request.user.department
    if curr_department == None:
      UDA = models.UserDepartmentAssignment.objects.all()[0]
      request.user.department = UDA.department
      request.user.save()
      curr_department = UDA.department

    studies = [study for study in models.GFRStudy.objects.filter(
      Department = curr_department
    )]

    user_groups_assignment = models.UserDepartmentAssignment.objects.all().filter(user=request.user)
    user_groups = [(UDA.department.id, UDA.department.hospital.name) for UDA in user_groups_assignment]
    # Return rendered view
    context = {
      "title"              : server_config.SERVER_NAME,
      "version"            : server_config.SERVER_VERSION,
      "registered_studies" : studies,
      "user_groups"        : user_groups,
    }

    return render(request, self.template_name, context)

  def post(self, request):
    """
    This is used for deleting all studies which are more than a day old
    """
    curr_department = request.user.department
    hospital_shortname = curr_department.hospital.short_name

    registered_datasets = []

    _, _ = ris.check_if_old(
      registered_datasets,
      hospital_shortname,
      ris.move_to_deleted,
      threshold=0
    )

    return redirect("main_page:list_studies")
