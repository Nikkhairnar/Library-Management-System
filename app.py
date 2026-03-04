from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# =============================================================================
# MODELS
# =============================================================================

class Author(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    bio        = db.Column(db.Text)
    city       = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    books = db.relationship('Book', backref='author_info', lazy=True,
                            cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'bio':        self.bio,
            'city':       self.city,
            'book_count': len(self.books),
            'books':      [book.title for book in self.books],
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Book(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    year       = db.Column(db.Integer)
    isbn       = db.Column(db.String(20), unique=True)
    genre      = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id  = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)

    def to_dict(self):
        return {
            'id':          self.id,
            'title':       self.title,
            'author_id':   self.author_id,
            'author_name': self.author_info.name if self.author_info else 'Unknown',
            'year':        self.year,
            'isbn':        self.isbn,
            'genre':       self.genre,
            'created_at':  self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# FRONTEND ROUTE
# =============================================================================

@app.route('/')
def index():
    return render_template('index.html')


# =============================================================================
# AUTHOR ROUTES  (full CRUD)
# =============================================================================

@app.route('/api/authors', methods=['GET'])
def get_authors():
    """GET /api/authors?q=<name>&sort=name&order=asc&page=1&per_page=20"""
    query  = Author.query
    search = request.args.get('q', '').strip()
    if search:
        query = query.filter(Author.name.ilike(f'%{search}%'))

    sort_field = request.args.get('sort', 'name')
    order      = request.args.get('order', 'asc')
    col_map    = {'name': Author.name, 'city': Author.city, 'created_at': Author.created_at,
                  'book_count': Author.name}  # book_count: approximate via name fallback
    sort_col   = col_map.get(sort_field, Author.name)
    query      = query.order_by(sort_col.desc() if order == 'desc' else sort_col.asc())

    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success':  True,
        'authors':  [a.to_dict() for a in paginated.items],
        'total':    paginated.total,
        'page':     page,
        'pages':    paginated.pages,
    })


@app.route('/api/authors/<int:id>', methods=['GET'])
def get_author(id):
    """GET /api/authors/<id>"""
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    return jsonify({'success': True, 'author': author.to_dict()})


@app.route('/api/authors', methods=['POST'])
def create_author():
    """POST /api/authors  — body: {name, bio, city}"""
    data = request.get_json()
    if not data or not data.get('name', '').strip():
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    author = Author(
        name=data['name'].strip(),
        bio=data.get('bio', '').strip() or None,
        city=data.get('city', '').strip() or None,
    )
    db.session.add(author)
    db.session.commit()
    return jsonify({'success': True, 'author': author.to_dict()}), 201


@app.route('/api/authors/<int:id>', methods=['PUT'])
def update_author(id):
    """PUT /api/authors/<id>  — body: {name?, bio?, city?}"""
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    data = request.get_json() or {}
    if 'name' in data:
        if not data['name'].strip():
            return jsonify({'success': False, 'error': 'Name cannot be empty'}), 400
        author.name = data['name'].strip()
    if 'bio'  in data: author.bio  = data['bio'].strip()  or None
    if 'city' in data: author.city = data['city'].strip() or None
    db.session.commit()
    return jsonify({'success': True, 'author': author.to_dict()})


@app.route('/api/authors/<int:id>', methods=['DELETE'])
def delete_author(id):
    """DELETE /api/authors/<id>  — cascades to books"""
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404
    db.session.delete(author)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Author "{author.name}" deleted'})


# =============================================================================
# BOOK ROUTES  (full CRUD)
# =============================================================================

@app.route('/api/books', methods=['GET'])
def get_books():
    """GET /api/books?q=<title>&author=<name>&genre=<g>&sort=title&order=asc&page=1&per_page=20"""
    query = Book.query.join(Author)

    title_q  = request.args.get('q', '').strip()
    author_q = request.args.get('author', '').strip()
    genre_q  = request.args.get('genre', '').strip()
    if title_q:  query = query.filter(Book.title.ilike(f'%{title_q}%'))
    if author_q: query = query.filter(Author.name.ilike(f'%{author_q}%'))
    if genre_q:  query = query.filter(Book.genre.ilike(f'%{genre_q}%'))

    sort_field = request.args.get('sort', 'title')
    order      = request.args.get('order', 'asc')
    col_map    = {'title': Book.title, 'year': Book.year,
                  'author': Author.name, 'created_at': Book.created_at}
    sort_col   = col_map.get(sort_field, Book.title)
    query      = query.order_by(sort_col.desc() if order == 'desc' else sort_col.asc())

    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'books':   [b.to_dict() for b in paginated.items],
        'total':   paginated.total,
        'page':    page,
        'pages':   paginated.pages,
    })


