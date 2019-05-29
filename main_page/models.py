import datetime

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .libs import server_config


# Manager class of Sser class
class UserManager(BaseUserManager):
  def create_user(self, username, password, hosp):
    # Args checking
    if not username:
      raise ValueError('Users must have a username')

    if not password:
      raise ValueError('Users must have a password')

    if not hosp:
      raise ValueError('Users must be assigned a hospital')

    # User construction
    user = self.model(
      username,
      hosp
    )

    user.set_password(password)
    user.save(using=self._db)

    return user

  def create_superuser(self, username, password, hosp):
    return self.create_user(username, password, hosp)

# Configuration for a user
class Config(models.Model):
  config_id = models.AutoField(primary_key=True)
  accepted_procedures = models.CharField(max_length=1000, default='', blank=True) # '^' separated list of procedures
  rigs_aet = models.CharField(max_length=200, default='')
  rigs_ip = models.CharField(max_length=200, default='')
  rigs_port = models.CharField(max_length=200, default='')
  rigs_calling = models.CharField(max_length=200, default='')
  pacs_aet = models.CharField(max_length=200, default='')
  pacs_ip = models.CharField(max_length=200, default='')
  pacs_port = models.CharField(max_length=200, default='')
  pacs_calling = models.CharField(max_length=200, default='')

# Department class,
# The purpose of this class is to hold information specific to a department
class Department(models.Model):
  department_id = models.AutoField(primary_key=True)
  thining_factor = models.FloatField(default=0.0, null=True)
  thining_factor_change_date = models.DateField(default=datetime.date(1,1,1))
  department = models.CharField(default='', max_length = 200, null=True)
  hospital_Name = models.CharField(default='', max_length = 200, null=True) 
  address = models.CharField(default='', max_length = 200, null=True)


# User class
# REMARK / TODO: User creation MUST be done through the command line, see the README for instructions
class User(AbstractBaseUser):
  id = models.AutoField(primary_key=True)
  username = models.CharField(max_length=120, unique=True)
  password = models.CharField(max_length=120)
  
  # TODO: Put some of the below text and argumentation into the README or a documentation doc.
  # OneToOne field, since we don't want QuerySets when retreiving the objects, see: https://stackoverflow.com/questions/5870537/whats-the-difference-between-django-onetoonefield-and-foreignkey
  # CASCADE, since we want to just delete the config if a user is deleted.
  config = models.OneToOneField(
    Config,
    on_delete=models.SET_NULL,
    null=True
  )
  
  department = models.ForeignKey(
    Department,
    on_delete=models.SET_NULL,
    null=True
  )
  


  hospitals = [(k,v) for k,v in server_config.hospitals.items()]
  hospital = models.CharField(max_length=3, choices=hospitals)

  USERNAME_FIELD = 'username'
  REQUIRED_FIELDS = ['password', 'hospital']

  def __str__(self):
    return self.username


# Maintains a list of all patients which have been sent to PACS
class HandledExaminations(models.Model):
  rigs_nr = models.CharField(primary_key=True, max_length=20)
