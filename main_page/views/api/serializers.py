from django.db import models

from typing import Type, Dict


class JSONSerializer:
  CONTINUATION_FIELDS = {
    models.ForeignKey,
    models.OneToOneField,
  }

  def __init__(self) -> None:
    self._SERIALIZER_MAPPINGS = {
      models.ForeignKey: self.__serialize_ForeignKey,
      models.OneToOneField: self.__serialize_OneToOneField,
      models.AutoField: self.__serialize_AutoField,
      models.CharField: self.__serialize_CharField,
      models.FloatField: self.__serialize_FloatField,
      models.DateTimeField: self.__serialize_DateTimeField,
      models.DateField: self.__serialize_DateField,
      models.BooleanField: self.__serialize_BooleanField
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

  def __serialize_BooleanField(self, obj: Type[models.Model], field: Type[models.BooleanField]) -> str:
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
        # Ignore weird internal django fields, since they have no .name
        continue
    
    if fields:
      if not isinstance(fields, list):
        raise ValueError(f"Invalid object type for 'fields'. Expected: '{list}', Got: {type(fields)}")

      # TODO: Extend this to handle the new dot notation
      # for field in fields:
      #   if field not in obj_fields:
      #     raise ValueError(f"Unable to find field: '{field}', in the objects actual fields.")
    else:
      fields = list(obj_fields)

    # Serialize each field
    ret = { }
    for field in fields:
      curr_obj = obj
      curr_field_name = field
      
      if '.' in field:
        field_split = field.split('.')

        # Continuously update curr_obj
        for field_component in field_split:
          if curr_obj == None:
            continue
          inner_field = curr_obj._meta.get_field(field_component)
          inner_field_type = type(inner_field)

          if inner_field_type not in self.CONTINUATION_FIELDS:
            curr_field_name = field_component
            break

          try:
            inner_pk = getattr(curr_obj, inner_field.name).pk
          except AttributeError:
            continue

          # NOTE: This is kinda hacky, for details see function specifications at: 
          # https://github.com/django/django/blob/7f612eda80db1c1c8e502aced54c2062080eae46/django/db/models/fields/related.py#L444
          to_model = inner_field.related_model

          curr_obj = to_model.objects.get(pk=inner_pk)
      
      curr_field = curr_obj._meta.get_field(curr_field_name)
      curr_field_type = type(curr_field)
      serialze_func = None

      if curr_field_type in self._SERIALIZER_MAPPINGS:
        serialze_func = self._SERIALIZER_MAPPINGS[curr_field_type]
      else:
        raise NotImplementedError(f"Unsupported field type in object. Got: {curr_field_type}")

      try:
        ret[field] = serialze_func(curr_obj, curr_field)
      except AttributeError: # Serialization failed in internal function
        ret[field] = None

    return ret
