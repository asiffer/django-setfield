from typing import Any, Optional

from django import forms


class MultiCheckbox(forms.CheckboxSelectMultiple):
    def format_value(self, value: Any) -> Optional[str]:
        return value
