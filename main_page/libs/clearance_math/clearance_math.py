import numpy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas
import datetime
import os, shutil
import logging
from PIL import Image
from scipy.stats import linregress

from ..query_wrappers import pacs_query_wrapper as pacs
from .. import server_config
from .. import dicomlib
from .. import dirmanager

logger = logging.getLogger()

class UNKNOWNMETHODEXEPTION(Exception):
  def __init__(self):
    self.message = 'Unknown Method'
  

def surface_area(height, weight, method = "Haycock"):
  """Estimate the surface area of a human being, based on height and height

  Args:
    height: Height of person in centimeters 
    weight: Weight of person in Kilograms
    method: Method for calculating the Body surface area

  Returns:
    A float estimating the surface area of a human
  """
  if method == "Du Bois": 
      return 0.007184*(weight**0.425)*(height**0.725)
  elif method == "Mosteller":
      return 0.016667*(weight**0.5)*(height**0.5)
  elif method == "Haycock":
      return 0.024265*(weight**0.5378)*(height**0.3964)
  else:
    return -1

def calc_clearance(inj_time, sample_time, tec99_cnt, BSA, dosis, method = "EPV"):
  """
  Calculate the Clearence, using the functions from clearance_function.php

  Argument:
    inj_time: A Date from datetime containing information when injection happened 
    sample_time: a list of dates from datetime containing formation when the bloodsample was taken
    tec99_cnt: A list of int containing the counts from the samples
    BSA: a float, representing body surface area, Use Surface_area
    dosis: A float with calculation of the dosis size, Use dosis

  Optional Arguments
    method for calculating 

  return
    clearance, clearance-normalized
  """
  
  delta_times = [(time - inj_time).seconds / 60 + 86400*(time - inj_time).days for time in sample_time] #timedelta list from timedate
  # for time in sample_time:
  #   #Compute how many minutes between injection and 
  #   delta_times.append((time-inj_time).seconds / 60)

  if method == "EPV":
    #In this method deltatimes and tec99_cnt lenght is equal to one
    #Magical number a credible doctor once found, See documentation
    magic_number_1 = 0.213
    magic_number_2 = 104
    magic_number_3 = 1.88
    magic_number_4 = 928

    clearance_normalized = (magic_number_1 * delta_times[0] - magic_number_2) * numpy.log(tec99_cnt[0] * BSA / dosis ) + magic_number_3 * delta_times[0] - magic_number_4
    
 
  elif method == "EPB":
    #
    #Magical Numbers
    magic_number_1 = 0.008
    two_hours_min = 120
    ml_per_liter = 1000

    P120 = tec99_cnt[0] * numpy.exp(magic_number_1 * (delta_times[0] - two_hours_min))
    V120 = dosis / (P120 * ml_per_liter)

    magic_number_2 = 2.602
    magic_number_3 = 0.273

    GFR = ((magic_number_2 * V120) - magic_number_3)

    normalizing_constant = 1.73

    clearance_normalized = GFR * normalizing_constant / BSA 

  elif method == "Multi-4" :

    log_tec99_cnt = [numpy.log(x) for x in tec99_cnt]

    slope, intercept, _, _, _ =  linregress(delta_times , log_tec99_cnt)
  
    clearance_1 = (dosis * (-slope)) / numpy.exp(intercept) 



    magic_number_1 = 0.0032
    magic_number_2 = 1.3

    clearance =  clearance_1 / ( 1 + magic_number_1 * BSA**(-magic_number_2) * clearance_1)
    
    magic_number_3 = 1.73

    clearance_normalized = clearance * magic_number_3 / BSA

    #Inulin Korrigering for 24 prøver 
    if delta_times[-1] > 1440:
      magic_number_4 = 0.5

      clearance_normalized  = clearance_normalized - 0.5
      clearance = clearance_normalized * BSA * magic_number_3

      return clearance, clearance_normalized

  else:
    raise UNKNOWNMETHODEXEPTION

  #inulin Korrigering 
  magic_number_1 = 3.7
  magic_number_2 = 1.1

  clearance_normalized = (clearance_normalized - magic_number_1) * magic_number_2
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
    year_of_birth = int(cprnr[4:6])
    month_of_birth = int(cprnr[2:4])
    day_of_birth = int(cprnr[0:2])
    Control = int(cprnr[7]) #SINGLE diget
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

