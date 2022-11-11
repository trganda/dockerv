# Openldap + phpLdapAdmin

This is openldap container with phpldapadmin based on https://github.com/osixia/docker-openldap and https://github.com/osixia/docker-phpLDAPadmin.

Add the `java.schema` and `corba.schema` has been added to bootstrap schema for support Java JNDI.

```
FROM osixia/openldap:1.5.0

ADD schema/java.schema /container/service/slapd/assets/config/bootstrap/schema/custom/
ADD schema/corba.schema /container/service/slapd/assets/config/bootstrap/schema/custom/
```

