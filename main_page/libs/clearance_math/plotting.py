from pydicom import Dataset, Sequence
from dataclasses import dataclass, field
from pprint import pprint
from typing import List, Optional, Tuple, Union

import numpy
import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator
from matplotlib.dates import DateFormatter, DateLocator, MonthLocator

from main_page.libs import formatting
from main_page.libs import enums
from main_page.libs import server_config
from main_page.libs.clearance_math.clearance_math import kidney_function, surface_area, _age_string, calculate_birthdate, calc_mean_gfr_for_toddlers


# Plotting constants
SAMPLE_COLOR = "blue"
REFERENCE_COLOR = "black"
TEXT_LINE_COLOR = "grey"

KIDNEY_FUNCTION_NORMAL_COLOR = "#EFEFEF"
KIDNEY_FUNCTION_MINORLY_REDUCED_COLOR = "#FFA71A"
KIDNEY_FUNCTION_REDUCED_COLOR = "#FBA0A0"
KIDNEY_FUNCTION_MAJORLY_REDUCED_COLOR = "#F96564"

@dataclass
class GraphTexts:
  figure_text_name: str
  figure_text_patient_id: str
  figure_text_date_of_examination: str
  figure_text_accession_number: str
  figure_text_gender: str
  figure_text_age: str
  figure_text_weight: str
  figure_text_height: str
  figure_text_body_surface: str
  figure_text_vial_number: str
  figure_text_method: str
  figure_text_gfr: str
  figure_text_gfr_normalized: str
  figure_text_kidney_function: str
  figure_text_reference_percentage: str
  kidney_function_normal : str
  kidney_function_lightly_reduced : str
  kidney_function_reduced : str
  kidney_function_majorly_reduced: str
  kidney_function_reference: str
  historic_table_date: str
  historic_table_gfr: str
  historic_table_gfr_normalized: str
  historic_table_reference: str
  legend_gfr: str
  title_hospital_prefix: str
  x_axis_label: str
  x_axis_historic_label: str
  x_axis_toddler_tick_suffix: str
  x_axis_toddler_label: str
  y_axis_label: str

# Move this into the database.
graph_texts = GraphTexts(
  figure_text_accession_number="Accession nr.:",
  figure_text_age="Alder:",
  figure_text_body_surface="Overflade:",
  figure_text_date_of_examination="Undersøgelsedato:",
  figure_text_gender="Køn:",
  figure_text_gfr="GFR:",
  figure_text_gfr_normalized="GFR, normaliseret til 1,73m²:",
  figure_text_height="Højde:",
  figure_text_kidney_function="Nyrefunktion:",
  figure_text_method="Metode:",
  figure_text_name="Navn:",
  figure_text_patient_id="CPR:",
  figure_text_reference_percentage="Nyrefunktion i procent af normal:",
  figure_text_vial_number="Sprøjte:",
  figure_text_weight="Vægt:",
  kidney_function_lightly_reduced="Moderat nedsat",
  kidney_function_reduced="Middelsvært nedsat",
  kidney_function_majorly_reduced="Svært nedsat",
  kidney_function_normal="Normal",
  kidney_function_reference="Reference",
  historic_table_date="Dato",
  historic_table_gfr="GFR",
  historic_table_gfr_normalized="GFR, norm.",
  historic_table_reference="% af ref",
  legend_gfr="GFR",
  title_hospital_prefix="Undersøgelse udført på:",
  x_axis_label="Alder (år)",
  x_axis_historic_label="Prøve Datoer",
  x_axis_toddler_label="Alder (dage)",
  x_axis_toddler_tick_suffix="Måneder",
  y_axis_label="GFR (ml/min pr. 1.73m²)",
)


