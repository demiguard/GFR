import requests
from subprocess import check_output
import pydicom


test_user = {
  'csrfmiddlewaretoken': [''], 
  'username': ['rh_test'], 
  'password': ['rh_test'], 
  'hospital': ['RH']
}

rigs_numbers = [
  'REGH13727725',
  'REGH13716821',
]

tests = [
  {
    'age': ['77'],
    'calculate': ['Beregn'],
    'cpr': ['131041-0272'],
    'csrfmiddlewaretoken': [''],
    'height': ['158'],
    'injection_date': ['2019-01-24'],
    'injection_time': ['09:20'],
    'name': ['Frederikke Lerche Andersen'],
    'sex': ['Dame'],
    'std_cnt': ['7525'],
    'study_date': ['2019-01-24', '2019-01-24'],
    'study_time': ['12:45', ''],
    'study_type': ['0'],
    'test_value': ['216'],
    'thin_fac': ['980'],
    'vial_weight_after': ['3.112'],
    'vial_weight_before': ['4.094'],
    'weight': ['55']
  },
  {
    'age': ['71'],
    'calculate': ['Beregn'],
    'cpr': ['	280247-1044'],
    'csrfmiddlewaretoken': [''],
    'height': ['164'],
    'injection_date': ['2018-12-13'],
    'injection_time': ['10:20'],
    'name': ['Lise Birte Dreyer'],
    'sex': ['Dame'],
    'std_cnt': ['11579'],
    'study_date': ['2018-12-13', '2018-12-13', '2018-12-13', '2018-12-13', '2019-01-24'],
    'study_time': ['14:21', '14:42', '15:00', '15:21', ''],
    'study_type': ['2'],
    'test_value': ['183', '168', '161', '155'],
    'thin_fac': ['917'],
    'vial_weight_after': ['3.1070'],
    'vial_weight_before': ['3.7770'],
    'weight': ['73']
  },
]

def get_csrftoken(session, url):
  session.get(url)
  if 'csrftoken' in session.cookies:
    return session.cookies['csrftoken']
  else:
    return session.cookies['csrf']

def main(): 
  # Create login session
  base_url = 'http://localhost:8000'
  
  s = requests.Session()
  
  test_user['csrfmiddlewaretoken'][0] = get_csrftoken(s, base_url)
  s.post(base_url, data=test_user)

  # Send test payloads
  for rigs_nr, payload in zip(rigs_numbers, tests):
    exam_url = '{0}/fill_study/{1}'.format(base_url, rigs_nr)
    s.get(exam_url)

    payload['csrfmiddlewaretoken'][0] = get_csrftoken(s, exam_url)

    s.post(exam_url, data=payload)

  # Send the output dicom objects to the dcm4chee database
  obj_paths = ['./Active_Dicom_objects/RH/{0}.dcm'.format(x) for x in rigs_numbers]
  
  # Set the StudyDate for this specific person
  ds = pydicom.dcmread(obj_paths[1])
  ds.StudyDate = '20181213'
  ds.SOPInstanceUID = '1.3.51.0.1.1.10.143.20.159.13716821.6705280'
  ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.7'
  ds.save_as(obj_paths[1])

  store_query = [
    'storescu',
    '-aet',
    'RH_EDTA',
    '-aec',
    'TEST_DCM4CHEE',
    '127.0.0.1',
    '11112',
  ] + obj_paths

  check_output(store_query)


if __name__ == '__main__':
  main()