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
from main_page.libs import examination_info
from main_page.libs import dataset_creator
from main_page.libs import server_config
from main_page.libs import samba_handler
from main_page.libs import formatting
from main_page.libs import dicomlib
from main_page.libs import enums
from main_page import forms
from main_page import models

logger = logging.getLogger()


class ListStudiesView(LoginRequiredMixin, TemplateView):
  """
  Lists all registered studies in RIS
  """
  template_name = "main_page/list_studies.html"

  def get(self, request: Type[WSGIRequest]) -> HttpResponse:
    # Fetch all registered studies
    curr_department = request.user.department
    hospital_shortname = curr_department.hospital.short_name
    
    registered_datasets = ris.get_studies(
      f"{server_config.FIND_RESPONS_DIR}{hospital_shortname}"
    )

    # Move 7 day old studies to deleted_studies
    registered_studies, failed_old = ris.check_if_old(
      registered_datasets, 
      hospital_shortname,
      ris.move_to_deleted
    )
    
    # Filter out datasets based on procedure blacklist
    procedure_blacklist = [
      x.type_name for x in curr_department.config.accepted_procedures.all()
    ]

    registered_datasets = ris.procedure_filter(
      registered_datasets,
      procedure_blacklist
    )

    # Sort by descending date
    registered_datasets = ris.sort_datasets_by_date(registered_datasets)

    # Extract required booking information
    registered_studies, failed_studies = ris.extract_list_info(registered_datasets)
    failed_studies += failed_old
    
    # Report on failed datasets
    failed_accession_nr = [ ]
    no_accession_nr = 0
    for dataset in failed_studies:
      try:
        failed_accession_nr.append(dataset.AccessionNumber)
      except AttributeError: # Somehow dataset doesn't have an AccessionNumber
        no_accession_nr += 1

    # Construct error message if any errors occured duing info extraction
    if failed_accession_nr:
      error_message = f"Kunne ikke indlæse undersøgelser med accession numre: {[', '.join(failed_accession_nr)]}"

      if no_accession_nr > 0:
        error_message += f", fandt {no_accession_nr} undersøgelser uden accession nr."
    else:
      error_message = ""

    # Return rendered view
    context = {
      "title"              : server_config.SERVER_NAME,
      "version"            : server_config.SERVER_VERSION,
      "registered_studies" : registered_studies,
      "error_message"      : error_message
    }

    return render(request, self.template_name, context)
