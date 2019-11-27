from django.views.generic import TemplateView
from django.shortcuts import render, redirect
from django.template import loader
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest

import shutil
import os
import datetime
import logging
import PIL
import glob
from pandas import DataFrame
from typing import Type, List, Tuple, Union, Generator, Dict

from main_page.libs.dirmanager import try_mkdir
from main_page.libs.query_wrappers import pacs_query_wrapper as pacs
from main_page.libs.query_wrappers import ris_query_wrapper as ris
from main_page.libs import dataset_creator
from main_page.libs import server_config
from main_page.libs import samba_handler
from main_page.libs import formatting
from main_page.libs import dicomlib
from main_page.libs import enums
from main_page import models

logger = logging.getLogger()


class DeletedStudiesView(LoginRequiredMixin, TemplateView):
  """
  Displays any deleted studies.

  A study will only remain deleted for 21 days after which it is permanetly
  deleted from the server's system
  """
  template_name = "main_page/deleted_studies.html"

  def get(self, request: Type[WSGIRequest]) -> HttpResponse:
    hospital_shortname = request.user.department.hospital.short_name

    # Fetch all deleted studies
    deleted_studies = ris.get_studies(
      f"{server_config.DELETED_STUDIES_DIR}{hospital_shortname}"
    )

    # Permantly delete any old studies
    deleted_studies, _ = ris.check_if_old(
      deleted_studies,
      hospital_shortname,
      ris.permanent_delete,
      threshold=21
    )

    # Sort by descending date
    deleted_studies = ris.sort_datasets_by_date(deleted_studies)

    # Extract required booking information
    deleted_studies, _ = ris.extract_list_info(deleted_studies)

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      "deleted_studies" : deleted_studies
    }

    return render(request, self.template_name, context)
