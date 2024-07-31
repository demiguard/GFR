from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name="format_cpr")
@stringfilter
def format_cpr(value: str):
  if len(value) == 10:
    return f"{value[:6]}-{value[6:]}"
  return value

@register.filter(name="danish_number")
def danish_number(value):
  if isinstance(value, float):
    value_int = int(value)
    if value_int == value:
      return f"{value_int}"
    else:
      return f"{value}".replace('.', ',')
  return value