import numpy
import matplotlib.pyplot as plt
import pandas
import datetime
from scipy.stats import linregress

class table_info():
  def __init__(self, study_time, cnt, pos, rack, date, run_id):
    self.time = study_time
    self.cnt  = cnt
    self.pos  = pos
    self.rack = rack
    self.date = date
    self.run_id = run_id


def surface_area(height, weight, method = "Du Bois"):
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
      return 0.24265*(weight**0.5378)*(height**0.3964)
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
  
  delta_times = [(time - inj_time).seconds / 60 for time in sample_time] #timedelta list from timedate
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
    magic_number_1 = 5867
    magic_number_2 = 1.1792
    
    ECV = magic_number_1 * (BSA ** magic_number_2)

    magic_number_3 = 1.01
    magic_number_4 = -0.00011
    magic_number_5 = 0.538
    magic_number_6 = -0.0178 
  
    g = magic_number_3 * numpy.exp(magic_number_4 * delta_times[0]) + magic_number_5 * numpy.exp(magic_number_6 * delta_times[0])
    clearence = ( -numpy.log(tec99_cnt[0]* ECV / dosis) * ECV) / (delta_times[0] * g)
    
    magic_number_7 = 1.73

    clearence_normalized =  (clearence * magic_number_7) / BSA
  elif method == "Multi-4" :

    log_tec99_cnt = [numpy.log(x) for x in tec99_cnt]

    slope, intercept, _, _, _ =  linregress(delta_times , log_tec99_cnt)
  
    clearence_reg = (dosis * (-slope)) / numpy.exp(intercept) 

    magic_number_1 = 0.990778
    magic_number_2 = 0.001218

    clearence = magic_number_1 * clearence_reg - magic_number_2 * clearence_reg**2
    
    magic_number_3 = 1.73

    clearence_normalized = clearence * magic_number_3 / BSA

  else:
    print("this shouldnt happen")
    return -1, -1
  return clearence, clearence_normalized

def dosis(inj, fac, stc):
  """Compute dosis based on args.

  Args:
    inj: injection weight
    fac: factor
    stc: standard count

  """
  return int(inj*fac*stc)

def cpr_birth(cpr):
  pass

def cpr_runnr(cpr):
  pass

def cpr_age(cpr):
  pass

def check_cpr(cpr):
  pass

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
  

  # Generate backgrounds for second graph
  ax[1].set_xlim(0, 110)
  ax[1].set_ylim(0, 160)
  ax[1].fill_between(x, zeros, darkred_y, facecolor='#F96564', label='Svært nedsat')
  ax[1].fill_between(x, darkred_y, light_red_y, facecolor='#FBA0A0', label='Middelsvært nedsat')
  ax[1].fill_between(x, light_red_y, yellow_y, facecolor='#FFA71A', label='Moderat nedsat')
  ax[1].fill_between(x, yellow_y, lightgrey_y, facecolor='#EFEFEF', label='Normal')
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
  image_path = "{0}/{1}.png".format(save_dir,rigs_nr)
  if save_fig : 
    plt.savefig(image_path)
  if show_fig :
    plt.show()

  return image_path
