import pydicom

from pydicom.values import convert_SQ, convert_string
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.datadict import DicomDictionary, keyword_dict

new_dict_items = {
  0x00231001 : ('LO', '1', 'GFR', '', 'GFR'), #Normal, Moderat Nedsat, Svært nedsat
  0x00231002 : ('LO', '1', 'GFR Version', '', 'GFRVersion'), #Version 1.
  0x00231010 : ('LO', '1', 'GFR Method', '', 'GFRMethod'),
  0x00231011 : ('LO', '1', 'Body Surface Method', '', 'BSAmethod'),
  0x00231012 : ('DS', '1', 'clearence', '', 'clearence'),
  0x00231014 : ('DS', '1', 'normalized clearence', '', 'normClear'),
  0x00231018 : ('DT', '1', 'Injection time', '', 'injTime'),     #Tags Added
  0x0023101A : ('DS', '1', 'Injection weight', '', 'injWeight'),
  0x0023101B : ('DS', '1', 'Vial weight before injection', '', 'injbefore'),
  0x0023101C : ('DS', '1', 'Vial weight after injection', '', 'injafter'),
  0x00231020 : ('SQ', '1', 'Clearence Tests', '', 'ClearTest'),
  0x00231021 : ('DT', '1', 'Sample Time', '', 'SampleTime'), #Sequence Items
  0x00231022 : ('DS', '1', 'Count Per Minuts', '', 'cpm'),
  0x00231024 : ('DS', '1', 'Standart Counts Per', '', 'stdcnt'),
  0x00231028 : ('DS', '1', 'Thining Factor', '', 'thiningfactor')
}


def dcmread_wrapper(filename, is_little_endian=True, is_implicit_VR=True):
  """
    Takes a file path and reads it, update the private tags accordingly

    Supports only VM 1

  """
  DicomDictionary.update(new_dict_items)  
  new_names_dict = dict([(val[4], tag) for tag, val in new_dict_items.items()])
  keyword_dict.update(new_names_dict)

  obj = pydicom.dcmread(filename)
  obj = update_tags(obj, is_little_endian, is_implicit_VR)
  #Update Private tags
  return obj
  
def update_tags(obj, is_little_endian=True, is_implicit_VR=True):
  for ds in obj.iterall():
    if ds.VR == 'UN':
      if new_dict_items[ds.tag][0] == 'SQ':
        ds_sq = convert_SQ(ds.value, is_implicit_VR , is_little_endian)
        seq_list = []
        for sq in ds_sq:
          sq = update_tags(sq,is_little_endian=is_little_endian, is_implicit_VR=is_implicit_VR)
          seq_list.append(sq)
        obj.add_new(ds.tag, new_dict_items[ds.tag][0], Sequence(seq_list)) 
      elif new_dict_items[ds.tag][0] == 'LO':
        new_val = convert_string(ds.value, is_little_endian)
        obj.add_new(ds.tag, new_dict_items[ds.tag][0], new_val)
      else:
        obj.add_new(ds.tag, new_dict_items[ds.tag][0], ds.value)
  return obj



    

  

  