@app.route('/api/books/<int:id>', methods=['GET'])
def get_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    return jsonify({'success': True, 'book': book.to_dict()})


@app.route('/api/books', methods=['POST'])
def create_book():
    """POST /api/books  — body: {title, author_id, year?, isbn?, genre?}"""
    data = request.get_json()
    if not data or not data.get('title', '').strip():
        return jsonify({'success': False, 'error': 'Title is required'}), 400
    if not data.get('author_id'):
        return jsonify({'success': False, 'error': 'author_id is required'}), 400

    author = Author.query.get(data['author_id'])
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404

    # ISBN uniqueness
    isbn = data.get('isbn', '').strip() or None
    if isbn and Book.query.filter_by(isbn=isbn).first():
        return jsonify({'success': False, 'error': 'ISBN already exists'}), 400

    book = Book(
        title=data['title'].strip(),
        author_id=data['author_id'],
        year=data.get('year') or None,
        isbn=isbn,
        genre=data.get('genre', '').strip() or None,
    )
    db.session.add(book)
    db.session.commit()
    return jsonify({'success': True, 'book': book.to_dict()}), 201


@app.route('/api/books/<int:id>', methods=['PUT'])
def update_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    data = request.get_json() or {}
    if 'title' in data:
        if not data['title'].strip():
            return jsonify({'success': False, 'error': 'Title cannot be empty'}), 400
        book.title = data['title'].strip()
    if 'author_id' in data:
        if not Author.query.get(data['author_id']):
            return jsonify({'success': False, 'error': 'Author not found'}), 404
        book.author_id = data['author_id']
    if 'year'  in data: book.year  = data['year']  or None
    if 'isbn'  in data:
        isbn = data['isbn'].strip() or None
        if isbn:
            conflict = Book.query.filter_by(isbn=isbn).first()
            if conflict and conflict.id != id:
                return jsonify({'success': False, 'error': 'ISBN already exists'}), 400
        book.isbn = isbn
    if 'genre' in data: book.genre = data['genre'].strip() or None
    db.session.commit()
    return jsonify({'success': True, 'book': book.to_dict()})


@app.route('/api/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    db.session.delete(book)
    db.session.commit()
    return jsonify({'success': True, 'message': f'Book "{book.title}" deleted'})


# =============================================================================
# STATS ROUTE (for dashboard)
# =============================================================================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_books   = Book.query.count()
    total_authors = Author.query.count()
    recent_books  = Book.query.order_by(Book.created_at.desc()).limit(5).all()
    recent_authors = Author.query.order_by(Author.created_at.desc()).limit(5).all()
    return jsonify({
        'success':        True,
        'total_books':    total_books,
        'total_authors':  total_authors,
        'recent_books':   [b.to_dict() for b in recent_books],
        'recent_authors': [a.to_dict() for a in recent_authors],
    })


# =============================================================================
# INITIALIZE DATABASE WITH SAMPLE DATA
# =============================================================================

def init_db():
    with app.app_context():
        db.create_all()
        if Author.query.count() == 0:
            authors_data = [
                {'name': 'Robert C. Martin', 'city': 'USA',
                 'bio': 'Software engineer and author known as \"Uncle Bob\".'},
                {'name': 'Eric Evans',        'city': 'USA',
                 'bio': 'Author of Domain-Driven Design.'},
                {'name': 'Martin Fowler',     'city': 'USA',
                 'bio': 'British software developer, author & public speaker.'},
            ]
            authors = []
            for ad in authors_data:
                a = Author(**ad)
                db.session.add(a)
                authors.append(a)
            db.session.commit()

            books_data = [
                {'title': 'Clean Code',                 'year': 2008, 'genre': 'Software',   'author': authors[0]},
                {'title': 'The Clean Coder',             'year': 2011, 'genre': 'Software',   'author': authors[0]},
                {'title': 'Domain-Driven Design',        'year': 2003, 'genre': 'Software',   'author': authors[1]},
                {'title': 'Refactoring',                 'year': 1999, 'genre': 'Software',   'author': authors[2]},
                {'title': 'Patterns of Enterprise App.', 'year': 2002, 'genre': 'Software',   'author': authors[2]},
            ]
            for bd in books_data:
                b = Book(title=bd['title'], year=bd['year'],
                         genre=bd['genre'], author_id=bd['author'].id)
                db.session.add(b)
            db.session.commit()
            print('✓ Sample data initialized!')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)