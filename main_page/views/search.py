from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

import datetime
import logging

from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs import server_config
from main_page import forms

logger = logging.getLogger()


class SearchView(LoginRequiredMixin, TemplateView):
  """
  Search view dislaying studies which have been sent to PACS
  """
  template_name = 'main_page/search.html'
  
  def get(self, request):
    search_form = forms.SearchForm()

    context = {
      'title'       : server_config.SERVER_NAME,
      'version'     : server_config.SERVER_VERSION,
      'search_form' : search_form
    }

    return render(request, self.template_name, context)
