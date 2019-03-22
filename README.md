# GFR

---
## Install, Deploy, Run
### General dependencies
The project was built using:
* python 3.6
* pip3
* dcmtk v3.6.2
  * findscu
  * getscu
  * storescu 
* Nginx (+ uWSGI)

### Installing and using virtualenv
Virtualenv is install through pip3:
```
> pip3 install virtualenv
```

Running the virtualenv
```

```


### Installing requirements


### Running in debug mode


### Deploying with nginx


---

## Example of user creation
```
> python3 manage.py shell
>>> from main_page.models import User, Config
>>> c = Config(config_id=1, accepted_procedures='Clearance Fler-blodprøve^Clearance blodprøve 2. gang^GFR, Cr-51-EDTA, one sampel^GFR, Tc-99m-DTPA', rigs_aet='VIMCM', rigs_ip='10.143.128.247', rigs_port='3320', rigs_calling='RH_EDTA', pacs_aet='TEST_DCM4CHEE', pacs_ip='127.0.0.1', pacs_port='11112', pacs_calling='RH_EDTA')
>>> u = User(id=1, username='rh_test', hospital='RH', config=c)
>>> u.set_password('rh_test')
>>> c.save()
>>> u.save()
>>> exit()
```

The creation can be validated using the sqlitebrowser, where the users lie under the table called "main_page_user" and user configurations under "main_page_config".

## Linking with BAM id
...Feature to come in the future...

---

## Code documentation
...to come in the future...