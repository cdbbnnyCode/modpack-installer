import os
import json
import shutil
import sys

def main():
    user_mcdir = os.getenv('HOME') + '/.minecraft'
    if len(sys.argv) > 1:
        if sys.argv[1] == '-h' or sys.argv[1] == '--help':
            print("Usage:")
            print("    %s -h|--help    Print this help message")
            print("    %s [mcdir]      Migrate modpack launcher data")
            return
        else:
            user_mcdir = sys.argv[1]

    with open(user_mcdir + '/launcher_profiles.json', 'r') as f:
        launcher_profiles = json.load(f)

    for packdirn in os.listdir('packs/'):
        print(packdirn)
        pack_profiles_file = 'packs/' + packdirn + '/.minecraft/launcher_profiles.json'
        if os.path.exists(pack_profiles_file):
            with open(pack_profiles_file, 'r') as f:
                old_profiles = json.load(f)
            
            found = False
            for profname in old_profiles['profiles']:
                profile = old_profiles['profiles'][profname]
                if profile['type'] == 'custom' or profile['type'] == '':
                    found = True
                    # print(profile)

                    version = profile['lastVersionId']
                    launcher_profiles['profiles'][packdirn] = {
                        "icon": "Chest",
                        "javaArgs": "-Xmx4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M",
                        "lastVersionId": version,
                        "name": packdirn.replace('+', ' '),
                        "gameDir": os.path.abspath('packs/' + packdirn + '/.minecraft'),
                        "type": "custom"
                    }

                    launcher_dir = 'packs/' + packdirn + '/.minecraft/launcher'
                    print("add profile %s -- version %s" % (packdirn, version))
                    if os.path.exists(launcher_dir):
                        print("remove launcher directory")
                        shutil.rmtree(launcher_dir)

                    # copy the version json
                    version_dir = user_mcdir + '/versions/' + version
                    if not os.path.exists(version_dir):
                        print("copying version info")
                        os.mkdir(version_dir)
                        shutil.copy2('packs/' + packdirn + '/.minecraft/versions/' + version + '/' + version + '.json',
                            version_dir)

            if not found:
                print("failed to migrate modpack %s, no launcher profile found" % packdirn)

    print("copying libraries")
    if os.path.exists('global/libraries'):
        shutil.copytree('global/libraries', user_mcdir + '/libraries', dirs_exist_ok=True)
    
    with open(user_mcdir + '/launcher_profiles.json', 'w') as f:
        json.dump(launcher_profiles, f, indent=2)
    # print(json.dumps(launcher_profiles, indent=2))

if __name__ == "__main__":
    main()

        