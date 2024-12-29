from urllib.parse import urlparse

from flask import Blueprint, request, jsonify, render_template, url_for
from app.models import Document, db
from app.scraper import scrape_website
from app.search import search, search_database

search_api = Blueprint('search_api', __name__)
scraper_api = Blueprint('scraper_api', __name__)


@search_api.route('/search', methods=['GET'])
def search_endpoint():
    query = request.args.get('q')
    results = search_database(query)
    return render_template('search_results.html', results=results, query=query)

@search_api.route('/document/<int:doc_id>', methods=['GET'])
def display_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    return render_template('document.html', document=document)

@search_api.route('/database', methods=['GET'])
def display_database():
    page = request.args.get('page', 1, type=int)
    per_page = 500
    documents = Document.query.paginate(page=page, per_page=per_page, error_out=False)
    results = [{'id': doc.id, 'url': doc.url, 'title': doc.title, 'content': doc.content} for doc in documents.items]
    next_url = url_for('search_api.display_database', page=documents.next_num) if documents.has_next else None
    prev_url = url_for('search_api.display_database', page=documents.prev_num) if documents.has_prev else None
    total_entries = Document.query.count()
    return render_template('database.html', results=results, next_url=next_url, prev_url=prev_url, total_entries=total_entries)

@scraper_api.route('/start-scraping', methods=['GET'])
def start_scraping():
    start_url = 'https://www.hostinger.in/tutorials/weird-websites'
    results = scrape_website(start_url)
    return jsonify(results)

@search_api.route('/domains', methods=['GET'])
def list_domains():
    domains = db.session.query(Document.url).distinct().all()
    unique_domains = {urlparse(doc.url).netloc for doc in domains}
    return render_template('domains.html', domains=unique_domains)

@search_api.route('/domain/<domain>', methods=['GET'])
def list_pages_by_domain(domain):
    documents = Document.query.filter(Document.url.like(f'%{domain}%')).all()
    results = [{'id': doc.id, 'url': doc.url, 'title': doc.title, 'content': doc.content} for doc in documents]
    return render_template('pages_by_domain.html', domain=domain, results=results)