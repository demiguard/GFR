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
#Configuration
class Config(models.Model):
  config_id = models.AutoField(primary_key=True)
  Accepted_predure = models.TextField()

  def __str__(self):
    return 'config-' + self.config_id


# User class
class User(AbstractBaseUser):
  id = models.AutoField(primary_key=True)
  username = models.CharField(max_length=120, unique=True)
  password = models.CharField(max_length=120)
  #config   = models.ForeignKey(Config, on_delete= models.CASCADE, unique=True, default=Config())


  HOSPS = (
    ('RH', 'Rigshospitalet'),
    ('HH', 'Herlev hospital'),
    ('FH', 'Frederiksberg hospital'),
    ('BH', 'Bispebjerg hospital'),
    ('GL', 'Glostrup hospital'),
  )
  hospital = models.CharField(max_length=3, choices=HOSPS)

  USERNAME_FIELD = 'username'
  REQUIRED_FIELDS = ['password', 'hospital']

  def __str__(self):
    return self.username

  
