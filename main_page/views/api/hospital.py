from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from django.http import JsonResponse, HttpResponseNotFound

from main_page import models
from main_page.views.mixins import AdminRequiredMixin
from main_page.views.api.serializers import JSONSerializer


class GetEndpoint(View):
  pass


class HospitalEndpoint(AdminRequiredMixin, LoginRequiredMixin, View):
  def get(self, request, hospital_id=None):
    context = { }
    
    serializer = JSONSerializer()
    
    if hospital_id:
      try:
        hospitals = [models.Hospital.objects.get(pk=hospital_id)]
      except ObjectDoesNotExist:
        return HttpResponseNotFound()
    else:
      hospitals = models.Hospital.objects.all()

    # Serialize users
    json_hospitals = [ ]
    for hospital in hospitals:
      json_hospitals.append(serializer.serialize(hospital, fields={
        'id',
        'name',
        'short_name',
        'address'
      }))

    context['users'] = json_hospitals

    return JsonResponse(context)
