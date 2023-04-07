import re
import os
import asyncio

from bs4 import BeautifulSoup
import time
import requests
import sys
import random
import subprocess

import asyncio
import aiohttp
import aiofiles
import multiprocessing
async def process_url(url):
    _CURRENTURL = remove_url_hash(url)
    result = await asyncio.to_thread(await pex_fetch_allpages, _CURRENTURL)
    return result

def remove_url_hash(url):
    """
    Removes any hash string at the end of a URL using regex.

    Args:
        url (str): The URL to modify.

    Returns:
        str: The modified URL with any hash string removed.
    """
    return re.sub(r'#.*$', '', url)

cookies = ("cookies.txt")
_tempdir = "tmp"
_datadir = "dat"
_catdir  = "cat"

_postsdir = "posts"
_usersdir = "users"

http_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept-Language": "en-US,en;q=0.5"
}

def pex_remove_page_string(url):
    return re.sub(r"/p\d+", "", url)

def mkdir_(directory):
    # directory = 'my_folder'
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except:
            print("Attempt to make dir failed")
        return True
def get_pex_id(url):
    # pattern = r"/discussion/(\d+)/(.+)(?:/p(\d+))?"
    pattern = r"/discussion/(\d+)/([^/?&]+)(?:/p(\d+))?"

    match = re.search(pattern, url)
    if match:
        id_str = match.group(1)
        title_str = match.group(2)
        page_str = match.group(3)

        # Create a dictionary with the extracted values
        result = {
            "id": id_str,
            "title": title_str,
            "page": int(page_str) if page_str else 1
        }

        return result
    else:
        return False

async def get_pex_fileid(url,no_page_str=False):
    # Call get_pex_id() function to get the discussion ID, title, and page number
    pex_info = get_pex_id(url)
    pagenum_length_lpad = 5 
    # Check if the URL is a valid PEX discussion URL
    if pex_info:
        # Extract the discussion ID, title, and page number from the dictionary
        id_str = pex_info["id"]
        title_str = pex_info["title"]
        page_num = pex_info["page"]

        # Format the page number as a three-digit string
        page_fmt = f"{page_num:0>{pagenum_length_lpad}}"

        # Construct the file ID string
        result = f"{id_str}_{title_str}_p{page_fmt}"
        if no_page_str is True:
            result = f"{id_str}_{title_str}"

        print(f"PEX ID: {result}")
        return result
    else:
        return False


def url_get(url):
    headers = http_headers
    print(f"Start URL GET{url}")
    try:
        for i in range(1,4):
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print("200 OK")
                return response.content
            elif response.status_code == 502 or response.status_code == 504:
                print("Bad Gateway. Retrying...")
                time.sleep(random.uniform(0, 0))    
            else:
                print(f"Error: Status code {response.status_code}")                
                return None
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        sys.exit()
        print(f"Error: {str(e)}")
        return None


async def pex_fetch_file(url,forceDL=False):
    pex_fileid = await get_pex_fileid(url)
    temp_pex_data = f'{_tempdir}/posts/{pex_fileid}'
    if os.path.isfile(temp_pex_data) and forceDL is False:
        print(f"{pex_fileid} :  FILE EXIST. - {temp_pex_data}")
        async with aiofiles.open(temp_pex_data, 'rb') as f:
            filedata = await f.read()
            filedata = filedata.decode()
            return filedata
    else:
        print(f"{pex_fileid} : NOT EXIST. -  {temp_pex_data}")
        
        async with aiohttp.ClientSession() as session:
            content = await fetch(session,url)
            if content is not None:
                async with aiofiles.open(temp_pex_data, 'wb') as f:
                    await f.write(content.encode())
                return content

# def download_efficient_return(url,)
async def pex_pfp_dl(user_name,user_id,user_pic):
    pfp_path = f'{_datadir}/{_usersdir}/{user_id}.{user_name}.{os.path.splitext(filename)[1]}'
    download_efficient(user_pic,pfp_path)

async def pex_extract_posts(HTML):
    soup = BeautifulSoup(HTML, 'html.parser')
    posts = []
    for discussion in soup.find_all('li', {'class': 'ItemDiscussion'}):
        post_url = discussion.find('div', {'class': 'Title'}).find('a')['href']
        post_title = discussion.find('div', {'class': 'Title'}).text.strip()
        post_id = discussion['id'].split('_')[-1]
        post_category = discussion.find('span', {'class': 'Category'}).find('a')['href'].split('/')[-1]
        post_info = {'post_url': post_url, 'post_title': post_title, 'post_id': post_id, 'post_category': post_category}
        posts.append(post_info)
    return posts
