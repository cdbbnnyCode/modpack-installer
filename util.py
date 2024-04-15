# utility functions
import requests
import shutil
import json
import os

def status_bar(text, progress, bar_width=0.5, show_percent=True, borders='[]', progress_ch='#', space_ch=' '):
    ansi_el = '\x1b[K\r' # escape code to clear the rest of the line plus carriage return
    term_width = shutil.get_terminal_size().columns
    if term_width < 10:
        print(end=ansi_el)
        return
    bar_width_c = max(int(term_width * bar_width), 4)
    text_width = min(term_width - bar_width_c - 6, len(text)) # subract 4 characters for percentage and 2 spaces
    text_part = '' if (text_width == 0) else text[-text_width:]
    
    progress_c = int(progress * (bar_width_c - 2))
    remaining_c = bar_width_c - 2 - progress_c
    padding_c = max(0, term_width - bar_width_c - text_width - 6)

    bar = borders[0] + progress_ch * progress_c + space_ch * remaining_c + borders[1]
    pad = ' ' * padding_c
    print("%s %s%3.0f%% %s" % (text_part, pad, (progress * 100), bar), end=ansi_el)
    
def download(url, dest, progress=False, session=None):
    print("Downloading %s" % url)

    try:
        if session is not None:
            r = session.get(url, stream=True)
        else:
            r = requests.get(url, stream=True)
        
        if r.status_code != 200:
            return r.status_code
        
        # size is only for the progress bar
        size = int(r.headers.get('Content-Length', 1))

        with open(dest, 'wb') as f:
            if progress:
                n = 0
                for chunk in r.iter_content(1048576):
                    f.write(chunk)
                    n += len(chunk)
                    status_bar(url, min(n / size, 1))
            else:
                f.write(r.content)
    except requests.RequestException as e:
        print("Download failed with an internal error:")
        print(repr(e))
        return -1
    except OSError as e:
        print("Download failed with an OS error:")
        print(repr(e))
        return -2

    if progress:
        print()
    
    return r.status_code

def rename_profile(launcher_profiles, orig_name, new_name):
    orig_profile = launcher_profiles['profiles'][orig_name].copy()
    del launcher_profiles['profiles'][orig_name]
    launcher_profiles['profiles'][new_name] = orig_profile
    launcher_profiles['profiles'][new_name]['name'] = new_name

def __user_preferences_file():
    # create the user preferences file if it doesn't exist
    if not os.path.isfile('user-preferences.json'):
        with open('user-preferences.json', 'w') as f:
            json.dump({}, f)

def get_user_preference(key):
    __user_preferences_file()

    # load the user preferences file
    with open('user-preferences.json', 'r') as f:
        prefs = json.load(f)
    
    # return the value if it exists, otherwise return None
    if key not in prefs:
        return None
    return prefs[key]

def set_user_preference(key, value):
    __user_preferences_file()

    # load the user preferences file
    with open('user-preferences.json', 'r') as f:
        prefs = json.load(f)

    # set the value and save the file
    prefs[key] = value
    with open('user-preferences.json', 'w') as f:
        json.dump(prefs, f, indent=4)
