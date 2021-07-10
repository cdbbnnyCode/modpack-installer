#!/usr/bin/env python3
import sys
import os
import json
import requests
import subprocess
from util import *

# https://files.minecraftforge.net/maven/net/minecraftforge/forge/1.12.2-14.23.5.2847/forge-1.12.2-14.23.5.2847-universal.jar


def main(manifest, mcver, mlver, packname, mc_dir, manual):

    forge_fullver = mcver + '-' + mlver
    url = 'https://files.minecraftforge.net/maven/net/minecraftforge/forge/%s/forge-%s-installer.jar' \
            % (forge_fullver, forge_fullver)
    outpath = '/tmp/forge-%s-installer.jar' % forge_fullver
    if not os.path.exists(outpath):
        resp = download(url, outpath)
        if resp != 200:
            print("Got %d error trying to download Forge" % resp)
            sys.exit(2)

    # Run the Forge auto-install hack
    if manual:
        subprocess.run(['java', '-jar', outpath])
    else:
        if not os.path.exists('ForgeHack.class'):
            subprocess.run(['javac', 'ForgeHack.java'])
        subprocess.run(['java', 'ForgeHack', outpath, mc_dir])

    # Rename the forge profile
    with open(mc_dir + '/launcher_profiles.json', 'r') as f:
        launcher_profiles = json.load(f)

    if 'forge' not in launcher_profiles['profiles']:
        print("ERROR: Forge did not install correctly!")
        sys.exit(3)

    rename_profile(launcher_profiles, 'forge', packname)

    with open(mc_dir + '/launcher_profiles.json', 'w') as f:
        json.dump(launcher_profiles, f)
