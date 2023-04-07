import os
import re
import sys
import requests
import subprocess
from bs4 import BeautifulSoup
pexurls_file = "someurls.txt" 
default_starting_point = 11500
default_end_ing_point = 90218
# import threading
import asyncio
willdlforumpost = True

def checkifempty_url(url):
    # Define regular expression pattern
    pattern = r'^((http(s)?://)?(www.)?pinoyexchange.com/)?discussion/(\d+)(/)?$'

    # Use re.match() to search for pattern in url
    match = re.match(pattern, url)

    # Check if a match was found
    if match:
        return True
    return False    

def pex_geturlid(url):
    match = re.search(r"^(?:(?:http(s)?://)?(?:www.)?pinoyexchange.com/)?discussion/(?P<id>\d+)(/)?$", url)
    if match:
        return int(match.group("id"))
    else:
        return None

if len(sys.argv) > 0+1:
    stt_ = int(sys.argv[1])
else:
    stt_ = default_starting_point
if len(sys.argv) > 1+1:
    end_ = int(sys.argv[2])
else:
    end_ = default_end_ing_point
print("STARTING")

uris = []

import aiohttp
import aiofiles
import asyncio
from bs4 import BeautifulSoup

async def url_get(url):
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                elif response.status in {502, 504}:
                    print("", end="")
                else:
                    return response.status
    return None

async def get_link_next(url):
    response = await url_get(url)
    if response == 404 or isinstance(response, int):
        # get_link_prev()
        return f'https://www.pinoyexchange.com/discussion/{pex_geturlid(url)+1}/'
    elif response is not None:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response, "html.parser")

        # Find the <link> tag with "prev" relationship
        prev_link = soup.find("link", rel="prev")

        # Extract the URL of the previous page
        if prev_link:
            prev_url = prev_link.get("href")
            # print("Previous URL:", prev_url)
            return prev_url

        else:            
            canon_link = soup.find("link", rel="canonical")
            if canon_link:
                    return canon_link.get("href")

        return f'https://www.pinoyexchange.com/discussion/{pex_geturlid(url)+1}/'
    return f'https://www.pinoyexchange.com/discussion/{pex_geturlid(url)+1}/'

async def append_to_file(file_path, text):
    async with aiofiles.open(file_path, "a") as file:
        await file.write(text)

async def stt_as(start_=10000, end_=911218):
    async with aiohttp.ClientSession() as session:
        di_id = start_
        tasks = []
        while int(di_id) <= int(end_):
            # create multiple tasks for each url
            for i in range(10+1):
                url = f'https://www.pinoyexchange.com/discussion/{di_id}'
                curlink_task = asyncio.create_task(get_link_next(url))
                tasks.append(curlink_task)
                di_id += 1
                # break the loop if reached the end
                if di_id > end_:
                    break
            # wait for all tasks to complete
            curlinks = await asyncio.gather(*tasks)
            # tasks = []
            # write non-empty curlinks to file\
            async with aiofiles.open(pexurls_file, "a") as f:
                for curlink in curlinks:
                    if curlink and not checkifempty_url(curlink) and curlink != "https://www.pinoyexchange.com/entry/signin":
                        print(curlink)
                        # await f.write(text)
                        await f.write(f"\n{curlink}")#execute python pex.py dlpost for each curlink
                        if willdlforumpost:
                            await asyncio.create_subprocess_exec("python", "pex.py", "dlpost", curlink)
            tasks.clear()


def start(strt=10000, end_=911218):
    asyncio.run(stt_as(stt_,end_))

if __name__ == '__main__':
    print()
    start(stt_,end_)
# stt_as(strt,end_)
