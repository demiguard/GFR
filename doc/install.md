# Install, Deploy, Run
## General dependencies
The project was built using:
* python 3.8
* pip
* Nginx (+ uWSGI)
* MySQL 8 or later (MariaDB 10 or later)

The project was built and tested on CentOS 8 and Ubuntu 18.04

## Installing pytho 3.8
Ubuntu:
```
> sudo apt install -y python3.8
```
CentOS:
```
> sudo yum install -y python38
```

## Installing and using virtualenv
Virtualenv is installed through pip:
```
> python3.8 -m pip install virtualenv
```

Initializing virtualenv
```
> python3.8 -m virtualenv venv
```

Running virtualenv:
```
> source venv/bin/activate
```

Exitting the virtualenv:
```
> deactivate
```

## Installing MySQL
This step *MUST* be done before install requirements using pip, as the ```mysqlclient``` package has additional external dependencies.

Ubuntu:
```
> sudo apt install mysql-server
> sudo apt install python3.8-devel
```

CentOS:
```
> sudo yum install -y mysql-server
> sudo yum install -y python38-devel
```

The ```python3.8-devel```/```python38-devel``` is required for the ```mysqlclient``` package.

## Installing requirements
Once in the virtualenv, the required python packages can be installed by running:
```
(venv)> pip install -r requirements.txt
```

### Installing new packages
Whenever a new package is added the ```requirements.txt``` must be updated. This can be done by running:
```
(venv)> pip freeze > requirements.txt
```
and then adding it to git (with a ```git add``` and ```git commit```).

## Installing Git Hooks
All custom git hooks are located in the directory ```git_hooks```. To install a git hook run (from the ```git_hooks``` directory):
```
> cp <HOOK> ../.git/hooks/<HOOK_NAME>
```
Example for ```python-compile-hook``` which is a pre-commit hook, it checks if all staged python files can be correctly compiled/interpreted, before allowing you to commit the files:
```
> cp python-compile-hook ../.git/hooks/pre-commit
```

## Initialize database
### Databse and user creation
The database and user *MUST* be created with below commands, as changing them will differ from the database connection settings under ```clairvoyance/settings.py```.
```
> sudo mysql
mysql> CREATE DATABASE gfrdb;
mysql> CREATE USER 'gfr'@'localhost' IDENTIFIED BY 'gfr';
mysql> GRANT ALL PRIVILEGES ON gfrdb.* TO 'gfr'@'localhost';
mysql> FLUSH PRIVILEGES;
mysql> quit
```
Ensure that the user can login with
```
> mysql -u gfr -p
```

### Table schemas
The easiest way to initialize database tables and data is by using a snapshot from the existing database using an SQL dump.
```
(gfr) > mysqldump gfrdb > dbdump.sql
```
which can then be loaded into the new database by
```
> mysql -u gfr -p gfrdb < dbdump.sql
```

### MariaDB specifics
If MariaDB is being used instead of MySQL, e.g. for development purposes, then the SQL dump file might have be modified:
1. Open the SQL dump file and replace all occurrences of ```utf8mb4_0900_ai_ci``` with ```utf8mb4_general_ci```.
2. MariaDB should now be able to import the dump.

## Running in debug mode
The Django comes with a development/debugging minimal web server, which can be ran by setting the variable ```debug=True```, under the ```settings.py``` file in the main project directory.

Once this is done, the web development web server can be ran using:
```
(venv)> python manage.py runserver
```

### Debug mode on local network
To allow hosts on the local network to access the debug test site, run the command:
```
(venv)> python manage.py runserver 0.0.0.0:8000
```

Now the site should be accessible via.: http://<YOUR_IP_ADDRESS>:8000

## Deploying with nginx
The following steps is a minor rewrite of https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html, if any problems occur this tutorial can possibly of help.

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
3. Install nginx (**CentOS**)
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

## Running tests
The following script will run the tests and generate reports using ```coverage.py```. The reports are ```xml``` files and can be interpreted with e.g. the VS Code extension; Coverage Gutter
```
(venv)> ./run-tests.sh
```

The script comes with help information for more advanced usage:
```
(venv)> ./run-tests.sh --help
```

Remember to make the script executable using:
```
(venv)> chmod a+x ./run-tests.sh
```
