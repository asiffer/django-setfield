from typing import List

from django.db import models

from django_set_field.fields import SetField


class TestModel(models.Model):
    OPTIONS: List[str] = ["TOMTOM", "NANA"]

    tags = SetField(options=OPTIONS)


class TestModelWithDefault(models.Model):
    OPTIONS: List[str] = ["TOMTOM", "NANA"]

    tags = SetField(options=OPTIONS, default=set(OPTIONS[:1]))
