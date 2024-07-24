from enum import Enum


class Gender(Enum):
  MALE = 0    # 'Mand'
  FEMALE = 1  # 'Kvinde'

GENDER_NAMINGS = ['Mand', 'Kvinde']
GENDER_SHORT_NAMES = ['M', 'F']

class StudyType(Enum):
  ONE_SAMPLE_ADULT = 0  # 'En blodprøve, Voken'
  ONE_SAMPLE_CHILD = 1  # 'En blodprøve, Barn'
  MULTI_SAMPLE = 2      # 'Flere blodprøver'

STUDY_TYPE_NAMES = [
  "En blodprøve, Voksen",
  "En blodprøve, Barn",
  "Flere blodprøver"
]

class ExamStatus(Enum):
  NO_CHANGES = 0      # The study has not been edited yet
  SAVED_CHANGES = 1   # Study was edited
  READY = 2           # Study and is ready for review