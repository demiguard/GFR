# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
<!-- and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). -->

## 1.1 TODO Features
  - [ ] csv export


## 1.0.3 - 2019-08-26
### Added
  - Sorting of admin panel table.
  - Fetching backup files now support Hidex files.

### Changed
  - Resolve minor spelling mistake in tooltip for delete and edit buttons on admin panel.
  - Disabled enter keypress on all input fields on fill_study
  - Deletion and recovery of studies is now in the RESTful api instead of /ajax.

### Fixed
  - Made deletion and recovery of studies work again


## 1.0.2 - 2019-08-23
### Added

### Changed
  - Fixed a few Spelling mistakes
  - QA plot changed from a log plot to a Exponentail plot

### Fixed
  - Auto Character add no longer adds an extra character if the character being added is the same as the function would add.
  - Updated Color plot such that it reflect the underlying method
  - Resolved issue in ```calc_clearance``` under clearance_math.py with days to minutes conversion for tests done over multiple days


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
