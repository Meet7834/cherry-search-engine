import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.models import db, Document
from flask import current_app

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme) and parsed.scheme in ['http', 'https']

def get_all_links(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return set()

    soup = BeautifulSoup(response.text, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(url, href)
        if is_valid_url(full_url):
            links.add(full_url)
    return links

def save_to_database(current_url):
    existing_document = Document.query.filter_by(url=current_url).first()
    if existing_document:
        print(f"URL {current_url} already exists in the database. Skipping.")
        return

    try:
        response = requests.get(current_url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {current_url}: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string if soup.title and soup.title.string else 'No Title'
    content = soup.getText()  # Extract and clean the HTML content

    document = Document(url=current_url, title=title, content=content)
    db.session.add(document)
    db.session.commit()

def normalize_domain(url):
    parsed = urlparse(url)
    domain_parts = parsed.netloc.split('.')
    if len(domain_parts) > 2:
        return '.'.join(domain_parts[-2:])
    return parsed.netloc

def scrape_page(current_url, depth, max_depth, visited_urls, visited_domains, depth_count, domain_count, app):
    with app.app_context():
        if depth > max_depth or current_url in visited_urls or depth_count[depth] >= 250:
            return []

        domain = normalize_domain(current_url)
        if domain_count[domain] >= 250:
            return []

        save_to_database(current_url)
        print(f"scraping website {current_url} at depth {depth}")
        visited_urls.add(current_url)
        visited_domains.add(domain)
        depth_count[depth] += 1
        domain_count[domain] += 1
        links = get_all_links(current_url)
        return [(link, depth + 1) for link in links if link not in visited_urls and normalize_domain(link) not in visited_domains]

def scrape_website(start_url, max_depth=1000, max_workers=12):
    visited_urls = set()
    visited_domains = set()
    depth_count = defaultdict(int)
    domain_count = defaultdict(int)
    queue = deque([(start_url, 0)])
    results = []
    app = current_app._get_current_object()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_page, url, depth, max_depth, visited_urls, visited_domains, depth_count, domain_count, app): (url, depth)
                   for url, depth in queue}

        while futures:
            for future in as_completed(futures):
                url, depth = futures[future]
                try:
                    new_links = future.result()
                    results.append(url)
                    for link in new_links:
                        if link not in visited_urls:
                            futures[
                                executor.submit(scrape_page, link[0], link[1], max_depth, visited_urls, visited_domains,
                                                depth_count, domain_count, app)] = link
                    # Remove elements from the queue that are from depths less than the current depth
                    while queue and queue[0][1] < depth:
                        queue.popleft()
                except Exception as e:
                    print(f"Error scraping {url} at depth {depth}: {e}")
                del futures[future]

    return results