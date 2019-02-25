from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


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
  accepted_procedures = models.TextField(default='') # '^' separated list of procedures
  rigs_aet = models.TextField(default='')
  rigs_ip = models.TextField(default='')
  rigs_port = models.TextField(default='')
  rigs_calling = models.TextField(default='')
  pacs_aet = models.TextField(default='')
  pacs_ip = models.TextField(default='')
  pacs_port = models.TextField(default='')
  pacs_calling = models.TextField(default='')

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
    on_delete=models.CASCADE,
    null=True
  )

  HOSPS = (
    ('RH', 'Rigshospitalet'),
    ('HH', 'Herlev hospital'),
    ('HI', 'Hillerød hospital'),
    ('FH', 'Frederiksberg hospital'),
    ('BH', 'Bispebjerg hospital'),
    ('GL', 'Glostrup hospital'),
  )
  hospital = models.CharField(max_length=3, choices=HOSPS)

  USERNAME_FIELD = 'username'
  REQUIRED_FIELDS = ['password', 'hospital']

  def __str__(self):
    return self.username

  
