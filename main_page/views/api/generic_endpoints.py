from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from django.http import JsonResponse, HttpResponseNotFound, HttpResponse
from django.db import models
from django.core.handlers.wsgi import WSGIRequest

from typing import Type, Union

from main_page.views.api.serializers import JSONSerializer


class GetEndpoint(View):
  """
  Defines an api endpoint which allows for retreival of object information
  through GET requests for either all objects or a specific object given an id.

  Args:
    model: any valid django model
  
  Kwargs:
    fields: fields to make available through the endpoint, if None all fields
            are to be presented.
  """
  def get(self, request: Type[WSGIRequest], obj_id=None) -> HttpResponse:
    """
    Handles incoming GET requests to the endpoint

    Args:
      request: incoming HTTP request

    Kwargs:
      obj_id: if given only returns information about the object related to the
              objects id.
    
    Returns:
      JSONResponse containing the requeted information about the model,
      otherwise 404 on failure (e.g. if a requested field is not contained 
      within the model).
    """
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


class DeleteEndpoint(View):
  def delete(self, request: Type[WSGIRequest], obj_id: Union[str, int]) -> HttpResponse:
    try:
      obj = self.model.objects.get(pk=obj_id)
    except ObjectDoesNotExist:
      return HttpResponseNotFound()

    obj.delete()
  
    return JsonResponse({'action': 'success'})


class PutEndpoint(View):
  pass


class PostEndpoint(View):
  pass


class PatchEndpoint(View):
  pass