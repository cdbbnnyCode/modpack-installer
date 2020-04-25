#!/usr/bin/env python3
import sys
import os
import json
import requests
import subprocess

# https://files.minecraftforge.net/maven/net/minecraftforge/forge/1.12.2-14.23.5.2847/forge-1.12.2-14.23.5.2847-universal.jar
def download(url, dest):
    print("Downloading %s" % url)
    r = requests.get(url)
    print("Status: %s" % r.status_code)
    with open(dest, 'wb') as f:
        f.write(r.content)
    return r.status_code

def main(manifest_json, mc_dir, profile_name):
    with open(manifest_json, 'r') as f:
        mandata = json.load(f)

    mcver = mandata['minecraft']['version']
    forgever = None
    for modloader in mandata['minecraft']['modLoaders']:
        if 'forge' in modloader['id']:
            forgever = modloader['id'][6:]
    if forgever is None:
        print("This loader currently only supports Minecraft Forge.")
        sys.exit(1)

    forge_fullver = mcver + '-' + forgever
    url = 'https://files.minecraftforge.net/maven/net/minecraftforge/forge/%s/forge-%s-installer.jar' \
            % (forge_fullver, forge_fullver)
    outpath = '/tmp/forge-%s-installer.jar' % forge_fullver
    if not os.path.exists(outpath):
        resp = download(url, outpath)
        if resp != 200:
            print("Got %d error trying to download Forge" % resp)
            sys.exit(2)

    # Run the Forge auto-install hack
    if not os.path.exists('ForgeHack.class'):
        subprocess.run(['javac', 'ForgeHack.java'])
    subprocess.run(['java', 'ForgeHack', outpath, mc_dir])

    # Rename the forge profile
    with open(mc_dir + '/launcher_profiles.json', 'r') as f:
        launcher_profiles = json.load(f)

    if 'forge' not in launcher_profiles['profiles'].keys():
        print("ERROR: Forge did not install correctly!")
        sys.exit(3)

    forge_profile = launcher_profiles['profiles']['forge'].copy()
    del launcher_profiles['profiles']['forge']
    launcher_profiles['profiles'][profile_name] = forge_profile
    launcher_profiles['profiles'][profile_name]['name'] = profile_name

    with open(mc_dir + '/launcher_profiles.json', 'w') as f:
        json.dump(launcher_profiles, f)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
