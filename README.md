# BikeParts Django Demo
## Project structure
```
bikeshop/
  manage.py
  requirements.txt
  bikeshop/
    settings.py
    urls.py
    wsgi.py
    asgi.py
  shop/
    models.py
    views.py
    urls.py
    admin.py
    cart.py
    templates/
      base.html
      shop/
        product_list.html
        cart.html
        signup.html
        login.html
    static/
      shop/css/styles.css
    management/
      commands/
        load_bike_data.py
```

## Quickstart

Now available on website: https://bikeshop-u77v.onrender.com/

1) Create a virtualenv:
```
cd bikeshop
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) Migrate data:
```
python manage.py migrate
python manage.py createsuperuser
```

3) Run server:
```
python manage.py runserver
```

Open http://127.0.0.1:8000/
