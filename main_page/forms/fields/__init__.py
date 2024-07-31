# Python3 Standard library
from datetime import date, time
from math import floor, modf

# Third party packages
from typing import Any
from django.forms import DateField, FloatField, TimeField, TextInput
from django.utils.translation import gettext_lazy as _
# Clairvoyance modules


def datify(input_int: int):
  if input_int < 10:
    return f"0{input_int}"
  return str(input_int)

class DanishDateField(DateField):
  input_formats = [
    '%d-%m-%Y',
    '%d/%m/%Y',
    '%Y-%m-%d',
    '%Y/%m/%d',
  ]

  widget=TextInput(attrs={'class' : 'form-control'})

  def prepare_value(self, value: Any) -> Any:
    if isinstance(value, date):
      return f"{datify(value.day)}-{datify(value.month)}-{datify(value.year)}"

    return super().prepare_value(value)

class DanishFloatField(FloatField):
  widget=TextInput(attrs={'class' : 'form-control'})
  def clean(self, value: str) -> Any:
    if value:
      value = value.replace(',', '.')

    return super().clean(value)

  def prepare_value(self, value: Any) -> Any:
    if isinstance(value, float):
      integers = floor(value)
      decimals = value - integers
      if decimals < 0.0005:
        return str(integers)
      else:
        return str(value).replace('.', ',')

    return super().prepare_value(value)

class SecondLessTimeField(TimeField):
  widget=TextInput(attrs={'class' : 'form-control'})

  def prepare_value(self, value: Any) -> Any:
    if isinstance(value, time):
      return f"{datify(value.hour)}:{datify(value.minute)}"

    return super().prepare_value(value)