# print(pex_extract_posts(HTML))

async def pex_comment_parser(html,will_pfp_dl=False):
    soup = BeautifulSoup(html, 'html.parser')
    comments = []

    for li in soup.select('li:has(.Comment)'):
        comment_id = li.get('id').split('_')[1]
        comment = li.select_one('.Comment')
        user_name = comment.select_one('.Username').text
        user_id = comment.select_one('.Username')['data-userid']
        user_pic = comment.select_one('.ProfilePhoto')['src']
        time_posted = comment.select_one('time')['datetime']
        # comment_text = comment.select_one('.Message').text.strip()
        comment_text = comment.select_one('.Message').text.strip()
        if(will_pfp_dl):
            await pex_pfp_dl(user_name,user_id,user_pic)

        comment_info = {
            "comment_id": comment_id,
            "user_name": user_name,
            "user_id": user_id,
            "user_pic": user_pic,
            "time_posted": time_posted,
            "comment_text": comment_text
        }
        comments.append(comment_info)
    return comments

async def pex_get_pagenum(url):
    html = await pex_fetch_file(url)
    if html is not None:
        soup = BeautifulSoup(html, 'html.parser')
        last_page_element = soup.select_one(".Pager-p.LastPage")
        if last_page_element:
            last_page = last_page_element.text
        else:
            last_page = "1"
        return int(last_page)
    return 1

async def pex_fetch_allpages(url,i=1):    
    base_url = pex_remove_page_string(url)
    pex_page_id_noid= await get_pex_fileid(url,True)
    total_pages = int(await pex_get_pagenum(url))
    has_downloaded = False    
    if (has_downloaded is False):
        await pex_fetch_somepages(url,i,total_pages)

async def pex_fetch_somepages(url,i=1,to=0):    
    pex_fileid = await get_pex_fileid(url)

    base_url = pex_remove_page_string(url)
    pex_page_id_noid= await get_pex_fileid(url,True)
    total_pages = int(await pex_get_pagenum(url))
    to = total_pages if to <= 0 or to > total_pages else to
    i = 0 if i < 0 or i > total_pages else i
    has_downloaded = False    
    if (has_downloaded is False):
        for i in range(i,to+1):
            print(f'{pex_fileid} : Page {i}/{total_pages} ({(i/total_pages)*100}%)')
            await pex_fetch_singlefile(url,i)
        print(f"{pex_fileid}: {i}/{total_pages}")

async def pex_fetch_singlefile(url,i=1):
    total_pages = int(await pex_get_pagenum(url))
    if i > -1 or i < total_pages+1:
        return await pex_fetch_file(f'{url}/p{i}')

async def pex_readurlfile(txtname):
    # Define the regex pattern    
    print("WHY")
    pattern = r'https?:\/\/(www\.)?pinoyexchange\.com*'
    async with aiofiles.open(txtname, "r") as f:
        urls = await f.readlines(encoding='utf-8')
        print(urls)

    # Loop through the URLs and filter out those that match the pattern
    urls_accepted = []
    for url in urls:    
        print(url)
        if url.startswith("#"):
            # print(url)
            continue # Skip the line and move to the next one
        if re.match(pattern, url):
            urls_accepted.append(url.strip())
    # Print the resulting URLs
    for url in urls_accepted:
        print(url)
    return urls_accepted
def _create_dirs():    
    
    mkdir_(f"{_tempdir}/{_postsdir}")
    mkdir_(f"{_tempdir}/{_postsdir}")
    mkdir_(f"{_tempdir}/{_catdir}")
    mkdir_(f"{_datadir}/{_postsdir}")
    mkdir_(f"{_datadir}/{_usersdir}") 
    mkdir_(f"{_datadir}/{_catdir}")
async def process_url(url):
    _CURRENTURL = remove_url_hash(url)
    result = await asyncio.to_thread(await pex_fetch_allpages, _CURRENTURL)
    return result

import asyncio
import aiohttp
import os
import aiofiles

