from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from main_page.libs import server_config
from main_page.forms.base_forms import FilterForm
from main_page.models import ProcedureType

"""

  This class is for the Filterview, The purpose of this is to make the filtering Easier

"""


class FilterView(LoginRequiredMixin, TemplateView):
  template_name = 'main_page/filter.html'
  
  #Display
  def get(self, request):
    department = request.user.department
    config_id = department.config.id
    query = list(department.config.accepted_procedures.through.objects.filter(config_id=config_id))
    procedures = [ procedure.proceduretype for procedure in query ]
    procedure_id = [ procedure.id for procedure in query ]
    context = {
      'FilterForm' : FilterForm(initial={}),
      'active_filters' : zip(procedures, procedure_id)
    }


    return render(request, self.template_name, context=context) 
  #Creation
  def post(self, request):
    department = request.user.department
    Filter = request.POST['FilterName']
    
    existsing_filter = ProcedureType.objects.filter(type_name=Filter)
    if existsing_filter:
      existsing_filter = existsing_filter[0]
      department.config.accepted_procedures.add(existsing_filter)
    else:
      new_filter = ProcedureType.objects.create(type_name=Filter)
      new_filter.save()
      department.config.accepted_procedures.add(new_filter)

    return redirect('main_page:list_studies')
