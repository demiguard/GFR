from django.core.exceptions import PermissionDenied

from main_page import log_util


# TODO: Add logging to check who attempted to access
class AdminRequiredMixin:
  # Checks if the currently signed in user belongs to the 'admin' user group
  
  def dispatch(self, request, *args, **kwargs):
    curr_user = request.user

    if curr_user:
      if curr_user.user_group.name == 'admin':
        return super().dispatch(request, *args, **kwargs)
    
    raise PermissionDenied


class LoggingMixin:
  # Logs current user name, ip address and site for every incoming request to a
  # view if added as a mixin.

  def dispatch(self, request, *args, **kwargs):
    logger = log_util.get_logger(__name__)
    log_msg = ""

    if request.user:
      log_msg += f"User: {request.user.username}"
    else:
      log_msg += "User: None"
    
    log_msg += f", IP address: {request.META.get('REMOTE_ADDR')}"
    log_msg += f", PATH: {request.META.get('PATH_INFO')}"

    logger.info(log_msg)

    return super().dispatch(request, *args, **kwargs)