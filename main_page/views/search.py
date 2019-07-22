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
  Search view
  """
  template_name = 'main_page/search.html'
  
  def get(self, request):
    # Default date case: display the patients from the last week
    now = datetime.datetime.now()
    default_date_to = now.strftime('%Y-%m-%d')

    week_delta = datetime.timedelta(days=7)
    week_datetime = now - week_delta
    default_date_from = week_datetime.strftime('%Y-%m-%d')

    # Extract search parameters from url
    if 'name' in request.GET:
      search_name = request.GET['name']
    else:
      search_name = ''

    if 'cpr' in request.GET:
      search_cpr = request.GET['cpr']
    else:
      search_cpr = ''

    if 'Rigs' in request.GET:
      search_rigs_nr = request.GET['Rigs']
    else:
      search_rigs_nr = ''

    date_set = False
    if 'Dato_start' in request.GET:
      search_date_from = request.GET['Dato_start']
      date_set = True
    else:
      search_date_from = ''

    if 'Dato_finish' in request.GET:
      search_date_to = request.GET['Dato_finish']
      date_set = True
    else:
      search_date_to = ''

    if not date_set:
      search_date_from = default_date_from
      search_date_to = default_date_to

    #Removed initial 
  
    search_resp = pacs.search_query_pacs(
      request.user,
      name=search_name,
      cpr=search_cpr,
      accession_number=search_rigs_nr,
      date_from=search_date_from,
      date_to=search_date_to,
    )
    

    logger.info(f"Initial search responses: {search_resp}")

    # Add specific bootstrap class to the form item and previous search parameters
    get_study_form = forms.GetStudy(initial={
      'name': search_name,
      'cpr': search_cpr,
      'Rigs': search_rigs_nr,
      'Dato_start': search_date_from,
      'Dato_finish': search_date_to
    })
    
    for item in get_study_form:
      item.field.widget.attrs['class'] = 'form-control'

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'getstudy' : get_study_form,
      'responses': search_resp,
    }

    return render(request, self.template_name, context)
