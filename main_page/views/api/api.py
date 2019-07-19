from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict, HttpResponseNotFound

from main_page.views.api.generic_endpoints import RESTEndpoint, GetEndpoint, PostEndpoint, DeleteEndpoint
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

  foreign_fields = {
    'department': models.Department,
    'user_group': models.UserGroup,
  }

  def patch(self, request, obj_id):
    # Compute all the corresponding department and hospital combinations 
    hosp_depart = { }
    for choice_id, department in enumerate(models.Department.objects.all()):
      hosp_depart[choice_id + 1] = (department.id, department.hospital.id)
    
    # Validate hosp_depart from request
    request_body = QueryDict(request.body)
    in_req_depart = int(request_body['hosp_depart']) + 1

    if 'hosp_depart' in request_body:
      if in_req_depart not in hosp_depart:
        return HttpResponseNotFound()

    # Modify request - split department to seperate update fields
    req_depart, _ = hosp_depart[in_req_depart]

    request._body = f"username={str(request_body['username'])}&department={req_depart}".encode()

    return super().patch(request, obj_id)

  def post(self, request):
    # Compute all the corresponding department and hospital combinations 
    hosp_depart = { }
    for choice_id, department in enumerate(models.Department.objects.all()):
      hosp_depart[choice_id + 1] = (department.id, department.hospital.id)
    
    # Validate hosp_depart from request
    request_body = request.POST

    if 'hosp_depart' in request_body:
      if int(request_body['hosp_depart']) not in hosp_depart:
        return HttpResponseNotFound()

    # Modify request - split department to seperate update fields
    _, req_depart = hosp_depart[int(request_body['hosp_depart'])]

    request._body = f"username={request_body['username']}&password={request_body['password']}&department={req_depart}&user_group={request_body['user_group']}".encode()

    return super().post(request)

  
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

  foreign_fields = {
    'hospital': models.Hospital,
    'config': models.Config,
  }


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


class HandledExaminationsEndpoint(AdminRequiredMixin, LoginRequiredMixin, GetEndpoint, PostEndpoint, DeleteEndpoint):
  model = models.HandledExaminations

  fields = [
    'accession_number'
  ]
