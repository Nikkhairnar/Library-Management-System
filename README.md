# Part 4: Library Management System — REST API with Flask

## Overview
A full-featured **Library Management System** REST API built with Flask & SQLAlchemy.  
Supports complete **CRUD operations** for both **Authors** and **Books**, with search, sorting, and pagination.

---

## What Learned
- REST API concepts (GET, POST, PUT, DELETE)
- JSON responses with `jsonify()`
- API error handling and HTTP status codes
- Query parameters for filtering, sorting & pagination
- Relational data models with Flask-SQLAlchemy
- Cascade deletes and foreign key relationships
- Testing APIs with `curl`

---

## How to Run

```bash
cd part-4
python app.py
```

Visit: **http://localhost:5000**

> The database is **auto-created** on first run and seeded with sample authors & books.

---

## Project Structure

```
Library-Management-System/
├── app.py              ← Models + all REST API routes
├── templates/
│   └── index.html      ← Single-page frontend (SPA)
├── instance/
│   └── library.db      ← SQLite database (auto-created)
└── README.md
```

---

## Data Models

### Author
| Field        | Type     | Notes                         |
|--------------|----------|-------------------------------|
| `id`         | Integer  | Primary key (auto-increment)  |
| `name`       | String   | **Required**                  |
| `bio`        | Text     | Optional biography            |
| `city`       | String   | Optional city                 |
| `created_at` | DateTime | Auto-set on creation          |

### Book
| Field        | Type     | Notes                                  |
|--------------|----------|----------------------------------------|
| `id`         | Integer  | Primary key (auto-increment)           |
| `title`      | String   | **Required**                           |
| `author_id`  | Integer  | Foreign key → Author (**Required**)    |
| `year`       | Integer  | Published year                         |
| `isbn`       | String   | Must be unique if provided             |
| `genre`      | String   | Optional genre/category                |
| `created_at` | DateTime | Auto-set on creation                   |

> Deleting an **Author** automatically deletes all their books (cascade delete).

---

## API Reference

### Authors — `/api/authors`

| Method     | URL                    | Body / Params                  | Description                        |
|------------|------------------------|--------------------------------|------------------------------------|
| `GET`      | `/api/authors`         | `?q=name&sort=name&order=asc&page=1&per_page=100` | List / search authors |
| `GET`      | `/api/authors/<id>`    | —                              | Get one author by ID               |
| `POST`     | `/api/authors`         | `{ name, bio?, city? }`        | Create a new author                |
| `PUT`      | `/api/authors/<id>`    | `{ name?, bio?, city? }`       | Update an existing author          |
| `DELETE`   | `/api/authors/<id>`    | —                              | Delete author + all their books    |

---

### Books — `/api/books`

| Method     | URL                 | Body / Params                                 | Description               |
|------------|---------------------|-----------------------------------------------|---------------------------|
| `GET`      | `/api/books`        | `?q=title&author=name&genre=g&sort=title&order=asc&page=1&per_page=100` | List / search books |
| `GET`      | `/api/books/<id>`   | —                                             | Get one book by ID        |
| `POST`     | `/api/books`        | `{ title, author_id, year?, isbn?, genre? }`  | Create a new book         |
| `PUT`      | `/api/books/<id>`   | `{ title?, author_id?, year?, isbn?, genre? }` | Update an existing book  |
| `DELETE`   | `/api/books/<id>`   | —                                             | Delete a book             |

---

### Stats — `/api/stats`

| Method | URL          | Description                                            |
|--------|--------------|--------------------------------------------------------|
| `GET`  | `/api/stats` | Returns total author/book counts + 5 most recent each |

---

## HTTP Status Codes

| Code  | Meaning       | When Used                        |
|-------|---------------|----------------------------------|
| `200` | OK            | Successful GET, PUT, DELETE      |
| `201` | Created       | Successful POST                  |
| `400` | Bad Request   | Missing or invalid data          |
| `404` | Not Found     | Record doesn't exist             |

---

## API Response Format

All endpoints return JSON in this shape:

```json
{
    "success": true,
    "message": "Optional message",
    "data": { }
}
```

---

## Testing with curl

### Authors

```bash
# List all authors
curl http://localhost:5000/api/authors

# Search + sort
curl "http://localhost:5000/api/authors?q=martin&sort=name&order=asc"

# Get one author
curl http://localhost:5000/api/authors/1

# Create
curl -X POST http://localhost:5000/api/authors \
  -H "Content-Type: application/json" \
  -d '{"name": "J.K. Rowling", "city": "UK", "bio": "British author."}'

# Update
curl -X PUT http://localhost:5000/api/authors/1 \
  -H "Content-Type: application/json" \
  -d '{"city": "London"}'

# Delete (also removes their books)
curl -X DELETE http://localhost:5000/api/authors/1
```

### Books

```bash
# List all books
curl http://localhost:5000/api/books

# Filter by author + genre
curl "http://localhost:5000/api/books?author=martin&genre=software&sort=year&order=desc"

# Get one book
curl http://localhost:5000/api/books/1

# Create
curl -X POST http://localhost:5000/api/books \
  -H "Content-Type: application/json" \
  -d '{"title": "Clean Architecture", "author_id": 1, "year": 2017, "genre": "Software"}'

# Update
curl -X PUT http://localhost:5000/api/books/1 \
  -H "Content-Type: application/json" \
  -d '{"year": 2018, "isbn": "978-0134494166"}'

# Delete
curl -X DELETE http://localhost:5000/api/books/1
```

### Stats

```bash
curl http://localhost:5000/api/stats
```

---

## Key Concepts

### JSON Response
```python
return jsonify({'success': True, 'data': {...}}), 200
```

### Reading Request Data
```python
data = request.get_json()          # JSON body (POST / PUT)
value = request.args.get('key')    # Query params (?key=value)
```

### Model → Dictionary
```python
def to_dict(self):
    return {'id': self.id, 'title': self.title}
```

### Cascade Delete
```python
# Deleting an Author automatically deletes all linked Books
books = db.relationship('Book', backref='author_info',
                        lazy=True, cascade='all, delete-orphan')
```

---

## Sample Data (Auto-loaded on First Run)

| Author           | Books                                                       |
|------------------|-------------------------------------------------------------|
| Robert C. Martin | *Clean Code* (2008), *The Clean Coder* (2011)               |
| Eric Evans       | *Domain-Driven Design* (2003)                               |
| Martin Fowler    | *Refactoring* (1999), *Patterns of Enterprise App.* (2002)  |

---

## Exercises Performed

1. Added pagination controls: `/api/books?page=2&per_page=10`
2. Added sort controls: `/api/books?sort=year&order=desc`
3. Added a new route `/api/authors/<id>/books` — list all books for one author
4. Added ISBN lookup: `/api/books/isbn/<isbn>`