@dataclass
class FigureTextDataClass:
  """This class represents the data that is written in side of an image."""
  # The code here is, what you call, fucking ugly.
  # But it's just extracting a bunch of data values.

  name : str
  CPR : str
  injection_date : str
  accession_number : str
  age : str
  gender : str
  height : str
  weight : str
  body_surface_area : str
  vial_number : str
  gfr_method : str
  clearance : str
  clearance_normalized : str
  kidney_result : str
  reference_percentage : str

  @classmethod
  def from_dataset(cls, dataset : Dataset) -> 'FigureTextDataClass':
    """Alternative constructor from a dataset

    Args:
        dataset (Dataset): Dataset to construct from

    Returns:
        FigureTextDataClass: dataclass ready to stringed
    """
    name = formatting.person_name_to_name(dataset.PatientName)
    cpr = formatting.format_cpr(dataset.PatientID)
    injection_date =  datetime.datetime.strptime(dataset.injTime,"%Y%m%d%H%M").strftime('%d-%b-%Y')
    dateOfBirth = calculate_birthdate(cpr)
    dateTimeOfBirth = datetime.datetime.strptime(dataset.PatientBirthDate, "%Y%m%d")
    accession_number = dataset.AccessionNumber
    if dataset.PatientSex == 'M':
      gender = enums.GENDER_NAMINGS[0]
      gender_enum = enums.Gender.MALE
    else:
      gender = enums.GENDER_NAMINGS[1]
      gender_enum = enums.Gender.FEMALE
    age = _age_string(dateOfBirth)
    height = f"{(dataset.PatientSize * 100):.0f}" # type: ignore
    weight = f"{(dataset.PatientWeight):.1f}"
    body_surface_area = f"{surface_area(dataset.PatientSize * 100, dataset.PatientWeight):.2f}" #type: ignore # Don't Care about numerical stability
    vial_number = f"{dataset.VialNumber}"
    gfr_method = f"{dataset.GFRMethod}"
    clearance = f"{dataset.clearance:.0f}"
    clearance_normalized = f"{dataset.normClear:.0f}"
    kidney_result, reference_percentage_number = kidney_function(
      dataset.normClear,
      dateTimeOfBirth,
      gender_enum
    )

    reference_percentage = f"{(100.0 - reference_percentage_number):.1f}"

    return cls(
      name, cpr, injection_date, accession_number, age, gender, height, weight,
      body_surface_area, vial_number, gfr_method, clearance, clearance_normalized,
      kidney_result, reference_percentage
    )

  def __str__(self) -> str:
    string = f"""\n
    {graph_texts.figure_text_name} {self.name}\n
    {graph_texts.figure_text_patient_id} {self.CPR}\n
    {graph_texts.figure_text_date_of_examination} {self.injection_date}\n
    {graph_texts.figure_text_accession_number} {self.accession_number}\n
    {graph_texts.figure_text_gender} {self.gender}\n
    {graph_texts.figure_text_age} {self.age}\n
    {graph_texts.figure_text_weight} {self.weight} kg\n
    {graph_texts.figure_text_height} {self.height} cm\n
    {graph_texts.figure_text_body_surface} {self.body_surface_area} m²\n
    {graph_texts.figure_text_vial_number} {self.vial_number} \n
    {graph_texts.figure_text_method} {self.gfr_method}\n
    \n
    {graph_texts.figure_text_gfr} {self.clearance} ml / min\n
    {graph_texts.figure_text_gfr_normalized} {self.clearance_normalized} ml / min\n
    {graph_texts.figure_text_kidney_function} {self.kidney_result}\n
    {graph_texts.figure_text_reference_percentage} {self.reference_percentage}%
    """
    return string

