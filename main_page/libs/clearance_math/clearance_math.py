import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

import datetime
import os
import shutil
import logging
from PIL import Image
from scipy.stats import linregress
from typing import List, Tuple

from ..query_wrappers import pacs_query_wrapper as pacs
from .. import server_config
from .. import dicomlib
from main_page.libs import enums

logger = logging.getLogger()


def surface_area(height: float, weight: float, method: str="Haycock") -> float:
  """
  Estimate the surface area of a human being, based on height and height

  Args:
    height: Height of person in centimeters 
    weight: Weight of person in Kilograms
    method: Method for calculating the Body surface area

  Returns:
    A float estimating the surface area of a human

  Raises:
    ValueError: if the given method is not supported
  """
  if method == "Du Bois": 
      return 0.007184 * (weight ** 0.425) * (height ** 0.725)
  elif method == "Mosteller":
      return 0.016667 * (weight ** 0.5) * (height ** 0.5)
  elif method == "Haycock":
      return 0.024265 * (weight ** 0.5378) * (height ** 0.3964)
  else:
    raise ValueError(f"Unable to estimate surface area. Got unknown method: '{method}'")


def calc_clearance(
  inj_time: datetime.date, 
  sample_time: List[datetime.date], 
  tec99_cnt: List[float], 
  BSA: float, 
  dosis: float, 
  study_type: enums.StudyType
  ) -> Tuple[float, float]:
  """
  Calculate the clearence as specified in the pdf documentation found under: 
  GFR/main_page/static/main_page/pdf/GFR_Tc-DTPA-harmonisering_20190223.pdf

  Args:
    inj_time: A date object containing information when the injection happened 
    sample_time: a list of date objects containing formation when the bloodsample was taken
    tec99_cnt: A list of floats containing the counts from the samples
    BSA: a float, the estimated body surface area, see function: surface_area
    dosis: A float with calculation of the dosis size, see function: dosis
    study_type: the type of study performed, e.g. 'En blodprøve, Voken', etc.

  Returns:
    Tuple of float w/ clearance and clearance-normalized
  
  Remarks:
    The constants throughout the below calculations are specified in
    the documentation pdf. "We" (Simon & Christoffer) didn't come up with
    these, they were found by doctors so just trust them...
  """
  # timedelta list from timedate
  # TODO: WTF is this list comprehension doing???....
  delta_times = [(time - inj_time).seconds / 60 + 86400 * (time - inj_time).days for time in sample_time]

  if study_type == enums.StudyType.ONE_SAMPLE_ADULT:
    # In this study_type deltatimes and tec99_cnt lenght is equal to one
    clearance_normalized = (0.213 * delta_times[0] - 104) * np.log(tec99_cnt[0] * BSA / dosis ) + 1.88 * delta_times[0] - 928

  elif study_type == enums.StudyType.ONE_SAMPLE_CHILD:
    two_hours_min = 120
    ml_per_liter = 1000

    P120 = tec99_cnt[0] * np.exp(0.008 * (delta_times[0] - two_hours_min))
    V120 = dosis / (P120 * ml_per_liter)

    GFR = ((2.602 * V120) - 0.273)

    normalizing_constant = 1.73

    clearance_normalized = GFR * normalizing_constant / BSA

  elif study_type == enums.StudyType.MULTI_SAMPLE:
    log_tec99_cnt = [np.log(x) for x in tec99_cnt]

    slope, intercept, _, _, _ =  linregress(delta_times, log_tec99_cnt)
  
    clearance_1 = (dosis * (-slope)) / np.exp(intercept) 

    clearance =  clearance_1 / (1 + 0.0032 * BSA ** (-1.3) * clearance_1)

    clearance_normalized = clearance * 1.73 / BSA

    # Inulin Korrigering for 24 prøver 
    if delta_times[-1] > 1440:
      clearance_normalized  = clearance_normalized - 0.5
      clearance = clearance_normalized * BSA * 1.73

      return clearance, clearance_normalized
  else:
    raise ValueError(f"Unable to compute clearance. Got unknown study_type: '{study_type}'")

  # inulin Korrigering
  clearance_normalized = (clearance_normalized - 3.7) * 1.1
  clearance = clearance_normalized * BSA / 1.73

  return clearance, clearance_normalized

