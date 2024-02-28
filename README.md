# django-setfield

[![Build](https://github.com/asiffer/django-setfield/actions/workflows/build.yaml/badge.svg)](https://github.com/asiffer/django-setfield/actions/workflows/build.yaml)
[![Publish](https://github.com/asiffer/django-setfield/actions/workflows/publish.yaml/badge.svg)](https://github.com/asiffer/django-setfield/actions/workflows/publish.yaml)
[![PyPI version](https://badge.fury.io/py/django-setfield.svg)](https://badge.fury.io/py/django-setfield)

Django model field to handle sets (in the python/math sense)

> [!CAUTION]
> Since version `0.3.0` the "choices" must be passed through the `options` keyword.

## Installation

```shell
pip install django-setfield
```

## Get started

```python
from django.db import models
from django_set_field.fields import SetField


class TestModel(models.Model):
    OPTIONS = ["TOMTOM", "NANA"]

    tags = SetField(options=OPTIONS)
```

Now you can manipulate the field like a python set

```python
m = TestModel()
m.tags.add("TOMTOM")
m.save()
```

The default value for the `SetField` is the empty set (you do not have to declare it) but you can define a different one.

```python
class TestModel(models.Model):
    OPTIONS = ["TOMTOM", "NANA"]

    tags = SetField(options=OPTIONS, default={"NANA"})
```

> [!WARNING]
> The parameter `options` does not create a constraint on the DB side (see [Internals](#internals)). It means that you can change it without migration but the **previous stored values will lose their meaning**. The _good_ practice is obviously not to modify it but if you really need to add new option, you must **append** them to the list.

## Querying

The package provides a custom lookup `__includes` that performs a subset query.

```python
# find all the objects such that 'tags ⊇ {"TOMTOM"}'
TestModel.objects.filter(tags__includes={"TOMTOM"})
```

## Admin

Models with `SetField` can be registered in the admin panel. We also recommend to use the dedicated `SetFieldFilter` if you want to filter on the field.

```python
from django.contrib import admin
from django_set_field.admin import SetFieldFilter
from app.models import TestModel

class TestModelAdmin(admin.ModelAdmin):
    list_display = ["id", "tags"]
    list_filter = [("tags", SetFieldFilter)]

admin.site.register(TestModel, TestModelAdmin)
```

The `SetField` is currently "displayable" as a raw string.

![admin model list](assets/django_admin_list_display.png)

You can modify this behaviour by referencing a method in the admin model

```python
class TestModelAdmin(admin.ModelAdmin):
    list_display = ["id", "get_tags"]
    # you can display the filter
    list_filter = [("tags", SetFieldFilter)]

    def get_tags(self, obj: TestModel) -> str:
        return "+".join(sorted(obj.tags))

    get_tags.short_description = "tags"
```

You can even provide a fancier result by returning html

```python
from django.utils.safestring import mark_safe

def to_css(d: dict):
    return ";".join([f"{k}: {v}" for k, v in d.items()])


class TestModelAdmin(admin.ModelAdmin):
    list_display = ["id", "get_tags"]
    list_filter = [("tags", SetFieldFilter)]

    def get_tags(self, obj: TestModel) -> str:
        base_style = {
            "margin": "0 0.2em",
            "padding": "0.2em 0.5em",
            "border-radius": "5px",
            "color": "white",
        }
        style = {
            "TOMTOM": base_style | {"background-color": "#e9c46a"},
            "NANA": base_style | {"background-color": "#2a9d8f"},
        }
        spans = [
            f"""<span style="{to_css(style[tag])}">{tag}</span>"""
            for tag in sorted(obj.tags)
        ]
        return mark_safe("".join(spans))

    get_tags.short_description = "tags"
```

![admin fancy list display](assets/django_admin_list_display_fancy.png)

In the creation form, a multi-checkbox widget is used to select among the available options.

![admin form create](assets/django_admin_create_form.png)

## DRF

[DRF](https://www.django-rest-framework.org/) supports `SetField` through the `MultipleChoiceField` (but currently you must pass the choices manually)

```python
from rest_framework import serializers

from .models import TestModel

class TestSerializer(serializers.ModelSerializer):
    tags = serializers.MultipleChoiceField(choices=TestModel.OPTIONS)

    class Meta:
        model = TestModel
        fields = ["tags"]
        read_only_fields = ["id"]
```

## Testing

After local installation, you can run the tests with the `runtests.py` dedicated command.

```shell
poetry install
poetry run ./runtests.py
```

If you want to interact with simple example, and explore the admin panel:

```shell
poetry run ./rundev.py
# You can visit http://127.0.0.1:8000/admin/ - default credentials: admin/admin
```

## Internals

The strategy to implement such a field is merely to use the bits of an integer. Thus, a `SetField` is a `PositiveBigIntegerField`. As an example, with `options=["TOMTOM", "NANA"]` we have

| Set                  | Binary | Integer |
| -------------------- | ------ | ------- |
| `{}`                 | `0b00` | `0`     |
| `{"TOMTOM"}`         | `0b01` | `1`     |
| `{"NANA"}`           | `0b10` | `2`     |
| `{"TOMTOM", "NANA"}` | `0b11` | `3`     |

The order of the options is then very important to keep your logic coherent. You should not change it if some records are stored in DB.
