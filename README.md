# GFR

## How to run tests
The following script will run the tests and generate reports using ```coverage.py```. The reports are ```xml``` files and can be interpreted with e.g. the VS Code extension; Coverage Gutter
```
(venv)> ./run-tests.sh
```
Remember to make the script executable using:
```
(venv)> chmod a+x ./run-tests.sh
```

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

The project was built and tested on CentOS 7 and Ubuntu 18.04 (bionic beaver)

### Installing and using virtualenv
Virtualenv is install through pip3:
```
> pip3 install virtualenv
```

Initializing virtualenv
```
> virtualenv venv
```

Running virtualenv:
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
1. Install uwsgi:
```
> pip3 install uwsgi
```
2. Test that the Django application can run using uwsgi
```
(venv)> uwsgi --http :8000 --module clairvoyance.wsgi
```
3. Install nginx (**Ubuntu**)
```
> sudo apt install nginx
```
3. Install nginx (**CentOS 7**)
```
> sudo yum install epel-release
> sudo yum install nginx
```
4. Test that nginx was correctly installed
```
sudo systemctl start nginx
```
Then goto localhost:80 in a browser, this should display a welcome message.

5. Configure nginx
Download the file: https://github.com/nginx/nginx/blob/master/conf/uwsgi_params, and place it in the main Django project directory.

If the /etc/nginx/sites-available and /etc/nginx/sites-enabled directories doesn't exist, then create them and edit the file /etc/nginx/nginx.conf and add the line:
```
include /etc/nginx/sites-enabled/*;
```
(No need to include the sites-avaiable since sites-enabled will contain symlinks to configs inside this directory)

Write the following to a config file under /etc/nginx/sites-available/clairvoyance_nginx.conf
```
# clairvoyance_nginx.conf

# the upstream component nginx needs to connect to
upstream django {
    server unix:///home/simon/Documents/clearance-stuff/GFR/clairvoyance.sock; # for a file socket
}

# configuration of the server
server {
    listen      80; # the port your site will be served on
    server_name 193.3.238.103; # substitute your machine's IP address
    charset     utf-8;

    # max upload size
    client_max_body_size 75M;

    location /static {
        alias /home/simon/Documents/clearance-stuff/GFR/main_page/static; # your Django project's static files
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        uwsgi_pass  django;
        include     /home/simon/Documents/clearance-stuff/GFR/uwsgi_params; # the uwsgi_params file you installed
    }
}
```
Allow nginx to see this file by creating a symlink to it under the directory: /etc/nginx/sites-enabled/ by using the following command:
```
> sudo ln -s /etc/nginx/sites-available/clairvoyance_nginx.conf /etc/nginx/sites-enabled/clairvoyance_nginx.conf
```

Edit the file /etc/nginx/default, so that nginx runs on port 8081 by default.

6. Restart the nginx service:
```
> sudo /etc/init.d/nginx restart
```
7. Test that the server can run using:
```
> uwsgi --socket clairvoyance.sock --module clairvoyance.wsgi --chmod-socket=666
```
Now you should be able to go to 'localhost' in a browser and see the server running (we can use just 'localhost' since we are running on port 80)

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

## Notes
Example of different user agents (```request.META['HTTP_USER_AGENT']```):
Internet explorer on the RH laptop: 
Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko

Firefox on Ubuntu 18.04: 
Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:66.0) Gecko/20100101 Firefox/66.0

Chrome on Ubuntu 18.04: 
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36


## Code documentation
...to come in the future...