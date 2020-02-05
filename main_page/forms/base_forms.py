from django import forms

from main_page import models
from main_page.libs.enums import GENDER_NAMINGS

# Login form
class LoginForm(forms.Form):
  username = forms.CharField()
  password = forms.CharField(widget=forms.PasswordInput())


# Ny undersøgelse
class NewStudy(forms.Form):
  cpr = forms.CharField(label='Cpr-nr.')
  name = forms.CharField(label='Navn')
  study_date = forms.DateField(label='Dato (DD-MM-ÅÅÅÅ)')
  rigs_nr = forms.CharField(label='Accession nummer')


#Form Control Study
class GrandControlPatient(forms.Form):
  #Init
  sex_options = [(i, gender) for i, gender in enumerate(GENDER_NAMINGS)]
  types = [
    (0, 'En blodprøve, voksen'),
    (1, 'En blodprøve, barn'),
    (2, 'Flere blodprøver')
  ]

  #Standard fields
  cpr                 = forms.CharField(label='Cpr-nr.',        required=False )
  name                = forms.CharField(label='Navn',           required=False )
  sex                 = forms.ChoiceField(label='Køn', choices=sex_options,  required=False, disabled=True)
  birthdate           = forms.DateField(label='Fødseldato',     required=False)
  height              = forms.CharField(label='Højde (cm)',  widget=forms.TextInput(attrs={'class' : "col-md-12"}))
  weight              = forms.CharField(label='Vægt (kg)',   widget=forms.TextInput(attrs={'class' : "col-md-12"}))
  vial_weight_before  = forms.FloatField(label='Sprøjtevægt før injektion (g)', required=False, widget=forms.TextInput(attrs={'class' : "col-md-12"}))  
  vial_weight_after   = forms.FloatField(label='Sprøjtevægt efter injektion (g)', required=False, widget=forms.TextInput(attrs={'class' : "col-md-12"}))
  injection_time      = forms.TimeField(label='Injektionstidspunkt', required=False)
  injection_date      = forms.DateField(label='InjektionsDato',      required=False, input_formats=['%d-%m-%Y'])
  thin_fac            = forms.IntegerField(label='Fortyndingsfaktor', required=False, widget=forms.TextInput(attrs={'class' : "", 'step': '1'}))
  study_type          = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect(), disabled=True)  
  stdCnt              = forms.DecimalField(label='Standardtælletal', max_digits=1 , required=False, widget=forms.TextInput(attrs={'class' : "col-md-5"}))
  bamID = forms.CharField(label='Bam ID', max_length=8, required=False, widget=forms.TextInput(attrs={'class' : "col-md-3"}))

  #Confirmation Fields
  cpr_confirm                 = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")  
  name_confirm                = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  sex_confirm                 = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  birthdate_confirm           = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  height_confirm              = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  weight_confirm              = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  vial_weight_before_confirm  = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  vial_weight_after_confirm   = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")  
  injection_time_confirm      = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  injection_date_confirm      = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  thin_fac_confirm            = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  study_type_confirm          = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class' : "confirm-checkbox"}), label="")
  stdCnt_confirm              = forms.BooleanField(required=False, label="")

  #Startup
  def __init__(self, *args, **kwargs):
    super(GrandControlPatient, self).__init__(*args, **kwargs)
    self.fields['cpr'].widget.attrs['readonly']                 = True
    self.fields['name'].widget.attrs['readonly']                = True
    self.fields['sex'].widget.attrs['readonly']                 = True    
    self.fields['birthdate'].widget.attrs['readonly']           = True
    self.fields['height'].widget.attrs['readonly']              = True
    self.fields['weight'].widget.attrs['readonly']              = True
    self.fields['vial_weight_before'].widget.attrs['readonly']  = True
    self.fields['vial_weight_after'].widget.attrs['readonly']   = True
    self.fields['injection_time'].widget.attrs['readonly']      = True
    self.fields['injection_date'].widget.attrs['readonly']      = True
    self.fields['thin_fac'].widget.attrs['readonly']            = True
    self.fields['study_type'].widget.attrs['readonly']          = True
    self.fields['stdCnt'].widget.attrs['readonly']              = True
    self.fields['stdCnt'].widget.attrs['class']                 = 'form-input'
    self.fields['stdCnt_confirm'].widget.attrs['class']         = 'confirm-row-checkbox'    


