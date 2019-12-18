from urllib import request
from http import HTTPStatus
import re
from typing import List, Optional


def get_domain(url: str) -> Optional[str]:
    m = re.search(r"([\w-]+\.)+(\w+)", url)
    return m.group(0) if m is not None else None


def get_html_from_url(url: str, timeout: str = 10):
    print('acesso')
    req = request.urlopen(url, timeout=timeout)
    if req.status == HTTPStatus.OK:
        data = req.read()
        data = data.decode('utf-8')
        return data
    else:
        return None


def find_links(html: str) -> List[str]:
    return re.findall(r'href="(.+?)"', html)


def search_on_page(base_url: str, result_map: dict) -> None:
    result = {'urls': [], 'assets': []}
    page_html = get_html_from_url(base_url)
    urls = find_links(page_html)
    print(urls)
    for url in urls:
        if url[0] == '/':
            result['urls'].append(base_url + url)
        elif get_domain(url) is None:
            result['urls'].append(f'{base_url}/{url}')
        elif get_domain(url) == get_domain(base_url):
            result['urls'].append(url)
    result_map[base_url] = result
    # TODO remove duplicated

        
def main():
    base_url = 'https://elixir-lang.org'
    result_map = {}
    
    # TODO async
    search_on_page(base_url, result_map)
    print(result_map)

main()
