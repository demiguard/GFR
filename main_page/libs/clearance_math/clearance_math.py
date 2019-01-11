import numpy
import matplotlib.pyplot as plt
import pandas

def surface_area(height, weight, method = "Du Bois"):
  """Estimate the surface area of a human being, based on height and height

  Args:
    height: Height of person in centimeters 
    weight: Weight of person in Kilograms
    method: Method for calculating the Body surface area

  Returns:

  """
  if method == "Du Bois": 
      return 0.007184*(weight**0.425)*(height**0.725)
  elif method == "Mosteller":
      return 0.016667*(weight**0.5)*(height**0.5)
  elif method == "Haycock":
      return 0.24265*(weight**0.5378)*(height**0.3964)
  else:
    return -1

def dosis(inj, fac, stc):
  """Compute dosis based on args.

  Args:
    inj: injection weight
    fac: factor
    stc: standard count

  """
  pass

def cpr_birth(cpr):
  pass

def cpr_runnr(cpr):
  pass

def cpr_age(cpr):
  pass

def check_cpr(cpr):
  pass

def import_csv(csv_path, dicom, machine =''):
  """
  Imports a generated csv file and extracts the data

  Params:
    machine : Is the machine that made CSV file, used to figure out the encoding of the CSV file
    dicom   : A Dicom object for data to written to. Note that data in the object may be overwritten.

  Returns:
    Error_msg: A string list containing any Error messages
    Changed_tags: A uint list containing all tags that have been written to 

  Remarks:
    It's the user responsibility to save the Dicom object
  """




  Error_msg = []
  Changed_tags = []




  return Error_msg, Changed_tags



def generate_plot(data_points1, data_points2, rigs_nr, hosp_dir='RH', imageHeight = 10.8, imageWidth = 19.2):
  """
  Generate GFR plot

  Args:
    data_points1: Data points for first graph
    data_points2: Data points for second graph



  Remark:
    Generate as one image, with multiple subplots.
  """
  # Generate background fill19.2
  # TODO: These values defin19.2e changed
  save_dir = 'main_page/Graphs/{0}'.format(hosp_dir)

  x =           [0, 40, 100]
  zeros =       [0, 0, 0]
  darkred_y =   [30, 30, 10]
  light_red_y = [50, 50, 30]
  yellow_y =    [75, 75, 35]
  lightgrey_y = [130, 130, 90]
  grey_y =      [130, 130, 130]

  fig, ax = plt.subplots(1, 2)

  # Generate backgrounds for second graph
  ax[1].set_xlim(0, 100)
  ax[1].set_ylim(0, 130)
  ax[1].fill_between(x, zeros, darkred_y, facecolor='#F96564', label='Svært nedsat')
  ax[1].fill_between(x, darkred_y, light_red_y, facecolor='#FBA0A0', label='Middelsvært nedsat')
  ax[1].fill_between(x, light_red_y, yellow_y, facecolor='#FFA71A', label='Moderat nedsat')
  ax[1].fill_between(x, yellow_y, lightgrey_y, facecolor='#EFEFEF', label='Normal')
  ax[1].fill_between(x, lightgrey_y, grey_y, facecolor='#BEBEBE')
  
  # Set titles and labels
  ax[0].set_xlabel('min. efter inj.')
  ax[0].set_ylabel('log(CPM)')
  ax[0].grid(color='black')

  ax[1].set_xlabel('Alder (år)')
  ax[1].set_ylabel('GFR (ml/min pr. 1.73m²)')
  ax[1].grid(color='black')

  fig.set_figheight(imageHeight)
  fig.set_figwidth(imageWidth)
  plt.legend()
  image_path = "{0}/{1}.png".format(save_dir,rigs_nr)
  plt.savefig(image_path)
  
  return image_path
