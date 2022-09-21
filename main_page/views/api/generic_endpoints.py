from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import View
from django.http import JsonResponse, HttpResponseNotFound, HttpResponse, QueryDict
from django.db import models
from django.core.handlers.wsgi import WSGIRequest

from typing import Type, Union

from main_page.views.api.serializers import JSONSerializer


class GetEndpoint(View):
  """
  Defines an api endpoint which allows for retreival of object information
  through GET requests for either all objects or a specific object given an id.
  """

  def get(self, request: Type[WSGIRequest], obj_id: Union[int, str]=None) -> HttpResponse:
    """
    Handles incoming GET requests to the endpoint

    Args:
      request: incoming HTTP request

    Kwargs:
      obj_id: if given only returns information about the object related to the
              objects id.

    Returns:
      JSONResponse containing the requested information about the model,
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
  """
  Defines an api endpoint which allows for deletion of object instances,
  by a given object id.
  """

  def delete(self, request: Type[WSGIRequest], obj_id: Union[str, int]) -> HttpResponse:
    """
    Handles incoming DELETE requests to the endpoint

    Args:
      request: incoming HTTP request
      obj_id: id of object to delete

    Returns:
      JSONResponse containing information regarding the status of the action,
      otherwise 404 on failure.
    """
    try:
      obj = self.model.objects.get(pk=obj_id)
    except ObjectDoesNotExist:
      return HttpResponseNotFound()

    obj.delete()

    return JsonResponse({'action': 'success'})


# REPLACES STUFF
class PutEndpoint(View):
  pass


class PostEndpoint(View):
  """
  Defines an api endpoint which allows for creation of object instances,
  using information from the incoming request.
  """

  def post(self, request: Type[WSGIRequest]) -> HttpResponse:
    """
    Handles incoming POST requests to the endpoint

    Args:
      request: incoming HTTP request

    Returns:
      JSONResponse containing information regarding the status of the action.
    """

    # Create the new instance
    obj = self.model()

    # Find next id available, if the model has an 'id' field
    if getattr(self.model, 'id', False):
      try:
        obj_id = self.model.objects.all().order_by("-id")[0].id
        obj.id = obj_id + 1
      except IndexError: # No model instance currently exists
        obj.id = 1

    # Set additional fields
    request_body = QueryDict(request.body)

    for key, value in request_body.items():
      # If key is a password, set it
      if key == 'password':
        obj.set_password(value)
        continue

      # Retreive foreign object if model specifies it
      if 'foreign_fields' in dir(self):
        if key in self.foreign_fields:
          foreign_model = self.foreign_fields[key]
          value = foreign_model.objects.get(pk=int(value))

      setattr(obj, key, value)

    obj.save()

    resp = JsonResponse({'action': 'success'})
    resp.status_code = 201
    return resp


class PatchEndpoint(View):
  """
  Defines an api endpoint which allows for updating the information within
  a specified object instance, using information from the request.
  """

  def patch(self, request: Type[WSGIRequest], obj_id: Union[str, int]) -> HttpResponse:
    """
    Handles incoming PATCH requests to the endpoint

    Args:
      request: incoming HTTP request
      obj_id: id of object to update

    Returns:
      JSONResponse containing information regarding the status of the action,
      otherwise 404 on failure.
    """

    # Retreive object instance
    try:
      obj = self.model.objects.get(pk=obj_id)
    except ObjectDoesNotExist:
      return HttpResponseNotFound()

    # Update model instance
    patch = QueryDict(request.body)
    for key, value in patch.items():
      # Retreive foreign object if model specifies it
      if value != '':
        if 'foreign_fields' in dir(self):
          if key in self.foreign_fields:
            foreign_model = self.foreign_fields[key]
            value = foreign_model.objects.get(pk=int(value))
      else:
        value = None

      setattr(obj, key, value)

    obj.save()

    return JsonResponse({'action': 'success'})


class RESTEndpoint(GetEndpoint, DeleteEndpoint, PatchEndpoint, PutEndpoint, PostEndpoint):
  """
  Endpoint encapsulating all the basic REST endpoints into one for simplicity

  Remark:
    When specifying the url the instance id MUST be named 'obj_id'
  """
  def get(self, request: Type[WSGIRequest], obj_id: Union[int, str]=None) -> HttpResponse:
    return super().get(request, obj_id=obj_id)

  def delete(self, request: Type[WSGIRequest], obj_id: Union[str, int]) -> HttpResponse:
    return super().delete(request, obj_id)

  def patch(self, request: Type[WSGIRequest], obj_id: Union[str, int]) -> HttpResponse:
    return super().patch(request, obj_id)

  def put(self, request: Type[WSGIRequest], obj_id: Union[str, int]) -> HttpResponse:
    raise NotImplementedError()

  def post(self, request: Type[WSGIRequest]) -> HttpResponse:
    return super().post(request)
