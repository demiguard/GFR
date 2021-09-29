import ldap



ldap_server_url = "ldaps://regionh.top.local"


conn = ldap.initialize(ldap_server_url)
conn.set_option(ldap.OPT_X_TLS_CACERTFILE, '/home/christoffer/Documents/clairvoyance/GFR/ldap/ldapcert.pem')
conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
#
#conn.set_option(ldap.OPT_X_TLS_CERTFILE, "/home/christoffer/Documents/clairvoyance/GFR/ldap/ldapcert.crt")
#conn.set_option(ldap.OPT_X_TLS_KEYFILE, 'ldapkey.key')
#print(dir(conn))

conn.unbind_s()



print(res)
