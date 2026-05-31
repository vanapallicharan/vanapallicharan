# Django E-Commerce Website

Academic portfolio implementation of a basic e-commerce workflow.

## Features

- Product listing and categories
- Cart add/remove/update flow
- Checkout page
- Order placement model
- Admin-manageable products and orders
- SQLite-backed development setup

## Tech Stack

- Django
- SQLite
- HTML templates
- CSS
- JavaScript-ready structure

## Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open `http://127.0.0.1:8000/`.
