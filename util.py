# utility functions
import requests

def download(url, dest):
    print("Downloading %s" % url)
    r = requests.get(url)
    print("Status: %s" % r.status_code)
    with open(dest, 'wb') as f:
        f.write(r.content)
    return r.status_code

def rename_profile(launcher_profiles, orig_name, new_name):
    orig_profile = launcher_profiles['profiles'][orig_name].copy()
    del launcher_profiles['profiles'][orig_name]
    launcher_profiles['profiles'][new_name] = orig_profile
    launcher_profiles['profiles'][new_name]['name'] = new_name
