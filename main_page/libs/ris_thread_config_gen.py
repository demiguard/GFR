#
#
# This file generates a Ris_thread_config, for the ris_thread
#
import logging

logger = logging.getLogger()

Filename = 'Ris_thread_config'

header = """# This file generates the config for ris_thread
#
# Use the ris_thread_config_generator to make this file
# 
# Guide:
#  - put a # for comments
#  - <key>, <item>
#  - item non-list and non-dir will take string
#  - ENSURE there're no special chars like: ,:;[], and so forth
# \n"""

def _check_config(input_config):
  
  required_config = {
    'Delay_minimum' : False,
    'Delay_maximum' : False,
    'ris_ip'        : False,
    'ris_port'      : False,
    'ris_AET'       : False,
    'AE_items'      : False
  } 
  required_keys = required_config.keys()
  input_keys    = input_config.keys()
  return_value = True
  
  for key in required_keys:
    if key in input_keys:
      required_config[key] = True
    return_value &= required_config[key]

  return return_value

def generate_config(config):
  """

  arg:
    config: directory

  """

  #Check if valid config file
  if not (_check_config(config)):
    logger.error('Attempted to generate a config from ')
    return

  with open(Filename, 'w') as a_file: # Removes previous file
    pass
  with open(Filename, 'w') as a_file:
    a_file.write(header)
    for key in config.keys():
      item = config[key]
      
      if type(item) == type({}): #Type based programming, pretty sure this is not best pratice...
        special_char_begin = '{'
        special_char_end   = '}'
        a_file.write(f'{key}, {special_char_begin}')
        for item_key in item.keys():
          a_file.write(f'{item_key}:{str(item[item_key])};')        
        a_file.write(f'{special_char_end}\n')
      elif type(item) == type([]):
        a_file.write(f'{key}, [')
        for list_item in item:
          a_file.write(f'{str(list_item)};')
        a_file.write(']\n')
      else:
        a_file.write(f'{key}, {str(item)}\n')



def read_config():
  config = {}
  with open(Filename, 'r') as a_file:
    for line in a_file:
      #String preprossessing
      line = line.replace(' ','') #Removes spaces from file
      if line[0] == '#' or line[0] == '\n': #coment line or empty line
        continue
       
      try:
        key, val = line.split(',')
      except ValueError as E:
        logger.info(f'Line: {line}')
        continue
      
      #decode val
      if val[0] == '{': #TODO Error handling
        ae_config = {}
        val = val.replace('{','').replace(';}','').replace('\n','') #Remove indentifiers
        ae_list = val.split(';')
        for dir_item in ae_list:
          ae, hospital_sn = dir_item.split(':') #This could fail
          ae_config[ae] = hospital_sn
        config[key] = ae_config
      elif val[0] == '[': #TODO Even more Error handling
        val = val.replace('[','').replace(';]','').replace('\n','')
        val_list = val.split(';')
        config_list = []
        for item in val_list:
          config_list.append(item)
        config[key] = config_list
      else: 
        config[key] = val.replace('\n','')
  return config