def dosis(inj, fac, stc):
  """Compute dosis based on args.

  Args:
    inj: injection weight
    fac: factor
    stc: standard count

  """
  return int(inj*fac*stc)

def calculate_age(cprnr):
  """
  Determine the age of a patient based on CPR
  
  Params:
    cprnr: CPR number on the form DDMMYY-CCCC, where D - Day, M - Month, Y - year, C - control
  
  Returns: 
    The age in int format

  """
  try:
    if len(cprnr) == 11:
      year_of_birth = int(cprnr[4:6])
      month_of_birth = int(cprnr[2:4])
      day_of_birth = int(cprnr[0:2])
      Control = int(cprnr[7]) #SINGLE diget
    elif len(cprnr) == 10:
      year_of_birth = int(cprnr[4:6])
      month_of_birth = int(cprnr[2:4])
      day_of_birth = int(cprnr[0:2])
      Control = int(cprnr[6]) #SINGLE diget

  except ValueError:
    return 1

  current_time = datetime.datetime.now()
  
  century = []
  
  # Logic and reason can be found at https://www.cpr.dk/media/17534/personnummeret-i-cpr.pdf
  if Control in [0,1,2,3] or (Control in [4,9] and 37 <= year_of_birth ): 
    century.append(1900)
  elif (Control in [4,9] and year_of_birth <= 36) or (Control in [5,6,7,8] and year_of_birth <= 57):
    century.append(2000)
  #The remaining CPR-numbers is used by people from the 19-century AKA dead. 

# Age with no birthday
  if 2000 in century :
    age = current_time.year - 2000 - year_of_birth - 1
  elif 1900 in century : 
    age = current_time.year - 1900 - year_of_birth - 1  
  else:  #This is only used if resurrect dead people, Necromancy I guess
    age = current_time.year - 1800 - year_of_birth - 1

# Have you had your birthday this year

  if month_of_birth < current_time.month:
    age += 1
  elif current_time.month == month_of_birth and day_of_birth <= current_time.day:
    age += 1

  return age

def calculate_age_in_days(cpr):
  """
  DO NOT USE THIS FUNCTION ON PEOPLE BORN IN THE TWENTIES CENTURY
  IT'S INTENTED FOR PEOPLE BORN IN 20XX

  Arg:
    cprnr: string, Cpr number of a person born in 20XX

  REMARKS: DONT BE DUMB, READ FUNCTION DECRIPTION
  YES, ALL CAPS IS NECESSARY, DONT YOU DARE QUESTION MY EGO
  """
  day_of_birth = int(cpr[0:2])
  month_of_birth = int(cpr[2:4])
  year_of_birth = int(cpr[4:6]) + 2000
  birthdate = datetime.date(year_of_birth, month_of_birth, day_of_birth)
  today = datetime.date.today()

  return (today - birthdate).days

def calculate_sex(cprnr):
  """
  Determine wheter the patient is male or female
  """
  if int(cprnr[-1]) % 2 == 0:
    return 'F'
  else:
    return 'M'

