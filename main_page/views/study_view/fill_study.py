# Python standard library
import logging
import datetime
from typing import Dict, Generator, List, Tuple, Union

# Third party Modules
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import modelformset_factory
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.utils.timezone import get_current_timezone
from django.views.generic import TemplateView

# Clairvoyance packages
from constants import GFR_LOGGER_NAME

from main_page import models
from main_page.models import InjectionSample, GFRStudy
from main_page.forms import GFRStudyForm, SampleForm, SampleTimeForm

from main_page.libs import formatting
from main_page.libs import server_config
from main_page.libs import samba_handler

# Custom type - for representation of csv files to be loaded on to page
CsvDataType = Tuple[Generator[List[str], List[List[List[Union[int, float]]]], List[int]], int]
logger = logging.getLogger(GFR_LOGGER_NAME)



class FillStudyView(LoginRequiredMixin, TemplateView):
  """
  View for filling out a specific study/examination
  """
  template_name = 'main_page/fill_study.html'

  def get_counter_data(self, hospital: str) -> CsvDataType:
    """
    Tries to retrieve counter data from the Samba Share to display on the site

    Args:
      hospital: short name of the hospital to retrieve data from

    Returns:
      Tuple with the zipped data and the length of the data

    Raises:
      ConnectionError: if no connection to the Samba Share can be made
    """
    try:
      server_configuration = models.ServerConfiguration.objects.get(id=1)

      data_files, error_messages = samba_handler.smb_get_all_csv(hospital, server_configuration, timeout=10)
    except Exception as E:
      logger.warning(f'SMB Connection Failed: {E}')
      raise ConnectionError('Hjemmesiden kunne ikke få kontakt til serveren med prøve resultater.\n Kontakt din lokale IT-ansvarlige \n Server kan ikke få kontakt til sit Samba-share.')

    # Read requested data from each csv file
    csv_present_names = []
    csv_data = []
    data_indicies = []

    for data_file in data_files:
      selected = data_file[['Rack', 'Pos', 'Tc-99m CPM']]

      base_name = data_file['Measurement date & time'][0]

      measurement_date, measurement_time = base_name.split(' ')
      measurement_date = formatting.convert_date_to_danish_date(measurement_date, sep='-')

      csv_present_names.append( f'{measurement_time} - {measurement_date}')

      # Cast to int, as to remove dots when presenting on the site
      csv_data.append(
        [[int(rack), int(pos), int(cnt)]
          for rack, pos, cnt in selected.to_numpy().tolist()]
        )

      data_indicies.append(selected.index.tolist())

    # Flatten list of lists
    data_indicies = [idx for sublist in data_indicies for idx in sublist]

    return zip(csv_present_names, csv_data, data_indicies), len(data_indicies), error_messages


  def get(self, request: WSGIRequest, accession_number: str) -> HttpResponse:
    """
    Handles GET requests to the view, i.e. the presentation side

    Args:
      request: the incoming HTTP request
      accession_number: RIS number for the study
    """
    hospital = request.user.department.hospital.short_name # type: ignore #failure ensured by login required
    # Data fetching
    try:
      study = GFRStudy.objects.get(AccessionNumber=accession_number)
    except ObjectDoesNotExist:
      return HttpResponseNotFound(request)

    injection_samples = InjectionSample.objects.filter(Study=study)

    # Retrieve counter data to display from Samba Share
    error_message = "Der er ikke lavet nogen prøver de sidste 24 timer"
    try:
      csv_data, csv_data_len, error_messages = self.get_counter_data(hospital)
    except ConnectionError as conn_err:
      csv_data, csv_data_len = [], 0
      error_message = conn_err

    # Forms
    study_form = GFRStudyForm(instance=study)
    sample_time_form = SampleTimeForm()
    SampleFormset = modelformset_factory(InjectionSample,
                                         SampleForm, max_num=len(injection_samples))

    sample_formset = SampleFormset(queryset=injection_samples)

    context = {
      'sample_time_form' : sample_time_form,
      'sample_formset' :  sample_formset,
      'grand_form' : study_form,
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'rigsnr': accession_number,
      'csv_data': csv_data,
      'csv_data_len': csv_data_len,
      'error_message' : error_message
    }

    return render(request, self.template_name, context=context)

  def post(self, request: WSGIRequest, accession_number: str) -> HttpResponse:
    """
      This function handles the post request of /fill_study/accession_number

      The purpose of the post request is the study have been made or is being saved
      In other words the responsiblity for this function is:
        Updating Department based thining factor
        Handling different POST-request methods
    """

    hospital = request.user.department.hospital.short_name # type: ignore #failure ensured by login required

    try:
      study = GFRStudy.objects.get(AccessionNumber=accession_number)
    except ObjectDoesNotExist:
      return HttpResponseNotFound(request)

    injection_samples = InjectionSample.objects.filter(Study=study)

    SampleFormset = modelformset_factory(InjectionSample,
                                         SampleForm, extra=0)
    sample_formset = SampleFormset(request.POST)

    # Okay so really fucked stuff going on
    # So since it's a model form it includes an id, but if it's a new form
    # you can't assign an id to it, hence the fuckery below.

    print(request.POST)
    sample_formset.clean()
    cleaned_data = [form.cleaned_data for form in sample_formset.forms]
    all_samples_valid = True
    print(cleaned_data)
    samples = []

    for sample in cleaned_data:
      print('CountPerMinutes' in sample,
            'SampleTime' in sample,
            'SampleDate' in sample,
            'DeviationPercentage' in sample)

      all_samples_valid &= 'CountPerMinutes' in sample and sample['CountPerMinutes'] is not None and \
                           'SampleTime' in sample and sample['SampleTime'] is not None and \
                           'SampleDate' in sample and sample['SampleDate'] is not None and \
                           'DeviationPercentage' in sample and sample['DeviationPercentage'] is not None

    injection_samples.delete()
    if all_samples_valid:
      for sample in cleaned_data:
        sample_obj = InjectionSample.objects.create(
          Study=study,
          CountPerMinutes=sample['CountPerMinutes'],
          DeviationPercentage=sample['DeviationPercentage'],
          DateTime=datetime.datetime.combine(
            sample['SampleDate'],
            sample['SampleTime'],
            tzinfo=get_current_timezone()
          )
        )
        samples.append(sample_obj)
    # end of fuckery

    error_message = "Der er ikke lavet nogen prøver de sidste 24 timer"
    try:
      csv_data, csv_data_len, error_messages = self.get_counter_data(hospital)
    except ConnectionError as conn_err:
      csv_data, csv_data_len = [], 0
      error_message = conn_err

    study_form = GFRStudyForm(request.POST, instance=study)


    if 'calculate' in request.POST or 'save' in request.POST:
      calculating = 'calculate' in request.POST
      if study_form.is_valid():
        study = study_form.save(True)
        if calculating:
          if len(samples):
            return redirect('main_page:present_study', accession_number=accession_number)
        else:
          return redirect('main_page:list_studies')
      else:
        print("Not valid need some tests here")

    # Recreate the form
    sample_formset = SampleFormset(queryset=InjectionSample.objects.filter(Study=study))
    sample_time_form = SampleTimeForm()
    context = {
      'sample_time_form' : sample_time_form,
      'sample_formset' : sample_formset,
      'grand_form' : study_form,
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'rigsnr': accession_number,
      'csv_data': csv_data,
      'csv_data_len': csv_data_len,
      'error_message' : error_message
    }

    return render(request, self.template_name, context=context)
