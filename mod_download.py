#!/usr/bin/env python3
import os
import sys
import requests
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

api_url = 'https://addons-ecs.forgesvc.net/api/v2'
files_url = 'https://media.forgecdn.net/files'

def download(session, url, dest):
    print("Downloading %s" % url)
    r = session.get(url)
    with open(dest, 'wb') as f:
        f.write(r.content)
    return r.status_code

def get_json(session, url):
    r = session.get(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:75.0) Gecko/20100101 Firefox/75.0'})
    if r.status_code != 200:
        print("Error %d trying to access %s" % (r.status_code, url))
        print(r.text)
        return None
    return json.loads(r.text)

def fetch_mod(session, f, out_dir):
    pid = f['projectID']
    fid = f['fileID']
    project_info = get_json(session, api_url + ('/addon/%d' % pid))
    # print(project_info['websiteUrl'])
    file_type = project_info['websiteUrl'].split('/')[4] # mc-mods or texture-packs
    info = get_json(session, api_url + ('/addon/%d/file/%d' % (pid, fid)))
    if info is None:
        return None
    fn = info['fileName']
    dl = info['downloadUrl']
    out_file = out_dir + '/' + fn
    if os.path.exists(out_file):
        if os.path.getsize(out_file) == info['fileLength']:
            print("%s OK" % fn)
            return (out_file, file_type)
    download(session, dl, out_file)
    return (out_file, file_type)

async def download_mods_async(manifest, out_dir):
    with ThreadPoolExecutor(max_workers=4) as executor, \
            requests.Session() as session:
        loop = asyncio.get_event_loop()
        tasks = []
        for f in manifest['files']:
            task = loop.run_in_executor(executor, fetch_mod, *(session, f, out_dir))
            tasks.append(task)

        jars = []
        for resp in await asyncio.gather(*tasks):
            jars.append(resp)
        return jars


def main(manifest_json, mods_dir):
    mod_jars = []
    with open(manifest_json, 'r') as f:
        manifest = json.load(f)

    print("Downloading mods")

    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(download_mods_async(manifest, mods_dir))
    loop.run_until_complete(future)
    return future.result()

if __name__ == "__main__":
    print(main(sys.argv[1], sys.argv[2]))