def kidney_function(clearance_norm, cpr, birthdate, gender):
  """expression
    Calculate the Kidney function compared to their age and gender
  Args:
    Clearence_norm: Float, Clearence of the patient
    cpr:            string, cpr matching the patient
  Returns
    Kidney_function: string, Describing the kidney function of the patient
  """
  #Calculate Age and gender from Cpr number
  try:
    age = calculate_age(cpr)
    age_in_days = calculate_age_in_days(cpr)
    gender = calculate_sex(cpr)
  except:
    now = datetime.datetime.today()
    birthdate = datetime.datetime.strptime(birthdate, '%Y-%m-%d')

    age_in_days = (now - birthdate).days
    age = int((now - birthdate).days / 365)
    gender = gender

  logging.info(f"gender: {gender}")
  logging.info(f"Age: {age}")
  logging.info(f"age in days: {age_in_days}")

  #Calculate Mean GFR
  if age < 2 : # Babies
    magic_number_1 = 0.209
    magic_number_2 = 1.44
    Mean_GFR = 10**(magic_number_1 * np.log10(age_in_days) + magic_number_2)
  elif age < 15 : # Childern
    Mean_GFR = 109
  elif age < 40: # Grown ups
    if gender == 'M':
      Mean_GFR = 111
    else:
      Mean_GFR = 103
  else : #Elders
    magic_number_1 = -1.16
    magic_number_2 = 157.8
    if gender == 'M':
      Mean_GFR = magic_number_1 * age + magic_number_2
    else:  
      Female_reference_pct = 0.929 #
      Mean_GFR = (magic_number_1 * age + magic_number_2) * Female_reference_pct

  #Use the mean GFR to calculate the index GFR, Whatever that might be
  index_GFR = 100 * (Mean_GFR - clearance_norm) / Mean_GFR
  #From the index GFR, Conclude on the kidney function
  if index_GFR < 25 : 
    return "Normal", index_GFR
  elif index_GFR < 48 :
    return "Moderat nedsat", index_GFR
  elif index_GFR < 72:
    return "Middelsvært nedsat", index_GFR
  else:
    return "Svært nedsat", index_GFR

def compute_times(inj_time, times):
  """
  Calculates the times between the injection, and when samples are taken

  Args:
    inj_time : Datetime object with matching 
    times    : List of Datetime objects with time of sample

  returns
    A np array of the difference in minutes
  """
  return np.array([(time - inj_time).seconds / 60 for time in times])

def calculate_birthdate(cpr):
  """
    Calculate birthdate from cpr 

    Return a string on format
      YYYY-MM-DD
  """
  #logger.debug('Called with argument:{0}'.format(cpr))

  cpr = cpr.replace('-','')

  day_of_birth = cpr[0:2] # string
  month_of_birth = cpr[2:4] #string 
  last_digits_year_of_birth = cpr[4:6] #string
  control = cpr[6] #string

  # Logic and reason can be found at https://www.cpr.dk/media/17534/personnummeret-i-cpr.pdf
  if int(control) in [0,1,2,3] or (int(control) in [4,9] and 37 <= int(last_digits_year_of_birth)): 
    first_digits_year_of_birth = '19'
  elif (int(control) in [4,9] and int(last_digits_year_of_birth) <= 36) or (int(control) in [5,6,7,8] and int(last_digits_year_of_birth) <= 57):
    first_digits_year_of_birth = '20'
  else:
    raise ValueError('Dead person Detected')
  #The remaining CPR-numbers is used by people from the 19-century AKA dead. 

  returnstring = f'{first_digits_year_of_birth}{last_digits_year_of_birth}-{month_of_birth}-{day_of_birth}'

  #logger.debug('Returning with string:{0}'.format(returnstring))
  
  return returnstring 


def _age_string(day_of_birth):

  logger.debug('Called with argument:{0}'.format(day_of_birth))

  today = datetime.datetime.today()
  date_of_birth = datetime.datetime.strptime(day_of_birth, '%Y-%m-%d')

  diff = today - date_of_birth

  age_in_years = int(diff.days / 365)
  if age_in_years > 2:
    return '{0} år'.format(age_in_years)
  else:
    days_since_last_birthday = diff.days % 365
    months_since_last_birthday = int(days_since_last_birthday / 30)

    month_str = 'måneder'
    if months_since_last_birthday == 1:
      month_str = 'måned'
    elif months_since_last_birthday == 0:
      month_str = ''

    if age_in_years > 0 and not(months_since_last_birthday == 0) :
      return '{0} år, {1} {2}'.format(age_in_years, months_since_last_birthday, month_str)
    elif age_in_years > 0:
      return '{0} år'.format(age_in_years)
    elif not(months_since_last_birthday == 0):
      return '{0} {1}'.format(months_since_last_birthday, month_str)
    else:
      return '{0} Dage'.format(diff.days)


