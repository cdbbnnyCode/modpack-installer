#!/usr/bin/env python3
# CurseForge modpack installer
# This program is an alternative to the Twitch client, written for Linux users,
# so that they can install Minecraft modpacks from CurseForge.
# This tool requires that the user download the pack zip from CurseForge. It
# will then generate a complete Minecraft install directory with all of the
# mods and overrides installed.

import os
import sys
import json
import subprocess
import time
import random
import shutil
import argparse
import webbrowser
import pathlib
import tqdm

import forge_install
import fabric_install
import mod_download
from zipfile import ZipFile
from util import get_user_preference, set_user_preference

# shutil.copytree doesn't accept dirs_exist_ok until 3.8 which is fairly modern (I think some LTS distros still use 3.6)
# fall back to distutils copy_tree (the old solution) if needed
if sys.version_info.minor >= 8:
    import shutil

    def copy_tree(src, dest):
        shutil.copytree(src, dest, dirs_exist_ok=True)

else:
    from distutils import copy_tree


def start_launcher(mc_dir):
    subprocess.run(["minecraft-launcher", "--workDir", os.path.abspath(mc_dir)])


def get_user_mcdir():
    # get the possibles minecraft home folder
    possible_homes = (
        os.getenv("HOME") + "/.minecraft",
        os.getenv("HOME") + "/.var/app/com.mojang.Minecraft/.minecraft/",
    )

    # remove unexistant paths
    possible_homes = [h for h in possible_homes if os.path.exists(h)]

    # no minecraft path found, ask the user to insert it
    if len(possible_homes) == 0:
        return input(
            "No minecraft installation detected, please instert the .minecraft folder path (ctrl + c to cancel): "
        )

    # only one possible home has been found, just return it
    elif len(possible_homes) == 1:
        return possible_homes[0]

    # check if more than two paths exists, ask for the user which one should be used for install
    elif len(possible_homes) >= 2:
        while True:
            print("Multiple minecraft installations detected:")
            # print each folder with a number
            i = 1  # to have more natural numbers, we're starting to 1
            for home in possible_homes:
                print(i, "- ", home)
                i += 1

            # ask the user which one to use
            home = input("Which minecraft folder should be used: ")

            # if the user replied with something else than a number print an error and loop back
            if not home.isdigit():
                print("Error: the response should be a number!")

            # if the option doesn't exists, tell the user
            elif int(home) - 1 > len(possible_homes):
                print("Error: this option doesn't exists!")

            # everything seems to be ok, returning the associated path
            else:
                return possible_homes[int(home) - 1]


# try to create a directory and all of its parent directories if they do not exist (like mkdir -p)
def mkdirp(path):
    if type(path) != pathlib.Path:
        path = pathlib.Path(path)  # convert to pathlib path if a string is provided
    try:
        path.mkdir(parents=True, exist_ok=True)
    except TypeError:  # exist_ok not defined
        try:
            path.mkdir(parents=True)
        except FileExistsError:
            if not path.is_dir():
                raise  # keep exception if a non-directory file exists here


