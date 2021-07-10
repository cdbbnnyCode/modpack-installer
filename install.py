#!/usr/bin/env python3
# CurseForge modpack installer
# This program is an alternative to the Twitch client, written for Linux users,
# so that they can install Minecraft modpacks from CurseForge.
# This tool requires that the user download the pack zip from CurseForge. It
# will then generate a complete Minecraft install directory with all of the
# mods and overrides installed.

import forge_install
import fabric_install
import mod_download
import os
import sys
import json
import subprocess
import time
import random
import shutil
import argparse
from distutils.dir_util import copy_tree
from zipfile import ZipFile

def start_launcher(mc_dir):
    subprocess.run(['minecraft-launcher', '--workDir', os.path.abspath(mc_dir)])

def main(zipfile, manual=False):
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
        launcher_profiles = {
            "profiles": {},
            "settings": {
                "crashAssistance": True,
                "enableAdvanced": False,
                "enableAnalytics": False,
                "enableHistorical": False,
                "enableReleases": True,
                "enableSnapshots": False,
                "keepLauncherOpen": True,
                "profileSorting": "ByLastPlayed",
                "showGameLog": False,
                "showMenu": False,
                "soundOn": False
            }
        }
        with open(mc_dir + '/launcher_profiles.json', 'w') as f:
            json.dump(launcher_profiles, f)

    # Install Forge
    print("Installing modloader")
    try:
        with open(packdata_dir + '/manifest.json', 'r') as mf:
            manifest = json.load(mf)
    except (json.JsonDecodeError, OSError) as e:
        print("Manifest file not found or was corrupted.")
        print(e)
        return

    # supported modloaders and their run-functions
    # The run function will take the following arguments:
    # * manifest JSON
    # * minecraft version
    # * modloader version
    # * modpack name
    # * minecraft directory
    # * manual flag: run automatically or show GUI
    modloaders = {
        'forge': forge_install.main,
        'fabric': fabric_install.main
    }

    # I have not yet seen a modpack that has multiple modloaders
    if len(manifest['minecraft']['modLoaders']) != 1:
        print("This modpack (%s) has %d modloaders, instead of the normal 1."
                % (packname, len(manifest['minecraft']['modLoaders'])))
        print("This is currently unsupported, so expect the installation to fail in some way.")
        print("Please report which modpack caused this to the maintainer at:")
        print("  https://github.com/cdbbnnyCode/modpack-installer/issues")
    modloader, mlver = manifest['minecraft']['modLoaders'][0]["id"].split('-')
    mcver = manifest['minecraft']['version']

    if not modloader in modloaders:
        print("This modloader (%s) is not supported." % modloader)
        print("Currently, the only supported modloaders are %s" % modloaders)
        return

    modloaders[modloader](manifest, mcver, mlver, packname, mc_dir, manual)

    # Download mods
    if not os.path.exists(mc_dir + '/.mod_success'):
        if not os.path.isdir(mc_dir + '/mods'):
            os.mkdir(mc_dir + '/mods')
        print("Downloading mods")
        if not os.path.isdir('.modcache'):
            os.mkdir('.modcache')

        # if not os.path.isdir('node_modules'):
        #     print("Installing NodeJS dependencies")
        #     subprocess.run(['npm', 'install'])
        # subprocess.run(['node', 'mod_download.js', packdata_dir + '/manifest.json', '.modcache', packdata_dir + '/mods.json'])

        mods = mod_download.main(packdata_dir + '/manifest.json', '.modcache')

        # Link mods
        print("Linking mods")
        if not os.path.isdir(mc_dir + '/resources'):
            os.mkdir(mc_dir + '/resources')

        for mod in mods:
            jar = mod[0]
            type = mod[1]
            if type == 'mc-mods':
                modfile = mc_dir + '/mods/' + os.path.basename(jar)
                if not os.path.exists(modfile):
                    os.symlink(os.path.abspath(jar), modfile)
            elif type == 'texture-packs':
                print("Extracting texture pack %s" % jar)
                texpack_dir = '/tmp/%06d' % random.randint(0, 999999)
                os.mkdir(texpack_dir)
                with ZipFile(jar, 'r') as zip:
                    zip.extractall(texpack_dir)
                for dir in os.listdir(texpack_dir + '/assets'):
                    f = texpack_dir + '/assets/' + dir
                    if os.path.isdir(f):
                        copy_tree(f, mc_dir + '/resources/' + dir)
                    else:
                        shutil.copyfile(f, mc_dir + '/resources/' + dir)
                shutil.rmtree(texpack_dir)
            else:
                print("Illegal type %s" % type)
                sys.exit(1)

    # Create success marker
    with open(mc_dir + '/.mod_success', 'wb') as f:
        pass

    # Copy overrides
    print("Copying overrides")
    for dir in os.listdir(packdata_dir + '/overrides'):
        print(dir + "...")
        if os.path.isdir(packdata_dir + '/overrides/' + dir):
            copy_tree(packdata_dir + '/overrides/' + dir, mc_dir + '/' + dir)
        else:
            shutil.copyfile(packdata_dir + '/overrides/' + dir, mc_dir + '/' + dir)
    print("Done!")
    print()
    print()
    print()
    print("To launch your new modpack, use:")
    print("  cd %s" % (mc_dir[:-11]))
    print("  minecraft-launcher --workDir $(realpath .minecraft)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('zipfile')
    parser.add_argument('--manual', dest='forge_disable', action='store_true')
    args = parser.parse_args(sys.argv[1:])
    main(args.zipfile, args.forge_disable)
