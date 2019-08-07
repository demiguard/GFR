from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template import loader
from django.http import HttpResponse

import datetime
import PIL
import logging

from main_page.libs import server_config
from main_page.libs import dicomlib
from main_page.libs.clearance_math import clearance_math

logger = logging.getLogger()


class QAView(LoginRequiredMixin, TemplateView):
  """
  Displays quality accessment of a multi-sample test
  """
  template_name = 'main_page/QA.html'

  def get(self, request, accession_number):
    logger.info('A user have used the QA plot for something')
    try:
      logger.debug(f"{server_config.FIND_RESPONS_DIR}{request.user.department.hospital.short_name}/{accession_number}.dcm")
      dicom_obj = dicomlib.dcmread_wrapper(f"{server_config.FIND_RESPONS_DIR}{request.user.department.hospital.short_name}/{accession_number}.dcm")
      sample_times = []
      tch99_cnt = []

      logger.debug(f'loaded dicom object:\n {dicom_obj}')

      # Use a for loop to get tch count from file 
      for test in dicom_obj.ClearTest:
        if 'SampleTime' in test:
          sample_times.append(datetime.datetime.strptime(test.SampleTime, '%Y%m%d%H%M'))
        
        # Use a for loop to get sample_time
        if 'cpm' in test:
          tch99_cnt.append(float(test.cpm))
    except:
      # Could not load dicom object 'accession_number'.dcm
      logger.error(f'failed to load dicom object for {accession_number}')
      return render(request, self.template_name)

    # Get injection time
    inj_time = datetime.datetime.strptime(dicom_obj.injTime, '%Y%m%d%H%M') 
    
    # Get Thining Factor
    thin_fact = dicom_obj.thiningfactor

    # Create list of timedeltas from timedates
    delta_times = [(time - inj_time).seconds / 60 + 86400 * (time - inj_time).days for time in sample_times]
    
    image_bytes = clearance_math.generate_QA_plot(delta_times, tch99_cnt, thin_fact, accession_number)
    image_path = f"main_page/images/{request.user.department.hospital.short_name}/QA-{accession_number}.png"

    Im = PIL.Image.frombytes('RGB', (1920, 1080), image_bytes)
    Im.save(f"{server_config.IMG_RESPONS_DIR}{request.user.department.hospital.short_name}/QA-{accession_number}.png")

    logger.info(image_path)

    context = {
      'title'     : server_config.SERVER_NAME,
      'version'   : server_config.SERVER_VERSION,
      'image_path' : image_path
    }

    return render(request, self.template_name, context=context)
