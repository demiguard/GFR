from django.views.generic import View
from django.http import FileResponse
import logging

from main_page import log_util

logger = log_util.get_logger(__name__)


class UserGuideView(View):
  def get(self, request):
    """
    Generates the file response for the documentation pdf page
    """

    logger.info("SOMEONE OPENED THE USERGUIDE!") 

    return FileResponse(
      open('main_page/static/main_page/pdf/brugervejledning.pdf', 'rb'),
      content_type='application/pdf'
    )