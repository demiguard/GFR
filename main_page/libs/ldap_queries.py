import ldap
from ldap.ldapobject import LDAPObject
from key import LDAP_PASSWORD

base_ldap_path = "OU=Region Hovedstaden,DC=regionh,DC=top,DC=local"
ldap_username  = "REGIONH\RGH-S-GFRLDAP"
ldap_server    = "ldap://regionh.top.local"

def initialize_connection():
  """
    Initializes the ldap connection with server side ldap credentials
  
    Returns:
      ldap.LDAPObject - this is a primary object in python-ldap module.

    Note you probbally can make this django_auth_ldap module by using group queries, but this includes populating the User with tags.
  """
  conn = ldap.initialize(ldap_server)
  conn.start_tls_s()
  conn.simple_bind_s(ldap_username, LDAP_PASSWORD)
  return conn

def CheckGroup(conn : LDAPObject, group_ldap_path : str, BAMID : str) -> bool:
  """
    Checks if a user, indentified by their bamID, is member of a group.
    The group name should be an LDAP path.
    Args:
      conn : ldap.LDAPObject - a active ldap connection, use ldap_queries.initialize_connection() to get this object
      group_ldap_path : str  - A valid ldap group path to be checked for. 
        Example : CN=RGH-B-SE Jabber Adgang,OU=Jabber,OU=Ressource Grupper,OU=FAELLES Administration,OU=Region Hovedstaden,DC=regionh,DC=top,DC=local
      BAMID : str - The bam id of the user to be checked.
        Example: 
          AAAA0000
    Returns
      query_answer : bool - if the user is part of the group or not
  """
  searchFilter = f"(&(objectClass=user)(memberof:1.2.840.113556.1.4.1941:=CN={group_ldap_path},OU=GFR Clearance,OU=Ressource Grupper,OU=FAELLES Administration,OU=Region Hovedstaden,DC=regionh,DC=top,DC=local)(cn={BAMID}))"
  res = conn.search_s(base_ldap_path, ldap.SCOPE_SUBTREE, searchFilter)
  if res:
    return True
  else:
    return False
