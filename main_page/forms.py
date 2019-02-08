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

class Fillpatient_1(forms.Form):
  cpr = forms.CharField(label='Cpr nr.', required=False)
  name = forms.CharField(label='Navn', required=False)
  sex = forms.CharField(label='Køn', required=False)
  age = forms.IntegerField(label='Alder', required=False, min_value=0)
  
class Fillpatient_2(forms.Form):
  height = forms.FloatField(label='Højde (cm)', required=False, min_value=0)
  weight = forms.FloatField(label='Vægt (kg)', required=False, min_value=0)

class Fillexamination(forms.Form):
  vial_weight_before = forms.FloatField(label='Sprøjtevægt før Injektion (g)', required=False, min_value=0)
  vial_weight_after = forms.FloatField(label='Sprøjtevægt efter injektion (g)', required=False, min_value=0)
  injection_time = forms.TimeField(label='Injektionstidspunkt (tt:mm)', required=False)
  injection_date = forms.DateField(label='Injektionsdato (YYYY-MM-DD)', required=False)  

class Filldosis(forms.Form):
  std_cnt = forms.IntegerField(label='Standard tælletal', required=False, min_value=0)
  thin_fac = forms.IntegerField(label='Faktor', required=False, min_value = 0)

class FillStudyType(forms.Form):
  types = [
    (0, 'Et punkt voksen'),
    (1, 'Et punkt barn'),
    (2, 'Flere punkter voksen'),
    (3, 'Flere punkter barn')
  ]

  study_type = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect())

class FillStudyTest(forms.Form):
  test_time = forms.TimeField(label='Prøvetidspunkt (tt:mm)', required=False)
  test_date = forms.DateField(label='Dato (YYYY-MM-DD)', required=False)

class GetStudy(forms.Form):
  name = forms.CharField(label='Navn',required = False)
  cpr  = forms.CharField(label='CPR', required = False)
  Rigs = forms.CharField(label='Rigs Nummer')
  Dato = forms.DateField(label='Dato')
