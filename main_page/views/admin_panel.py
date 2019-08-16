from django.http import HttpResponseNotFound
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from main_page.views.mixins import AdminRequiredMixin

from main_page import models
from main_page import forms


class AdminPanelView(AdminRequiredMixin, LoginRequiredMixin, TemplateView):
  """
  Administrator panel for e.g. user creation, user deletion, etc...
  """
  template_name = "main_page/admin_panel.html"

  def get(self, request):
    context = {

    }

    return render(request, self.template_name, context)


# TODO: Change the HttpResponseNotFound to display danish messages
# TODO: Change the HttpResponseNotFound to display our 404 site with the message
class AdminPanelEditView(AdminRequiredMixin, LoginRequiredMixin, TemplateView):
  template_name = "main_page/admin_panel_edit.html"

  MODEL_NAME_MAPPINGS = {
    'user': models.User,
    'department': models.Department,
    'config': models.Config,
    'hospital': models.Hospital,
    'handled_examination': models.HandledExaminations,
    'proceduretype': models.ProcedureType,
    'procedure_mapping': models.Config.accepted_procedures.through
  }

  EDIT_FORM_MAPPINGS = {
    'user': forms.EditUserForm,
    'department': forms.EditDepartmentForm,
    'config': forms.EditConfigForm,
    'hospital': forms.EditHospitalForm,
    'handled_examination': forms.EditHandledExaminationsForm,
    'proceduretype' : forms.EditProcedureForm,
  }

  def get(self, request, model_name, obj_id):
    # Attempt to get the corresponding model for the requets name
    try:
      model = self.MODEL_NAME_MAPPINGS[model_name]
    except KeyError:
      return HttpResponseNotFound(f"Unable to find corresponding model with key: '{model_name}'")

    # Attempt to get specific model instance
    try:
      obj_instance = model.objects.get(pk=obj_id)
    except ObjectDoesNotExist:
      return HttpResponseNotFound(f"Unable to find model instance for object id: '{obj_id}'")

    # Construct corresponding edit form for the model, initialized with
    # parameters from the retreived instance
    try:
      edit_form = self.EDIT_FORM_MAPPINGS[model_name]
    except KeyError:
      return HttpResponseNotFound(f"Unable to find corresponding form for model with key: '{model_name}'")

    edit_form = edit_form(instance=obj_instance)

    context = {
      'model_name': model_name,
      'edit_form': edit_form,
    }

    return render(request, self.template_name, context)


class AdminPanelAddView(AdminRequiredMixin, LoginRequiredMixin, TemplateView):
  template_name = "main_page/admin_panel_add.html"

  MODEL_NAME_MAPPINGS = {
    'user': models.User,
    'department': models.Department,
    'config': models.Config,
    'hospital': models.Hospital,
    'handled_examination': models.HandledExaminations,
    'proceduretype' : models.ProcedureType,
    'procedure_mapping': models.Config.accepted_procedures.through
  }

  ADD_FORM_MAPPINGS = {
    'user': forms.AddUserForm,
    'department': forms.AddDepartmentForm,
    'config': forms.AddConfigForm,
    'hospital': forms.AddHospitalForm,
    'handled_examination': forms.AddHandledExaminationsForm,
    'proceduretype': forms.AddProcedureForm,
    'procedure_mapping': forms.AddProcedureMapping
  }

  def get(self, request, model_name):
    # Construct corresponding add form for the model
    try:
      add_form = self.ADD_FORM_MAPPINGS[model_name]()
    except KeyError:
      return HttpResponseNotFound(f"Unable to find corresponding form for model with key: '{model_name}'")

    context = {
      'model_name': model_name,
      'add_form': add_form,
    }

    return render(request, self.template_name, context)
