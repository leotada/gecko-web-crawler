from urllib import request
import urllib
from http import HTTPStatus
from typing import List, Optional, Dict
import re
import json


def get_domain(url: str) -> Optional[str]:
    """
    Get domain part from url
    """
    match = re.search(r"([\w-]+\.)+(\w+)", url)
    return match.group(0) if match is not None else None


def get_html_from_url(url: str, timeout: int = 10) -> Optional[str]:
    """
    Get HTML string after making a url request
    """
    try:
        req = request.urlopen(url, timeout=timeout)
        if req.status == HTTPStatus.OK:
            data: str = req.read().decode('utf-8')
            return data
        return None
    except urllib.error.HTTPError:
        return None


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


def search_on_page(root_url: str, base_url: str, result_map: dict) -> bool:
    """
    Receive a url and a result map and do a search of links and assets on the
    page accessing url.
    """
    # don't repeat a url
    if base_url in result_map:
        return False

    result: Dict = {'urls': [], 'assets': []}
    page_html = get_html_from_url(base_url)
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


def main() -> None:
    root_url = 'https://elixir-lang.org'
    save_urls = False
    result_map: Dict[str, Dict] = {}
    queue = [root_url]
    count = 0

    def run() -> int:
        count = 0
        current_url = queue[0]
        print('URL: ', current_url)
        result = search_on_page(root_url, current_url, result_map)
        if result:
            count += 1
            queue.extend(result_map[current_url]['urls'])
        queue.pop(0)
        return count

    while queue:
        r = run()
        count += r
        print('Queue: ', len(queue))
        print(f'Requests: {count}')

    if not save_urls:
        for key, value in result_map.items():
            del value['urls']
    print(f'Total Requests: {count}')
    result_json = json.dumps(result_map)
    print(result_json)
    with open('output.json', 'w') as output_file:
        output_file.write(result_json)


if __name__ == '__main__':
    main()
