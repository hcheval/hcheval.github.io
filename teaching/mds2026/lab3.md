# Lab 3 - MVC

## What is MVC?

MVC (Model-View-Controller) is an architectural pattern that splits an application into three components:

- **Model** - the data and business logic. Defines the database schema.
- **View** - the presentation layer. Renders data as HTML (or JSON, etc.).
- **Controller** - receives user requests, queries the model, picks which view to display.

Without this separation, you end up with SQL queries mixed into HTML, business logic scattered across templates, and code nobody wants to touch. MVC forces a structure where each part does one thing.

Many MVC frameworks exist across languages and ecosystems (Spring for Java, Rails for Ruby, ASP.NET for C#, etc.). For this lab we'll use Django, a Python framework.

Django uses a variant called **MTV** (Model-Template-View) with the same structure but different names. The terminology is confusing: what MVC calls "Controller", Django calls "View"; what MVC calls "View", Django calls "Template".

| MVC        | Django     | File              |
|------------|------------|-------------------|
| Model      | Model      | `models.py`       |
| Controller | View       | `views.py`        |
| View       | Template   | `templates/*.html`|

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install django
```

## Creating the project

```bash
django-admin startproject catalog .
python manage.py startapp courses
```

This creates two directories:
- `catalog/` holds the project configuration (`settings.py`, `urls.py`). No business logic goes here.
- `courses/` is the actual application: models, views, templates.

A Django project can contain multiple apps (e.g. `courses`, `students`, `reviews`).

Register the app in `catalog/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'courses',
]
```

## 1. Model

`courses/models.py` defines the data structure. Each class that inherits from `models.Model` becomes a database table, and each attribute becomes a column. You don't write SQL; Django handles that.

```python
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Course(models.Model):
    title = models.CharField(max_length=200)
    instructor = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    year = models.IntegerField()
    semester = models.CharField(
        max_length=10,
        choices=[('fall', 'Fall'), ('spring', 'Spring')],
        default='fall',
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='courses',
    )

    def __str__(self):
        return f"{self.title} ({self.year})"
```

`ForeignKey` creates a relationship between `Course` and `Category` (each course belongs to one category).
Django uses SQLite by default (the `db.sqlite3` file appears in your project directory). Run the commands below to generate the SQL tables from the Python models: `makemigrations` generates a script describing the changes, and `migrate` executes it against the database.

```bash
python manage.py makemigrations
python manage.py migrate
```

Start the server with `python manage.py runserver` and go to `http://127.0.0.1:8000/`. There are no views or templates yet, so you'll see the default Django page.

## 2. Views (Controller)

`courses/views.py` is where you write the functions that handle HTTP requests and return responses. Each view receives a `request` object (containing the HTTP method, URL parameters, form data, etc.) and must return a `response` (usually HTML rendered from a template).

The typical pattern is: pull data from the model, pass it to a template, return the resulting HTML.

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Course, Category
from .forms import CourseForm


def course_list(request):
    courses = Course.objects.all().order_by('-year', 'title')
    categories = Category.objects.all().order_by('name')

    category_id = request.GET.get('category')
    if category_id:
        courses = courses.filter(category_id=category_id)

    query = request.GET.get('q', '')
    if query:
        courses = courses.filter(
            Q(title__icontains=query) | Q(instructor__icontains=query)
        )

    return render(request, 'courses/course_list.html', {
        'courses': courses,
        'categories': categories,
        'query': query,
    })


def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    return render(request, 'courses/course_detail.html', {'course': course})


@login_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            return redirect('course_detail', pk=course.pk)
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {'form': form, 'action': 'Add'})
```

A few things to notice:

- `get_object_or_404` looks up an object in the database and automatically returns an HTTP 404 if it doesn't exist. You could do `try/except Course.DoesNotExist` manually, but this is shorter and more idiomatic in Django.
- `@login_required` is a decorator that checks if the user is authenticated. If not, it redirects to the login page.
- `request.GET` is a dictionary of URL parameters. When a user visits `/?q=algebra`, `request.GET.get('q')` returns `'algebra'`.
- `Q(title__icontains=query)` does a case-insensitive search. `Q` lets you combine multiple conditions with `|` (OR) or `&` (AND).

**Exercise:** The code above only covers `course_list`, `course_detail`, and `course_create`. Write the `course_edit` and `course_delete` views yourself. `course_edit` is very similar to `course_create` (it also uses `CourseForm`), but it receives a `pk` argument and passes an existing `instance` to the form. `course_delete` should handle GET (show a confirmation page) and POST (actually delete the course and redirect to the list).

## 3. Forms

Django can auto-generate forms from models. In `courses/forms.py`:

```python
from django import forms
from .models import Course


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'instructor', 'description', 'year', 'semester', 'category']
```

`ModelForm` looks at the `Course` model, takes the specified fields, and generates the corresponding HTML form fields (text input for `CharField`, dropdown for `ForeignKey`, etc.). Validation comes for free: if someone submits a form with the year left blank, Django returns an error automatically.

## 4. URLs

Routes map URLs to view functions. When a user visits `http://127.0.0.1:8000/new/`, Django scans the route list for a matching pattern (`new/`) and calls the associated function (`views.course_create`).

In `courses/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('new/', views.course_create, name='course_create'),
    path('<int:pk>/', views.course_detail, name='course_detail'),
    path('<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('<int:pk>/delete/', views.course_delete, name='course_delete'),
]
```

`<int:pk>` is a dynamic segment: `path('<int:pk>/', views.course_detail)` matches `/1/`, `/2/`, `/57/`, etc., and passes the value as the `pk` argument to `course_detail`.

