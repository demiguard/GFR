from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseNotFound

import datetime
import logging
import datetime
from pathlib import Path
from pydicom import uid
import random

from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs import server_config
from main_page.libs import dicomlib
from main_page.libs.dirmanager import try_mkdir
from main_page.forms import base_forms

from main_page import log_util

logger = log_util.get_logger(__name__)


class SearchView(LoginRequiredMixin, TemplateView):
  """
  Search view dislaying studies which have been sent to PACS
  """
  template_name = 'main_page/search.html'
  
  def get(self, request):
    search_form = base_forms.SearchForm()

    context = {
      'title'       : server_config.SERVER_NAME,
      'version'     : server_config.SERVER_VERSION,
      'search_form' : search_form
    }

    return render(request, self.template_name, context)