@dataclass
class HistoricFigureTextDataClass:
  name : str
  CPR : str
  injection_date : str
  accession_number : str
  age : str
  gender : str
  height : str
  weight : str
  body_surface_area : str
  vial_number : str
  gfr_method : str
  clearance : str
  clearance_normalized : str
  kidney_result : str
  reference_percentage : str
  historic: list[Tuple[str,str,str,str]] = field(default_factory=list)

  @classmethod
  def from_dataset(cls, dataset : Dataset) -> 'HistoricFigureTextDataClass':
    """Alternative constructor from a dataset

    Args:
        dataset (Dataset): Dataset to construct from

    Returns:
        FigureTextDataClass: dataclass ready to stringed
    """
    name = formatting.person_name_to_name(dataset.PatientName)
    cpr = formatting.format_cpr(dataset.PatientID)
    injection_date =  datetime.datetime.strptime(dataset.injTime,"%Y%m%d%H%M").strftime('%d-%b-%Y')
    dateOfBirth = calculate_birthdate(cpr)
    dateTimeOfBirth = datetime.datetime.strptime(dataset.PatientBirthDate, "%Y%m%d")
    accession_number = dataset.AccessionNumber
    if dataset.PatientSex == 'M':
      gender = enums.GENDER_NAMINGS[0]
      gender_enum = enums.Gender.MALE
    else:
      gender = enums.GENDER_NAMINGS[1]
      gender_enum = enums.Gender.FEMALE
    age = _age_string(dateOfBirth)
    height = f"{(dataset.PatientSize * 100):.0f}" #type: ignore
    weight = f"{(dataset.PatientWeight):.1f}"
    body_surface_area = f"{surface_area(dataset.PatientSize * 100, dataset.PatientWeight):.2f}" #type: ignore # Don't Care about numerical stability
    vial_number = f"{dataset.VialNumber}"
    gfr_method = f"{dataset.GFRMethod}"
    clearance = f"{dataset.clearance:.0f}"
    clearance_normalized = f"{dataset.normClear:.0f}"
    kidney_result, reference_percentage_number = kidney_function(
      dataset.normClear,
      dateTimeOfBirth,
      gender_enum
    )

    history=[]
    if not isinstance(dataset.clearancehistory, Sequence):
      raise ValueError("History is not a sequence")

    for historic_dataset in dataset.clearancehistory:
      historic_study_date = datetime.datetime.strptime(historic_dataset.StudyDate,"%Y%m%d")
      _ , index_gfr = kidney_function(historic_dataset.normClear, dateTimeOfBirth, dataset.PatientSex, now=historic_study_date)
      historic_study_date_str = historic_study_date.strftime("%d/%m/%Y")
      history.append((historic_study_date_str,f"{historic_dataset.clearance:.1f}", f"{historic_dataset.normClear:.1f}",f"{(100.0 - index_gfr):.1f}"))

    reference_percentage = f"{(100.0 - reference_percentage_number):.1f}"

    history.sort(key=lambda t: datetime.datetime.strptime(t[0],'%d/%m/%Y'), reverse=True)

    return cls(
      name, cpr, injection_date, accession_number, age, gender, height, weight,
      body_surface_area, vial_number, gfr_method, clearance, clearance_normalized,
      kidney_result, reference_percentage, history
    )

  def __str__(self) -> str:
    string = f"""
    {graph_texts.figure_text_name} {self.name}
    {graph_texts.figure_text_patient_id} {self.CPR}
    {graph_texts.figure_text_date_of_examination} {self.injection_date}
    {graph_texts.figure_text_accession_number}.: {self.accession_number}
    {graph_texts.figure_text_gender} {self.gender}
    {graph_texts.figure_text_age} {self.age}
    {graph_texts.figure_text_weight} {self.weight} kg
    {graph_texts.figure_text_height} {self.height} cm
    {graph_texts.figure_text_body_surface} {self.body_surface_area} m²
    {graph_texts.figure_text_vial_number} {self.vial_number}
    {graph_texts.figure_text_method}  {self.gfr_method}
    {graph_texts.figure_text_gfr} {self.clearance} ml / min
    {graph_texts.figure_text_gfr_normalized} {self.clearance_normalized} ml / min
    {graph_texts.figure_text_kidney_function} {self.kidney_result}
    {graph_texts.figure_text_reference_percentage} {self.reference_percentage}%
    """
    return string

