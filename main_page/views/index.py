# Python standard library
from ldap import FILTER_ERROR
import logging

from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout

from constants import GFR_LOGGER_NAME

from main_page.forms import base_forms
from main_page.libs import ldap_queries
from main_page.libs import server_config
from main_page.models import UserGroup, Department, UserDepartmentAssignment


logger = logging.getLogger(GFR_LOGGER_NAME)

def is_browser_supported(user_agent: str) -> bool:
  """
  Determines if the browser is supported

  Args:
    user_agent: the user agent string

  Returns:
    True if the browser is supported, False otherwise
  """
  SUPPORTED_BROWSERS = [
    'chrome',
    'firefox'
  ]

  user_agent = user_agent.lower()

  for browser in SUPPORTED_BROWSERS:
    if browser in user_agent:
      return True

  return False


class IndexView(TemplateView):
  """
  Index page - serves as the login page
  """
  template_name = 'main_page/index.html'

  def get(self, request):
    user_agent = request.META['HTTP_USER_AGENT']
    browser_support = is_browser_supported(user_agent)

    login_form = base_forms.LoginForm()

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'browser_supported': browser_support,
      'login_form': login_form,
    }

    return render(request, self.template_name, context)


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
          user.save()

        # Here we grab all the departments the user is part of. The idea here that some LDAP groups determines what hospital.
        # If you need to assign people to these group it's done through CBAS
        # The groups are:
        # - RGH-B-SE GFR BFH - Bispebjerg
        # - RGH-B-SE GFR HGH - Herlev
        # - RGH-B-SE GFR HVH - Hvidovre
        # - RGH-B-SE GFR NOH - Nordsjælland
        # - RGH-B-SE GFR RH Blegdamsvej - Rigshospitalet
        # - RGH-B-SE GFR RH Glostrup
        userGroups = UserDepartmentAssignment.objects.filter(user=user)

        # I think you can do some stuff with the backend instead of what i did. Instead i wrote my own LDAP connector
        ldap_connection = ldap_queries.initialize_connection()
        # Loop over all departments to see, what kind of departments the user is associated.
        for department in Department.objects.all():
          if ldap_group_name := department.ldapPath: # If the departments is set up correctly. If this is a problem you should put some sort of validating on the ldap_path
            try:
              if ldap_queries.CheckGroup(ldap_connection, ldap_group_name, user.username):
                if userGroups.filter(department=department):
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
          userGroups = UserDepartmentAssignment.objects.filter(user=user)
          if len(userGroups) == 0: # User is a valid BamID but is not set up in CBAS for access to
            return JsonResponse({
              "signed_in" : False,
              "no_permissions" : True,
            })
          else:
            UDA = userGroups[0]
            user.department = UDA.department
            user.save()


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
    else:
      return redirect('main_page:list_studies')

    return resp
