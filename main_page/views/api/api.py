from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict, HttpResponseNotFound

from main_page.views.api.generic_endpoints import RESTEndpoint
from main_page.views.mixins import AdminRequiredMixin
from main_page import models


class UserEndpoint(AdminRequiredMixin, LoginRequiredMixin, RESTEndpoint):
  model = models.User
  
  fields = [
    'id',
    'username',
    'department',
    'user_group'
  ]

  def patch(self, request, obj_id):
    # Compute all the corresponding department and hospital combinations 
    hosp_depart = { }
    for choice_id, department in enumerate(models.Department.objects.all()):
      hosp_depart[choice_id] = (department.id, department.hospital.id)
    
    # Validate hosp_depart from request
    request_body = QueryDict(request.body)
    
    if 'hosp_depart' in request_body:
      if int(request_body['hosp_depart']) not in hosp_depart:
        return HttpResponseNotFound()

    # Modify request - split department to seperate update fields
    _, req_depart = hosp_depart[int(request_body['hosp_depart'])]

    request._body = f"username={str(request_body['username'])}&department={req_depart}".encode()

    return super().patch(request, obj_id)

  
class HospitalEndpoint(AdminRequiredMixin, LoginRequiredMixin, RESTEndpoint):
  model = models.Hospital

  fields = [
    'id',
    'name',
    'short_name',
    'address'
  ]


class DepartmentEndpoint(AdminRequiredMixin, LoginRequiredMixin, RESTEndpoint):
  model = models.Department
  
  fields = [
    'id',
    'name',
    'hospital',
    'config',
    'thining_factor',
    'thining_factor_change_date'
  ]


class ConfigEndpoint(AdminRequiredMixin, LoginRequiredMixin, RESTEndpoint):
  model = models.Config

  fields = [
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


class HandledExaminationsEndpoint(AdminRequiredMixin, LoginRequiredMixin, RESTEndpoint):
  model = models.HandledExaminations

  fields = [
    'accession_number'
  ]
