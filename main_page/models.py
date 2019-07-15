import datetime

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

from .libs import server_config


class Hospital(models.Model):
  id = models.AutoField(primary_key=True)
  name = models.CharField(default='', max_length=200, null=True)

  short_name = models.CharField(max_length=8, null=True)
  address = models.CharField(default='', max_length = 200, null=True)


# Used to filter reveiced dicom objects from PACS
class ProcedureType(models.Model):
  id = models.AutoField(primary_key=True)
  type_name = models.CharField(max_length=200, default='', blank=True)


# Configuration for a department
class Config(models.Model):
  id = models.AutoField(primary_key=True)

  # List of procedure types related to GFR examinations
  accepted_procedures = models.ManyToManyField(ProcedureType)

  # Configuration to ris server
  ris_aet = models.CharField(max_length=200, default='')
  ris_ip = models.CharField(max_length=200, default='')
  ris_port = models.CharField(max_length=200, default='')
  ris_calling = models.CharField(max_length=200, default='')

  # Configuration to PACS server
  pacs_aet = models.CharField(max_length=200, default='')
  pacs_ip = models.CharField(max_length=200, default='')
  pacs_port = models.CharField(max_length=200, default='')
  pacs_calling = models.CharField(max_length=200, default='')


class Department(models.Model):
  id = models.AutoField(primary_key=True)
  name = models.CharField(default='', max_length = 200, null=True)

  # Associated hospital for this department
  hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True)

  config = models.OneToOneField(Config, on_delete=models.SET_NULL, null=True)

  # Temporarily store daily thinning factors
  thining_factor = models.FloatField(default=0.0, null=True)
  thining_factor_change_date = models.DateField(default=datetime.date(1,1,1))


# Defines user permissions
class UserGroup(models.Model):
  id = models.AutoField(primary_key=True)
  name = models.CharField(max_length=200)


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


# Maintains a list of examinations sent to PACS
# This means we don't have to query PACS for all previous examinations
class HandledExaminations(models.Model):
  accession_number = models.CharField(primary_key=True, max_length=20)
