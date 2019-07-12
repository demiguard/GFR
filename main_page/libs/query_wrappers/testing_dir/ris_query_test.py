#!/usr/bin/env python3

import os
import shutil

import ..ris_query_wrapper as ris


# Creates the testing directories
def init_setup(test_dir):
  try:
    os.mkdir(test_dir)
  except FileExistsError:
    shutil.rmtree(test_dir)
    os.mkdir(test_dir)


# Correct query to retreive patient in the test database 
def test_get_from_pacs(test_dir):
  # Copy base query files from rsp
  shutil.copyfile(
    "/home/simon/Documents/clearance-stuff/GFR/rsp/base_find_query.dcm",
    test_dir + "base_find_query.dcm"  
  )

  shutil.copyfile(
    "/home/simon/Documents/clearance-stuff/GFR/rsp/base_get_image.dcm",
    test_dir + "base_get_image.dcm"  
  )

  # Test the function
  res = ris.get_from_pacs('REGH13671016', test_dir, resp_path=test_dir)
  print(res)


# Test execute query, with a valid and an invalid command 
def test_execute_query():
  # Test valid command
  q1 = ['ls']
  r1 = ris.execute_query(q1)
  print('Result 1: {0}'.format(r1))

  # Test invalid command
  q2 = ['This is not a command']
  r2 = ris.execute_query(q2)
  print('Result 2: {0}'.format(r2))


def main():
  test_dir = "./test_dir/"

  init_setup(test_dir)

  test_get_from_pacs(test_dir)

  test_execute_query()

if __name__ == '__main__':
  main()
