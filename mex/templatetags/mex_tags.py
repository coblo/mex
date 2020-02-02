from django import template
from mex.utils import render_json


register = template.Library()


@register.filter(name="render_json")
def _render_json(value):
    """Removes all values of arg from the given string"""
    return render_json(value)