def generate_plot_text(
  weight: float,
  height: float,
  BSA: float,
  clearance: float,
  clearance_norm: float,
  kidney_function: str,
  day_of_birth: str,
  gender: str,
  rigs_nr: str,
  cpr: str='',
  method: str='',
  name: str='',
  history_age=[],
  history_clr_n=[],
  hosp_dir: str='',
  image_height: float=server_config.PLOT_HEIGHT,
  image_width: float=server_config.PLOT_WIDTH,
  index_gfr: float=0.0,
  injection_date=None,
  procedure_description: str='',
  ) -> bytes:
  """
  Generates GFR plot

  Args:
    weight          : float, Weight of patient
    height          : float, Height of patient
    BSA             : float, Body Surface Area
    clearance       : float, clearance value of examination 
    clearance_norm  : float, Normalized Clearence of examination
    kidney_function : string, describing the kidney function of the patient 
    rigs_nr         : String
    
  KWargs:
    cpr             : string, CPR number of Patient 
    method          :
    name            : string, Name of patient
    history_age     :
    history_clr_n   :
    hosp_dir        :
    image_height    :
    image_width     :
    index_gfr       :
    injection_date  :
    procedure_description:

  Returns:
    bytes object containing the generated plot

  Remark:
    Generate as one image, with multiple subplots.
  """
  x =           [ 0,   40, 110]
  zeros =       [ 0,    0,   0]
  darkred_y =   [ 25,  25,  10]
  light_red_y = [ 50,  50,  30]
  yellow_y =    [ 75,  75,  35]
  lightgrey_y = [160, 160, 160]

  age = int((datetime.datetime.now() - datetime.datetime.strptime(day_of_birth, '%Y-%m-%d')).days / 365) 

  ymax = 120
  while clearance_norm > ymax:
    ymax += 20

  xmax = 90
  while age > xmax :
    xmax += 20 

  # Generate plot
  fig, ax = plt.subplots(1, 2)

  # Set meta information
  fig.set_figheight(image_height)
  fig.set_figwidth(image_width)
  
  plt.rc('axes', labelsize=server_config.AXIS_FONT_SIZE)

  titlestring = f"""Undersøgelsen udført på: {server_config.HOSPITALS[hosp_dir]}
    {procedure_description}"""

  fig.suptitle(titlestring, fontsize=server_config.TITLE_FONT_SIZE)
  
  # Left side - the actual graph
  ax[0].set_xlim(0, xmax)      
  ax[0].set_ylim(0, ymax)
  ax[0].fill_between(x, yellow_y,    lightgrey_y, facecolor='#EFEFEF', label='Normal')
  ax[0].fill_between(x, light_red_y, yellow_y,    facecolor='#FFA71A', label='Moderat nedsat')
  ax[0].fill_between(x, darkred_y,   light_red_y, facecolor='#FBA0A0', label='Middelsvært nedsat')
  ax[0].fill_between(x, zeros,       darkred_y,   facecolor='#F96564', label='Svært nedsat')

  ax[0].tick_params(labelsize=14)

  # Right side - text information
  reference_percentage = 100 - index_gfr

  print_str = f"""    Navn: {name}\n
    CPR: {cpr}\n
    Undersøgelsedato: {injection_date}\n
    Accession Nummer: {rigs_nr}\n
    Køn: {gender}\n
    Alder: {_age_string(day_of_birth)}\n
    Vægt: {weight:.1f} kg\n
    Højde: {height:.1f} cm\n
    Overflade: {BSA:.2f} m²\n
    Metode:  {method}\n
    GFR: {clearance:.1f} ml / min\n
    GFR, normaliseret til 1,73m²: {clearance_norm:.1f} ml / min\n
    Nyrefunktion: {kidney_function}\n
    Nyrefunktion ift. Reference Patient: {reference_percentage:.1f}%
  """

  ax[1].text(0, 0.00, print_str, ha='left', fontsize=server_config.TEXT_FONT_SIZE) 
  ax[1].axis('off')

  ax[0].set_xlabel('Alder (år)', fontsize=server_config.AXIS_FONT_SIZE)
  ax[0].set_ylabel('GFR (ml/min pr. 1.73m²)', fontsize=server_config.AXIS_FONT_SIZE)
  ax[0].grid(color='black')
  if len(history_age) == len(history_clr_n):
    ax[0].scatter(history_age, history_clr_n, marker='x', s=8, color='blue')
  ax[0].plot(age, clearance_norm, marker='o', markersize=12, color='black')
  
  ax[0].legend(framealpha=1.0 , prop={'size': server_config.LEGEND_SIZE})

  fig.canvas.draw()
  return fig.canvas.tostring_rgb()


