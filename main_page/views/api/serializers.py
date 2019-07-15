from django.db import models

from typing import Type, Dict


class JSONSerializer:
  def __init__(self):
    self._SERIALIZER_MAPPINGS = {
      models.ForeignKey: self.__serialize_ForeignKey,
      models.AutoField: self.__serialize_AutoField,
      models.CharField: self.__serialize_CharField,
      models.DateTimeField: self.__serialze_DateTimeField,
    }

  def __serialize_ForeignKey(self, obj: Type[models.Model], field: Type[models.ForeignKey]) -> str:    
    foreign_obj = getattr(obj, field.name)
    return foreign_obj.pk

  def __serialize_CharField(self, obj: Type[models.Model], field: Type[models.CharField]) -> str:
    return getattr(obj, field.name)

  def __serialize_AutoField(self, obj: Type[models.Model], field: Type[models.AutoField]) -> str:
    return getattr(obj, field.name)

  def __serialze_DateTimeField(self, obj: Type[models.Model], field: Type[models.DateTimeField]) -> str:
    return getattr(obj, field.name)

  def serialize(self, obj: Type[models.Model], fields=None) -> Dict:
    """
    Serializes a django Model object to JSON

    Args:
      obj: model object to serialize
      fields: dict of fields contian in the model object

    Returns:
      dict containing the serialize fields

    Raises:
      ValueError: if the object is not a django Model.
      ValueError: if a field from the fields dict is not included within the
                  model objects actual fields.
    """
    # Args checking
    if not isinstance(obj, models.Model):
      raise ValueError(f"Invalid object type for 'obj'. Expected: '{models.Model}', Got: {type(obj)}")

    # Validate every field is present
    # NOTE: If fields is available iterate over it rather than obj._meta.fields
    obj_fields = [ ]
    for field in obj._meta.fields:
      try:
        obj_fields.append(field.name)
      except:
        # Ignore weird internal django fields
        continue
    
    if fields:
      if not isinstance(fields, set):
        raise ValueError(f"Invalid object type for 'fields'. Expected: '{set}', Got: {type(fields)}")

      for field in fields:
        if field not in obj_fields:
          raise ValueError(f"Unable to find field: '{field}', in the objects actual fields.")
    else:
      fields = set(obj_fields)

    # Serialize each field
    ret = { }
    for field in fields:      
      curr_field = obj._meta.get_field(field)
      curr_field_type = type(curr_field)
      serialze_func = None

      if curr_field_type in self._SERIALIZER_MAPPINGS:
        serialze_func = self._SERIALIZER_MAPPINGS[curr_field_type]
      else:
        raise NotImplementedError(f"Unsupported field type in object. Got: {type(curr_field_type)}")

      ret[field] = serialze_func(obj, curr_field)

    return ret
