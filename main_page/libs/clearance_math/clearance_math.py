import numpy
import matplotlib.pyplot as plt
import pandas
import datetime
import os
from PIL import Image
from scipy.stats import linregress

class table_info():
  def __init__(self, study_time, cnt, pos, rack, date, run_id):
    self.time = study_time
    self.cnt  = cnt
    self.pos  = pos
    self.rack = rack
    self.date = date
    self.run_id = run_id

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
    clearence, clearence-normalized
  """
  
  delta_times = [(time - inj_time).seconds / 60 + 86400*(time - inj_time).days for time in sample_time] #timedelta list from timedate
  # for time in sample_time:
  #   #Compute how many minutes between injection and 
  #   delta_times.append((time-inj_time).seconds / 60)

  if method == "EPV":
    #In this method deltatimes and tec99_cnt lenght is equal to one
    #Magical number a credible doctor once found
    magic_number_1 = 0.213
    magic_number_2 = 104
    magic_number_3 = 1.88
    magic_number_4 = 928

    clearence_normalized = (magic_number_1 * delta_times[0] - magic_number_2) * numpy.log(tec99_cnt[0] * BSA / dosis ) + magic_number_3 * delta_times[0] - magic_number_4
    #
    magic_number_5 = 1.73
    clearence = clearence_normalized * BSA / magic_number_5 
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

    clearence = ((magic_number_2 * V120) - magic_number_3)

    normalizing_constant = 1.73

    clearence_normalized = clearence * normalizing_constant / BSA 

  elif method == "Multi-4" :

    log_tec99_cnt = [numpy.log(x) for x in tec99_cnt]

    slope, intercept, _, _, _ =  linregress(delta_times , log_tec99_cnt)
  
    clearence_1 = (dosis * (-slope)) / numpy.exp(intercept) 



    magic_number_1 = 0.0032
    magic_number_2 = 1.3

    clearence =  clearence_1 / ( 1 + magic_number_1 * BSA**(-magic_number_2) * clearence_1)
    
    magic_number_3 = 1.73

    clearence_normalized = clearence * magic_number_3 / BSA

    if delta_times[-1] > 1440:
      magic_number_4 = 0.5

      clearence             = clearence - 0.5
      clearence_normalized  = clearence_normalized - 0.5

      return clearence, clearence_normalized

  else:
    raise UNKNOWNMETHODEXEPTION

  magic_number_1 = 3.7
  magic_number_2 = 1.1

  clearence = (clearence - magic_number_1) * magic_number_2
  clearence_normalized = (clearence_normalized - magic_number_1) * magic_number_2

  return clearence, clearence_normalized

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
    return 0

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
    return 'Kvinde'
  else:
    return 'Mand'

def kidney_function(clearence_norm, cpr):
  """
    Calculate the Kidney function compared to their age and gender
  Args:
    Clearence_norm: Float, Clearence of the patient
    cpr:            string, cpr matching the patient
  Returns
    Kidney_function: string, Describing the kidney function of the patient
  """
  #Calculate Age and gender from Cpr number
  age = calculate_age(cpr)
  age_in_days = calculate_age_in_days(cpr)
  gender = calculate_sex(cpr)
  
  #Calculate Mean GFR
  if age < 2 : # Babies
    magic_number_1 = 0.209
    magic_number_2 = 1.44
    Mean_GFR = 10**(magic_number_1 * numpy.log10(age_in_days) + magic_number_2)
  elif age < 15 : # Childern
    Mean_GFR = 109
  elif age < 40: # Grown ups
    if gender == 'Mand':
      Mean_GFR = 111
    else:
      Mean_GFR = 103
  else : #Elders
    magic_number_1 = -1.16
    magic_number_2 = 157.8
    if gender == 'Mand':
      Mean_GFR = magic_number_1 * age + magic_number_2
    else:  
      Female_reference_pct = 0.929 #
      Mean_GFR = (magic_number_1 * age + magic_number_2) * Female_reference_pct

  #Use the mean GFR to calculate the index GFR, Whatever that might be
  index_GFR = 100 * (Mean_GFR - clearence_norm) / Mean_GFR
  #From the index GFR, Conclude on the kidney function
  if index_GFR < 25 : 
    return "Normal"
  elif index_GFR < 48 :
    return "Moderat nedsat"
  elif index_GFR < 72:
    return "Middelsvært nedsat"
  else:
    return "Svært nedsat"

def import_csv(csv_path, machine ='', method='Cr-51 Counts'):
  """
  Imports a generated csv file and extracts the data

  Params:
    machine : Is the machine that made CSV file, used to figure out the encoding of the CSV file
    dicom   : A Dicom object for data to written to. Note that data in the object may be overwritten.
    vials   : A list with vials for the dicom

  Returns:
    Error_msg: A string list containing any Error messages
    Changed_tags: A uint list containing all tags that have been written to 

  Remarks:
    It's the user responsibility to save the Dicom object
  """

  data = pandas.read_csv(csv_path)

  table_infos = []

  for i in numpy.arange(data.shape[0]):
    new_table_info = table_info(
      data['Time'][i],
      data[method][i],
      data['Pos'][i],
      data['Rack'][i],
      data['Measurement date & time'][i], 
      data['Run ID'][i]
      )
    table_infos.append(new_table_info)

  return table_infos

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

def generate_plot(
  data_points1,
  data_points2,
  rigs_nr,
  hosp_dir='RH',
  imageHeight = 10.8,
  imageWidth = 19.2,
  save_fig = True,
  show_fig = False
  ):
  """
  Generate GFR plot

  Args:
    data_points1: [[npoints],[npoints]] - numpy.array Data points for first graph 
    data_points2: Data points for second graph



  Remark:
    Generate as one image, with multiple subplots.
  """

  def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    fig.canvas.draw ( )
 
    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    buf = numpy.fromstring ( fig.canvas.tostring_argb(), dtype=numpy.uint8 )
    buf.shape = ( w, h,4 )
 
    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = numpy.roll ( buf, 3, axis = 2 )
    return buf

  def fig2img ( fig ):
    """
    @brief Convert a Matplotlib figure to a PIL Image in RGBA format and return it
    @param fig a matplotlib figure
    @return a Python Imaging Library ( PIL ) image
    """
    # put the figure pixmap into a numpy array
    buf = fig2data ( fig )
    w, h, d = buf.shape
    return Image.frombytes( "RGBA", ( w ,h ), buf.tostring( ) )

  # Generate background fill
  # TODO: These values define changed
  save_dir = 'main_page/static/main_page/images/{0}'.format(hosp_dir)

  x =           [0, 40, 110]
  zeros =       [0, 0, 0]
  darkred_y =   [30, 30, 10]
  light_red_y = [50, 50, 30]
  yellow_y =    [75, 75, 35]
  lightgrey_y = [160, 160, 160]
  #grey_y =      [130, 130, 130]

  fig, ax = plt.subplots(1, 2)
  

  # Generate backgroundsage = int(request.POST['age'])second graph
  ax[1].set_xlim(0, 110)      
  ax[1].set_ylim(0, 160)
  ax[1].fill_between(x, yellow_y, lightgrey_y, facecolor='#EFEFEF', label='Normal')
  ax[1].fill_between(x, light_red_y, yellow_y, facecolor='#FFA71A', label='Moderat nedsat')
  ax[1].fill_between(x, darkred_y, light_red_y, facecolor='#FBA0A0', label='Middelsvært nedsat')
  ax[1].fill_between(x, zeros, darkred_y, facecolor='#F96564', label='Svært nedsat')
  #ax[1].fill_between(x, lightgrey_y, grey_y, facecolor='#BEBEBE')
  
  titlesize = 8
  labelsize = 18

  # Set titles and labels
  ax[0].set_xlabel('min. efter inj.')
  ax[0].set_ylabel('log(CPM)')
  ax[0].grid(color='black')
  plt.rc('axes', titlesize=titlesize)
  plt.rc('axes', labelsize=labelsize)

  ax[1].set_xlabel('Alder (år)')
  ax[1].set_ylabel('GFR (ml/min pr. 1.73m²)')
  ax[1].grid(color='black')

  ax[0].scatter(data_points1[0,:], data_points1[1,:])
  ax[1].scatter(data_points2[0,:], data_points2[1,:])
    
  fig.set_figheight(imageHeight)
  fig.set_figwidth(imageWidth)
  plt.legend()
  image_path = "{0}/{1}.bmp".format(save_dir,rigs_nr)
  if save_fig : 
    im = fig2img(fig)
    im.save(image_path)
  if show_fig :
    plt.show()

  return image_path

def generate_plot_text(
  weight,
  height,
  BSA,
  clearence,
  clearence_norm,
  kidney_function,
  cpr,
  rigs_nr,
  hosp_dir='',
  image_Height = 10.8,
  image_Width = 19.2,
  save_fig = True,
  show_fig = False
  ):
  """
  Generate GFR plot

  Args:
    weight          : float, Weight of patient
    height          : float, Height of patient
    BSA             : float, Body Surface Area
    clearnece       : float, clearence value of examination 
    clearnece_norm  : float, Normalized Clearence of examination
    kidney_function : string, describing the kidney function of the patient 
    cpr             : string, CPR number of Patient 
    rigs_nr         : String

  Remark:
    Generate as one image, with multiple subplots.
  """

  def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    fig.canvas.draw ( )
 
    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    buf = numpy.fromstring ( fig.canvas.tostring_argb(), dtype=numpy.uint8 )
    buf.shape = ( w, h,4 )
 
    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = numpy.roll ( buf, 3, axis = 2 )
    return buf

  def fig2img ( fig ):
    """
    @brief Convert a Matplotlib figure to a PIL Image in RGBA format and return it
    @param fig a matplotlib figure
    @return a Python Imaging Library ( PIL ) image
    """
    # put the figure pixmap into a numpy array
    buf = fig2data ( fig )
    w, h, d = buf.shape
    return Image.frombytes( "RGBA", ( w ,h ), buf.tostring( ) )

  # Generate background fill
  # TODO: These values define changed
  save_dir = 'main_page/static/main_page/images/{0}'.format(hosp_dir)

  x =           [0, 40, 110]
  zeros =       [0, 0, 0]
  darkred_y =   [25, 25, 10]
  light_red_y = [50, 50, 30]
  yellow_y =    [75, 75, 35]
  lightgrey_y = [160, 160, 160]
  #grey_y =      [130, 130, 130]

  gender = calculate_sex(cpr)
  age = calculate_age(cpr)
  
  ymax = 120
  while clearence_norm > ymax:
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

  if hosp_dir:
    if hosp_dir == 'RH':
      fig.suptitle('Undersøgelse udført på Rigshospitalet', fontsize = 30)
    if hosp_dir == 'GL':
      fig.suptitle('Undersøgelse udført på Glostrup Hospital', fontsize = 30)
    if hosp_dir == 'HH':
      fig.suptitle('Undersøgelse udført på Herlev Hospital', fontsize = 30)
    if hosp_dir == 'FH':
      fig.suptitle('Undersøgelse udført på Frederiksberg Hospital', fontsize = 30)
    if hosp_dir == 'BH':
      fig.suptitle('Undersøgelse udført på Bispeberg Hospital', fontsize = 30)
    if hosp_dir == 'HI':
      fig.suptitle('Undersøgelse udført på Hillerød Hospital', fontsize = 30)

  
  ax[0].tick_params(labelsize = 14)

  #Text setup for graph 1
  gender_str          = "Køn: {0}\n\n".format(gender)
  age_str             = "Alder: {0} år\n\n".format(age)
  weight_str          = "Vægt: {0} kg\n\n".format(weight)
  height_str          = "Højde: {0} cm\n\n".format(height)
  BSA_str             = "Overflade: {0:.2f} m²\n\n".format(BSA)
  clearence_str       = "Clearance: {0:.2f} ml / min\n\n".format(clearence)
  clearence_norm_str  = "Clearance, Normaliseret til 1,73: {0:.2f} ml / min\n\n".format(clearence_norm) 
  kidney_function_str = "Nyrefunktion: {0}\n\n".format(kidney_function)

  print_str = "{0}{1}{2}{3}{4}{5}{6}{7}".format(
    gender_str,
    age_str,
    weight_str,
    height_str,
    BSA_str,
    clearence_str,
    clearence_norm_str,
    kidney_function_str
  )

  ax[1].text(0, 0.25, print_str, ha='left', fontsize = 20) 
  ax[1].axis('off')
  
  
  plt.rc('axes', titlesize=titlesize)
  plt.rc('axes', labelsize=labelsize)

  ax[0].set_xlabel('Alder (år)', fontsize = 18)
  ax[0].set_ylabel('GFR (ml/min pr. 1.73m²)', fontsize = 18)
  ax[0].grid(color='black')
  ax[0].plot(age, clearence_norm, marker = 'o', markersize = 12)
    
  fig.set_figheight(image_Height)
  fig.set_figwidth(image_Width)
  ax[0].legend(framealpha = 1.0 ,prop = {'size' : 18})

  if not os.path.exists(save_dir):
    os.mkdir(save_dir)

  image_path = "{0}/{1}.bmp".format(save_dir, rigs_nr)

  if save_fig:
    im = fig2img(fig)
    im.save(image_path)
  if show_fig:
    plt.show()

  return image_path

