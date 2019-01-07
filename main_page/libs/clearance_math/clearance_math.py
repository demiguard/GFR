import numpy
import matplotlib.pyplot as plt

def surface_area(height, weight):
  """Estimate the surface area of a human being, based on height and height

  Args:
    height:
    weight:

  Returns:

  """
  pass

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

def generate_plot(data_points1, data_points2):
  """
  Generate GFR plot

  Args:
    data_points1: Data points for first graph
    data_points2: Data points for second graph

  Remark:
    Generate as one image, with multiple subplots, to simplify storage as dicom object
  """
  # Generate background fills
  # TODO: These values defining the background fills should possibly be changed
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

  fig.set_figheight(10.8)
  fig.set_figwidth(19.2)
  plt.legend()
  plt.savefig("test.png")
  plt.show()
