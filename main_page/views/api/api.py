from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, QueryDict, HttpResponseNotFound, JsonResponse, HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from django.views.generic import View
from django.core.handlers.wsgi import WSGIRequest

from smb.base import NotConnectedError
from pathlib import Path
from datetime import datetime
import logging
import time
import os
import shutil
import json

from typing import Type

from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs import samba_handler
from main_page.libs import dicomlib
from main_page.libs import server_config
from main_page.libs.dirmanager import try_mkdir
from main_page.libs.status_codes import *
from main_page.views.api.generic_endpoints import RESTEndpoint, GetEndpoint, PostEndpoint, DeleteEndpoint
from main_page.views.mixins import AdminRequiredMixin, LoggingMixin
from main_page import models

logger = logging.getLogger()

"""
  TODO: Soooo Look at all these Class Names, do they look like a snake? No? Well my dear unlucky sod, this is where you come in
"""

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


class AddressEndpoint(AdminRequiredMixin, LoggingMixin, RESTEndpoint):
  model = models.Address

  fields = [
    'id',
    'ae_title',
    'ip',
    'port',
    'description'
  ]

class ServerConfigurationEndpoint(AdminRequiredMixin, LoginRequiredMixin, RESTEndpoint):
  model = models.ServerConfiguration

  fields = [
    'id',
    'samba_ip',
    'samba_name',
    'samba_user',
    'samba_pass',
    'samba_pc',
    'samba_share',
    'AE_title'
  ]

class ProcedureMappingsEndpoint(AdminRequiredMixin, LoginRequiredMixin, RESTEndpoint):
  model = models.Config.accepted_procedures.through # Retreive the underlying relation model

  fields = [
    'id',
    'config_id',
    'proceduretype_id',
    'proceduretype.type_name'
  ]

  foreign_fields = {
    'proceduretype': models.ProcedureType
  }

  def get(self, request):
    # Call generic base endpoint and inject additional response info
    generic_resp = super().get(request)

    json_resp = json.loads(generic_resp.content)
    config_ids = [x['config_id'] for x in json_resp['config_accepted_procedures']]

    for i, cid in enumerate(config_ids):
      tmp_depart = models.Department.objects.get(config=cid)
      json_resp['config_accepted_procedures'][i]['department'] = str(tmp_depart)

    new_resp = JsonResponse(json_resp)

    return new_resp

  def post(self, request):
    # Modify request to contain correct config id instead of department id
    request_body = request.POST
   
    department_id = request_body['department']
    config_id = models.Department.objects.get(pk=department_id).config.id

    proceduretype_id = request_body['proceduretype_id']

    request._body = f"config_id={config_id}&proceduretype_id={proceduretype_id}".encode()

    return super().post(request)


class SambaBackupEndpoint(LoginRequiredMixin, View):
  def get(self, request, date):
    # Extract search parameters
    try:
      date = datetime.strptime(date, '%Y-%m-%d')
      hospital = request.user.department.hospital.short_name
    except ValueError: # Unable to parse date
      return HttpResponseBadRequest()

    # Attempt to get backup data
    logger.info(f"Handling Ajax Get backup request with date: {date} and hospital: {hospital}")

    #There always exists a server config with an id of 1, All other are ignored
    model_server_config = models.ServerConfiguration.objects.get(id=1)

    try:
      backup_data = samba_handler.get_backup_file(date, hospital, model_server_config)
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
      try:
        df = df[USED_COLUMNS]
      except KeyError: # Ignore F-18 files
        continue

      # Put in dict. Assuming 2 tests cannot be made at the exact same time. If they are, they will be overwritten
      _, time_of_messurement = df['Measurement date & time'][0].split(' ')
      context[time_of_messurement] = df.to_dict()
    
    return JsonResponse(context)


