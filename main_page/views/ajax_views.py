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

from django_auth_ldap.backend import LDAPBackend

import ldap
from ldap import FILTER_ERROR

from main_page.models import UserGroup, Department, UserDepartmentAssignment
from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs import samba_handler
from main_page.libs import server_config
from main_page.libs.status_codes import *
from main_page.libs.dirmanager import try_mkdir
from main_page.forms import base_forms


from main_page import log_util
from main_page.libs import ldap_queries

from key import LDAP_PASSWORD

logger = log_util.get_logger(__name__)



class AjaxLogin(TemplateView):
  """
  Handles processing of login requests from javascript
  """
  def post(self, request):
    signed_in = False
    
    login_form = base_forms.LoginForm(data=request.POST)
    
    if login_form.is_valid():
      # Authtication is using the ldap backend
      user = authenticate(
        request, 
        username=request.POST['username'], 
        password=request.POST['password']
      )

      # If authentication was successful a user is returned else nothing is returned.
      if user:
        
        # User group determines if a user have access to the admin panel and other fun stuff. 
        # When a user log in for the first time, they need a user group. In this case 2
        # Although you should probbally change this to a default in the model.User.user_group
        if user.user_group == None:
          user.user_group = UserGroup.objects.get(id=2) # Default usergroup assignment if user is created
        
        # Here we grab all the departments the user is part of. The idea here that some LDAP groups determines what hospital.
        # If you need to assign people to these group it's done through CBAS
        # The groups are:
        # - RGH-B-SE GFR BFH - Bispebjerg
        # - RGH-B-SE GFR HGH - Herlev
        # - RGH-B-SE GFR HVH - Hvidovre
        # - RGH-B-SE GFR NOH - Nordsjælland
        # - RGH-B-SE GFR RH Blegdamsvej - Rigshospitalet  
        # - RGH-B-SE GFR RH Glostrup
        usergroups = UserDepartmentAssignment.objects.filter(user=user)

        # I think you can do some stuff with the backend instead of what i did. Instead i wrote my own LDAP connector
        ldap_connection = ldap_queries.initialize_connection()
        # Loop over all departments to see, what kind of departments the user is associated.
        for department in Department.objects.all():
          if ldap_group_name := department.ldapPath: # If the departments is set up correctly. If this is a problem you should put some sort of validating on the ldap_path
            try:
              if ldap_queries.CheckGroup(ldap_connection, ldap_group_name, user.username): 
                if usergroups.filter(department=department):
                  pass
                else:
                  UserDepartmentAssignment(user=user, department=department).save()
              else:
                if userDepartmentAssignment := UserDepartmentAssignment.objects.all().filter(department=department, user=user):
                  userDepartmentAssignment.delete()
            except FILTER_ERROR:
              logger.error(f"{department.name} ldap path is setup incorrectly")
          else:
            logger.error(f"{department.name}'s ldap path is not setup, so new users cannot be assigned.")                

        # if the user have not set an department set it for them
        if user.department == None:
          usergroups = UserDepartmentAssignment.objects.filter(user=user)
          if len(usergroups) == 0: # User is a valid BamID but is not set up in CBAS for access to 
            return JsonResponse({
              "signed_in" : False,
              "no_permissions" : True,
            })


        login(request, user) # Login the user aka set some tokens and cookies
        logger.info(f'User: {request.user.username} logged in successful')


        signed_in = True
      else:
        logger.warning(f"User: {request.POST['username']} Failed to log in, from IP address: {request.META.get('REMOTE_ADDR')}")

    data = {
      'signed_in': signed_in,
      "no_permissions" : False,
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