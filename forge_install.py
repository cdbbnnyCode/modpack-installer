#!/usr/bin/env python3
import sys
import os
import subprocess
import time
from util import *

# https://files.minecraftforge.net/maven/net/minecraftforge/forge/1.12.2-14.23.5.2847/forge-1.12.2-14.23.5.2847-universal.jar


def main(manifest, mcver, mlver, packname, mc_dir, manual):

    forge_fullver = mcver + '-' + mlver
    url = 'https://files.minecraftforge.net/maven/net/minecraftforge/forge/%s/forge-%s-installer.jar' \
            % (forge_fullver, forge_fullver)
    outpath = '/tmp/forge-%s-installer.jar' % forge_fullver
    if not os.path.exists(outpath):
        resp = download(url, outpath, True)
        if resp != 200:
            print("Got %d error trying to download Forge" % resp)
            sys.exit(2)

    # Run the Forge auto-install hack
    if manual:
        print("Using the manual installer!")
        print("***** NEW: INSTALL TO THE MAIN .MINECRAFT DIRECTORY *****")
        print("*****   (Just hit 'OK' with the default settings)   *****")
        for i in range(20):
            print("^ ", end="", flush=True)
            time.sleep(0.05)

        subprocess.run(['java', '-jar', outpath])
    else:
        if not os.path.exists('ForgeHack.class'):
            subprocess.run(['javac', 'ForgeHack.java'])
        exit_code = subprocess.run(['java', 'ForgeHack', outpath, mc_dir]).returncode
        if exit_code != 0:
            print("Error running the auto-installer, try using --manual.")
            sys.exit(3)

    if not os.path.exists(mc_dir + '/versions/' + get_version_id(mcver, mlver)):
        print("Forge installation failed.")
        sys.exit(3)


def get_version_id(mcver, mlver):
    mcv_split = mcver.split('.')
    mcv = int(mcv_split[0]) * 1000 + int(mcv_split[1])

    if mcv > 1012:
        return '%s-forge-%s' % (mcver, mlver)
    else:
        return '%s-forge%s-%s' % (mcver, mcver, mlver)
