from typing import Any

from django import forms


class TypedMultipleChoiceField(forms.TypedMultipleChoiceField):
    """Custom form field to manage sets"""

    def has_changed(self, initial: Any, data: Any) -> bool:
        if isinstance(initial, list):
            initial = set(initial)
        if isinstance(data, list):
            data = set(data)

        return initial != data

    def valid_value(self, value: str):
        print("VALUE:", value, self.choices)
        return (value, value) in self.choices