def generate_QA_plot(
  delta_times, 
  tch_cnt, 
  thining_factor, 
  accession_number, 
  image_height=server_config.PLOT_HEIGHT, 
  image_width=server_config.PLOT_WIDTH
  ):
  """
  Generates a plot showing the predicted regression line

  Args:
    delta_times:
    tch_cnt:
    thining_factor:
    accession_number:

  kwArgs:
    image_height: float, the height in pixels times 100. So 1 = 100 pixels high
    image_width: float, the width in pixels times 100. So 1 = 100 pixels wide

  Returns:
    A bytestring forming a RBG pictures of scale 1920x1080 (Default size)
  """
  # Log of tec-count as the formula calls for
  log_tec99_cnt = [np.log(x) for x in tch_cnt]

  # Linear Regression
  slope, intercept, r_value, p_value, standard_error = linregress(delta_times, log_tec99_cnt)

  logger.info(f'max delta:{max(delta_times)}, Slope:{slope}, intercept:{intercept}')

  x = np.arange(min(delta_times), max(delta_times), 0.1)
  y = slope * x + intercept

  # Plot generation
  fig, ax = plt.subplots(nrows = 1, ncols=2)

  # Set meta information
  plt.rc('axes', labelsize=server_config.AXIS_FONT_SIZE)

  plot_title = f"Regressionsanalyse for {accession_number}"
  fig.suptitle(plot_title, fontsize=server_config.TITLE_FONT_SIZE)

  fig.set_figheight(image_height)
  fig.set_figwidth(image_width)

  # Left side - the plot
  ax[0].tick_params(labelsize=14) # Axis tick size
  ax[0].set_xlabel('Tid i minutter', fontsize=server_config.AXIS_FONT_SIZE)
  ax[0].set_ylabel('log(tec99 count)', fontsize=server_config.AXIS_FONT_SIZE)
  
  for i, val in enumerate(log_tec99_cnt):
    points              = [val, slope * delta_times[i] + intercept]
    time_of_examination = [delta_times[i], delta_times[i]]
    ax[0].plot(time_of_examination, points, color='black', linestyle='--', zorder=1)
    ax[0].scatter(delta_times[i], slope * delta_times[i] + intercept, marker='o', color='red', zorder=2, s=25)
  
  ax[0].plot(x, y, label = 'Regressionslinje', color='red', zorder=2)
  ax[0].scatter(delta_times, log_tec99_cnt, marker = 'x', s=100, label='Datapunkter', zorder=3)

  ax[0].legend(framealpha=1.0, prop={'size': server_config.LEGEND_SIZE})

  # Right side - text information
  p_value_str         = f"P Værdi: {p_value:.6f}\n" 
  r_value_str         = f"R Værdi: {r_value:.6f}\n"
  std_err_str         = f"Standard fejl: {standard_error:.6}\n"
  thining_factor_str  = f"Fortyndingsfaktor: {thining_factor}\n"

  text_str = f"""
    {thining_factor_str}
    {p_value_str}
    {r_value_str}
    {std_err_str}
  """
  
  ax[1].axis('off')
  ax[1].text(0, 0.10, text_str, ha='left', fontsize=server_config.TEXT_FONT_SIZE)

  fig.canvas.draw()
  return fig.canvas.tostring_rgb()