class StudyEndpoint(LoginRequiredMixin, View):
  """
  Custom endpoint for handling moving of studies 
  (i.e. for moving to trash and recovering them)
  """
  def patch(
    self,
    request: Type[WSGIRequest],
    accession_number: str
    ) -> HttpResponse:
    """
    Handles recovery of studies (i.e. moving them out from trash)

    Args:
      request: incoming HTTP request
      accession_number: accession number of study to recover

    Remark:
      Places a file named server_config.RECOVERED_FILENAME containing a time-
      stamp of when the study was recovered. This file is used when checking
      for auto deletion of studies under list_studies, as to not have
      recovered files be instantly deleted if their StudyDate has already
      passed the days threshold.
    """
    hospital_shortname = request.user.department.hospital.short_name

    logger.info(
      f"Attempting to recover study w/ accession number: {accession_number}"
    )
    
    resp = JsonResponse({ })

    # Attempt to create directory of active studies
    active_studies_dir = Path(
      server_config.FIND_RESPONS_DIR,
      hospital_shortname
    )

    try_mkdir(str(active_studies_dir), mk_parents=True)

    # Create src and dst paths, then perform move
    move_src = Path(
      server_config.DELETED_STUDIES_DIR,
      hospital_shortname,
      accession_number
    )

    move_dst = Path(
      active_studies_dir,
      accession_number
    )

    try:
      shutil.move(move_src, move_dst)

      # Create recovery file
      recover_filepath = Path(
        move_dst,
        server_config.RECOVERED_FILENAME
      )

      with open(recover_filepath, 'w') as fp:
        fp.write(datetime.now().strftime('%Y%m%d'))

      logger.info(
        f"Successfully recovered study w/ accession number: {accession_number}"
      )
    except (FileNotFoundError, FileExistsError):
      logger.error(
        f"Unable to find dicom object for study to recover: '{move_src}'"
      )
      resp.status_code = HTTP_STATUS_BAD_REQUEST

    return resp

  def delete(
    self, 
    request: Type[WSGIRequest], 
    accession_number: str
    ) -> HttpResponse:
    """
    Handles deletion of studies (i.e. moving them to trash)

    Args:
      request: incoming HTTP request
      accession_number: accession_number of study to delete
    """
    user_hosp = request.user.department.hospital.short_name
    
    request_body = QueryDict(request.body)
    resp = JsonResponse({ })

    if "purge" in request_body:
      if request_body["purge"] == "true":
        # HANDLE COMPLETE PURGE (DELETE STUDY FROM THE SYSTEM)
        deletion_dir = Path(
          server_config.DELETED_STUDIES_DIR,
          user_hosp,
          accession_number
        )

        try:
          # This check if here to prevent anyone from sending a request
          # containing an accession_number with e.g. "/", that could possibly
          # remove the / directory of the server
          if '.' in accession_number or '/' in accession_number:
            raise FileNotFoundError()

          shutil.rmtree(deletion_dir)
        except FileNotFoundError:
          resp.status_code = HTTP_STATUS_NO_CONTENT
    else:
      # HANDLE MOVE TO TRASH
      logger.info(
        "Attempting to move study to trash "
        f"with accession number: {accession_number}"
      )
      
      # Create deleted studies directory if doesn't exist
      deletion_dir = Path(
        server_config.DELETED_STUDIES_DIR, 
        user_hosp
      )
      try_mkdir(str(deletion_dir), mk_parents=True)

      # Get src and dst, then move attempt to move
      move_src = Path(
        server_config.FIND_RESPONS_DIR,
        user_hosp,
        accession_number
      )

      move_dst = Path(
        deletion_dir,
        accession_number
      )

      try:
        shutil.move(move_src, move_dst)

        logger.info(f"Successfully moved study to trash can: {accession_number}")
      except (FileNotFoundError, FileExistsError):
        logger.error(
          f"Unable to find dicom object for study to move to trash: '{move_src}'"
        )
        resp.status_code = HTTP_STATUS_NO_CONTENT

    return resp


class ListEndpoint(AdminRequiredMixin, LoginRequiredMixin, View):
  """
  Endpoint for handling performing actions on the directory for list_studies
  and delete_studies (e.g. actions on all dicom objects in a directory)
  """
  def delete(self, request): # hard purge everything, e.g. nuke    
    request_body = QueryDict(request.body)
    hospital_shortname = ""
    context = { 'action': 'failed' }

    try:
      hospital_shortname = request_body['hospital_shortname']
    except KeyError:
      pass

    if hospital_shortname:
      del_dir = ""
      
      if 'list_studies' in request_body:
        del_dir = Path(server_config.FIND_RESPONS_DIR, hospital_shortname)
      elif 'deleted_studies' in request_body:
        del_dir = Path(server_config.DELETED_STUDIES_DIR, hospital_shortname)

      try:
        shutil.rmtree(del_dir)
        context['action'] = 'success'
      except (FileNotFoundError, NotADirectoryError):
        pass

    return JsonResponse(context)

class CsvEndpoint(LoginRequiredMixin, View):
  def get(self, request, accession_number):
    """
    Endpoint providing csv export for completed studies

    Args:
      request: incoming HTTP request
      accession_number: accession number of study to export to csv
    
    Returns:
      HTTP file reponse of content type 'text/csv' with the export file
    """
    user = request.user
    hospital_sn = user.department.hospital.short_name
    csv_dir = f'{server_config.CSV_DIR}/{hospital_sn}/'
    csv_file_path = f'{csv_dir}{accession_number}.csv'
    dataset_file_path = f'{server_config.FIND_RESPONS_DIR}{hospital_sn}/{accession_number}.dcm'
    
    try:
      dataset = dicomlib.dcmread_wrapper(dataset_file_path)
    except: # Unable to find dicom object
      logger.info(f"Unable to export study to csv for accession number: {accession_number}")
      return HttpResponseNotFound()
    
    # Create csv file
    try_mkdir(csv_dir,mk_parents=True)
    export_status = dicomlib.export_dicom(dataset, csv_file_path)
    
    # Create response if csv file creation was successful
    if export_status == 'OK':
      with open(csv_file_path, 'r') as csv_file:
        response = HttpResponse(
          csv_file,
          content_type="text/csv"
        )
        response['Content-Disposition'] = f"attachment; filename={accession_number}.csv"
        return response
    else:
      logger.info(f"Unable to export study to csv for accession number: {accession_number}")
      return HttpResponseServerError()

  def delete(self, request, accession_number):
    logger.info(f'Recieved Delete request of csv file for {accession_number}')

    user = request.user
    hospital_sn = user.department.hospital.short_name
    csv_dir = f'{server_config.CSV_DIR}/{hospital_sn}/'
    csv_file_path = f'{csv_dir}{accession_number}.csv'
    
    if os.path.exists(csv_file_path):
      os.remove(csv_file_path)

      response = HttpResponse()
      response.status_code = HTTP_STATUS_OK

      return response
    else:
      return HttpResponseNotFound()


class SearchEndpoint(LoginRequiredMixin, View):
  """
  Handles search requests api
  """
  def get(self, request):  
    # Extract search parameters
    search_name = request.GET['name']
    search_cpr = request.GET['cpr']
    search_accession_number = request.GET['accession_number']
    search_date_from = request.GET['date_from']
    search_date_to = request.GET['date_to']

    search_results = pacs.search_query_pacs(
      request.user.department.config,
      name=search_name,
      cpr=search_cpr,
      accession_number=search_accession_number,
      date_from=search_date_from,
      date_to=search_date_to,
    )

    data = {
      'search_results': search_results
    }

    return JsonResponse(data)
