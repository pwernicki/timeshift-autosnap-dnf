import sys 
import dnf 
import re
import subprocess

class bcolors:
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

class Timeshift(dnf.Plugin):
    name = 'timeshift'
 
    def __init__(self, base):
        self.base = base
        self.description = " ".join(sys.argv)
        self._pre_snap_created = False
 
    def pre_transaction(self):
        if not self.base.transaction:
            return
 
        try:
            print (bcolors.OKCYAN+'timeshift: creating pre snapshot'+bcolors.ENDC)
            subprocess.run(["timeshift", "--create", "--comments", "before dnf"+self.description.split('dnf')[1]], capture_output=True)
           
            self._pre_snap_created = True
 
        except subprocess.CalledProcessError as e:
            print(bcolors.FAIL+'creating of pre snapshot failed: %s'+bcolors.ENDC, e.output)
 
    def transaction(self):
        if not self.base.transaction:
            return
 
        if not self._pre_snap_created:
            print (bcolors.WARNING+'timeshift: skipping post snapshot because creation of pre snapshot failed'+bcolors.ENDC)
            return
 
        try:
            print (bcolors.OKCYAN+'timeshift: creating post snapshot'+bcolors.ENDC)
            subprocess.run(["timeshift", "--create", "--comments", "after dnf"+self.description.split('dnf')[1]], capture_output=True)

            timeshift_out = subprocess.run(["timeshift", "--list"], capture_output=True).stdout

            regexp = "[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2}\\s+[A-Z]+"

            snap_find = re.findall(regexp, str(timeshift_out))

            snap_list = []

            for find in snap_find:
                find_tup = tuple(find.split())
                if (find_tup[1] == 'O'):
                    snap_list.append(find_tup[0])

            snap_list.sort(reverse=True)

            i = 0
            max_backups = 10

            for snap in snap_list:
                if (i >= max_backups):
                    print (bcolors.OKCYAN+'timeshift: deleting snapshot '+snap+bcolors.ENDC)
                    subprocess.run(["timeshift", "--delete", "--snapshot", snap], capture_output=True)
                i += 1
 
        except subprocess.CalledProcessError as e:
            print(bcolors.FAIL+'creating of post snapshot failed: %s'+bcolors.ENDC, e.output)
