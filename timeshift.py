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

    def __init__(self, base, cli):
        self.base = base
        self.cli = cli
        self.description = " ".join(sys.argv)
        self._pre_snap_created = False
        self.max_backups = 10
        self.pre_snap = True
        self.post_snap = True
        self.actions = "update, upgrade"
        self.action_description = self.description.split('dnf')[1]

    def config(self):
        conf = self.read_config(self.base.conf)

        if conf.has_section('main'):
            if conf.has_option('main', 'max_backups'):
                self.max_backups = conf.getint('main', 'max_backups')
            if conf.has_option('main', 'actions'):
                self.actions = conf.get('main', 'actions')
            if conf.has_option('main', 'pre_snap'):
                self.pre_snap = conf.getbool('main', 'pre_snap')
            if conf.has_option('main', 'post_snap'):
                self.post_snap = conf.getbool('main', 'post_snap')

        self.actions_list = [x.strip() for x in self.actions.split(',')]

    def pre_transaction(self):
        if not self.pre_config:
            return
        if not self.base.transaction:
            return

        try:
            check = any(item in self.actions for item in self.cli.command.aliases)
            if check:
                print (bcolors.OKCYAN+'timeshift: creating pre snapshot'+bcolors.ENDC)
                subprocess.run(["timeshift", "--create", "--comments", "before dnf"+self.action_description], capture_output=True)
                self._pre_snap_created = True

        except subprocess.CalledProcessError as e:
            print(bcolors.FAIL+'creating of pre snapshot failed: %s'+bcolors.ENDC, e.output)

    def transaction(self):
        if not self.post_snap:
            return
        if not self.base.transaction:
            return

        try:
            check = any(item in self.actions for item in self.cli.command.aliases)
            if check:
                if not self._pre_snap_created:
                    print (bcolors.WARNING+'timeshift: skipping post snapshot because creation of pre snapshot failed'+bcolors.ENDC)

                print (bcolors.OKCYAN+'timeshift: creating post snapshot'+bcolors.ENDC)
                subprocess.run(["timeshift", "--create", "--comments", "after dnf"+self.action_description], capture_output=True)

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
            for snap in snap_list:
                if (i >= self.max_backups):
                    print (bcolors.OKCYAN+'timeshift: deleting snapshot '+snap+bcolors.ENDC)
                    subprocess.run(["timeshift", "--delete", "--snapshot", snap], capture_output=True)
                i += 1

        except subprocess.CalledProcessError as e:
            print(bcolors.FAIL+'creating of post snapshot failed: %s'+bcolors.ENDC, e.output)
