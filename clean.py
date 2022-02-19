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
        return True
    return False

def main():
    print("Modpack Maintenance v1.0.0")

    mods = set()

    moved = 0
    deleted = 0

    for packdirn in os.listdir('packs/'):
        packdir = 'packs/' + packdirn
        upd = make_global(packdir + '/.minecraft/assets', 'global/assets')
        moved += upd
        for mod in os.listdir(packdir + '/.minecraft/mods'):
            mods.add(mod)

    for mod in os.listdir('.modcache'):
        if mod not in mods:
            print("cleaning up %s" % mod)
            deleted += os.stat('.modcache/' + mod).st_size
            os.remove('.modcache/' + mod)

    print("Done! Deleted %.3f MiB of mods and migrated %d data folders" % \
        (deleted / 1048576, moved))

if __name__ == "__main__":
    main()
