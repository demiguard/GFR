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

  def post(self, request):
    # Create new study from the historical one
    user = request.user
    hospital = user.department.hospital.short_name
    hist_accession_number = request.POST["hist_accession_number"]
    
    # Save dataset to new study
    hist_dir = Path(
      server_config.FIND_RESPONS_DIR, 
      hospital, 
      hist_accession_number
    )
    try_mkdir(hist_dir, mk_parents=True)

    hist_filepath = Path(hist_dir, f"{hist_accession_number}.dcm")

    # Get historical dataset from PACS - if not already there
    if not hist_filepath.exists():
      dataset = pacs.move_from_pacs(user, hist_accession_number)

      if isinstance(dataset, type(None)):
        return HttpResponseNotFound()

      # Increament InstanceNumber counter, s.t. the generated SeriesInstanceUID doesn't conlict in PACS
      # See dicomlib.py/try_update_exam_meta_data function for more
      dataset.InstanceNumber = str(int(dataset.InstanceNumber) + 1)

      dicomlib.save_dicom(hist_filepath, dataset)
      
      # Create recovery file, such that the dicom file isn't immediately deleted from list_studies
      recovery_file = Path(hist_dir, server_config.RECOVERED_FILENAME)
      with recovery_file.open("w") as fp:
        fp.write(datetime.datetime.now().strftime('%Y%m%d'))

      # Retreive the study history as well
      if "clearancehistory" in dataset:
        for study in dataset.clearancehistory:
          study_accession_number = study.AccessionNumber
          study_dataset = pacs.move_from_pacs(user, study_accession_number)
          dicomlib.save_dicom(Path(hist_dir, f"{study_accession_number}.dcm"), study_dataset)

    return JsonResponse({
      "redirect_url": f"/fill_study/{hist_accession_number}" # URL of new study to redirect to
    })