def figure_text_factory(dataset: Dataset) -> Union[HistoricFigureTextDataClass, FigureTextDataClass]:
  if 'clearancehistory' in dataset:
    return HistoricFigureTextDataClass.from_dataset(dataset)
  else:
    return FigureTextDataClass.from_dataset(dataset)

def __draw_color_area(
    axes: Axes,
    x_min: int,
    x_max: int,
    y_max: int,
    x_axes: numpy.ndarray,
    reference_gfr: numpy.ndarray,
    dark_red_y: numpy.ndarray,
    light_red_y: numpy.ndarray,
    yellow_y: numpy.ndarray,
    light_gray_y: numpy.ndarray,
  ):
  axes.set_xlim(x_min, x_max)
  axes.set_ylim(0, y_max)

  axes.fill_between(x_axes, numpy.zeros_like(light_gray_y), light_gray_y, facecolor=KIDNEY_FUNCTION_NORMAL_COLOR, label=graph_texts.kidney_function_normal) # type: ignore
  axes.fill_between(x_axes, numpy.zeros_like(yellow_y), yellow_y, facecolor=KIDNEY_FUNCTION_MINORLY_REDUCED_COLOR, label=graph_texts.kidney_function_lightly_reduced) # type: ignore
  axes.fill_between(x_axes, numpy.zeros_like(light_red_y), light_red_y, facecolor=KIDNEY_FUNCTION_REDUCED_COLOR, label=graph_texts.kidney_function_reduced) # type: ignore
  axes.fill_between(x_axes, numpy.zeros_like(dark_red_y), dark_red_y, facecolor=KIDNEY_FUNCTION_MAJORLY_REDUCED_COLOR, label=graph_texts.kidney_function_majorly_reduced) # type: ignore
  axes.plot(x_axes, reference_gfr, color=REFERENCE_COLOR, label=graph_texts.kidney_function_reference)


def __draw_text_axes(axes: Axes, input: Union[FigureTextDataClass, HistoricFigureTextDataClass]) -> None:
  axes.set_xlim(0, 1)
  axes.set_ylim(-0.121, 1)
  axes.axis('off')
  if isinstance(input, FigureTextDataClass):
    axes.plot([0, 1], [0.155, 0.155], color='grey')
    axes.text(0, -0.205, str(input), ha='left', fontsize=server_config.TEXT_FONT_SIZE)
  elif isinstance(input, HistoricFigureTextDataClass):
    table_y = 0.18
    axes.text(0,table_y + 0.02, str(input), ha='left', fontsize=server_config.TEXT_FONT_SIZE, linespacing=1.75)
    axes.text(0.10, table_y + 0.01, graph_texts.historic_table_date, ha='left', fontsize=server_config.TEXT_FONT_SIZE)
    axes.text(0.32, table_y + 0.01, graph_texts.historic_table_gfr, ha='left', fontsize=server_config.TEXT_FONT_SIZE)
    axes.text(0.52, table_y + 0.01, graph_texts.historic_table_gfr_normalized, ha='left', fontsize=server_config.TEXT_FONT_SIZE)
    axes.text(0.73, table_y + 0.01, graph_texts.historic_table_reference, ha='left', fontsize=server_config.TEXT_FONT_SIZE)

    axes.plot([0.05, 0.95], [table_y + 0.26, table_y + 0.26],color = TEXT_LINE_COLOR)
    axes.plot([0.05, 0.95], [table_y + 0.06, table_y + 0.06],color = TEXT_LINE_COLOR)

    inputs = 0


    for date_str, clearance_str, clearance_norm_str, index in input.historic:
      if inputs < 5:
        inputs += 1
      else:
        break
      axes.plot([0.09,0.92],[table_y, table_y], color=TEXT_LINE_COLOR)
      axes.plot([0.09,0.09],[table_y, table_y - 0.06], color=TEXT_LINE_COLOR)
      axes.plot([0.32,0.32],[table_y, table_y - 0.06], color=TEXT_LINE_COLOR)
      axes.plot([0.52,0.52],[table_y, table_y - 0.06], color=TEXT_LINE_COLOR)
      axes.plot([0.72,0.72],[table_y, table_y - 0.06], color=TEXT_LINE_COLOR)
      axes.plot([0.92,0.92],[table_y, table_y - 0.06], color=TEXT_LINE_COLOR)
      table_y -= 0.05
      axes.text(0.1, table_y, date_str, ha='left', fontsize=server_config.TEXT_FONT_SIZE)
      axes.text(0.33, table_y, clearance_str, ha='left', fontsize=server_config.TEXT_FONT_SIZE)
      axes.text(0.53, table_y, clearance_norm_str , ha='left', fontsize=server_config.TEXT_FONT_SIZE)
      axes.text(0.73, table_y, index + "%", ha='left', fontsize=server_config.TEXT_FONT_SIZE)
      table_y -= 0.01
      print(table_y)
    axes.plot([0.09, 0.92],[table_y, table_y], color=TEXT_LINE_COLOR) # bottom line of the table

