from django.views.generic import View
from django.http import FileResponse


from main_page.libs import server_config



class UserGuideView(View):
  def get(self, request):
    """
    Generates the file response for the documentation pdf page
    """



    return FileResponse(
      open(f'{server_config.STATIC_DIR}pdf/brugervejledning-metode.pdf', 'rb'),
      content_type='application/pdf'
    )