from django.shortcuts import render
from django.views.generic import TemplateView

from main_page.libs import server_config
from main_page import forms


def is_browser_supported(user_agent: str) -> bool:
  """
  Determines if the browser is supported

  Args:
    user_agent: the user agent string

  Returns:
    True if the browser is supported, False otherwise
  """
  SUPPORTED_BROWSERS = [
    #'chrome',
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

    login_form = forms.LoginForm()

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'browser_supported': browser_support,
      'login_form': login_form,
    }

    return render(request, self.template_name, context)