def kidney_function(clearance_norm, cpr, birthdate, gender='Kvinde'):
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

  #Calculate Mean GFR
  if age < 2 : # Babies
    magic_number_1 = 0.209
    magic_number_2 = 1.44
    Mean_GFR = 10**(magic_number_1 * numpy.log10(age_in_days) + magic_number_2)
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
    return "Normal"
  elif index_GFR < 48 :
    return "Moderat nedsat"
  elif index_GFR < 72:
    return "Middelsvært nedsat"
  else:
    return "Svært nedsat"

def compute_times(inj_time, times):
  """
  Calculates the times between the injection, and when samples are taken

  Args:
    inj_time : Datetime object with matching 
    times    : [List of Datetime objects with time of sample]

  returns
    A numpy array of the difference in minutes

  Remarks: List comp are REALLY HARD
  """
  return numpy.array([(time - inj_time).seconds / 60 for time in times])

def calculate_birthdate(cpr):
  """
    Calculate birthdate from cpr 

    Return a string on format
      YYYY-MM-DD
  """
  logger.debug('Called with argument:{0}'.format(cpr))

  cpr = cpr.replace('-','')

  day_of_birth = cpr[0:2]
  month_of_birth = cpr[2:4]
  last_digits_year_of_birth = cpr[4:6]
  control = cpr[6]

  # Logic and reason can be found at https://www.cpr.dk/media/17534/personnummeret-i-cpr.pdf
  if control in [0,1,2,3] or (control in [4,9] and 37 <= last_digits_year_of_birth ): 
    first_digits_year_of_birth = 19
  elif (control in [4,9] and last_digits_year_of_birth <= 36) or (control in [5,6,7,8] and last_digits_year_of_birth <= 57):
    first_digits_year_of_birth = 20
  #The remaining CPR-numbers is used by people from the 19-century AKA dead. 

  returnstring = f'{first_digits_year_of_birth}{last_digits_year_of_birth}-{month_of_birth}-{day_of_birth}'

  logger.debug('Returning with string:{0}'.format(returnstring))
  
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
  weight,
  height,
  BSA,
  clearance,
  clearance_norm,
  kidney_function,
  day_of_birth,
  sex,
  rigs_nr,
  name = '',
  cpr = '',
  hosp_dir='',
  history_age = [],
  history_clr_n = [],
  procedure_description = '',
  image_Height = 10.8,
  image_Width = 19.2,
  ):
  """
  Generate GFR plot

  Args:
    weight          : float, Weight of patient
    height          : float, Height of patient
    BSA             : float, Body Surface Area
    clearance       : float, clearance value of examination 
    clearance_norm  : float, Normalized Clearence of examination
    kidney_function : string, describing the kidney function of the patient 
    rigs_nr         : String

  KWargs:
    Name            : string, Name of patient
    cpr             : string, CPR number of Patient 

  Remark:
    Generate as one image, with multiple subplots.
  """

  
  x =           [0, 40, 110]
  zeros =       [0, 0, 0]
  darkred_y =   [25, 25, 10]
  light_red_y = [50, 50, 30]
  yellow_y =    [75, 75, 35]
  lightgrey_y = [160, 160, 160]
  #grey_y =      [130, 130, 130]

  gender = sex
  age = int((datetime.datetime.now() - datetime.datetime.strptime(day_of_birth, '%Y-%m-%d')).days / 365) 

  ymax = 120
  while clearance_norm > ymax:
    ymax += 20

  xmax = 90
  while age > xmax :
    xmax += 20 

  fig, ax = plt.subplots(1, 2)

  # Generate backgroundsage = int(request.POST['age'])second graph
  ax[0].set_xlim(0, xmax)      
  ax[0].set_ylim(0, ymax)
  ax[0].fill_between(x, yellow_y, lightgrey_y, facecolor='#EFEFEF', label='Normal')
  ax[0].fill_between(x, light_red_y, yellow_y, facecolor='#FFA71A', label='Moderat nedsat')
  ax[0].fill_between(x, darkred_y, light_red_y, facecolor='#FBA0A0', label='Middelsvært nedsat')
  ax[0].fill_between(x, zeros, darkred_y, facecolor='#F96564', label='Svært nedsat')
  #ax[0].fill_between(x, lightgrey_y, grey_y, facecolor='#BEBEBE')
  
  titlesize = 8
  labelsize = 18

  #Example on a title string: 
  titlestring = f"""Undersøgelsen udført på: {server_config.hospitals[hosp_dir]}
    {procedure_description}""" 

  fig.suptitle(titlestring, fontsize = 28)
  
  ax[0].tick_params(labelsize = 14)

  #Text setup for graph 1
  name_str            = f"Navn: {name}\n"
  cpr_str             = f"CPR: {cpr}\n"
  gender_str          = f"Køn: {gender}\n"
  age_str             = f"Alder: {_age_string(day_of_birth)}\n"
  weight_str          = f"Vægt: {weight:.1f} kg\n"
  height_str          = f"Højde: {height:.1f} cm\n"
  BSA_str             = f"Overflade: {BSA:.2f} m²\n"
  clearance_str       = f"GFR: {clearance:.1f} ml / min\n"
  clearance_norm_str  = f"GFR, normaliseret til 1,73m²: {clearance_norm:.1f} ml / min\n" 
  kidney_function_str = f"Nyrefunktion: {kidney_function}\n"

  print_str = f"""    {name_str}
    {cpr_str}
    {gender_str}
    {age_str}
    {weight_str}
    {height_str}
    {BSA_str}
    {clearance_str}
    {clearance_norm_str}
    {kidney_function_str}"""

  ax[1].text(0, 0.10, print_str, ha='left', fontsize = 20) 
  ax[1].axis('off')
  
  
  plt.rc('axes', titlesize=titlesize)
  plt.rc('axes', labelsize=labelsize)

  ax[0].set_xlabel('Alder (år)', fontsize = 18)
  ax[0].set_ylabel('GFR (ml/min pr. 1.73m²)', fontsize = 18)
  ax[0].grid(color='black')
  if len(history_age) == len(history_clr_n):
    ax[0].plot(history_age, history_clr_n, marker = 'x', markersize = 8, color = 'blue')
  ax[0].plot(age, clearance_norm, marker = 'o', markersize = 12, color = 'black')
    
  fig.set_figheight(image_Height)
  fig.set_figwidth(image_Width)
  ax[0].legend(framealpha = 1.0 ,prop = {'size' : 18})

  fig.canvas.draw()
  return fig.canvas.tostring_rgb()

def Generate_QA_Picture(tch_cnt, delta_times, thining_factor, image_height = 10.8, image_width = 19.2):
  """
  Generates a picture showing the prediction
  The picture contains a numeric value of  thining factor

  Args:

  kwArgs:
    image_height: float, the height in pixels times 100. So 1 = 100 pixels high
    image_width: float, the width in pixels times 100. So 1 = 100 pixels wide

  Returns:
    A bytestring forming a RBG pictures of scale 1920x1080 (Default size)

  """
  #Math
  log_tch_cnt = [numpy.log(x) for x in tch_cnt]

  slope, intercept, r_value, p_value, standard_error, 


  #Plot generation
  fig, ax = plt.subplot(1,2)

  #Meta information
  fig.set_figheight(image_height)
  fig.set_figwidth(image_width)
  #Text information

  #Picture information
  fig.plot(log_tch_cnt, delta_times, label = 'Datapoints')



  fig.canvas.draw()
  return fig.canvas.tostring_rgb()