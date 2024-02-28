from django.contrib import admin
from django.utils.safestring import mark_safe

from django_set_field.admin import SetFieldFilter

from .models import TestModel


def to_css(d: dict):
    return ";".join([f"{k}: {v}" for k, v in d.items()])


class TestModelAdmin(admin.ModelAdmin):
    list_display = ["id", "get_tags"]

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

    setattr(get_tags, "short_description", "tags")
    list_filter = [
        ("tags", SetFieldFilter),
    ]


admin.site.register(TestModel, TestModelAdmin)
