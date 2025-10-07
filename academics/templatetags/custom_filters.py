# academics/templatetags/custom_filters.py

from django import template
from academics.models import Mark

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply two numbers."""
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0

@register.filter
def get_mark(marks, student_id):
    """
    Return the Mark object for a specific student.
    Handles both queryset and dict (student_id -> Mark object).
    """
    try:
        # If marks is a queryset
        if hasattr(marks, 'filter'):
            return marks.filter(student__id=student_id).first()
        # If marks is a dict
        return marks.get(student_id)
    except (Mark.DoesNotExist, AttributeError):
        return None

@register.filter
def get_sequence(mark, seq_number):
    """
    Get the numeric value of a sequence from a Mark object.
    seq_number = 1,2,3...
    """
    if not mark:
        return ''
    return getattr(mark, f'sequence{seq_number}', '')

@register.filter
def get_competence(mark, seq_number):
    """
    Get the competence string for a given sequence from a Mark object.
    seq_number = 1,2,3...
    """
    if not mark:
        return ''
    return getattr(mark, f'competence{seq_number}', '')
