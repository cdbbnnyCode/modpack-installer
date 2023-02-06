#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import time
from util import *

# https://files.minecraftforge.net/maven/net/minecraftforge/forge/1.12.2-14.23.5.2847/forge-1.12.2-14.23.5.2847-universal.jar

def get_forge_url(mcver, mlver):
    index_url = 'https://files.minecraftforge.net/net/minecraftforge/forge/index_%s.html' \
            % mcver

    outpath = '/tmp/forge-%s-index.html' % mcver
    if not os.path.exists(outpath):
        resp = download(index_url, outpath, False)
        if resp != 200:
            print("Got %d error trying to download index of Forge downloads" % resp)
            sys.exit(2)

    with open(outpath, 'r') as f:
        url = re.search("href=(?:.*url=)?(.*%s.*\.jar)" % mlver, f.read()).group(1)

    return url

def main(manifest, mcver, mlver, packname, mc_dir, manual):

    url = get_forge_url(mcver, mlver)
    outpath = '/tmp/%s' % url.split('/')[-1]

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
        compile_hack = False
        if not os.path.exists('ForgeHack.class'):
            compile_hack = True
        else:
            src_modtime = os.stat('ForgeHack.java').st_mtime
            cls_modtime = os.stat('ForgeHack.class').st_mtime
            if src_modtime > cls_modtime:
                print("hack source file updated, recompiling")
                compile_hack = True

        if compile_hack:
            subprocess.run(['javac', 'ForgeHack.java'])
        exit_code = subprocess.run(['java', 'ForgeHack', outpath, mc_dir]).returncode
        if exit_code != 0:
            print("Error running the auto-installer, try using --manual.")
            sys.exit(3)

    ver_id = get_version_id(mcver, mlver)
    if not os.path.exists(mc_dir + '/versions/' + ver_id):
        print("Forge installation not found.")
        if manual:
            print("Make sure you browsed to the correct minecraft directory.")
        print("Expected to find a directory named %s in %s" % (ver_id, mc_dir + '/versions'))
        print("If a similarly named directory was created in the expected folder, please submit a")
        print("bug report.")
        sys.exit(3)


def get_version_id(mcver, mlver):
    mcv_split = mcver.split('.')
    mcv = int(mcv_split[0]) * 1000 + int(mcv_split[1])
    mlv_split = mlver.split('.')
    mlv = int(mlv_split[-1]) # modloader patch version

    if mcv < 1008:
        # 1.7 (and possibly lower, haven't checked)
        return '%s-Forge%s-%s' % (mcver, mlver, mcver)
    elif mcv < 1010:
        # 1.8, 1.9
        return '%s-forge%s-%s-%s' % (mcver, mcver, mlver, mcver)
    elif mcv < 1012 or (mcv == 1012 and mlv < 2851):
        # 1.10, 1.11, 1.12 (up to 1.12.2-14.23.5.2847)
        return '%s-forge%s-%s' % (mcver, mcver, mlver)
    else:
        # 1.12.2-14.23.5.2851 and above
        return '%s-forge-%s' % (mcver, mlver)
        
