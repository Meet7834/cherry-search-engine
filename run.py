from flask import render_template
from app import create_app
from app.models import Document

app = create_app()

@app.route("/")
def home():
    total_entries = Document.query.count()
    return render_template('index.html', total_entries=total_entries)

if __name__ == '__main__':
    app.run(debug=True)