# GFR

---
## Install, Deploy, Run
### General dependencies
The project was built using:
* python 3.6
* pip3
* dcmtk v3.6.2 (https://dicom.offis.de/dcmtk.php.en)
  * findscu
  * getscu
  * storescu 
* Nginx (+ uWSGI)

### Installing and using virtualenv
Virtualenv is install through pip3:
```
> pip3 install virtualenv
```

Running the virtualenv:
```
> source venv/bin/activate
```

Exitting the virtualenv:
```
> deactivate
```

### Installing requirements
Once in the virtualenv, the required python packages can be installed by running:
```
(venv)> pip install -r requirements.txt
```

#### Installing new packages
Whenever a new package is added the ```requirements.txt``` must be updated. This can be done by running:
```
(venv)> pip freeze > requirements.txt
```
and then adding it to git (with a ```git add``` and ```git commit```).

### Running in debug mode
The Django comes with a development/debugging minimal web server, which can be ran by setting the variable ```debug=True```, under the ```settings.py``` file in the main project directory.

Once this is done, the web development web server can be ran using:
```
(venv)> python manage.py runserver
```

#### Debug mode on local network
To allow hosts on the local network to access the debug test site, run the command:
```
(venv)> python manage.py runserver 0.0.0.0:8000
```

### Deploying with nginx


---

## Example of user creation
```
(venv)> python manage.py shell
>>> from main_page.models import User, Config
>>> c = Config(config_id=1, accepted_procedures='Clearance Fler-blodprøve^GFR, Cr-51-EDTA, one sampel^GFR, Tc-99m-DTPA', rigs_aet='VIMCM', rigs_ip='10.143.128.247', rigs_port='3320', rigs_calling='RH_EDTA', pacs_aet='TEST_DCM4CHEE', pacs_ip='127.0.0.1', pacs_port='11112', pacs_calling='RH_EDTA')
>>> u = User(id=1, username='rh_test', hospital='RH', config=c)
>>> u.set_password('rh_test')
>>> c.save()
>>> u.save()
```

The creation can be validated using the sqlitebrowser, where the users lie under the table called "main_page_user" and user configurations under "main_page_config".

---

## Code documentation
...to come in the future...