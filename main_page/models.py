# Python Standard Module
import datetime
from datetime import date
from typing import Any, Dict, List, Optional

# Third party modules
from pydicom import Dataset
from pydicom.uid import SecondaryCaptureImageStorage, generate_uid
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

# GFR modules
from main_page.libs.enums import StudyType, Gender
from main_page.libs import server_config, classproperty
from main_page.libs.clearance_math.clearance_math import surface_area, calc_clearance, dosis, kidney_function

class Hospital(models.Model):
  id = models.AutoField(primary_key=True)
  name = models.CharField(default='', max_length=200, null=True)

  short_name = models.CharField(max_length=8, null=True)
  address = models.CharField(default='', max_length = 200, null=True)

  def __str__(self):
    return self.name

class Address(models.Model):
  id          = models.AutoField(primary_key=True)
  ae_title    = models.CharField(max_length=16, null=True, default=None)
  ip          = models.CharField(max_length=20)
  port        = models.CharField(max_length=5)
  description = models.CharField(max_length=255, default='')

  def __str__(self):
    return self.description


# Used to filter reveiced dicom objects from PACS
class ProcedureType(models.Model):
  id = models.AutoField(primary_key=True)
  type_name = models.CharField(max_length=200, default='', blank=True)

  def __str__(self):
    return self.type_name


# Configuration for a department
class Config(models.Model):
  id = models.AutoField(primary_key=True)

  # List of procedure types related to GFR examinations
  accepted_procedures = models.ManyToManyField(ProcedureType)
  black_list          = models.BooleanField(default=True)

  # Configuration to ris server
  ris = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='ris')
  ris_calling = models.CharField(max_length=200, default='')

  # Configuration to PACS server
  pacs = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='pacs')
  storage = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name="storage_ae", default=None)

  def __str__(self):
    return str(self.id)

class Department(models.Model):
  id = models.AutoField(primary_key=True)
  name = models.CharField(default='', max_length = 200, null=True)
  ldapPath = models.CharField(default='', max_length=500)
  # Associated hospital for this department
  hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True)
  config = models.OneToOneField(Config, on_delete=models.SET_NULL, null=True, blank=True)

  # Temporarily store daily thinning factors
  thining_factor = models.FloatField(default=0.0, null=True)
  thining_factor_change_date = models.DateField(default=datetime.date(1,1,1))

  def __str__(self):
    return f"{self.hospital.name} - {self.name}"

# Defines user permissions
class UserGroup(models.Model):
  id = models.AutoField(primary_key=True)
  name = models.CharField(max_length=200)

  def __str__(self):
    return self.name


class User(AbstractBaseUser):
  id = models.AutoField(primary_key=True)
  username = models.CharField(max_length=120, unique=True)
  password = models.CharField(max_length=120)
  department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)

  user_group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, null=True)

  USERNAME_FIELD = 'username'
  REQUIRED_FIELDS = ['password', 'hospital']

  def __str__(self):
    return self.username

class UserDepartmentAssignment(models.Model):
  id = models.AutoField(primary_key=True)
  user = models.ForeignKey(User, on_delete=models.CASCADE)
  department = models.ForeignKey(Department, on_delete=models.CASCADE)
  class Meta:
    unique_together = [["user", "department"]]


# Maintains a list of examinations sent to PACS
# This means we don't have to query PACS for all previous examinations
class HandledExaminations(models.Model):
  accession_number = models.CharField(primary_key=True, max_length=20)
  handle_day       = models.DateField(default=timezone.now)

# So Stuff breaks if there's no ServerConfiguration with an id=1 !IMPORTANT !NOTICE
# All server configs with an id different from 1 is ignored.
# This is something YOU have to check and ensure
# TODO: Put this in some more official documentation
class ServerConfiguration(models.Model):
  id          = models.AutoField(primary_key=True)
  samba_ip    = models.CharField(max_length=20)
  samba_name  = models.CharField(max_length=30)
  samba_user  = models.CharField(max_length=30)
  samba_pass  = models.CharField(max_length=30)
  samba_pc    = models.CharField(max_length=30)
  samba_share = models.CharField(max_length=30)

  AE_title    = models.CharField(max_length=30)

  def __str__(self):
    return self.AE_title