class ControlPatient6(forms.Form):
  sample_time = forms.TimeField(label='Dato',  required=False)
  sample_date = forms.DateField(label='Tidpunkt',  required=False, input_formats=['%d-%m-%Y'])
  sample_cnt  = forms.FloatField(label='Tælletal', required=False, widget=forms.TextInput(attrs={'class' : "sample_count"}))

  sample_confirm = forms.BooleanField(required=False, label='')

  def __init__(self, *args, **kwargs):
    super(ControlPatient6, self).__init__( *args, **kwargs)
    self.fields['sample_time'].widget.attrs['readonly'] = True    
    self.fields['sample_date'].widget.attrs['readonly'] = True  
    self.fields['sample_cnt' ].widget.attrs['readonly'] = True
    self.fields['sample_time'].widget.attrs['class']    = 'form-input'    
    self.fields['sample_date'].widget.attrs['class']    = 'form-input'
    self.fields['sample_cnt'].widget.attrs['class']     = 'form-input sample_count'
    self.fields['sample_confirm'].widget.attrs['class'] = 'confirm-row-checkbox' 

class FillStudyTest(forms.Form):
  study_time = forms.TimeField(label='Blodprøve taget kl:', required=False)
  study_date = forms.DateField(label='Blodprøve taget dato', required=False)

  def __init__(self, *args, **kwargs):
    super(FillStudyTest, self).__init__(*args, **kwargs)

    # Add bootstrap class to fields
    for _, field in self.fields.items():
      field.widget.attrs['class'] = 'form-control'


class SearchForm(forms.Form):
  name = forms.CharField(label='Navn', required=False)
  cpr  = forms.CharField(label='Cpr-nr.', required=False)
  accession_number = forms.CharField(label='Accession nummer', required=False)
  from_date = forms.DateField(label='Fra dato (DD-MM-ÅÅÅÅ)', required=False)
  to_date = forms.DateField(label='Til dato (DD-MM-ÅÅÅÅ)', required=False)

  def __init__(self, *args, **kwargs):
    super(SearchForm, self).__init__(*args, **kwargs)

    # Add bootstrap class to fields
    for _, field in self.fields.items():
      field.widget.attrs['class'] = 'form-control'


#This form is intented just to be one form containing all the other forms for fill study
#Note that this cannot contain Fillstudy Test, since there may be multiple Tests
class FillStudyGrandForm(forms.Form):
  #init
  types = [
    (0, 'En blodprøve, voksen'),
    (1, 'En blodprøve, barn'),
    (2, 'Flere blodprøver')
  ]
  sex_options = [(i, gender) for i, gender in enumerate(GENDER_NAMINGS)]
  
  #Fields
  bamID = forms.CharField(label='Bam ID', max_length=8, required=False, widget=forms.TextInput(attrs={'class' : "col-md-3"}))
  birthdate = forms.DateField(label='Fødselsdato (DD-MM-ÅÅÅÅ)', required=False)
  cpr  = forms.CharField(label='Cpr-nr', required=False)
  height = forms.CharField(label='Højde (cm)', required=False)
  injection_time = forms.TimeField(label='Injektionstidspunkt (tt:mm)', required=False)
  injection_date = forms.DateField(label='Injektionsdato (DD-MM-ÅÅÅÅ)', required=False)  
  name = forms.CharField(label='Navn', required=False)
  save_fac = forms.BooleanField(required=False, label='Gem')
  sex = forms.ChoiceField(choices=sex_options, label='Køn', required=False)
  standcount = forms.FloatField(label="Standardtælletal", required=False)
  study_type = forms.ChoiceField(label='Metode', choices=types, widget=forms.RadioSelect())
  thin_fac = forms.CharField(label='Fortyndingsfaktor', required=False)
  vial_weight_after = forms.CharField(label='Sprøjtevægt efter injektion (g)', required=False)
  vial_weight_before = forms.CharField(label='Sprøjtevægt før injektion (g)', required=False)
  weight = forms.CharField( label='Vægt (kg)', required=False)


  def __init__(self, *args, **kwargs):
    super(FillStudyGrandForm, self).__init__(*args, **kwargs)
    self.fields['cpr'].widget.attrs['readonly'] = True
    self.fields['name'].widget.attrs['readonly'] = True


class GetBackupDateForm(forms.Form):
  dateofmessurement = forms.DateField(label='Backup fra dato (DD-MM-ÅÅÅÅ)', required=False)

class NukeListStudiesForm(forms.Form):
  l_hospital = forms.ModelChoiceField(label='Hospital', required=True, widget=forms.Select, queryset=models.Hospital.objects.all().values_list('short_name', flat=True))
  l_bamID = forms.CharField(label='Bam ID', max_length=8, required=True, widget=forms.TextInput(attrs={'class' : "col-md-3"}))

class NukeDeletedStudiesForm(forms.Form):
  d_hospital = forms.ModelChoiceField(label='Hospital', required=True, widget=forms.Select, queryset=models.Hospital.objects.all().values_list('short_name', flat=True))
  d_bamID = forms.CharField(label='Bam ID', max_length=8, required=True, widget=forms.TextInput(attrs={'class' : "col-md-3"}))

