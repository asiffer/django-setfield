from typing import Type

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db import models
from django.http import HttpRequest

from .fields import SetField


class SetFieldFilter(admin.FieldListFilter):
    def __init__(
        self,
        field: SetField,
        request: HttpRequest,
        params: dict,
        model: Type[models.Model],
        model_admin: admin.ModelAdmin,
        field_path: str,
    ):

        if not isinstance(field, SetField):
            raise TypeError("the input field must be a SetField")
        self.options = field._options  # type: ignore
        self.lookup_kwarg = f"{field_path}__includes"
        self.lookup_val = params.get(self.lookup_kwarg, [])
        super().__init__(field, request, params, model, model_admin, field_path)

    def choices(self, changelist: ChangeList):
        for opt in self.options:
            yield {
                "selected": opt in self.lookup_val,
                "query_string": f"?{self.lookup_kwarg}={opt}",
                "display": f"{opt}",
            }

    def expected_parameters(self):
        return [self.lookup_kwarg]
