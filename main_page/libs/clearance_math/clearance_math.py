import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import datetime
import os
import shutil
import logging
from PIL import Image
from scipy.stats import linregress
from typing import List, Tuple, Type

from ..query_wrappers import pacs_query_wrapper as pacs
from .. import server_config
from .. import dicomlib
from main_page.libs import enums
from main_page import log_util

logger = log_util.get_logger(__name__)


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
  sample_times: List[datetime.date], 
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
    sample_times: a list of date objects containing formation when the bloodsample was taken
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
  # Computes difference between sample and injection time in minutes (timedelta list from timedate)
  delta_times = [ ]
  for sample_time in sample_times:
    time_diff = sample_time - inj_time
    
    diff_in_minutes = (time_diff.seconds / 60) + (time_diff.days * 1440)

    delta_times.append(diff_in_minutes)

  # Determine computation based on study type
  if study_type == enums.StudyType.ONE_SAMPLE_ADULT:
    # In this study_type deltatimes and tec99_cnt lenght is equal to one
    clearance_normalized = (0.213 * delta_times[0] - 104) * np.log(tec99_cnt[0] * BSA / dosis ) + 1.88 * delta_times[0] - 928

  elif study_type == enums.StudyType.ONE_SAMPLE_CHILD:
    """
    OLD METHOD

    two_hours_min = 120
    ml_per_liter = 1000

    GFR                 = -np.log(C_t * ECV / Q_0) * ECV /(time_from_injection * g_of_t)

    GFR = ((2.602 * V120) - 0.273)
    """
    ECV = 5867 * BSA ** (1.1792)

    t = delta_times[0] # Time from start of study till injection
    g_t = 1.01 * np.exp(-0.00011 * t) + 0.538 * np.exp(-0.0178 * t)

    C_t = tec99_cnt[0]
    Q_0 = dosis
    GFR = -np.log((C_t * ECV) / Q_0) * ECV / (t * g_t)

    normalizing_constant = 1.73

    clearance_normalized = GFR * normalizing_constant / BSA

  elif study_type == enums.StudyType.MULTI_SAMPLE:
    log_tec99_cnt = [np.log(x) for x in tec99_cnt]

    slope, intercept, _, _, _ =  linregress(delta_times, log_tec99_cnt)
  
    clearance_1 = (dosis * (-slope)) / np.exp(intercept) 

    clearance =  clearance_1 / (1 + 0.0032 * BSA ** (-1.3) * clearance_1)

    clearance_normalized = clearance * 1.73 / BSA

    # Inulin Korrigering for 24 prøver 
    if delta_times[-1] > 1200:
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
    cprnr: CPR number on the form DDMMYY-CCCC or DDMMYYCCCC, 
           where D - Day, M - Month, Y - year, C - control
  
  Returns: 
    Age as int
  """
  try:
    if len(cprnr) == 11:
      # With dash
      year_of_birth = int(cprnr[4:6])
      month_of_birth = int(cprnr[2:4])
      day_of_birth = int(cprnr[0:2])
      control = int(cprnr[7]) # SINGLE digit
    elif len(cprnr) == 10:
      # Without dash
      year_of_birth = int(cprnr[4:6])
      month_of_birth = int(cprnr[2:4])
      day_of_birth = int(cprnr[0:2])
      control = int(cprnr[6]) # SINGLE digit
    else:
      # Not in cpr-format
      return 1
  except ValueError:
    # Failed int casting, i.e. cpr is not in cpr format
    return 1

  current_time = datetime.datetime.now()
  
  century = []
  
  # Logic and reason can be found at https://www.cpr.dk/media/17534/personnummeret-i-cpr.pdf
  if control in [0,1,2,3] or (control in [4,9] and 37 <= year_of_birth ): 
    century.append(1900)
  elif (control in [4,9] and year_of_birth <= 36) or (control in [5,6,7,8] and year_of_birth <= 57):
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
  Computes the age in days for a given cpr

  Arg:
    cprnr: string, Cpr number of a person born in 20XX

  Remarks:
    This function is intended to be used on people born in the 21th centry, e.g. 20xx
    This function assumes correct formatting and validity of the cpr number 
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


def kidney_function(clearance_norm: float, birthdate: Type[datetime.datetime], gender: Type[enums.Gender]) -> str:
  """
  Calculate the Kidney function compared to their age and gender
  
  Args:
    clearence_norm: computed clearence of the patient
    birthdate: birthdate of patient (format: YYYYMMDD)
    gender: gender of patient
  
  Returns:
    String describing the kidney function of the patient
  """
  # Calulcate age in days and years
  now = datetime.datetime.today()
  
  age_in_days = (now - birthdate).days
  age = int(age_in_days / 365)

  logging.info(f"gender: {gender}")
  logging.info(f"Age: {age}")
  logging.info(f"age in days: {age_in_days}")

  # Calculate Mean GFR
  if age < 2 : # Babies
    Mean_GFR = 10 ** (0.209 * np.log10(age_in_days) + 1.44)
  elif age < 20 : # Childern
    Mean_GFR = 109
  elif age < 40: # Grown ups
    if gender == enums.Gender.MALE:
      Mean_GFR = 111
    else:
      Mean_GFR = 103
  else: # Elders
    if gender == enums.Gender.MALE:
      Mean_GFR = -1.16 * age + 157.8
    else:  
      Female_reference_pct = 0.929
      Mean_GFR = (-1.16 * age + 157.8) * Female_reference_pct

  # Use the mean GFR to calculate the index GFR, Whatever that might be
  index_GFR = 100 * (Mean_GFR - clearance_norm) / Mean_GFR

  # From the index GFR, Conclude on the kidney function
  if index_GFR < 25: 
    return "Normal", index_GFR
  elif index_GFR < 48:
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
  # The remaining CPR-numbers is used by people from the 19-century AKA dead. 

  returnstring = f'{first_digits_year_of_birth}{last_digits_year_of_birth}-{month_of_birth}-{day_of_birth}'

  # logger.debug('Returning with string:{0}'.format(returnstring))
  
  return returnstring 


def _age_string(day_of_birth: str) -> str:
  """

  """
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


def generate_gfr_plot(
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
  hospital_name: str='',
  image_height: float=server_config.PLOT_HEIGHT,
  image_width: float=server_config.PLOT_WIDTH,
  vial_num: str='',
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
    hospital_name   : Full name of the hospital the study is made at
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
  age = int((datetime.datetime.now() - datetime.datetime.strptime(day_of_birth, '%Y-%m-%d')).days / 365) 

  if age < 19:
    return generate_gfr_child_plot(
      weight = weight,
      height = height,
      BSA = BSA,
      clearance = clearance,
      clearance_norm = clearance_norm,
      kidney_function = kidney_function,
      day_of_birth = day_of_birth,
      gender = gender,
      rigs_nr = rigs_nr,
      cpr = cpr,
      method = method,
      name = name,
      history_age = history_age,
      history_clr_n = history_clr_n,
      hosp_dir = hosp_dir,
      hospital_name = hospital_name,
      image_height = image_height,
      image_width = image_width,
      vial_num = vial_num,
      index_gfr = index_gfr,
      injection_date = injection_date,
      procedure_description = procedure_description
    )

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

  titlestring = f"""Undersøgelsen udført på: {hospital_name}
    {procedure_description}"""

  fig.suptitle(titlestring, fontsize=server_config.TITLE_FONT_SIZE)
  
  # Left side - the actual graph
  def calc_mean_gfr_for_todlers(age, threshold):  
    return threshold * 10 ** (0.209 * np.log10(age*365) + 1.44) 
  
  
  x = np.arange(0.000001, 2, 1/365)
  zeros = np.zeros(len(x))
  darkred_y = calc_mean_gfr_for_todlers(x, 0.28)
  light_red_y = calc_mean_gfr_for_todlers(x, 0.52)
  yellow_y = calc_mean_gfr_for_todlers(x, 0.75)
  lightgrey_y = np.full(len(x), ymax)
  refline = calc_mean_gfr_for_todlers(x, 1)
  # convert to list to ensure
  x           = list(x)
  zeros       = list(zeros)
  darkred_y   = list(darkred_y)
  light_red_y = list(light_red_y)
  yellow_y    = list(yellow_y)
  lightgrey_y = list(lightgrey_y)
  refline     = list(refline)

  if gender == 'Mand':
    #after age of 2
    x +=           [2,     20,    20,    40,    xmax]
    zeros +=       [0,     0,     0,     0,     0]
    darkred_y +=   [30.52, 30.52, 31.08, 31.08, 0.28*(-1.16*xmax + 157.8)]
    light_red_y += [56.68, 56.68, 57.72, 57.72, 0.52*(-1.16*xmax + 157.8)]
    yellow_y +=    [81.75, 81.75, 83.25, 83.25, 0.75*(-1.16*xmax + 157.8)]
    lightgrey_y += [ymax,  ymax,  ymax,  ymax,  ymax]
    refline +=     [109, 109,111,111,-1.16* xmax + 157.8]
  
  else:
    x +=           [2,     20,    20,    40,    xmax]
    zeros +=       [0,     0,     0,     0,     0]
    darkred_y +=   [30.52, 30.52, 28.84, 28.84, 0.28*(-1.16*xmax + 157.8) * 0.929]
    light_red_y += [56.68, 56.68, 53.56, 53.56, 0.52*(-1.16*xmax + 157.8) * 0.929]
    yellow_y +=    [81.75, 81.75, 77.25, 77.25, 0.75*(-1.16*xmax + 157.8) * 0.929]
    lightgrey_y += [ymax,  ymax,  ymax,  ymax,  ymax]
    refline +=     [109, 109, 103, 103,(-1.16* xmax + 157.8)* 0.929]

  ax[0].plot(x, refline, label="Reference")
  ax[0].set_xlim(0, xmax)      
  ax[0].set_ylim(0, ymax)
  ax[0].fill_between(x, yellow_y,    lightgrey_y, facecolor='#EFEFEF', label='Normal')
  ax[0].fill_between(x, light_red_y, yellow_y,    facecolor='#FFA71A', label='Moderat nedsat')
  ax[0].fill_between(x, darkred_y,   light_red_y, facecolor='#FBA0A0', label='Middelsvært nedsat')
  ax[0].fill_between(x, zeros,       darkred_y,   facecolor='#F96564', label='Svært nedsat')
  #Reference values


  ax[0].tick_params(labelsize=14)

  # Right side - text information
  reference_percentage = 100 - index_gfr

  print_str = f"""    Navn: {name}\n
    CPR: {cpr}\n
    Undersøgelsedato: {injection_date}\n
    Accession nr.: {rigs_nr}\n
    Køn: {gender}\n
    Alder: {_age_string(day_of_birth)}\n
    Vægt: {weight:.1f} kg\n
    Højde: {height:.0f} cm\n
    Overflade: {BSA:.2f} m²\n
    Sprøjte: {vial_num} \n
    Metode:  {method}\n
    \n
    GFR: {clearance:.0f} ml / min\n
    GFR, normaliseret til 1,73m²: {clearance_norm:.0f} ml / min\n
    Nyrefunktion: {kidney_function}\n
    Nyrefunktion i procent af normal: {reference_percentage:.0f}%
  """

  ax[1].set_xlim(0, 1)
  ax[1].set_ylim(0, 1)
  ax[1].plot([0.05, 0.95], [0.235, 0.235], color='grey')
  ax[1].text(0, -0.075, print_str, ha='left', fontsize=server_config.TEXT_FONT_SIZE) 
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


def generate_gfr_child_plot(
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
  hospital_name: str='',
  image_height: float=server_config.PLOT_HEIGHT,
  image_width: float=server_config.PLOT_WIDTH,
  vial_num: str='',
  index_gfr: float=0.0,
  injection_date=None,
  procedure_description: str='',
  ) -> bytes:

  age = int((datetime.datetime.now() - datetime.datetime.strptime(day_of_birth, '%Y-%m-%d')).days / 365)   

  ymax = 120
  while clearance_norm > ymax:
    ymax += 20

  xmax = 18

  fig, ax = plt.subplots(1, 2)

  # Set meta information
  fig.set_figheight(image_height)
  fig.set_figwidth(image_width)
  
  plt.rc('axes', labelsize=server_config.AXIS_FONT_SIZE)

  titlestring = f"""Undersøgelsen udført på: {hospital_name}
    {procedure_description}"""

  fig.suptitle(titlestring, fontsize=server_config.TITLE_FONT_SIZE)
  


  def calc_mean_gfr_for_todlers(age, threshold):
    return threshold * 10 ** (0.209 * np.log10(age*365) + 1.44) 
  
  x = np.arange(0, 2, 1/365)
  zeros = np.zeros(len(x))
  darkred_y = calc_mean_gfr_for_todlers(x, 0.28)
  light_red_y = calc_mean_gfr_for_todlers(x, 0.52)
  yellow_y = calc_mean_gfr_for_todlers(x, 0.75)
  lightgrey_y = np.full(len(x), ymax)
  refline = calc_mean_gfr_for_todlers(x, 1)
  # convert to list to ensure appending is possible
  x           = list(x)
  zeros       = list(zeros)
  darkred_y   = list(darkred_y)
  light_red_y = list(light_red_y)
  yellow_y    = list(yellow_y)
  lightgrey_y = list(lightgrey_y)
  refline     = list(refline)

  if gender == 'Mand':
    #after age of 2
    x +=           [2,     18,    18    ]
    zeros +=       [0,     0,     0     ]
    darkred_y +=   [30.52, 30.52, 31.08 ]
    light_red_y += [56.68, 56.68, 57.72 ]
    yellow_y +=    [81.75, 81.75, 83.25 ]
    lightgrey_y += [ymax,  ymax,  ymax  ]
    refline +=     [109,   109,   111   ]
    ax[0].plot( x, refline)
  else:
    x +=           [2,     18,    18   ]
    zeros +=       [0,     0,     0    ]
    darkred_y +=   [30.52, 30.52, 28.84] 
    light_red_y += [56.68, 56.68, 53.56] 
    yellow_y +=    [81.75, 81.75, 77.25] 
    lightgrey_y += [ymax,  ymax,  ymax ]
    refline +=     [109,   109,   103  ]

  ax[0].plot(x, refline, label="Reference")
  ax[0].set_xlim(0, xmax)      
  ax[0].set_ylim(0, ymax)
  ax[0].fill_between(x, yellow_y,    lightgrey_y, facecolor='#EFEFEF', label='Normal')
  ax[0].fill_between(x, light_red_y, yellow_y,    facecolor='#FFA71A', label='Moderat nedsat')
  ax[0].fill_between(x, darkred_y,   light_red_y, facecolor='#FBA0A0', label='Middelsvært nedsat')
  ax[0].fill_between(x, zeros,       darkred_y,   facecolor='#F96564', label='Svært nedsat')

  reference_percentage = 100 - index_gfr

  print_str = f"""    Navn: {name}\n
    CPR: {cpr}\n
    Undersøgelsedato: {injection_date}\n
    Accession nr.: {rigs_nr}\n
    Køn: {gender}\n
    Alder: {_age_string(day_of_birth)}\n
    Vægt: {weight:.1f} kg\n
    Højde: {height:.0f} cm\n
    Overflade: {BSA:.2f} m²\n
    Sprøjte: {vial_num} \n
    Metode:  {method}\n
    \n
    GFR: {clearance:.0f} ml / min\n
    GFR, normaliseret til 1,73m²: {clearance_norm:.0f} ml / min\n
    Nyrefunktion: {kidney_function}\n
    Nyrefunktion i procent af normal: {reference_percentage:.0f}%
  """

  ax[1].set_xlim(0, 1)
  ax[1].set_ylim(0, 1)
  ax[1].plot([0.05, 0.95], [0.235, 0.235], color='grey')
  ax[1].text(0, -0.075, print_str, ha='left', fontsize=server_config.TEXT_FONT_SIZE) 
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
  tec99_cnt, 
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
  log_tec99_cnt = [np.log(x) for x in tec99_cnt]

  # Linear Regression
  slope, intercept, r_value, p_value, standard_error = linregress(delta_times, log_tec99_cnt)
  #slope, intercept, r_value, p_value, standard_error = linregress(delta_times, tec99_cnt)

  logger.info(f'max delta:{max(delta_times)}, Slope:{slope}, intercept:{intercept}')

  xmax = max(delta_times) + 10
  x = np.arange(0, xmax, 0.1)
  y = np.exp(slope * x + intercept)

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
  ax[0].set_ylabel('counts', fontsize=server_config.AXIS_FONT_SIZE)
  ax[0].axes.set_yscale('log')
  ax[0].grid(axis='y')
  ax[0].set_xlim(0,xmax)
  ax[0].set_ylim(min(tec99_cnt)*0.9, max(y)*1.1)

  #for i, val in enumerate(log_tec99_cnt):
  for i, val in enumerate(tec99_cnt):
    points              = [val, np.exp(slope * delta_times[i] + intercept)]
    time_of_examination = [delta_times[i], delta_times[i]]
    ax[0].plot(time_of_examination, points, color='black', linestyle='--', zorder=1)
    ax[0].scatter(delta_times[i], np.exp(slope * delta_times[i] + intercept), marker='o', color='red', zorder=2, s=25)
  
  ax[0].plot(x, y, label = 'Regressionslinje', color='red', zorder=2)
  #ax[0].scatter(delta_times, log_tec99_cnt, marker = 'x', s=100, label='Datapunkter', zorder=3)
  ax[0].scatter(delta_times, tec99_cnt, marker = 'x', s=75, label='Datapunkter', zorder=3)

  ax[0].legend(framealpha=1.0, prop={'size': server_config.LEGEND_SIZE})

  # Right side - text information
  r_value_str         = f"R Værdi: {r_value**2:.6f}\n"
  std_err_str         = f"Standard fejl: {standard_error:.6}\n"
  thining_factor_str  = f"Fortyndingsfaktor: {thining_factor}\n"

  text_str = f"""
    {thining_factor_str}
    {r_value_str}
    {std_err_str}
  """
  
  ax[1].axis('off')
  ax[1].text(0, 0.10, text_str, ha='left', fontsize=server_config.TEXT_FONT_SIZE)

  fig.canvas.draw()
  return fig.canvas.tostring_rgb()



