from urllib import request
from http import HTTPStatus
import re
from typing import List, Optional, Dict


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
    req = request.urlopen(url, timeout=timeout)
    if req.status == HTTPStatus.OK:
        data: str = req.read().decode('utf-8')
        return data
    return None


def find_links(html: str) -> List[str]:
    """
    Return a list of links found in the given HTML string
    """
    return re.findall(r'href="(.+?)"', html)


def search_on_page(base_url: str, result_map: dict) -> bool:
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
    return True


def main() -> None:
    base_url = 'https://elixir-lang.org'
    result_map: Dict[str, Dict] = {}
    # TODO request async
    search_on_page(base_url, result_map)
    print(result_map)


if __name__ == '__main__':
    main()
