from django.shortcuts import render
from django.views.generic import TemplateView

from main_page.libs import server_config
from main_page import forms


class IndexView(TemplateView):
  """
  Index page - serves as the login page
  """
  template_name = 'main_page/index.html'

  def get(self, request):
    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'login_form': forms.LoginForm()
    }

    return render(request, self.template_name, context)
