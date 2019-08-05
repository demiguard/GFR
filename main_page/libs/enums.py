from enum import Enum


class Gender(Enum):
  MALE = 0    # 'Mand'
  FEMALE = 1  # 'Kvinde'


class StudyType(Enum):
  ONE_SAMPLE_ADULT = 0  # 'En blodprøve, Voken'
  ONE_SAMPLE_CHILD = 1  # 'En blodprøve, Barn'
  MULTI_SAMPLE = 2      # 'Flere blodprøver'


class ExamStatus(Enum):
  NO_CHANGES = 0      # The study has not been edited yet
  SAVED_CHANGES = 1   # Study was edited and is ready for review
  READY = 2           # Study has been reviewed and is ready for PACS