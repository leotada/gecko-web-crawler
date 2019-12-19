from http import HTTPStatus
from typing import List, Optional, Dict
import re
import json
import asyncio
from time import time

import httpx


def get_domain(url: str) -> Optional[str]:
    """
    Get domain part from url
    """
    match = re.search(r"([\w-]+\.)+(\w+)", url)
    return match.group(0) if match is not None else None


def find_links(html: str) -> List[str]:
    """
    Return a list of links found in the given HTML string
    """
    urls = re.findall(r'href="(.+?)"', html)
    extensions = ['css', 'js', 'jpg', 'jpeg', 'gif', 'tiff', 'png', 'bmp',
                  'svg', 'ico', 'xml', 'pdf']
    result = []
    for url in urls:
        url_low: str = url.lower()
        asset = False
        for ext in extensions:
            if url_low.endswith(ext):
                asset = True
                break
        if not asset:
            result.append(url_low)
    return result


def find_assets(html: str) -> List[str]:
    """
    Return a list of assets found in the given HTML string
    """
    return re.findall(
        r'"([^"]+\.(?:css|js|jpg|jpeg|gif|tiff|png|bmp|svg|ico|pdf))"',
        html, flags=re.IGNORECASE)


async def get_html_from_url(url: str, timeout: int = 10) -> Optional[str]:
    """
    Get HTML string after making a url request
    """
    try:
        req = await httpx.get(url, timeout=timeout)
        if req.status_code == HTTPStatus.OK:
            data: str = req.text
            return data
        return None
    except httpx.HTTPError:
        return None


async def search_on_page(root_url: str, base_url: str,
                         result_map: dict) -> bool:
    """
    Receive a url and a result map and do a search of links and assets on the
    page accessing url.
    """
    result: Dict = {'urls': [], 'assets': []}
    page_html = await get_html_from_url(base_url)
    if page_html is None:
        return False

    # search for links
    urls = find_links(page_html)
    for url in urls:
        if url[0] == '/':
            result['urls'].append(root_url + url)
        elif get_domain(url) is None:
            result['urls'].append(f'{root_url}/{url}')
        elif get_domain(url) == get_domain(base_url):
            result['urls'].append(url)

    # search for assets
    result['assets'] = find_assets(page_html)

    result_map[base_url] = result
    return True


async def run_task(root_url: str,
                   current_url: str,
                   result_map: dict,
                   verbose: bool = False) -> Optional[List[str]]:
    """
    Run crawler task
    """
    if verbose:
        print('URL:', current_url)
    # don't repeat a url
    if current_url in result_map:
        return None
    result = await search_on_page(root_url, current_url, result_map)
    if result:
        return result_map[current_url]['urls']
    return None


async def simple_crawler(root_url: str,
                         concurrency: int,
                         timeout: int,
                         save_urls: bool = False,
                         verbose: bool = False) -> Optional[str]:
    """
    Simple crawler function that walk to all pages in the same domain and
    search for assets useds. Return JSON string.
    """
    result_map: Dict[str, Dict] = {}
    queue = [root_url]
    count = 0
    start_time = time()

    while queue:
        if len(queue) > concurrency:
            tasks = []
            for _ in range(concurrency):
                tasks.append(
                    run_task(root_url, queue.pop(0), result_map, verbose))
            for response in await asyncio.gather(*tasks):
                if response:
                    queue.extend(response)
                    count += 1
        else:
            current_url = queue.pop(0)
            response = await run_task(root_url, current_url, result_map,
                                      verbose)
            if response:
                queue.extend(response)
                count += 1
        if verbose:
            print('Queue:', len(queue))
            print(f'Requests: {count}')
        # timeout
        if time() - start_time >= timeout:
            return None

    if not save_urls:
        for _, value in result_map.items():
            del value['urls']
    if verbose:
        print(f'Total Requests: {count}')
    result_json = json.dumps(result_map)
    return result_json


if __name__ == '__main__':
    async def main() -> None:
        result = await simple_crawler(
            root_url=input('Root URL: '),
            concurrency=20,
            timeout=30,
            save_urls=False,
            verbose=True)
        if result is not None:
            with open('output.json', 'w') as output_file:
                output_file.write(result)
            print(f'Finished. Look output.json file.')
        else:
            print('Timeout reached!')

    asyncio.run(main())
