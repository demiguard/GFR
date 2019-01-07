from django import forms

# Login form
class LoginForm(forms.Form):
  username = forms.CharField()
  password = forms.CharField(widget=forms.PasswordInput())

  hosp_choices = [
    (0, 'Rigshospitalet'),
    (1, 'Herlev hospital'),
    (2, 'Frederiksberg hospital'),
    (3, 'Bispebjerg hospital')
  ]

  hospital = forms.CharField(widget=forms.Select(choices=hosp_choices))

# Ny undersøgelse
class NewStudy(forms.Form):
  cpr = forms.IntegerField(label='Cpr. nr.')
  name = forms.CharField(label='Navn')
  study_date = forms.DateField(label='Dato (YYYY-MM-DD)')
  ris_nr = forms.CharField(label='RIS nr.')

# Udfyld undersøgelse
class FillStudyDaily(forms.Form):
  factor = forms.IntegerField(label='Faktor')
  batch = forms.IntegerField(label='Batch')
  standard = forms.IntegerField(label='Standard tælletal')

class FillStudyInfo(forms.Form):
  name = forms.CharField(label='Navn')
  sex = forms.CharField(label='Køn')
  age = forms.IntegerField(label='Alder')
  height = forms.FloatField(label='Højde (cm)')
  weight = forms.FloatField(label='Vægt (kg)')
  vial = forms.IntegerField(label='Sprøjte')
  vial_weight_before = forms.FloatField(label='Sprøjtevægt før Injektion (g)')
  vial_weight_after = forms.FloatField(label='Sprøjtevægt efter injektion (g)')
  injection_time = forms.TimeField(label='Injektionstidspunkt (tt:mm)')

class FillStudyType(forms.Form):
  types = [
    (0, 'Et punkt voksen'),
    (1, 'Et punkt barn'),
    (2, 'Flere punkter voksen')
  ]

  study_type = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect())

class FillStudyTest(forms.Form):
  test_time = forms.TimeField(label='', required=False)
  test_value = forms.FloatField(label='', required=False)