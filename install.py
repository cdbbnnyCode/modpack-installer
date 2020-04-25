#!/usr/bin/env python3
# CurseForge modpack installer
# This program is an alternative to the Twitch client, written for Linux users,
# so that they can install Minecraft modpacks from CurseForge.
# This tool requires that the user download the pack zip from CurseForge. It
# will then generate a complete Minecraft install directory with all of the
# mods and overrides installed.

import forge_install
import os
import sys
import json
import subprocess
import time
from distutils.dir_util import copy_tree
from zipfile import ZipFile

def start_launcher(mc_dir):
    subprocess.run(['minecraft-launcher', '--workDir', mc_dir])

def main(zipfile):
    # Extract pack
    packname = os.path.splitext(zipfile)[0]
    packname = os.path.basename(packname)
    packdata_dir = '.packs/' + packname
    if os.path.isdir(packdata_dir):
        print("[pack data already unzipped]")
    else:
        if not os.path.isdir('.packs/'):
            os.mkdir('.packs')
        print("Extracting %s" % zipfile)
        with ZipFile(zipfile, 'r') as zip:
            zip.extractall(packdata_dir)

    # Generate minecraft environment
    mc_dir = 'packs/' + packname + '/.minecraft'
    if os.path.isdir(mc_dir):
        print("[minecraft dir already created]")
    else:
        print("Creating .minecraft directory")
        if not os.path.isdir('packs/'):
            os.mkdir('packs/')
        if not os.path.isdir('packs/' + packname):
            os.mkdir('packs/' + packname)
        os.mkdir(mc_dir)

        print("Creating symlinks")
        if not os.path.isdir('global/'):
            os.mkdir('global')
            os.mkdir('global/libraries')
            os.mkdir('global/resourcepacks')
            os.mkdir('global/saves')
            os.mkdir('global/shaderpacks')

        os.symlink(os.path.abspath('global/libraries'), mc_dir + '/libraries', True)
        os.symlink(os.path.abspath('global/resourcepacks'), mc_dir + '/resourcepacks', True)
        os.symlink(os.path.abspath('global/saves'), mc_dir + '/saves', True)
        os.symlink(os.path.abspath('global/shaderpacks'), mc_dir + '/shaderpacks', True)

        print("Creating launcher profiles")
        print("This requires starting the launcher")
        print("Please log in and then close the launcher.")
        time.sleep(2)
        start_launcher(mc_dir)

    # Install Forge
    print("Installing Forge")
    forge_install.main(packdata_dir + '/manifest.json', mc_dir, packname)

    # Download mods
    if not os.path.isdir(mc_dir + '/mods'):
        os.mkdir(mc_dir + '/mods')
        print("Downloading mods")
        if not os.path.isdir('.modcache'):
            os.mkdir('.modcache')

        if not os.path.isdir('node_modules'):
            print("Installing NodeJS dependencies")
            subprocess.run(['npm', 'install'])
        subprocess.run(['node', 'mod_download.js', packdata_dir + '/manifest.json', '.modcache', packdata_dir + '/mods.json'])

        # Link mods
        print("Linking mods")
        with open(packdata_dir + '/mods.json', 'r') as f:
            mods = json.load(f)['mods']

        for jar in mods:
            os.symlink(os.path.abspath('.modcache/' + jar), mc_dir + '/mods/' + jar)

    # Copy overrides
    print("Copying overrides")
    for dir in os.listdir(packdata_dir + '/overrides'):
        print(dir + "...")
        copy_tree(packdata_dir + '/overrides/' + dir, mc_dir + '/' + dir)
    print("Done!")
    print()
    print()
    print()
    print("To launch your new modpack, use:")
    print("  cd %s" % (mc_dir[:-11]))
    print("  minecraft-launcher --workDir .")

if __name__ == "__main__":
    main(sys.argv[1])
