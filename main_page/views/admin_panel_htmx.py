from django.shortcuts import render
from django.http import HttpResponseBadRequest, HttpResponse
from main_page.forms import model_add_forms

## Helper for thmx form in admin_panel

FORM_MAP = {
    "user": model_add_forms.AddUserForm,
    "hospital": model_add_forms.AddHospitalForm,
    "department": model_add_forms.AddDepartmentForm,
    "procedure": model_add_forms.AddProcedureForm,
    "config": model_add_forms.AddConfigForm,
    "handled_examination": model_add_forms.AddHandledExaminationsForm,
    "procedure_mapping": model_add_forms.AddProcedureMapping,
    "address": model_add_forms.AddAddressForm,
    "server_config": model_add_forms.AddServerConfigurationForm,
}

def LoadAddFormView(request):
    model_name = request.GET.get("model") or request.POST.get("model")
    form_class = FORM_MAP.get(model_name)

    if not form_class:
        return HttpResponseBadRequest("Ugyldigt modelnavn")

    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("<div class='alert alert-success'>Tilføjet!</div><script>document.getElementById('modal').style.display = 'none';</script>")
    else:
        form = form_class()

    return render(request, "main_page/partials/admin_add_form.html", {
        "add_form": form,
        "model_name": model_name,
    })
