import os
import shutil

def make_global(dir, gdir):
    if not os.path.exists(gdir):
        os.mkdir(gdir)
    
    if not os.path.islink(dir):
        print("Converting %s to a global directory" % dir)
        if os.path.isdir(dir):
            shutil.rmtree(dir) # safe for downloaded things, but not for user created content
        elif os.path.exists(dir):
            os.remove(dir)
        os.symlink(os.path.abspath(gdir), dir, True)

def main():
    print("Modpack Maintenance v1.0.0")

    mods = set()

    for packdirn in os.listdir('packs/'):
        packdir = 'packs/' + packdirn
        make_global(packdir + '/.minecraft/assets', 'global/assets')
        
        for mod in os.listdir(packdir + '/.minecraft/mods'):
            mods.add(mod)

    for mod in os.listdir('.modcache'):
        if mod not in mods:
            print("cleaning up %s" % mod)
            os.remove('.modcache/' + mod)

if __name__ == "__main__":
    main()