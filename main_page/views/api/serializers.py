from django.db import models

from typing import Type, Dict


class JSONSerializer:
  def __init__(self) -> None:
    self._SERIALIZER_MAPPINGS = {
      models.ForeignKey: self.__serialize_ForeignKey,
      models.OneToOneField: self.__serialize_OneToOneField,
      models.AutoField: self.__serialize_AutoField,
      models.CharField: self.__serialize_CharField,
      models.FloatField: self.__serialize_FloatField,
      models.DateTimeField: self.__serialize_DateTimeField,
      models.DateField: self.__serialize_DateField,
    }

  # TODO: Make the below serializer functions more generic
  def __serialize_ForeignKey(self, obj: Type[models.Model], field: Type[models.ForeignKey]) -> str:    
    foreign_obj = getattr(obj, field.name)
    return foreign_obj.pk

  def __serialize_OneToOneField(self, obj: Type[models.Model], field: Type[models.OneToOneField]) -> str:    
    oto_obj = getattr(obj, field.name)
    return oto_obj.pk

  def __serialize_AutoField(self, obj: Type[models.Model], field: Type[models.AutoField]) -> str:
    return getattr(obj, field.name)

  def __serialize_CharField(self, obj: Type[models.Model], field: Type[models.CharField]) -> str:
    return getattr(obj, field.name)
  
  def __serialize_FloatField(self, obj: Type[models.Model], field: Type[models.FloatField]) -> str:
    return getattr(obj, field.name)

  def __serialize_DateTimeField(self, obj: Type[models.Model], field: Type[models.DateTimeField]) -> str:
    return getattr(obj, field.name)

  def __serialize_DateField(self, obj: Type[models.Model], field: Type[models.DateField]) -> str:
    return getattr(obj, field.name)

  def serialize(self, obj: Type[models.Model], fields=None) -> Dict:
    """
    Serializes a django Model object to JSON

    Args:
      obj: model object to serialize

    Kwargs:  
      fields: list of fields to serialize, if None all fields are serialized

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
      if not isinstance(fields, list):
        raise ValueError(f"Invalid object type for 'fields'. Expected: '{list}', Got: {type(fields)}")

      for field in fields:
        if field not in obj_fields:
          raise ValueError(f"Unable to find field: '{field}', in the objects actual fields.")
    else:
      fields = list(obj_fields)

    # Serialize each field
    ret = { }
    for field in fields:
      curr_field = obj._meta.get_field(field)
      curr_field_type = type(curr_field)
      serialze_func = None

      if curr_field_type in self._SERIALIZER_MAPPINGS:
        serialze_func = self._SERIALIZER_MAPPINGS[curr_field_type]
      else:
        raise NotImplementedError(f"Unsupported field type in object. Got: {curr_field_type}")

      try:
        ret[field] = serialze_func(obj, curr_field)
      except AttributeError: # Serialization failed in internal function
        ret[field] = None

    return ret
