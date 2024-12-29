from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser
import os
from sqlalchemy import desc
from app.models import Document

schema = Schema(id=ID(stored=True), title=TEXT(stored=True), content=TEXT(stored=True))

if not os.path.exists("index"):
    os.mkdir("index")
ix = create_in("index", schema)

def add_document(doc_id, title, content):
    writer = ix.writer()
    writer.add_document(id=str(doc_id), title=title, content=content)
    writer.commit()

def search(query_str):
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema).parse(query_str)
        results = searcher.search(query)
        return [(r['id'], r['title']) for r in results]

def search_database(query):
    results = Document.query.filter(
        Document.title.ilike(f'%{query}%') |
        Document.content.ilike(f'%{query}%')
    ).order_by(desc(Document.content.ilike(f'%{query}%'))).all()
    return results