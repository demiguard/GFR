from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from django.http import JsonResponse, HttpResponseNotFound

from main_page.views.api.serializers import JSONSerializer


class GetEndpoint(View):
  def __init__(self, model, fields=None):
    self.model = model
    self.fields = fields

  def get(self, request, obj_id=None):
    context = { }
    
    serializer = JSONSerializer()
    
    # Get specific object if id is given
    if obj_id:
      try:
        objs = [self.model.objects.get(pk=obj_id)]
      except ObjectDoesNotExist:
        return HttpResponseNotFound()
    else:
      objs = self.model.objects.all()

    # Serialize objects
    json_objs = [ ]
    for obj in objs:
      json_objs.append(serializer.serialize(obj, fields=self.fields))

    model_name = str(self.model).split("'")[1].split('.')[-1]
    context[model_name.lower()] = json_objs

    return JsonResponse(context)
