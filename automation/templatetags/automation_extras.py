from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Usage in template: {{ some_dict|get_item:key }}
    Returns dictionary.get(key, "") safely, used to look up the
    trigger description text for a given trigger value.
    """

    if not dictionary:
        return ""

    return dictionary.get(key, "")
