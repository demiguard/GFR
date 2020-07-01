from django.views.generic import View
from django.http import FileResponse


class DocumentationView(View):
  def get(self, request):
    """
    Generates the file response for the documentation pdf page
    """
    return FileResponse(
      open('main_page/static/main_page/pdf/GFR_Tc-DTPA-harmonisering_20200221.pdf', 'rb'),
      content_type='application/pdf'
    )