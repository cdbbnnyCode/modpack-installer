#!/usr/bin/env python3
import os
import sys
import requests
import json
import asyncio
import time
from util import download
from concurrent.futures import ThreadPoolExecutor

api_url = 'https://api.curseforge.com/v1'
# NOTE: Modified and/or forked versions of this project must not use this API key.
# Instead, please apply for a new API key from CurseForge's website.
api_key = '$2a$10$t2BUHi3wKkiMw1YEqItui.XaHDvw4yMLK2peaKGkI9ufv3IsYRlkW'

# temporary rate limit before CF implements a real one
api_ratelimit = 20 # JSON requests per second
req_history = [0, 0] # time, request count so far

def get_json(session, url):
    r = session.get(url)
    if r.status_code != 200:
        print("Error %d trying to access %s" % (r.status_code, url))
        print(r.text)
        return None

    req_history[1] += 1
    while req_history[1] >= api_ratelimit:
        if time.perf_counter() > req_history[0] + 1:
            req_history[0] = time.perf_counter()
            req_history[1] = 0
            break
        s_remaining = max(0, req_history[0] + 1 - time.perf_counter())
        print("rate limiting (%.3fs)" % s_remaining)
        time.sleep(s_remaining)

    return json.loads(r.text)

def fetch_mod(session, f, out_dir):
    pid = f['projectID']
    fid = f['fileID']
    project_info = get_json(session, api_url + ('/mods/%d' % pid))
    if project_info is None:
        print("fetch failed")
        return (f, 'error')
    project_info = project_info['data']

    # print(project_info)
    print(project_info['links']['websiteUrl'])
    file_type = project_info['links']['websiteUrl'].split('/')[4] # mc-mods or texture-packs
    info = get_json(session, api_url + ('/mods/%d/files/%d' % (pid, fid)))
    if info is None:
        print("fetch failed")
        return (f, 'error')
    info = info['data']

    fn = info['fileName']
    dl = info['downloadUrl']
    out_file = out_dir + '/' + fn

    if not project_info['allowModDistribution']:
        print("distribution disabled for this mod")
        return (f, 'dist-error', project_info, out_file, file_type)

    if os.path.exists(out_file):
        if os.path.getsize(out_file) == info['fileLength']:
            print("%s OK" % fn)
            return (out_file, file_type)
    
    status = download(dl, out_file, session=session, progress=True)
    if status != 200:
        print("download failed (error %d)" % status)
        return (f, 'error')
    return (out_file, file_type)

async def download_mods_async(manifest, out_dir):
    with ThreadPoolExecutor(max_workers=1) as executor, \
            requests.Session() as session:
        session.headers['X-Api-Key'] = api_key
        loop = asyncio.get_event_loop()
        tasks = []
        for f in manifest['files']:
            task = loop.run_in_executor(executor, fetch_mod, *(session, f, out_dir))
            tasks.append(task)

        jars = []
        manual_downloads = []
        while len(tasks) > 0:
            retry_tasks = []

            for resp in await asyncio.gather(*tasks):
                if resp[1] == 'error':
                    print("failed to fetch %s, retrying later" % resp[0])
                    retry_tasks.append(resp[0])
                elif resp[1] == 'dist-error':
                    manual_dl_url = resp[2]['links']['websiteUrl'] + '/download/' + str(resp[0]['fileID'])
                    manual_dl_url = manual_dl_url.replace('www.curseforge.com', 'legacy.curseforge.com')
                    manual_downloads.append((manual_dl_url, resp))
                    # add to jars list so that the file gets linked
                    jars.append(resp[3:])
                else:
                    jars.append(resp)

            tasks = []
            if len(retry_tasks) > 0:
                print("retrying...")
                time.sleep(2)
            for f in retry_tasks:
                tasks.append(loop.run_in_executor(executor, fetch_mod, *(session, f, out_dir)))
        return jars, manual_downloads


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
