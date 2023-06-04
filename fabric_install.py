import os
import json
import sys
import requests
import subprocess
from util import *
import xml.etree.ElementTree as et


def get_latest_ver():
    url = "https://maven.fabricmc.net/net/fabricmc/fabric-installer/maven-metadata.xml"
    outpath = "/tmp/fabric-versions.xml"
    resp = download(url, outpath)
    if resp != 200:
        print("Error %d trying to download Fabric version list" % resp)
        return None

    xml_tree = et.parse(outpath)
    root = xml_tree.getroot()

    ver_info = xml_tree.find("versioning")
    release_ver = ver_info.find("release")
    return release_ver.text


def main(manifest, mcver, mlver, packname, mc_dir, manual):
    print("Installing Fabric modloader")

    installer_ver = get_latest_ver()
    if installer_ver is None:
        print("Failed to acquire Fabric installer version")
        sys.exit(2)

    url = (
        "https://maven.fabricmc.net/net/fabricmc/fabric-installer/%s/fabric-installer-%s.jar"
        % (installer_ver, installer_ver)
    )
    outpath = "/tmp/fabric-%s-installer.jar" % installer_ver
    if not os.path.exists(outpath):
        resp = download(url, outpath)
        if resp != 200:
            print("Got error %d trying to download Fabric" % resp)
            sys.exit(2)

    args = [
        "java",
        "-jar",
        outpath,
        "client",
        "-snapshot",
        "-dir",
        mc_dir,
        "-loader",
        mlver,
        "-mcversion",
        mcver,
    ]

    if manual:
        # I guess they want manual mode for some reason
        print("Using the manual installer!")
        print("***** NEW: INSTALL TO THE MAIN .MINECRAFT DIRECTORY *****")
        print("*****   (Just hit 'OK' with the default settings)   *****")
        subprocess.run(["java", "-jar", outpath])
    else:
        subprocess.run(args)

    if not os.path.exists(mc_dir + "/versions/" + get_version_id(mcver, mlver)):
        print("Forge installation failed.")
        sys.exit(3)


def get_version_id(mcver, mlver):
    return "fabric-loader-%s-%s" % (mlver, mcver)
