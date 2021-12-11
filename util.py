# utility functions
import requests
import shutil

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

    bar = borders[0] + progress_ch * progress_c + space_ch * remaining_c + borders[1]
    print("%s %3.0f%% %s" % (text_part, (progress * 100), bar), end=ansi_el)
    
def download(url, dest, progress=False):
    print("Downloading %s" % url)

    try:
        r = requests.get(url, stream=True)
        size = int(r.headers['Content-Length'])
        
        if r.status_code != 200:
            return r.status_code

        with open(dest, 'wb') as f:
            if progress:
                n = 0
                for chunk in r.iter_content(1024):
                    f.write(chunk)
                    n += len(chunk)
                    status_bar(url, n / size)
            else:
                f.write(r.content)
    except requests.RequestException:
        return -1
    except OSError:
        return -2

    if progress:
        print()
    
    return r.status_code

def rename_profile(launcher_profiles, orig_name, new_name):
    orig_profile = launcher_profiles['profiles'][orig_name].copy()
    del launcher_profiles['profiles'][orig_name]
    launcher_profiles['profiles'][new_name] = orig_profile
    launcher_profiles['profiles'][new_name]['name'] = new_name
