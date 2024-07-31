"""Module for generate images, note that this is the controller class for
building images, ie make sure that the images are put the correct place."""

# Python Standard library
from typing import List

# Third party packages
from django.conf import settings

from PIL import Image

# Clairvoyance modules
from main_page.models import GFRStudy, InjectionSample
from main_page.libs.server_config import PLOT_HEIGHT, PLOT_WIDTH
from main_page.libs.clearance_math.plotting import generate_plot_from_study

def get_standard_plot_path(study: GFRStudy):
  file_path = f"main_page/images/{study.Department.hospital.short_name}/{study.AccessionNumber}.png"
  save_path = f"{settings.STATIC_ROOT}{file_path}"

  return file_path, save_path



def generate_standard_plot(study: GFRStudy, samples: List[InjectionSample] ):
  """This creates a static image and then saves it at a path"""

  if study.GFR is None:
    study.derive(samples)

  plot_bytes = generate_plot_from_study(study)

  image = Image.frombytes('RGB', (1920,1080), plot_bytes)
  file_path, save_path = get_standard_plot_path(study)

  image.save(save_path)

  return file_path

def generate_QA_plot():
  pass