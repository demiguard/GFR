# Python Standard Library

# Third party
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import TemplateView

# Clairvoyance modules
from constants import GFR_LOGGER_NAME
from main_page.libs.query_wrappers import ris_query_wrapper as ris
from main_page.libs import server_config
from main_page import log_util
from main_page.models import GFRStudy, StudyStatus, UserDepartmentAssignment

logger = log_util.get_logger(GFR_LOGGER_NAME)


class ListStudiesView(LoginRequiredMixin, TemplateView):
  """
  Lists all registered studies in RIS
  """
  template_name = "main_page/list_studies.html"

  def get(self, request: WSGIRequest) -> HttpResponse:
    # Fetch all registered studies
    curr_department = request.user.department
    if curr_department == None:
      UDA = UserDepartmentAssignment.objects.all()[0]
      request.user.department = UDA.department
      request.user.save()
      curr_department = UDA.department

    studies = [study for study in GFRStudy.objects.filter(
      Department = curr_department,
      StudyStatus__in=[
        StudyStatus.INITIAL,
        StudyStatus.PARTIAL_FILLED,
        StudyStatus.READY
      ]
    )]

    user_groups_assignment = UserDepartmentAssignment.objects.all().filter(user=request.user)
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
