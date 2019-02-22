# GFR

## User creation
```
> pyhton3 manage.py shell

// Import the model
>> from main_page.models import User

// Create the config for the user
>> c = Config(
        accepted_procedures='Clearance Fler-blodprøve^Clearance blodprøve 2. gang^GFR, Cr-51-EDTA, one sampel^GFR, Tc-99m-DTPA',
        hosp_aet='',
        hosp_ip='',
        hosp_port=''
       )

// Create the user, using the previously created config
>> u = User(username="USERNAME_OF_USER", hospital="HOSPITAL_OF_USER", config=c)
>> u.set_password('PASSWORD_OF_USER')
>> u.save()
>> exit()
```

The creation can be validated using the sqlitebrowser, where the users lie under the table called "main_page_user".

## List of typic accepted procedures
Remember the accepted_procedures should be '^' separated.
'Clearance Fler-blodprøve^Clearance blodprøve 2. gang^GFR, Cr-51-EDTA, one sampel^GFR, Tc-99m-DTPA'