async def pex_get_pagenum(url):
    html = await pex_fetch_file(url)
    if html is not None:
        soup = BeautifulSoup(html, 'html.parser')
        last_page_element = soup.select_one(".Pager-p.LastPage")
        if last_page_element:
            last_page = last_page_element.text
        else:
            last_page = "1"
        return int(last_page)
    return 1

async def pex_fetch_allpages(url,i=1):
    base_url = pex_remove_page_string(url)
    pex_page_id_noid= await get_pex_fileid(url,True)
    total_pages = int(await pex_get_pagenum(url))
    has_downloaded = False

    if has_downloaded is False:
        await  pex_fetch_somepages(url,i,total_pages)

async def pex_fetch_somepages(url,i=1,to=0):
    pex_fileid = await get_pex_fileid(url)
    base_url = pex_remove_page_string(url)
    pex_page_id_noid= await get_pex_fileid(url,True)
    total_pages = int(await pex_get_pagenum(url))
    to = total_pages if to <= 0 or to > total_pages else to
    i = 0 if i < 0 or i > total_pages else i
    has_downloaded = False

    if has_downloaded is False:
        async with aiohttp.ClientSession() as session:
            for chunk_start in range(i, to + 1, 5):
                chunk_end = min(chunk_start + 4, to)
                tasks = []
                for page_num in range(chunk_start, chunk_end + 1):
                    # tasks.append(await pex_fetch_singlefile(session, f'{base_url}/p{page_num}', page_num))
                    # tasks.append( asyncio.ensure_future( pex_fetch_singlefile(session, f'{base_url}/p{page_num}', page_num )) )
                    tasks.append(  pex_fetch_singlefile(session, f'{base_url}/p{page_num}', page_num ) )
                    print(f"{pex_fileid}: INIT {page_num}/{total_pages}")

                await asyncio.gather(*tasks)
        print(f"{pex_fileid}: DONE {chunk_end}/{total_pages}")

async def pex_fetch_singlefile(session, url, i=1):
    total_pages = int(await pex_get_pagenum(url))
    
    pex_fileid = await get_pex_fileid(url)
    temp_pex_data = f'{_tempdir}/posts/{pex_fileid}'
    if i > -1 or i < total_pages+1:
        # cache_file_name = f"{await get_pex_fileid(url)}-p{i}.html"
        cache_file_name = temp_pex_data
        if os.path.isfile(cache_file_name):
            async with aiofiles.open(cache_file_name, "rb") as file:
                # await file.write(text)
                html = await file.read()
                html = html.decode()
                return html
        else:            
            async with aiohttp.ClientSession() as session:
                html = await fetch(session, f"{url}/p{i}")
                try:
                    async with aiofiles.open(cache_file_name, 'wb') as file:
                        await file.write(html.encode())
                except:
                    try: 
                        async with aiofiles.open(cache_file_name, 'w') as file:
                            await file.write(html.encode())
                    except:
                        return html

                    return html


async def fetch(session, url):
    retry_count = 0
    while retry_count < 10:
        async with session.get(url) as response:
            if response.status in [500, 502, 504]:
                retry_count += 1                        
                continue
            else:
                return await response.text()
                # return await response.content.read().decode('utf-8')

async def main(urls):
    num_processes = 10
    i = 0
    while i < len(urls):
        tasks = []
        for url in urls[i:i+num_processes]:
            tasks.append(asyncio.create_task( pex_fetch_allpages(url)))
        i += num_processes
        await asyncio.gather(*tasks)


async def __main_dl__():
    
    try:
        DEFAULT_URL_ = ["http://example.org/puppy.png", "http://fundraiser.com", "http://news.net"]
        
        URL_ = sys.argv[2:] if len(sys.argv) > 2 else DEFAULT_URL_
        if sys.argv[2] == "txt":            
            URL_ = []
            rawfiles = sys.argv[3:]
            print(rawfiles)
            for rawfile in rawfiles:
                urls_accepted = await pex_readurlfile(rawfile)
                for url in urls_accepted:
                    URL_.append(url)
        
        print(URL_) 
        
        num_processes = 10
        await main(URL_)
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(main(URL_))
    except KeyboardInterrupt:
        print("Program interrupted by user!")
        sys.exit()
if __name__ == "__main__":
    _create_dirs()
    if sys.argv[1] == "dlpost":
        # asyncio.run(__main_dl__)
        # await __main_dl__()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(__main_dl__())
    exit()
    
