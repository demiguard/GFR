from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class InsufficientPermissionsView(TemplateView):
  template_name = "main_page/insufficient_permissions.html"

  def get(self,request):
    
    context = {}
    
    return render(request, self.template_name, context=context)