"""
Custom Django form fields for the Data Space Backend application.

This module provides specialized form field classes that extend Django's
built-in form fields to handle specific data types and validation needs.

The primary field in this module is JsonField, which enables editing of
JSON data in Django admin forms through a textarea widget with automatic
serialization/deserialization.
"""

import json
from typing import Any

from django.forms import fields, widgets


class JsonField(fields.CharField):
    """
    A form field for editing JSON data in Django admin and forms.

    This field extends CharField to provide seamless JSON handling:
    - Displays JSON data as formatted text in a textarea widget
    - Automatically parses user input from JSON string to Python dict
    - Automatically serializes Python dict to JSON string for display

    Use Cases:
        - Editing JSONField model fields in Django admin
        - Forms that need to accept structured JSON input
        - Configuration forms with complex nested data

    Attributes:
        widget: Uses Textarea widget for multi-line JSON editing.
        rows: Number of rows for the textarea (default: 5).

    Example:
        class MyForm(forms.Form):
            config = JsonField(rows=10, required=False)

        # In admin.py:
        class MyModelAdmin(admin.ModelAdmin):
            formfield_overrides = {
                models.JSONField: {'form_class': JsonField},
            }
    """

    # Use Textarea widget instead of default TextInput for better JSON editing
    widget = widgets.Textarea

    def __init__(self, rows: int = 5, **kwargs: Any) -> None:
        """
        Initialize the JsonField with configurable textarea rows.

        Args:
            rows: Number of rows for the textarea widget. Larger values
                 provide more space for complex JSON structures.
                 Default is 5 rows.
            **kwargs: Additional arguments passed to CharField.__init__,
                     such as required, label, help_text, etc.
        """
        self.rows = rows
        super().__init__(**kwargs)

    def widget_attrs(self, widget: widgets.Widget) -> dict[str, Any]:
        """
        Return HTML attributes for the textarea widget.

        This method extends the parent's widget_attrs to include the
        custom rows setting, controlling the textarea's height.

        Args:
            widget: The widget instance that will render this field.

        Returns:
            Dictionary of HTML attributes including 'rows' for textarea height.
        """
        # Get base attributes from parent CharField
        attrs = super().widget_attrs(widget)
        # Add rows attribute to control textarea height
        attrs["rows"] = self.rows
        return attrs

    def to_python(self, value: Any) -> dict[str, Any]:  # type: ignore[override]
        """
        Convert the form input (JSON string) to a Python dictionary.

        This method is called during form validation to convert the raw
        string input from the textarea into a Python data structure that
        can be stored in a JSONField model field.

        Args:
            value: The raw string value from the form input, expected to
                  be valid JSON, or an empty/None value.

        Returns:
            A Python dictionary parsed from the JSON string.
            Returns an empty dict {} if the input is empty or falsy.

        Raises:
            json.JSONDecodeError: If the input is not valid JSON.
                This will be caught by Django's form validation and
                displayed as a form error to the user.

        Note:
            The return type is dict[str, Any] but json.loads can return
            other types (list, str, int, etc.). Callers should be aware
            that the actual return type depends on the JSON input.
        """
        if value:
            # Parse JSON string to Python object
            return json.loads(value)  # type: ignore[no-any-return]
        else:
            # Return empty dict for empty/None input
            return {}

    def prepare_value(self, value: Any) -> str:
        """
        Convert a Python value to a JSON string for display in the form.

        This method is called when rendering the form to convert the
        Python data structure (from the model or initial data) into a
        JSON string that can be displayed in the textarea.

        Args:
            value: The Python value to serialize, typically a dict or list
                  from a JSONField model field.

        Returns:
            A JSON-formatted string representation of the value.

        Note:
            The output is not pretty-printed by default. For better
            readability in the admin, consider using json.dumps with
            indent parameter in a subclass.
        """
        # Serialize Python object to JSON string
        return json.dumps(value)
