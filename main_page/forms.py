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
  cpr = forms.CharField(label='Cpr nr.', required=False, widget=forms.TextInput(attrs={'readonly':'readonly'}))
  name = forms.CharField(label='Navn', required=False)
  sex = forms.CharField(label='Køn', required=False)
  age = forms.IntegerField(label='Alder', required=False, min_value=0)
  height = forms.FloatField(label='Højde (cm)', required=False, min_value=0, max_value=300)
  weight = forms.FloatField(label='Vægt (kg)', required=False, min_value=0, max_value=1000)
  std_cnt = forms.IntegerField(label='Standart tælletal', min_value=0)
  thin_fac = forms.IntegerField(label='Fortyndings factor', min_value = 0)
  vial = forms.IntegerField(label='Sprøjte', required=False, min_value=0)
  vial_weight_before = forms.FloatField(label='Sprøjtevægt før Injektion (g)', required=False, min_value=0)
  vial_weight_after = forms.FloatField(label='Sprøjtevægt efter injektion (g)', required=False, min_value=0)
  injection_time = forms.TimeField(label='Injektionstidspunkt (tt:mm)', required=False)
  injection_date = forms.DateField(label='Injektionsdato (YYYY-MM-DD)', required=False)

class Fillpatient(forms.Form):
  cpr = forms.CharField(label='Cpr nr.', required=False, widget=forms.TextInput(attrs={'readonly':'readonly'}))
  name = forms.CharField(label='Navn', required=False)
  sex = forms.CharField(label='Køn', required=False)
  age = forms.IntegerField(label='Alder', required=False, min_value=0)
  
class Fillexamination(forms.Form):
  vial_weight_before = forms.FloatField(label='Sprøjtevægt før Injektion (g)', required=False, min_value=0)
  vial_weight_after = forms.FloatField(label='Sprøjtevægt efter injektion (g)', required=False, min_value=0)
  injection_time = forms.TimeField(label='Injektionstidspunkt (tt:mm)', required=False)
  injection_date = forms.DateField(label='Injektionsdato (YYYY-MM-DD)', required=False)  

class Filldosis(forms.Form):
  height = forms.FloatField(label='Højde (cm)', required=False, min_value=0, max_value=300)
  weight = forms.FloatField(label='Vægt (kg)', required=False, min_value=0, max_value=1000)
  std_cnt = forms.IntegerField(label='Standart tælletal', min_value=0)
  thin_fac = forms.IntegerField(label='Fortyndings factor', min_value = 0)

class FillStudyType(forms.Form):
  types = [
    (0, 'Et punkt voksen'),
    (1, 'Et punkt barn'),
    (2, 'Flere punkter voksen')
  ]

  study_type = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect())

class FillStudyTest(forms.Form):
  test_time = forms.TimeField(label='Prøvetidspunkt (tt:mm)', required=False)
  test_date = forms.DateField(label='Dato (YYYY-MM-DD)', required=False)
  test_value = forms.FloatField(label='Prøvetælletal (cpm)', required=False, min_value=0)