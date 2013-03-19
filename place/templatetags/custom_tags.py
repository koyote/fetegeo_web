from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def page_list(total, limit):
    r = [i + 1 for i in range(round((total / limit) + .5))]
    return r