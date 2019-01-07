set -e
img2dcm test.bmp test.dcm -sc -i BMP
storescu -aet RH_EDTA -aec TEST_DCM4CHEE localhost 11112 test.dcm