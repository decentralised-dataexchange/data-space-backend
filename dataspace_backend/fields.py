import json
from typing import Any

from django.forms import fields, widgets


class JsonField(fields.CharField):
    widget = widgets.Textarea

    def __init__(self, rows: int = 5, **kwargs: Any) -> None:
        self.rows = rows
        super().__init__(**kwargs)

    def widget_attrs(self, widget: widgets.Widget) -> dict[str, Any]:
        attrs = super().widget_attrs(widget)
        attrs["rows"] = self.rows
        return attrs

    def to_python(self, value: Any) -> dict[str, Any]:  # type: ignore[override]
        if value:
            return json.loads(value)  # type: ignore[no-any-return]
        else:
            return {}

    def prepare_value(self, value: Any) -> str:
        return json.dumps(value)
