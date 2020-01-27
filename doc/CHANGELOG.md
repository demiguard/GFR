# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
<!-- and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). -->

## 1.1 - 2020-01-27
### Added
  - Worklist prefecthing, to retrieve prior history of a study
  - Added control site, so studies are sent to control for second-hand evaluation before they can be sent to PACS
  - ae_controller, library to simplify C-FIND and C-MOVE requests
  - Added a rollover logfile, s.t. a new logfile is created every day at midnight
  - Added git branch (ldap-integration) for implementing future LDAP solution to enable BAM-Id login
  - Added enums to solidify the process of working with genders, study types and exam status
  - Added buttons to admin panel, for removal of all studies and deleted studies

### Changed
  - Refactored method for storing dicom files. I.e. the nested directories, which are able to also hold the history related to a study
  - Split Views and forms into multiple files
    - Merged PostRequestHandler into FillStudy view
  - Changed all C-FINDs and C-MOVEs to use the new ae_controller library
  - Changed all references of ```ris_nr``` or ```rigs_nr``` to ```accession_number``` (This should be the default from now on)
  - Moved most Ajax (JSON) endpoints to follow the RESTful design

### Fixed
  - Minor state-change issues related to the javascript alerter (including total rewrite of the alerter to an object-based design following: https://www.digitalocean.com/community/tutorials/understanding-classes-in-javascript)
  - Made Selenium tests use the new nested directories, so they work once again

### Removed
  - All references to examination_info class (just use purely dicom objects from now on)

---

## 1.0.5 - 2019-10-11
### Added
  - Javascript checks on entered study date to see if they differ from the injection date

### Changed
  - Procedure filtering is blacklisting instead of whitelisting

### Fixed
  - Exporting study results to csv now exports to .csv filetype.

---

## 1.0.4 - 2019-09-04
### Added
  -  csv export, on site single study

### Changed
  - Spelling of sample

### Fixed
  - Saving of the daily thining factor is initially uncheck if already entered previously.
  - Made SambaBackupEndpoint and StudyEndpoint have login required.

---

## 1.0.3 - 2019-08-26
### Added
  - Sorting of admin panel table.
  - Fetching backup files now support Hidex files.

### Changed
  - Resolve minor spelling mistake in tooltip for delete and edit buttons on admin panel.
  - Disabled enter keypress on all input fields on fill_study
  - Deletion and recovery of studies is now in the RESTful api instead of /ajax.
  - Increased thinning factor threshold to 10k

### Fixed
  - Made deletion and recovery of studies work again

---

## 1.0.2 - 2019-08-23
### Added

### Changed
  - Fixed a few Spelling mistakes
  - QA plot changed from a log plot to a Exponentail plot

### Fixed
  - Auto Character add no longer adds an extra character if the character being added is the same as the function would add.
  - Updated Color plot such that it reflect the underlying method
  - Resolved issue in ```calc_clearance``` under clearance_math.py with days to minutes conversion for tests done over multiple days

---

## 1.0.1 - 2019-08-21
### Added
- 'Tilføj tom prøve' button which makes it possible to add tests without samples from a counter.
- Separator line in result graph
- Warning if there is a difference between the injection date and sample date.

### Changed
- Result graph displays integer values for; 'højde', 'GFR', 'GFR, normaliseret' og 'Nyrefunktion ift. Reference Patient'. 
- ```kidney_function``` under clearance_math.py no longer computes age and gender based on CPR number.
- Name and cpr number fields in fill_study are readonly

### Fixed
- Correction of minor spelling errors
- Made 'Stardardtælletal' field have a corresponding label, instead of the strong tag
- Added support for RIS/Accession numbers in all formats
- Sample dates are now correctly converted to the internal format, to avoid problems with computing the time difference between injection time and sample time.
