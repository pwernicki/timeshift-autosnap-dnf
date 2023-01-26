# timeshift-autosnap-dnf

## Installation

Find dnf plugin  directory
```
dnf config-manager --dump | grep pluginpath
```
Copy timeshift.py to this directory.
Copy timeshift.conf to /etc/dnf/plugins/ directory.

We can change plugin behavior by modifying timeshift.conf.
