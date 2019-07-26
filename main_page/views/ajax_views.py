from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseServerError, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

import os
import shutil
import time
import datetime
import logging
from smb.base import NotConnectedError

from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs import samba_handler
from main_page.libs import server_config
from main_page.libs.status_codes import *
from main_page.libs.dirmanager import try_mkdir
from main_page import forms


logger = logging.getLogger()


class AjaxLogin(TemplateView):
  """
  Handles processing of login requests from javascript
  """
  def post(self, request):
    signed_in = False
    
    login_form = forms.LoginForm(data=request.POST)

    if login_form.is_valid():
      user = authenticate(
        request, 
        username=request.POST['username'], 
        password=request.POST['password']
      )

      if user:
        login(request, user)
        logger.info('User: {0} logged in successful'.format(request.user.username))

        if user.is_authenticated:
          signed_in = True
      else:
        logger.warning('User: {0} Failed to log in'.format(request.POST['username']))

    data = {
      'signed_in': signed_in,
    }
    resp = JsonResponse(data)

    if not signed_in:
      resp.status_code = 403

    return resp


class LogoutView(LoginRequiredMixin, TemplateView):
  """
  Logouts out the current user from the session.
  (either through a GET or POST request)
  """
  def logout_current_user(self, request):
    logger.info('User - {0} logged out from ip: {1}'.format(
      request.user.username,
      request.META['REMOTE_ADDR']
    ))

    logout(request)
    return redirect('main_page:index')

  def get(self, request):
    return self.logout_current_user(request)

  def post(self, request):
    return self.logout_current_user(request)


class AjaxDeleteStudy(TemplateView):
  def post(self, request):
    delete_status = True

    user_hosp = request.user.department.hospital

    delete_accession_number = request.POST['delete_accession_number']

    logger.info(f"Attempting to delete study: {delete_accession_number}")

    # Create deleted studies directory if doesn't exist
    try_mkdir(f"{server_config.DELETED_STUDIES_DIR}{user_hosp}", mk_parents=True)

    move_src = f"{server_config.FIND_RESPONS_DIR}{user_hosp}/{delete_accession_number}.dcm"

    if not os.path.exists(move_src):
      delete_status = False

    if delete_status:
      move_dst = f"{server_config.DELETED_STUDIES_DIR}{user_hosp}/{delete_accession_number}.dcm"
      
      # Reset modification time
      del_time = time.mktime(datetime.datetime.now().timetuple())
      os.utime(move_src, (del_time, del_time))

      # Move to deletion directory
      shutil.move(move_src, move_dst)

      logger.info(f"Successfully deleted study: {delete_accession_number}")

    data = { }
    resp = JsonResponse(data)

    if not delete_status:
      resp.status_code = 403

    return resp


class AjaxRestoreStudy(TemplateView):
  def post(self, request):
    recover_status = True

    user_hosp = request.user.department.hospital

    recover_accession_number = request.POST['recover_accession_number']

    logger.info(f"Attempting to recover study: {recover_accession_number}")

    # Create deleted studies directory if doesn't exist
    try_mkdir(f"{server_config.FIND_RESPONS_DIR}{user_hosp}", mk_parents=True)

    move_src = f"{server_config.DELETED_STUDIES_DIR}{user_hosp}/{recover_accession_number}.dcm"

    if not os.path.exists(move_src):
      recover_status = False

    if recover_status:
      move_dst = f"{server_config.FIND_RESPONS_DIR}{user_hosp}/{recover_accession_number}.dcm"
      
      # Move to deletion directory
      shutil.move(move_src, move_dst)

      logger.info(f"Successfully recovered study: {recover_accession_number}")

    data = { }
    resp = JsonResponse(data)

    if not recover_status:
      resp.status_code = 403

    return resp


class AjaxSearch(LoginRequiredMixin, TemplateView):
  """
  Handles ajax search requests
  """
  def get(self, request):  
    # Extract search parameters
    search_name = request.GET['name']
    search_cpr = request.GET['cpr']
    search_rigs_nr = request.GET['rigs_nr']
    search_date_from = request.GET['date_from']
    search_date_to = request.GET['date_to']

    search_resp = pacs.search_query_pacs(
      request.user,
      name=search_name,
      cpr=search_cpr,
      accession_number=search_rigs_nr,
      date_from=search_date_from,
      date_to=search_date_to,
    )

    # Serialize search results; i.e. turn ExaminationInfo objects into dicts.
    serialized_results = []
    for res in search_resp:
      serialized_results.append({
        'rigs_nr': res.rigs_nr,
        'name': res.name,
        'cpr': res.cpr,
        'date': res.date
      })

    data = {
      'search_results': serialized_results
    }

    return JsonResponse(data) 



class AjaxUpdateThiningFactor(TemplateView):
  def post(self, request):
    """
      Ajax from list_studies, called from list_studies.js

      Handles and updates thining factor 
    """
    logger.info(f"{request.user.username} Updated thining factor to {request.POST['thining_factor']}")
    request.user.department.thining_factor = float(request.POST['thining_factor'])
    request.user.department.thining_factor_change_date = datetime.date.today()
    request.user.department.save()

    return JsonResponse({})