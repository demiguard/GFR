# GFR

## User creation
```
> pyhton3 manage.py shell
>> from main_page.models import User
>> u = User(username="USERNAME_OF_USER", hospital="HOSPITAL_OF_USER")
>> u.set_password('PASSWORD_OF_USER')
>> u.save()
>> exit()
```

The creation can be validated using the sqlitebrowser, where the users lie under the table called "main_page_user".