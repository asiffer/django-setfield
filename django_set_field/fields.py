from typing import Any, Iterable, List, Set, Union

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Lookup
from django.utils.translation import gettext as _

from django_set_field.forms import TypedMultipleChoiceField


class NoFlatchoicesPropertyMixin:
    """This mixin is required to delete the "flatchoices" property
    which is used to display the model in the admin panel.
    It allows to use the SetField in list_display.
    However flatchoices is also used for list_filter: by overriding it, we
    cannot use the field for filtering. We should rather use a custom
    filter in the admin panel.
    """

    @property
    def flatchoices(self, *args, **kwargs):
        return []


class SetField(NoFlatchoicesPropertyMixin, models.Field):
    description: str = _("Multiple value selection within a set")
    _options: List[Any]
    _default: Set[Any]

    def __init__(
        self,
        *args: Any,
        options: List[Any],
        **kwargs: Any,
    ) -> None:
        self._options = list(options)
        default = kwargs.get("default", [])
        if default in self._options:
            self._default = {default}
        else:
            self._default = set(default)

        kwargs.pop("choices", None)

        self.choices = [
            (k, frozenset(self.int_to_choices(k)))
            for k in range(0, pow(2, len(self._options)))
        ]
        super().__init__(*args, **kwargs)

    def get_internal_type(self):
        return "PositiveBigIntegerField"

    def choices_to_int(self, choices: Union[int, Iterable[Any]]) -> int:
        """Converts a set into the corresponding integer"""
        if isinstance(choices, int):
            return choices
        return sum((1 << k) for k, c in enumerate(self._options) if c in choices)

    def int_to_choices(self, n: int) -> Iterable[Any]:
        """Convert an integer into the corresponding set"""
        return set(c for k, c in enumerate(self._options) if n & (1 << k))

    def deconstruct(self) -> Any:
        """ """
        name, path, args, kwargs = super().deconstruct()
        kwargs["options"] = self._options
        kwargs["default"] = self._default
        return name, path, args, kwargs

    def to_python(self, value: Any) -> Any:
        """
        Converts the value into the correct Python object. It acts as
        the reverse of value_to_string(), and is also called in clean().

        to_python() is called by deserialization and during the clean()
        method used from forms.
        As a general rule, to_python() should deal gracefully with any
        of the following arguments:

        - An instance of the correct type (e.g., a Set in our example).
        - A string
        - None (if the field allows null=True)
        """
        if isinstance(value, list):
            return set(value)
        p = super().to_python(value)
        return self.int_to_choices(p)

    def from_db_value(self, value, expression, connection):
        """Converts a value as returned by the database to a Python object.
        It is the reverse of get_prep_value().
        """
        if isinstance(value, int):
            return self.int_to_choices(value)
        return value

    def get_prep_value(self, value: Union[int, Iterable[Any]]) -> Any:
        """Since using a database requires conversion in both ways,
        if you override from_db_value() you also have to override
        get_prep_value() to convert Python objects back to query values.

        https://docs.djangoproject.com/en/4.1/howto/custom-model-fields/#converting-python-objects-to-query-values
        """
        if isinstance(value, int):
            v = 1 << value
        elif isinstance(value, str):
            v = self.choices_to_int([value])
        else:
            v = self.choices_to_int(value)
        x = super().get_prep_value(v)
        return x

    def formfield(self, **kwargs):
        defaults = {
            "form_class": TypedMultipleChoiceField,
            "choices": [(f"{o}", f"{o}") for o in self._options],
            "widget": forms.CheckboxSelectMultiple,
            "required": False,
        }
        kwargs.update(defaults)
        return super().formfield(**kwargs)

    def validate(self, value: set, model_instance: models.Model | None) -> None:
        if not value.issubset(self._options):
            raise ValidationError(
                _(f"Value {value} is not a subset of {self._options}")
            )

    def pre_save(self, model_instance: models.Model, add: bool) -> Any:
        # get the passed value
        obj = super().pre_save(model_instance, add)
        # turn it into set
        obj = set(obj)
        # validate value
        if add:
            self.validate(obj, model_instance)
        return obj

    def get_default(self) -> Any:
        return self._default

    def value_to_string(self, obj: Any) -> List[Any]:  # type:ignore
        """This method is called to serialiaze a field. In particular this is used
        while dumping data (creating fixture from db records). In the setfield
        case, one must return a list.
        """
        value: Set[Any] = self.value_from_object(obj)
        return list(value)


class Includes(Lookup):
    lookup_name = "includes"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return f"({lhs} & {rhs})", params


SetField.register_lookup(Includes)
