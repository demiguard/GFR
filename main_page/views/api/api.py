from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import QueryDict, HttpResponseNotFound, JsonResponse, HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from django.views.generic import View

from smb.base import NotConnectedError
from datetime import datetime
import logging
import time
import os
import shutil

from main_page.libs import samba_handler
from main_page.libs import server_config
from main_page.libs.status_codes import *
from main_page.libs.dirmanager import try_mkdir
from main_page.views.api.generic_endpoints import RESTEndpoint, GetEndpoint, PostEndpoint, DeleteEndpoint
from main_page.views.mixins import AdminRequiredMixin
from main_page import models


logger = logging.getLogger()


class UserEndpoint(AdminRequiredMixin, LoginRequiredMixin, RESTEndpoint):
  model = models.User
  
  fields = [
    'id',
    'username',
    'department',
    'department.name',
    'department.hospital.id',
    'department.hospital.name',
    'user_group',
    'user_group.name',
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
    'hospital.name',
    'config',
    'thining_factor',
    'thining_factor_change_date'
  ]

  foreign_fields = {
    'hospital': models.Hospital,
    'config': models.Config,
  }

class ProcedureEndpoint(AdminRequiredMixin, LoginRequiredMixin, RESTEndpoint):
  model = models.ProcedureType

  fields = [
    'id',
    'type_name'
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
    'pacs_calling',
  ]


class HandledExaminationsEndpoint(AdminRequiredMixin, LoginRequiredMixin, GetEndpoint, PostEndpoint, DeleteEndpoint):
  model = models.HandledExaminations

  fields = [
    'accession_number'
  ]


class ProcedureMappingsEndpoint(AdminRequiredMixin, LoginRequiredMixin, RESTEndpoint):
  model = models.Config.accepted_procedures.through # Retreive the underlying relation model

  fields = [
    'id',
    'config_id',
    'proceduretype_id',
  ]

  def post(self, request):
    # Modify request to contain correct config id instead of department id
    request_body = request.POST
   
    department_id = request_body['department']
    config_id = models.Department.objects.get(pk=department_id).config.id

    proceduretype_id = request_body['proceduretype_id']

    request._body = f"config_id={config_id}&proceduretype_id={proceduretype_id}".encode()

    return super().post(request)


class SambaBackupEndpoint(View):
  def get(self, request, date):
    # Extract search parameters
    try:
      date = datetime.strptime(date, '%Y-%m-%d')
      hospital = request.user.department.hospital.short_name
    except ValueError: # Unable to parse date
      return HttpResponseBadRequest()

    # Attempt to get backup data
    logger.info(f"Handling Ajax Get backup request with date: {date} and hospital: {hospital}")

    try:
      backup_data = samba_handler.get_backup_file(date, hospital)
    except NotConnectedError as err: 
      logger.warn(f"Error during handling of Samba Share files, got error: {err}")

      return HttpResponseServerError()

    # No data was found
    if not backup_data:
      # NOTE: Transform response to base class, HttpResponse, since 204 status 
      # code on a JsonResponse will reset the underlying connecting in
      # the Django request preprocessing step
      resp = HttpResponse()
      resp.status_code = HTTP_STATUS_NO_CONTENT
      return resp

    # Reformat data and present in Json for response
    context = { }
    
    USED_COLUMNS = ['Measurement date & time', 'Pos', 'Rack', 'Tc-99m CPM']
    for df in backup_data:
      # Remove unused columns  
      df = df[USED_COLUMNS]
 
      # Put in dict. Assuming 2 tests cannot be made at the exact same time. If they are, they will be overwritten
      _, time_of_messurement = df['Measurement date & time'][0].split(' ')
      context[time_of_messurement] = df.to_dict()
    
    return JsonResponse(context)


class StudyEndpoint(View):
  """
  Custom endpoint for handling moving of studies 
  (i.e. for moving to trash and recovering them)
  """
  def patch(self, request, ris_nr):
    """
    Handles recovery of studies (i.e. moving them out from trash)
    """
    user_hosp = request.user.department.hospital.short_name

    logger.info(f"Attempting to recover study: {ris_nr}")
    
    resp = JsonResponse({ })

    # Create deleted studies directory if doesn't exist
    try_mkdir(f"{server_config.FIND_RESPONS_DIR}{user_hosp}", mk_parents=True)

    move_src = f"{server_config.DELETED_STUDIES_DIR}{user_hosp}/{ris_nr}.dcm"

    if os.path.exists(move_src):
      move_dst = f"{server_config.FIND_RESPONS_DIR}{user_hosp}/{ris_nr}.dcm"
      
      # Move to deletion directory
      shutil.move(move_src, move_dst)

      logger.info(f"Successfully recovered study: {ris_nr}")
    else:
      logger.error(f"Unable to find dicom object for study to recover: '{move_src}'")
      resp.status_code = HTTP_STATUS_BAD_REQUEST

    return resp

  def delete(self, request, ris_nr):
    """
    Handles deletion of studies (i.e. moving them to trash)
    """
    user_hosp = request.user.department.hospital.short_name

    logger.info(f"Attempting to move study to trash with accession number: {ris_nr}")
    
    resp = JsonResponse({ })

    # Create deleted studies directory if doesn't exist
    try_mkdir(f"{server_config.DELETED_STUDIES_DIR}{user_hosp}", mk_parents=True)

    move_src = f"{server_config.FIND_RESPONS_DIR}{user_hosp}/{ris_nr}.dcm"

    if os.path.exists(move_src):
      move_dst = f"{server_config.DELETED_STUDIES_DIR}{user_hosp}/{ris_nr}.dcm"
      
      # Reset modification time
      del_time = time.mktime(datetime.now().timetuple())
      os.utime(move_src, (del_time, del_time))

      # Move to deletion directory
      shutil.move(move_src, move_dst)

      logger.info(f"Successfully moved study to trash can: {ris_nr}")
    else:
      logger.error(f"Unable to find dicom object for study to move to trash: '{move_src}'")
      resp.status_code = HTTP_STATUS_NO_CONTENT

    return resp
