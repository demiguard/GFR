import datetime

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

from .libs import server_config


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
# All server configs with an id differtn from 1 is ignored.
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


