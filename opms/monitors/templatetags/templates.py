from django import template
from datetime import timedelta

register = template.Library()

@register.filter(name='percentage')
def percentage(fraction, population):
    if not population:
        return 'n/a %'
    try:
        return "%.2f%%" % ((float(fraction) / float(population)) * 100)
    except TypeError:
        try:
            return "%.2f%%" % ((float(fraction.total_seconds()) / float(population.total_seconds())) * 100) #cope with timedeltas
        except:
            return 'TypeError'
    except ValueError:
        return ''

@register.filter(name='chop')
def chop(text, length=10):
    """Ensure that a string text is shorter than length, adding ... if appropriate."""
    if len(text) > length:
        return text[:length] + '...'
    else:
        return text

@register.filter(name='mean')
def chop(total, n):
    """Finds the mean from a total of values and the number of values."""
    if n and total:
        try:
            return round((float(total) / float(n)),2)
        except TypeError:
            return timedelta(seconds=int(float(total.total_seconds()) / float(n)))
    else:
        return 0