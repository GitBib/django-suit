import django
from django import template

from suit.config import get_config

register = template.Library()

if django.VERSION < (1, 9):
    simple_tag = register.assignment_tag
else:
    simple_tag = register.simple_tag


def get_form_size(fieldset):
    form_size_by_config = get_config("form_size")

    # Fallback to model admin definition
    form_size_by_model_admin = getattr(fieldset.model_admin, "suit_form_size", {})

    form_size = {}
    form_size |= form_size_by_config
    form_size |= form_size_by_model_admin

    return form_size


def get_form_class(field, fieldset, idx):
    field_class, extra_class = [], ""
    form_size = get_form_size(fieldset)

    if not form_size:
        raise Exception('"form_size" parameter must be set in Django Suit config')

    if not field_class:
        if form_size_fields := form_size.get("fields"):
            field_name = None
            if hasattr(field, "name"):
                field_name = field.name
            elif isinstance(field, dict) and "name" in field:
                # field may be a dict as well (for stacked inlines)
                field_name = field["name"]
            if field_name:
                field_class = form_size_fields.get(field_name)

    # Add widgets CSS class
    if idx == 1:
        extra_class = f" {suit_form_field_widget_class(field)}"

    # Try widgets config
    widget_class_name = get_field_widget_class_name(field)
    if not field_class and widget_class_name:
        if form_size_widgets := form_size.get("widgets"):
            field_class = form_size_widgets.get(widget_class_name)

    # Try fieldset config
    if not field_class:
        if form_size_fieldset := form_size.get("fieldsets"):
            field_class = form_size_fieldset.get(fieldset.name)

    # Fallback to default
    if not field_class:
        field_class = form_size.get("default")

    assert isinstance(field_class, (tuple, list)) and len(field_class) == 2, (
        "Django Suit form_size definition must be list or tuple containing two string items. "
        'You have: "%s" (%s)' % (field_class, field_class.__class__)
    )

    return field_class[idx] + extra_class


def get_field_widget_class_name(field):
    try:
        return field.field.widget.__class__.__name__
    except AttributeError:
        pass


@register.filter
def suit_form_label_class(field, fieldset):
    """
    Get CSS class for form-row label column
    """
    return get_form_class(field, fieldset, 0)


@register.filter
def suit_form_field_class(field, fieldset):
    """
    Get CSS class for form-row field column
    """
    return get_form_class(field, fieldset, 1)


@register.filter
def suit_form_field_widget_class(field):
    """
    Get CSS class for field by widget name, for easier styling
    """
    if widget_class_name := get_field_widget_class_name(field):
        return f"widget-{widget_class_name}"
    return ""


@simple_tag(takes_context=True)
def suit_form_conf(context, param_name, inline_admin_formset=None):
    """
    Get form config param
    """
    if inline_admin_formset:
        model_admin = inline_admin_formset.opts
    else:
        model_admin = context["adminform"].model_admin
    param_by_model_admin = getattr(model_admin, f"suit_{param_name}", None)
    if param_by_model_admin is not None:
        return param_by_model_admin
    return get_config(param_name, context["request"])


@register.filter
def suit_form_field_placeholder(field, placeholder):
    """
    Get CSS class for field by widget name, for easier styling
    """
    field.field.widget.attrs["placeholder"] = placeholder
    return field