class StudyStatus(models.IntegerChoices):
  INITIAL = 0
  PARTIAL_FILLED = 1
  READY = 2
  CONTROL = 3
  DELETED = 4
  HISTORIC = 5

class GFROptions(models.TextChoices):
  NORMAL = "Normal"
  MODERATE = "Moderat nedsat"
  MAJOR = "Middelsvært nedsat"
  STRONGLY = "Svært nedsat"

class BodySurfaceMethods(models.TextChoices):
  DU_BOIS = "Du Bois"
  MOSTELLER = "Mosteller"
  HAYCOCK = "HAYCOCK"

class GFRMethods(models.TextChoices):
  SINGLE = "En blodprøve, Voksen"
  CHILD = "En blodprøve, Barn"
  MULTI = "Flere blodprøver"

  @classproperty
  def form_choices(cls):
    return ((choice, choice.value) for choice in cls)

class GFRStudy(models.Model):
  # Core fields
  StudyUID = models.CharField(max_length=128, primary_key=True)
  StudyStatus = models.IntegerField(default=StudyStatus.INITIAL)
  AccessionNumber = models.CharField(max_length=24, unique=True)
  StudyID = models.CharField(max_length=24)
  StationName = models.CharField(max_length=24)
  PatientName = models.CharField(max_length=128)
  PatientBirthDate = models.DateField(null=True, default=None, blank=True)
  PatientID = models.CharField(max_length=10)
  StudyDateTime = models.DateTimeField()
  StudyDescription= models.CharField(max_length=26)
  Department = models.ForeignKey(Department, on_delete=models.RESTRICT)
  GFRVersion = models.CharField(max_length=20, default=f"GFRcalc - {server_config.SERVER_VERSION}")
  # Optional fields
  GFR = models.TextField(choices=GFROptions.choices, blank=True, default=None, null=True)
  Index_GFR = models.FloatField(default=None, blank=True, null=True)
  GFRMethod = models.TextField(choices=GFRMethods.choices, default=None, null=True, blank=True)
  BodySurfaceMethod=models.TextField(choices=BodySurfaceMethods.choices, default=None, null=True, blank=True)
  PatientSex = models.BooleanField(default=None, null=True)
  PatientHeightCM = models.FloatField(default=None, null=True, blank=True)
  PatientWeightKg = models.FloatField(default=None, null=True, blank=True)
  Clearance=models.FloatField(default=None, null=True, blank=True)
  ClearanceNormalized=models.FloatField(default=None, null=True, blank=True) # This is just here for convenience
  InjectionDateTime=models.DateTimeField(default=None, null=True, blank=True)
  VialNumber=models.SmallIntegerField(default=None, null=True, blank=True)
  InjectionWeightBefore = models.FloatField(default=None, null=True, blank=True)
  InjectionWeightAfter = models.FloatField(default=None, null=True, blank=True)
  Standard=models.FloatField(default=None, null=True, blank=True)
  ThinningFactor=models.FloatField(default=None, null=True, blank=True)
  Comment=models.CharField(max_length=250, default=None, null=None, blank=True)

  class Meta:
    indexes = [
      models.Index(fields=['StudyDateTime','Department'])
    ]

  def get_injections(self):
    return InjectionSample.objects.filter(study=self)

  def to_dataset(self):
    status = self.calculate_status()

    if status != StudyStatus.CONTROL:
      return None

    dataset = Dataset()

    dataset.SOPClassUID = SecondaryCaptureImageStorage
    dataset.SOPInstanceUID = generate_uid()
    dataset.StudyDate = self.StudyDateTime.date()
    dataset.StudyTime = self.StudyDateTime.time()
    dataset.SeriesDate = self.StudyDateTime.date()
    dataset.SeriesTime = self.StudyDateTime.time()
    dataset.AccessionNumber = self.AccessionNumber
    dataset.Modality = 'OT'
    dataset.ConversionType = 'SYN'
    if self.Department.hospital is not None:
      dataset.InstitutionName = self.Department.hospital.name
      dataset.InstitutionAddress = self.Department.hospital.address
      dataset.InstitutionalDepartmentName = self.Department.name
    dataset.StudyUID = self.StudyUID
    dataset.StationName = self.StationName
    dataset.StudyDescription = self.StudyDescription
    dataset.SeriesDescription = self.GFRMethod
    dataset.PatientName = self.PatientName
    dataset.PatientID = self.PatientID


    return dataset

  @classmethod
  def from_dataset(cls, dataset: Dataset) -> Optional[Dataset]:
    ris_sequence = dataset.ScheduledProcedureStepSequence[0]
    study_date_string = ris_sequence.ScheduledProcedureStepStartDate
    study_time_string = ris_sequence.ScheduledProcedureStepStartTime

    return cls.objects.create(
      StudyUID=dataset.StudyUID,
      AccessionNumber=dataset.AccessionNumber,
      StudyID=dataset.StudyID,
      PatientName=dataset.PatientName,
      PatientBirthDate=date(
        int(dataset.PatientBirthDate[0:4]),
        int(dataset.PatientBirthDate[4:6]),
        int(dataset.PatientBirthDate[6:8])
      ),
      PatientID=dataset.PatientID,
      StudyDateTime=datetime.datetime(
        int(study_date_string[0:4]),
        int(study_date_string[4:6]),
        int(study_date_string[6:8]),
        int(study_time_string[0:2]),
        int(study_time_string[2:4]),
        int(study_time_string[4:6])
      ),
      StudyDescription=dataset.StudyDescription
    )

  def calculate_status(self) -> 'StudyStatus':
    optional_any = False

    for field in self._meta.get_fields():
      if not isinstance(field, models.Field):
        continue

      if not field.null: # Optional
        continue

      optional_any |= self.__getattribute__(field.name) is not None

    if optional_any:
      return StudyStatus.PARTIAL_FILLED

    return StudyStatus.INITIAL

  def set_deleted(self, deleted: bool):
    if deleted:
      self.StudyStatus = StudyStatus.DELETED
    else:
      self.StudyStatus = self.calculate_status()
    self.save()

  def set_control(self, control: bool):
    if control:
      self.StudyStatus = StudyStatus.CONTROL
    else:
      self.StudyStatus = self.calculate_status()
    self.save()

  def derive(self, samples: List['InjectionSample']):
    if self.PatientHeightCM is None       or \
       self.PatientWeightKg is None       or \
       len(samples) == 0                  or \
       self.InjectionWeightBefore is None or \
       self.InjectionWeightBefore is None or \
       self.ThinningFactor is None        or \
       self.Standard is None              or \
       self.InjectionDateTime is None     or \
       self.GFRMethod is None            or \
       self.PatientBirthDate is None or \
       self.PatientSex is None:

      raise ValueError

    body_surface_area = surface_area(self.PatientHeightCM, self.PatientWeightKg)

    samples_times = [sample.DateTime for sample in samples]
    samples_counts = [sample.CountPerMinutes for sample in samples]

    injection_dosage = dosis(
      self.InjectionWeightBefore - self.InjectionWeightAfter,
      self.ThinningFactor,
      self.Standard
    )

    if self.GFRMethod == GFRMethods.SINGLE:
      study_type = StudyType.ONE_SAMPLE_ADULT
    elif self.GFRMethod == GFRMethods.CHILD:
      study_type = StudyType.ONE_SAMPLE_CHILD
    else:
      study_type = StudyType.MULTI_SAMPLE

    self.Clearance, self.ClearanceNormalized = calc_clearance(
      self.InjectionDateTime,
      samples_times,
      samples_counts,
      body_surface_area,
      injection_dosage,
      study_type
    )

    if self.PatientSex:
      gender = Gender.FEMALE
    else:
      gender = Gender.MALE

    GFR_string, self.Index_GFR = kidney_function(
      self.ClearanceNormalized,
      self.PatientBirthDate,
      gender
    )
    self.GFR = GFROptions(GFR_string)

    self.save()

class HistoricStudy(models.Model):
  id = models.BigAutoField(primary_key=True)
  active_study = models.ForeignKey(GFRStudy, related_name="origin", on_delete=models.CASCADE)
  historic_study = models.ForeignKey(GFRStudy, related_name="historic", on_delete=models.CASCADE)

class InjectionSample(models.Model):
  id = models.BigAutoField(primary_key=True)
  Study = models.ForeignKey(GFRStudy, on_delete=models.CASCADE)
  DateTime = models.DateTimeField()
  CountPerMinutes = models.FloatField()
  DeviationPercentage = models.FloatField()
