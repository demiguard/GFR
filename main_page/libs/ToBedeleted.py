import pydicom
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.datadict import DicomDictionary, keyword_dict


# Open Test file
dicom = pydicom.dcmread('rsp0001.dcm')

#Add Private Tags
new_dict_items = {
    0x00231001 : ('LO', '1', 'GFR', '', 'GFR'), #Normal, Moderat Nedsat, Svært nedsat
    0x00231002 : ('LO', '1', 'GFR Version', '', 'GFRVersion'), #Version 1.
    0x00231010 : ('LO', '1', 'GFR Method', '', 'GFRMethod'),
    0x00231011 : ('LO', '1', 'Body Surface Method', '', 'BSAmethod'),
    0x00231012 : ('DS', '1', 'clearence', '', 'clearence'),
    0x00231014 : ('DS', '1', 'normalized Clearence', '', 'normClear'),
    0x00231020 : ('SQ', '1-100', 'Clearence Tests', '', 'ClearTest'),
    0x00231021 : ('DT', '1', 'Sample Time', '', 'SampleTime'), #Sequence Items
    0x00231022 : ('DS', '1', 'Count Per Minuts', '', 'cpm'),
    0x00231024 : ('DS', '1', 'Standart Counts Per', '', 'stdcnt'),
    0x00231028 : ('DS', '1', 'Thining Factor', '', 'thiningfactor')
}

DicomDictionary.update(new_dict_items)

new_names_dirc = dict([(val[4], tag) for tag, val in new_dict_items.items()])
keyword_dict.update(new_names_dirc)

#Elem too add
dicom.GFR = 'Stuff'
dicom.GFRVersion = 'Version 1.0'
dicom.GFRMethod = '1 punkt barn'
dicom.BSAmethod = 'Du Bois'
dicom.clearence = 1000
dicom.NormClear = 1000


n = 4
seq_ds = Dataset()
seq = Sequence([])

for x in range(4): 
  ds = Dataset()
  ds.SampleTime = '20190110120000.000000'
  ds.cpm = 1000
  ds.stdcnt = 1000
  ds.thiningfactor = 1000
  seq.append(ds)

dicom.ClearTest = seq

#Save Test dicom thingy
print(dicom)

