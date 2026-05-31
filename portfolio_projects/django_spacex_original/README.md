# Django SpaceX E-Commerce Website

Recovered Django e-commerce project found in:

`C:\Users\chara\Desktop\study\intern\djangospacex.zip`

The archive included a full virtual environment named `djangospacex`, with `pyvenv.cfg`, `Scripts/activate`, `Scripts/python.exe`, and `Lib/site-packages`. For GitHub, only the project source and dependency files were imported. The virtual environment, caches, and local SQLite database are intentionally not tracked.

## Included Source

- `djangospacex/ecommerce/manage.py`
- `djangospacex/ecommerce/ecommerce/` - Django project settings and URLs
- `djangospacex/ecommerce/ecomapp/` - product, cart, checkout, auth, tracker, and contact logic
- `djangospacex/ecommerce/templates/` - site templates
- `djangospacex/ecommerce/static/` - CSS, JavaScript, and frontend assets
- `djangospacex/ecommerce/media/` - product/media assets from the original project
- `djangospacex/project/requirements.txt`
- Supporting scripts: `generate_bill.py`, `initialize_database.py`

## Safety Cleanup

- Replaced the hard-coded Django `SECRET_KEY` with `DJANGO_SECRET_KEY` environment lookup.
- Excluded `db.sqlite3`, `__pycache__/`, and virtual environment folders from Git.
- Paytm fields in the source are placeholders such as `add ur merchant id` / `addyour key`; no real payment credentials were found in the checked code.

## Run Locally

```bash
cd djangospacex/ecommerce
python -m venv .venv
.venv\Scripts\activate
pip install -r ..\project\requirements.txt
python manage.py migrate
python manage.py runserver
```
