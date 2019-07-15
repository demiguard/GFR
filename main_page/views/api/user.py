from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from django.http import JsonResponse, HttpResponseNotFound

from main_page import models
from main_page.views.mixins import AdminRequiredMixin
from main_page.views.api.serializers import JSONSerializer


class UserEndpoint(AdminRequiredMixin, LoginRequiredMixin, View):
  def get(self, request, user_id=None):
    context = { }
    
    serializer = JSONSerializer()
    
    if user_id:
      try:
        users = [models.User.objects.get(pk=user_id)]
      except ObjectDoesNotExist:
        return HttpResponseNotFound()
    else:
      users = models.User.objects.all()

    # Serialize users
    json_users = [ ]
    for user in users:
      json_users.append(serializer.serialize(user, fields={
        'id',
        'username',
        'department',
        'user_group'
      }))

    context['users'] = json_users

    return JsonResponse(context)
