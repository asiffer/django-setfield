from typing import Any, Iterable, List, Set, Union

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_set_field.debug import hook_class
from django_set_field.forms import TypedMultipleChoiceField
from django_set_field.widgets import MultiCheckbox


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


class SetField(NoFlatchoicesPropertyMixin, models.PositiveBigIntegerField):
    description: str = _("Multiple value selection within a set")
    _choices: List[Any]
    _default: Set[Any]

    def __init__(
        self,
        *args: Any,
        choices: List[Any] = [],
        default: Union[int, Iterable[Any]] = set(),
        **kwargs: Any,
    ) -> None:
        self._choices = list(choices)
        # if we pass the value as an int, we first convert it
        # to a set of choices
        if isinstance(default, int):
            default = self.int_to_choices(default)
        self._default = set(default)

        assert self._default.issubset(
            self._choices
        ), "the default set must be a subset of choices"
        # turn choice into django common 'choices' argument
        django_choices = [
            (f"{c}", f"{c}") for k, c in enumerate(self._choices)
        ]
        super().__init__(
            *args,
            choices=django_choices,
            default=self.choices_to_int(self._default),
            **kwargs,
        )

    def choices_to_int(self, choices: Union[int, Iterable[Any]]) -> int:
        """Converts a set into the corresponding integer"""
        if isinstance(choices, int):
            return choices
        return sum(
            (1 << k) for k, c in enumerate(self._choices) if c in choices
        )

    def int_to_choices(self, n: int) -> Iterable[Any]:
        """Convert an integer into the corresponding set"""
        return set(c for k, c in enumerate(self._choices) if n & (1 << k))

    def deconstruct(self) -> Any:
        """ """
        name, path, args, kwargs = super().deconstruct()
        kwargs["choices"] = self._choices
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
            "form_class": None,
            "choices_form_class": TypedMultipleChoiceField,
            "coerce": str,
            "widget": MultiCheckbox,
            "required": False,
        }
        kwargs.update(defaults)
        return super().formfield(**kwargs)

    def validate(self, value: set, model_instance: models.Model) -> None:
        if not value.issubset(self._choices):
            raise ValidationError(
                _(f"Value {value} is not a subset of {self._choices}")
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


DebugSetField = hook_class(SetField)
