from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseServerError, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import auth
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect

import os
import shutil
import time
import datetime
import logging
from smb.base import NotConnectedError

import django_auth_ldap

import ldap

from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs import samba_handler
from main_page.libs import server_config
from main_page.libs.status_codes import *
from main_page.libs.dirmanager import try_mkdir
from main_page.forms import base_forms


from main_page import log_util

logger = log_util.get_logger(__name__)


class AjaxLogin(TemplateView):
  """
  Handles processing of login requests from javascript
  """
  def post(self, request):
    signed_in = False
    
    login_form = base_forms.LoginForm(data=request.POST)
    
    if login_form.is_valid():
      user = authenticate(
        request, 
        username=request.POST['username'], 
        password=request.POST['password']
      )

      if user:
        login(request, user)
        logger.info(f'User: {request.user.username} logged in successful')

        if user.is_authenticated:
          signed_in = True
      else:
        logger.warning(f"User: {request.POST['username']} Failed to log in, from IP address: {request.META.get('REMOTE_ADDR')}")

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


class AjaxUpdateThiningFactor(LoginRequiredMixin, TemplateView):
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