In `catalog/urls.py`, include the app routes (along with admin and auth routes):

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('courses.urls')),
]
```

## 5. Templates (View)

Templates are HTML files with special Django syntax: `{{ variable }}` to display values and `{% tag %}` for logic (conditionals, loops, inheritance). Django has an inheritance system: you define a base template with the common layout (nav, CSS), and specific templates extend it and fill in the blocks.

First, create the template directory. Django expects a specific nested structure:

```bash
mkdir -p courses/templates/courses
mkdir -p courses/templates/registration
```

`courses/templates/courses/base.html` holds the common layout:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Course Catalog{% endblock %}</title>
</head>
<body>
    <nav>
        <a href="{% url 'course_list' %}">All Courses</a>
        {% if user.is_authenticated %}
        <a href="{% url 'course_create' %}">Add Course</a>
        {% endif %}
    </nav>
    {% block content %}{% endblock %}
</body>
</html>
```

`courses/templates/courses/course_list.html` displays the course list with filtering:

```html
{% extends "courses/base.html" %}

{% block content %}
<h1>Course Catalog</h1>

<form method="get">
    <input type="text" name="q" placeholder="Search..." value="{{ query }}">
    <select name="category">
        <option value="">All categories</option>
        {% for cat in categories %}
        <option value="{{ cat.pk }}">{{ cat.name }}</option>
        {% endfor %}
    </select>
    <button type="submit">Filter</button>
</form>

{% for course in courses %}
<div>
    <a href="{% url 'course_detail' course.pk %}">{{ course.title }}</a>
    <div>{{ course.instructor }} | {{ course.category.name }}</div>
</div>
{% empty %}
<p>No courses found.</p>
{% endfor %}
{% endblock %}
```

Notice `{% url 'course_detail' course.pk %}`: instead of hardcoding the URL `/3/`, you use the route name defined in `urls.py`. If you later change the URL structure, the templates don't need to be updated.

**Exercise:** Write the remaining templates yourself:
- `course_detail.html`: show all fields of a single course (title, instructor, description, year, semester, category). Add links to edit and delete (visible only if the user is authenticated).
- `course_form.html`: a form for creating/editing a course. Use `{{ form.as_p }}` to render the form fields and don't forget `{% csrf_token %}` inside the `<form>` tag.
- `course_confirm_delete.html`: a confirmation page ("Are you sure you want to delete X?") with a POST form to confirm.
- `registration/login.html`: a login page. Same idea as the form template: `{{ form.as_p }}` with a submit button.

All of these should `{% extends "courses/base.html" %}`.

Restart the server and verify that the list page loads, you can click into a course detail, and the create form works (you'll need to log in first).

## 6. Admin

So far the only way to add courses to the database is through the form. Django ships with a built-in admin interface that lets you manage data directly, without writing additional views or templates. You just need to register your models in `courses/admin.py`:

```python
from django.contrib import admin
from .models import Category, Course

admin.site.register(Category)
admin.site.register(Course)
```

Create a superuser and go to `http://127.0.0.1:8000/admin/`:

```bash
python manage.py createsuperuser
python manage.py runserver
```

From the admin panel you can add, edit, and delete categories and courses without any extra code.

## 7. REST API

So far all views return HTML. But the same model can also be exposed as JSON, for clients that aren't browsers (other apps, scripts, separate frontends). This is a key point of MVC separation: the model stays the same, only the representation changes.

In `views.py`:

```python
from django.http import JsonResponse

def api_courses(request):
    courses = Course.objects.all().order_by('-year', 'title')
    data = [
        {
            'id': c.pk,
            'title': c.title,
            'instructor': c.instructor,
            'year': c.year,
            'category': c.category.name,
        }
        for c in courses
    ]
    return JsonResponse(data, safe=False)
```

Don't forget to add the API routes in `courses/urls.py`:

```python
    path('api/courses/', views.api_courses, name='api_courses'),
    path('api/courses/<int:pk>/', views.api_course_detail, name='api_course_detail'),
```

**Exercise:** Write the `api_course_detail` view. It should return JSON for a single course (look up by `pk`, return 404 if not found).

Test with `curl`:

```bash
curl http://127.0.0.1:8000/api/courses/ | python -m json.tool
```

## 8. Authentication

Django has built-in authentication:

- `@login_required` goes on the create/edit/delete views. If the user isn't authenticated, they get redirected to the login page.
- `path('accounts/', include('django.contrib.auth.urls'))` automatically adds routes for `/accounts/login/`, `/accounts/logout/`, etc.
- In templates, `{% if user.is_authenticated %}` controls which buttons are shown.

In `catalog/settings.py`:

```python
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
```

## 9. Tests

Django comes with a test client that simulates HTTP requests without starting the server. Each test runs on a temporary database that gets created and destroyed automatically, so there's no risk of corrupting real data.

In `courses/tests.py`:

```python
from django.test import TestCase, Client
from .models import Category, Course


class CourseViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Mathematics')
        self.course = Course.objects.create(
            title='Linear Algebra',
            instructor='Georgescu Ana',
            year=2026,
            semester='fall',
            category=self.category,
        )

    def test_list_view(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Linear Algebra')

    def test_detail_view(self):
        response = self.client.get(f'/{self.course.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Georgescu Ana')

    def test_detail_404(self):
        response = self.client.get('/9999/')
        self.assertEqual(response.status_code, 404)

    def test_create_requires_login(self):
        response = self.client.get('/new/')
        self.assertEqual(response.status_code, 302)

    def test_api(self):
        response = self.client.get('/api/courses/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data[0]['title'], 'Linear Algebra')
```

Run the tests:

```bash
python manage.py test
```

## Exercises

1. Add a `credits` field (number of credits) to the `Course` model. Run `makemigrations` and `migrate`. Display the credits in the list and detail templates.

2. Add a page that shows all courses in a category (`/category/<int:pk>/`). Make the category name in the course list a link to this page.
