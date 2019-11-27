from django.http import HttpResponseNotFound
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from main_page.libs import server_config
from main_page.views.mixins import AdminRequiredMixin

from main_page import models
from main_page.forms import model_add_forms, model_edit_forms, base_forms


class AdminPanelView(AdminRequiredMixin, LoginRequiredMixin, TemplateView):
  """
  Administrator panel for e.g. user creation, user deletion, etc...
  """
  template_name = "main_page/admin_panel.html"

  def get(self, request):
    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'nuke_list_form': base_forms.NukeListStudiesForm(),
      'nuke_deleted_form': base_forms.NukeDeletedStudiesForm(),
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
    'procedure_mapping': models.Config.accepted_procedures.through,
    'address': models.Address,
    'server_config': models.ServerConfiguration
  }

  EDIT_FORM_MAPPINGS = {
    'user': model_edit_forms.EditUserForm,
    'department': model_edit_forms.EditDepartmentForm,
    'config': model_edit_forms.EditConfigForm,
    'hospital': model_edit_forms.EditHospitalForm,
    'handled_examination': model_edit_forms.EditHandledExaminationsForm,
    'proceduretype' : model_edit_forms.EditProcedureForm,
    'address': model_edit_forms.EditAddressForm,
    'server_config': model_edit_forms.EditServerConfigurationForm
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
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'model_name': model_name,
      'edit_form': edit_form,
    }

    return render(request, self.template_name, context)


class AdminPanelAddView(AdminRequiredMixin, LoginRequiredMixin, TemplateView):
  template_name = "main_page/admin_panel_add.html"

  MODEL_NAME_MAPPINGS = {
    'user'                : models.User,
    'department'          : models.Department,
    'config'              : models.Config,
    'hospital'            : models.Hospital,
    'handled_examination' : models.HandledExaminations,
    'proceduretype'       : models.ProcedureType,
    'procedure_mapping'   : models.Config.accepted_procedures.through,
    'address'             : models.Address,
    'server_config'       : models.ServerConfiguration
  }

  ADD_FORM_MAPPINGS = {
    'user'                : model_add_forms.AddUserForm,
    'department'          : model_add_forms.AddDepartmentForm,
    'config'              : model_add_forms.AddConfigForm,
    'hospital'            : model_add_forms.AddHospitalForm,
    'handled_examination' : model_add_forms.AddHandledExaminationsForm,
    'proceduretype'       : model_add_forms.AddProcedureForm,
    'procedure_mapping'   : model_add_forms.AddProcedureMapping,
    'address'             : model_add_forms.AddAddressForm,
    'server_config'       : model_add_forms.AddServerConfigurationForm
  }

  def get(self, request, model_name):
    # Construct corresponding add form for the model
    try:
      print(self.ADD_FORM_MAPPINGS[model_name]())
      add_form = self.ADD_FORM_MAPPINGS[model_name]()
    except KeyError:
      return HttpResponseNotFound(f"Unable to find corresponding form for model with key: '{model_name}'")

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'model_name': model_name,
      'add_form': add_form,
    }

    return render(request, self.template_name, context)