def __plot_single_point(axes,x, y):
  axes.scatter(x, y, s=64, label=graph_texts.legend_gfr, color=SAMPLE_COLOR)

def __calculate_kidney_function_yearly(dataset, today=datetime.datetime.now()):
  dateTimeOfBirth = datetime.datetime.strptime(dataset.PatientBirthDate, "%Y%m%d")
  years_old = (today - dateTimeOfBirth).days // 365

  x_max = int(max(years_old * 1.1, 90))
  x_axes = numpy.arange(0.00001,2, 1/365)
  reference_gfr = calc_mean_gfr_for_toddlers(x_axes, 1)
  dark_red_y = 0.28 * reference_gfr
  light_red_y = 0.52 * reference_gfr
  yellow_y = 0.75 * reference_gfr
  y_max = max(reference_gfr.max(), dataset.normClear) * 1.2
  light_grey_y = y_max + x_axes

  if dataset.PatientSex == 'M':
    #after age of 2
    x_axes = numpy.concatenate((x_axes, [2, 20, 20, 40, x_max]))
    dark_red_y = numpy.concatenate((dark_red_y,[30.52, 30.52, 31.08, 31.08, 0.28 * (-1.16*x_max + 157.8)]))
    light_red_y = numpy.concatenate((light_red_y, [56.68, 56.68, 57.72, 57.72, 0.52 * (-1.16*x_max + 157.8)]))
    yellow_y = numpy.concatenate((yellow_y, [81.75, 81.75, 83.25, 83.25, 0.75 * (-1.16*x_max + 157.8)]))
    light_grey_y = numpy.concatenate((light_grey_y, [y_max, y_max, y_max, y_max, y_max]))
    reference_gfr = numpy.concatenate((reference_gfr, [109, 109, 111, 111, -1.16 * x_max + 157.8]))
  else:
    x_axes = numpy.concatenate((x_axes, [2, 20, 20, 40, x_max]))
    dark_red_y = numpy.concatenate((dark_red_y,[30.52, 30.52,28.84, 28.84, 0.28 *(-1.16*x_max + 157.8) * 0.929]))
    light_red_y = numpy.concatenate((light_red_y, [56.68, 56.68, 53.56, 53.36, 0.52 * (-1.16*x_max + 157.8) * 0.929]))
    yellow_y = numpy.concatenate((yellow_y, [81.75, 81.75, 77.25, 77.25, 0.75 * (-1.16*x_max + 157.8) * 0.929]))
    light_grey_y = numpy.concatenate((light_grey_y, [y_max, y_max, y_max, y_max, y_max]))
    reference_gfr = numpy.concatenate((reference_gfr, [109, 109, 103, 103, (-1.16*x_max + 157.8) * 0.929]))

  return y_max, x_axes, dark_red_y, light_red_y, yellow_y, reference_gfr, light_grey_y

