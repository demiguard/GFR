from main_page.models import UserGroup  # Making usergroup accessible globally

def usergroup_constants(request):
    return {
        'UserGroup': UserGroup
    }