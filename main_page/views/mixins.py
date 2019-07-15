from django.core.exceptions import PermissionDenied


# TODO: Add logging to check who attempted to access
class AdminRequiredMixin:
  # Checks if the currently signed in user belongs to the 'admin' user group
  
  def dispatch(self, request, *args, **kwargs):
    curr_user = request.user

    if curr_user:
      if curr_user.user_group.name == 'admin':
        return super().dispatch(request, *args, **kwargs)
    
    raise PermissionDenied