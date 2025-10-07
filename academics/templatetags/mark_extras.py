from django import template
from academics.models import Mark, Competency

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0

@register.filter
def get_mark(marks, student_id):
    if hasattr(marks, 'filter'):
        return marks.filter(student__id=student_id).first()
    return marks.get(student_id)

@register.filter
def get_sequence(mark, seq_number):
    if not mark:
        return ''
    return getattr(mark, f'sequence{seq_number}', '')

@register.filter
def get_competency_by_teacher(mark, seq_number):
    if not mark:
        return ''
    try:
        comp = Competency.objects.get(
            subject=mark.subject,
            classroom=mark.student.classroom,
            teacher=mark.teacher,
            sequence=seq_number
        )
        return comp.description
    except Competency.DoesNotExist:
        return ''

@register.filter
def get_item(dictionary, key):
    """Return the value for the given key in a dictionary."""
    if not dictionary:
        return ''
    return dictionary.get(key, '')