def __calculate_background_colors(birthdate : datetime.datetime, date_of_examination: datetime.datetime, sex:str, y_max: float ) -> List[float]:
  days_old = (date_of_examination - birthdate).days

  if days_old // 365 < 2:
    reference = 10 ** (0.209 * numpy.log10(days_old) + 1.44)
    dark_red_y = reference * 0.28
    light_red_y = reference * 0.52
    yellow_y = 0.75 * reference
    light_grey_y = max(reference, y_max) * 1.2
    return [dark_red_y, light_red_y, yellow_y, reference, light_grey_y]
  elif days_old // 365 < 20:
    return [ 30.52, 56.68, 81.75, 109, max(109, y_max) * 1.2]
  elif days_old // 365 < 40:
    if sex == 'M':
      return [31.08, 57.72, 83.25,111, max(111, y_max) * 1.2]
    else:
      return [28.84, 53.56, 77.25,103, max(103, y_max) * 1.2]

  reference = -1.16 * (days_old // 365) + 157.8
  if sex == 'F':
    reference = reference * 0.929

  return [reference * 0.28, reference * 0.52, reference * 0.75, reference, max(reference,  y_max) * 1.2]


def __draw_graph_historic(axes: Axes, dataset: Dataset):
  birthdate = datetime.datetime.strptime(dataset.PatientBirthDate, "%Y%m%d")
  latest_datetime = datetime.datetime.strptime(dataset.StudyDate,"%Y%m%d")
  earliest_datetime = latest_datetime

  study_date_time = datetime.datetime.strptime(dataset.StudyDate,"%Y%m%d")

  data = []
  color_points = []

  if not isinstance(dataset.clearancehistory, Sequence):
    raise ValueError("History is not a Sequence")

  for historic_dataset in dataset.clearancehistory:
    historic_study_date = datetime.datetime.strptime(historic_dataset.StudyDate,"%Y%m%d")
    if (study_date_time - historic_study_date).days > 365 * 5: # if greater than 5 years skip adding
      continue
    historic_dataset.PatientSex = dataset.PatientSex
    data.append((numpy.datetime64(historic_study_date), historic_dataset.normClear, historic_study_date))

  data.sort(key=lambda x: x[0])

  data_x = []
  data_y = []

  for _data_point_x, _data_point_y, historic_study_date in data:
    color_points.append(__calculate_background_colors(birthdate, historic_study_date, dataset.PatientSex, dataset.normClear))
    data_x.append(_data_point_x)
    data_y.append(_data_point_y)
    if historic_study_date < earliest_datetime:
      earliest_datetime = historic_study_date

  color_points.append(__calculate_background_colors(birthdate, study_date_time, dataset.PatientSex, dataset.normClear))
  data_x.append(numpy.datetime64(latest_datetime))
  data_y.append(dataset.normClear)

  data_x_coloring = [data_x[0] - numpy.timedelta64(datetime.timedelta(days=14))] + data_x + [data_x[-1] + numpy.timedelta64(datetime.timedelta(days=14))]
  y_max = 0

  res = __calculate_background_colors(birthdate, (data_x[0] - numpy.timedelta64(datetime.timedelta(days=14))).astype(datetime.datetime), dataset.PatientSex, 0)

  for color_row in color_points:
    y_max = max(y_max, color_row[-1])

  zeroes: List[float] = [0]
  dark_red_y: List[float] = [res[0]]
  light_red_y: List[float] = [res[1]]
  yellow_y: List[float] = [res[2]]
  reference: List[float] = [res[3]]
  light_grey_y: List[float] = [y_max]

  for color_row in color_points:
    color_row[-1] = y_max
    zeroes.append(0)
    dark_red_y.append(color_row[0])
    light_red_y.append(color_row[1])
    yellow_y.append(color_row[2])
    reference.append(color_row[3])
    light_grey_y.append(y_max)

  res = __calculate_background_colors(birthdate, (data_x[-1] + numpy.timedelta64(datetime.timedelta(days=14))).astype(datetime.datetime), dataset.PatientSex, 0)

  zeroes += [0]
  dark_red_y += [res[0]]
  light_red_y += [res[1]]
  yellow_y += [res[2]]
  reference += [res[3]]
  light_grey_y += [res[4]]

  #axes.xaxis.set_major_locator(MonthLocator())
  axes.xaxis.set_major_formatter(DateFormatter("%b\n%Y"))
  axes.set_xlabel(graph_texts.x_axis_historic_label, fontsize=server_config.AXIS_FONT_SIZE)

  __draw_color_area(
    axes,
    data_x_coloring[0],
    data_x_coloring[-1],
    y_max,
    numpy.array(data_x_coloring),
    numpy.array(reference),
    numpy.array(dark_red_y),
    numpy.array(light_red_y),
    numpy.array(yellow_y),
    numpy.array(light_grey_y),
  )

  axes.plot(data_x, data_y, marker='o',markersize=12, label=graph_texts.legend_gfr, linestyle='dashed', color=SAMPLE_COLOR)


def __draw_graph_baby(axes: Axes, dataset: Dataset, today=datetime.datetime.today()):
  start_x = 1 # Days
  end_x = 730 # Days

  dateTimeOfBirth = datetime.datetime.strptime(dataset.PatientBirthDate, "%Y%m%d")
  days_old = (today - dateTimeOfBirth).days

  days_axis = numpy.arange(start_x, end_x, 1)
  reference_gfr = 10 ** (0.209 * numpy.log10(days_axis) + 1.44)
  y_max = max(dataset.normClear, reference_gfr.max()) * 1.2

  axes.set_xticks([0, 90, 180, 270, 365, 455, 545, 635, 730])
  axes.set_xticklabels([
    f'0 {graph_texts.x_axis_toddler_tick_suffix}',
    f'3 {graph_texts.x_axis_toddler_tick_suffix}',
    f'6 {graph_texts.x_axis_toddler_tick_suffix}',
    f'9 {graph_texts.x_axis_toddler_tick_suffix}',
    f'12 {graph_texts.x_axis_toddler_tick_suffix}',
    f'15 {graph_texts.x_axis_toddler_tick_suffix}',
    f'18 {graph_texts.x_axis_toddler_tick_suffix}',
    f'21 {graph_texts.x_axis_toddler_tick_suffix}',
    f'24 {graph_texts.x_axis_toddler_tick_suffix}',
  ], rotation = 45)

  x_axes = 0 * days_axis
  dark_red_y = 0.28 * reference_gfr
  light_red_y = 0.52 * reference_gfr
  yellow_y = 0.75 * reference_gfr
  light_gray_y = x_axes + y_max

  __draw_color_area(
    axes=axes,
    x_min=0,
    x_max=730,
    y_max=y_max,
    x_axes=days_axis,
    reference_gfr=reference_gfr,
    dark_red_y=dark_red_y,
    light_red_y=light_red_y,
    yellow_y=yellow_y,
    light_gray_y=light_gray_y
  )

  axes.set_xlabel(graph_texts.x_axis_toddler_label, fontsize=server_config.AXIS_FONT_SIZE)
  __plot_single_point(axes, days_old, dataset.normClear)

def __draw_graph_child(axes: Axes, dataset: Dataset, today=datetime.datetime.now()):
  dateTimeOfBirth = datetime.datetime.strptime(dataset.PatientBirthDate, "%Y%m%d")
  years_old = (today - dateTimeOfBirth).days // 365
  y_max, x_axes, dark_red_y, light_red_y, yellow_y, reference_gfr, light_grey_y = __calculate_kidney_function_yearly(dataset)

  __draw_color_area(
    axes=axes,
    x_min=0,
    x_max=18,
    y_max=y_max,
    x_axes=x_axes,
    reference_gfr=reference_gfr,
    dark_red_y=dark_red_y,
    light_red_y=light_red_y,
    yellow_y=yellow_y,
    light_gray_y=light_grey_y
  )

  axes.xaxis.set_minor_locator(AutoMinorLocator())
  axes.set_xlabel(graph_texts.x_axis_label, fontsize=server_config.AXIS_FONT_SIZE)
  __plot_single_point(axes, years_old, dataset.normClear)


def __draw_graph_grown_up(axes: Axes, dataset: Dataset, today=datetime.datetime.now()):
  dateTimeOfBirth = datetime.datetime.strptime(dataset.PatientBirthDate, "%Y%m%d")
  years_old = (today - dateTimeOfBirth).days // 365
  x_max = int(max(years_old * 1.1, 90))
  y_max, x_axes, dark_red_y, light_red_y, yellow_y, reference_gfr, light_grey_y = __calculate_kidney_function_yearly(dataset)

  __draw_color_area(
    axes=axes,
    x_min=0,
    x_max=x_max,
    y_max=y_max,
    x_axes=x_axes,
    reference_gfr=reference_gfr,
    dark_red_y=dark_red_y,
    light_red_y=light_red_y,
    yellow_y=yellow_y,
    light_gray_y=light_grey_y
  )

  axes.xaxis.set_minor_locator(AutoMinorLocator())
  axes.set_xlabel(graph_texts.x_axis_label, fontsize=server_config.AXIS_FONT_SIZE)
  __plot_single_point(axes, years_old, dataset.normClear)


def __draw_graph_axes(axes: Axes, dataset: Dataset, now=datetime.datetime.now()):
  age = int((datetime.datetime.now() - datetime.datetime.strptime(dataset.PatientBirthDate, '%Y%m%d')).days / 365)
  axes.grid(color='black')
  axes.set_ylabel(graph_texts.y_axis_label, fontsize=server_config.AXIS_FONT_SIZE)

  if 'clearancehistory' in dataset:
    __draw_graph_historic(axes, dataset)
  elif age < 2:
    __draw_graph_baby(axes, dataset)
  elif age < 19:
    __draw_graph_child(axes, dataset)
  else:
    __draw_graph_grown_up(axes, dataset)

  axes.legend(framealpha=1.0 , prop={'size': server_config.LEGEND_SIZE})

def __set_gfr_figure(figure: Figure, dataset: Dataset) -> None:
  figure.set_figheight(server_config.PLOT_HEIGHT)
  figure.set_figwidth(server_config.PLOT_WIDTH)

  title = f"""{graph_texts.title_hospital_prefix} {dataset.InstitutionName}
    {dataset.StudyDescription}"""

  figure.suptitle(title, fontsize=server_config.TITLE_FONT_SIZE)


def generate_plot_from_dataset(dataset : Dataset) -> bytes:
  """Generates the bytes for an image in rgb

  Args:
      dataset (Dataset): filled dataset with information of the examination to be plotted

  Returns:
      bytes: Bytes forming a picture of examination

  Throws:
    ValueError: If a tag required is missing
  """


  fig, ax = plt.subplots(nrows = 1, ncols=2)

  # Figure Stats
  __set_gfr_figure(fig, dataset)

  # Axes 0
  __draw_graph_axes(ax[0], dataset)

  # Axes 1
  figure_text_data = figure_text_factory(dataset)
  __draw_text_axes(ax[1], figure_text_data)


  fig.canvas.draw()
  image_bytes: bytes = fig.canvas.tostring_rgb() # type: ignore # method is added by draw call
  return image_bytes