def main(
    zipfile,
    user_mcdir=None,
    manual=False,
    open_browser=False,
    automated=False,
    sandbox=None,
):
    # check which minecraft folder to use
    if user_mcdir is None:
        # load the user preferences file
        user_mcdir = get_user_preference("minecraft_dir")

        # if the user didn't specify a minecraft folder, ask for it
        if user_mcdir is None:
            user_mcdir = get_user_mcdir()

    # check if the user wants to save the path as default if it's different from the one in the preferences
    pref_mcdir = get_user_preference("minecraft_dir")
    if user_mcdir != pref_mcdir and not automated:
        # ask the user if he wants to save the path as default
        print(
            "Changes detected in the minecraft folder path. \n OLD: %s\n NEW: %s"
            % (pref_mcdir, user_mcdir)
        )
        update_preferences = input(
            "would you like to save this new path as default? (Y/n) "
        )

        # if the user wants to save the path as default, save it
        if update_preferences.lower().startswith("y") or update_preferences == "":
            set_user_preference("minecraft_dir", user_mcdir)
            print("Preferences updated! You can change them with the --mcdir option.")
        else:
            print("Okay, no updates were made.")

    # check if the minecraft dir should be moved into a sandbox
    sandbox_root = str(pathlib.Path(user_mcdir).parent) + "/modpack"
    sandbox_pref = get_user_preference("sandbox")
    should_sandbox = sandbox_pref
    # if the preference was not set, check it
    # - also check if the mcdir has changed
    if should_sandbox is None or user_mcdir != pref_mcdir:
        should_sandbox = ".var/app" in user_mcdir  # flatpak paths look like this
    if sandbox is None:
        sandbox = should_sandbox
        # if this is new
        if sandbox and not sandbox_pref and not automated:
            # check if the user is ok with applying sandbox mode
            print(
                "This minecraft directory seems to be installed from Flatpak. Since Flatpak apps"
            )
            print(
                "can't access the filesystem, 'sandbox mode' has been enabled, which will place "
            )
            print(
                "modpacks alongside the main '.minecraft' installation so that they exist where "
            )
            print("the app can access them.")
            sandbox_ok = input("Is this OK? [Y/n]")
            if sandbox_ok.lower()[:1] not in ["y", ""]:
                sandbox = False
    if sandbox != sandbox_pref:
        # update preference
        if sandbox:
            print(
                "Enabling sandboxing - this can be changed with --no-sandbox if it breaks things"
            )
            print("* Modpack data will be stored at %s" % sandbox_root)
        set_user_preference("sandbox", sandbox)

    install_root = sandbox_root if sandbox else "."
    mkdirp(install_root)

    # Extract pack
    packname = os.path.splitext(zipfile)[0]
    packname = os.path.basename(packname)
    packdata_dir = ".packs/" + packname
    if os.path.isdir(packdata_dir):
        print("[pack data already unzipped]")
    else:
        mkdirp(".packs/")
        print("Extracting %s" % zipfile)
        with ZipFile(zipfile, "r") as zf:
            zf.extractall(packdata_dir)

    # Generate minecraft environment
    mc_dir = install_root + "/packs/" + packname + "/.minecraft"
    if os.path.isdir(mc_dir):
        print("[minecraft dir already created]")
    else:
        print("Creating .minecraft directory")
        mkdirp(mc_dir)

        print("Creating symlinks")
        global_dir = install_root + "/global"
        mkdirp(global_dir + "/libraries")
        mkdirp(global_dir + "/resourcepacks")
        mkdirp(global_dir + "/saves")
        mkdirp(global_dir + "/shaderpacks")
        mkdirp(global_dir + "/assets")

        os.symlink(
            os.path.abspath(global_dir + "/libraries"), mc_dir + "/libraries", True
        )
        os.symlink(
            os.path.abspath(global_dir + "/resourcepacks"),
            mc_dir + "/resourcepacks",
            True,
        )
        os.symlink(os.path.abspath(global_dir + "/saves"), mc_dir + "/saves", True)
        os.symlink(
            os.path.abspath(global_dir + "/shaderpacks"), mc_dir + "/shaderpacks", True
        )
        os.symlink(os.path.abspath(global_dir + "/assets"), mc_dir + "/assets", True)

    # Install Forge
    print("Installing modloader")
    try:
        with open(packdata_dir + "/manifest.json", "r") as mf:
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
    modloaders = {"forge": forge_install, "fabric": fabric_install}

    # I have not yet seen a modpack that has multiple modloaders
    if len(manifest["minecraft"]["modLoaders"]) != 1:
        print(
            "This modpack (%s) has %d modloaders, instead of the normal 1."
            % (packname, len(manifest["minecraft"]["modLoaders"]))
        )
        print(
            "This is currently unsupported, so expect the installation to fail in some way."
        )
        print("Please report which modpack caused this to the maintainer at:")
        print("  https://github.com/cdbbnnyCode/modpack-installer/issues")
    modloader, mlver = manifest["minecraft"]["modLoaders"][0]["id"].split("-")
    mcver = manifest["minecraft"]["version"]

    if modloader not in modloaders:
        print("This modloader (%s) is not supported." % modloader)
        print("Currently, the only supported modloaders are %s" % modloaders)
        return

    print("Updating user launcher profiles")

    # user_mcdir = get_user_mcdir()
    with open(user_mcdir + "/launcher_profiles.json", "r") as f:
        launcher_profiles = json.load(f)

    # add/overwrite the profile
    # TODO: add options for maximum memory
    # or config file for the java argument string
    ml_version_id = modloaders[modloader].get_version_id(mcver, mlver)
    launcher_profiles["profiles"][packname] = {
        "icon": "Chest",
        "javaArgs": "-Xmx4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M",
        "lastVersionId": ml_version_id,
        "name": packname.replace("+", " "),
        "gameDir": os.path.abspath(mc_dir),
        "type": "custom",
    }

    with open(user_mcdir + "/launcher_profiles.json", "w") as f:
        json.dump(launcher_profiles, f, indent=2)

    if not os.path.exists(user_mcdir + "/versions/" + ml_version_id):
        modloaders[modloader].main(manifest, mcver, mlver, packname, user_mcdir, manual)
    else:
        print("[modloader already installed]")

    # Download mods
    if not os.path.exists(mc_dir + "/.mod_success"):
        modcache_dir = install_root + "/.modcache"
        mkdirp(mc_dir + "/mods")
        mkdirp(modcache_dir)
        print("Downloading mods")

        mods, manual_downloads = mod_download.main(
            packdata_dir + "/manifest.json", modcache_dir
        )
        if len(manual_downloads) > 0:
            while True:
                actual_manual_dls = []  # which ones aren't already downloaded
                for url, resp in manual_downloads:
                    outfile = resp[3]
                    if not os.path.exists(outfile):
                        actual_manual_dls.append((url, outfile))
                if len(actual_manual_dls) > 0:
                    print("====MANUAL DOWNLOAD REQUIRED====")
                    print(
                        "The following mods cannot be downloaded due to the new Project Distribution Toggle."
                    )
                    print(
                        "Please download them manually; the files will be retrieved from your downloads directly."
                    )
                    print(
                        "If there is a 404 error opening any of these links, try replacing 'legacy.curseforge.com' with 'www.curseforge.com'"
                    )
                    for url, outfile in actual_manual_dls:
                        print("* %s (%s)" % (url, os.path.basename(outfile)))

                    if open_browser:
                        browser = webbrowser.get()
                        for url, _ in actual_manual_dls:
                            browser.open_new(url)

                    # TODO save user's configured downloads folder somewhere
                    user_downloads_dir = os.environ["HOME"] + "/Downloads"
                    print(
                        "Retrieving downloads from %s - if that isn't your browser's download location, enter"
                        % user_downloads_dir
                    )
                    print(
                        "the correct location below. Otherwise, press Enter to continue."
                    )
                    req_downloads_dir = input()

                    req_downloads_dir = os.path.expanduser(req_downloads_dir)
                    if len(req_downloads_dir) > 0:
                        if not os.path.isdir(req_downloads_dir):
                            print("- input directory is not a directory; ignoring")
                        else:
                            user_downloads_dir = req_downloads_dir
                    print("Finding files in %s..." % user_downloads_dir)

                    for url, outfile in actual_manual_dls:
                        fname = os.path.basename(outfile).replace(" ", "+")
                        dl_path = user_downloads_dir + "/" + fname
                        if os.path.exists(dl_path):
                            print(dl_path)
                            shutil.move(dl_path, outfile)
                else:
                    break

        # Link mods
        if not os.path.isdir(mc_dir + "/resources"):
            os.mkdir(mc_dir + "/resources")

        has_datapacks = False

        for mod in tqdm.tqdm(mods, unit="mods", desc="Linking mods"):
            jar = mod[0]
            ftype = mod[1]
            if ftype == "mc-mods":
                modfile = mc_dir + "/mods/" + os.path.basename(jar)
                if not os.path.exists(modfile):
                    os.symlink(os.path.abspath(jar), modfile)
            elif ftype == "texture-packs":
                tqdm.tqdm.write("Extracting texture pack %s" % jar)
                texpack_dir = "/tmp/%06d" % random.randint(0, 999999)
                os.mkdir(texpack_dir)
                with ZipFile(jar, "r") as zf:
                    zf.extractall(texpack_dir)
                if os.path.exists(texpack_dir + "/data"):
                    # we have a data pack, don't extract it
                    has_datapacks = True
                    tqdm.tqdm.write("-> is actually data pack, placing into datapacks")
                    if not os.path.isdir(mc_dir + "/datapacks"):
                        os.mkdir(mc_dir + "/datapacks")
                    os.symlink(
                        os.path.abspath(jar),
                        mc_dir + "/datapacks/" + os.path.basename(jar),
                    )
                else:
                    for subdir in os.listdir(texpack_dir + "/assets"):
                        f = texpack_dir + "/assets/" + subdir
                        if os.path.isdir(f):
                            copy_tree(f, mc_dir + "/resources/" + subdir)
                        else:
                            shutil.copyfile(f, mc_dir + "/resources/" + subdir)
                shutil.rmtree(texpack_dir)
            else:
                tqdm.tqdm.write("Unknown file type %s" % ftype)
                sys.exit(1)

    else:  # if mods already downloaded
        # assume there might be datapacks if a datapacks directory exists
        has_datapacks = os.path.isdir(mc_dir + "/datapacks")

    # Create success marker (does nothing if it already existed)
    with open(mc_dir + "/.mod_success", "wb") as f:
        pass

    # Copy overrides
    for subdir in tqdm.tqdm(
        os.listdir(packdata_dir + "/overrides"), unit="files", desc="Copying overrides"
    ):
        if os.path.isdir(packdata_dir + "/overrides/" + subdir):
            copy_tree(packdata_dir + "/overrides/" + subdir, mc_dir + "/" + subdir)
        else:
            shutil.copyfile(
                packdata_dir + "/overrides/" + subdir, mc_dir + "/" + subdir
            )
    print("Done!")
    print()
    print()
    print()
    print("To launch your new modpack, just open the Minecraft launcher normally.")
    print("The modpack will be available in your installations list.")
    if has_datapacks:
        print("!!!! THIS MODPACK CONTAINS DATA PACKS !!!!")
        print(
            "When creating a new world, please click the 'Data Packs' button and make sure the installed datapacks are present!"
        )
        print(
            "* Data packs have been stored in: "
            + os.path.abspath(mc_dir + "/datapacks")
        )
        print(
            "* If there are no data packs shown, drag all of the zip files from this directory into your game window "
            + "and make sure they are enabled for the world."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("zipfile")
    parser.add_argument("--manual", dest="forge_disable", action="store_true"),
    parser.add_argument(
        "--mcdir",
        dest="mcdir",
        help="Minecraft directory, overrides stored preferences",
    )
    parser.add_argument(
        "--automated",
        dest="automated",
        action="store_true",
        help="Intended for use by other scripts, limit blocking prompts",
    )
    parser.add_argument(
        "-b",
        "--open-browser",
        action="store_true",
        dest="open_browser",
        help="the browser to use to open the manual downloads",
    )
    parser.add_argument(
        "-s",
        "--sandbox",
        action="store_true",
        dest="sandbox",
        default=None,
        help="Force 'sandbox' mode (for Flatpak etc.), places files alongside .minecraft dir so that they are"
        + "accessible from inside a sandboxed environment",
    )
    parser.add_argument(
        "--no-sandbox",
        action="store_false",
        dest="sandbox",
        default=None,
        help="Force-disable 'sandbox' mode",
    )
    args = parser.parse_args(sys.argv[1:])
    main(
        args.zipfile,
        user_mcdir=args.mcdir,
        manual=args.forge_disable,
        automated=args.automated,
        open_browser=args.open_browser,
        sandbox=args.sandbox,
    )
