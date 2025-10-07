# academics/utils.py
from django.db import transaction
from .models import ClassRoom, Student, Mark
import logging

logger = logging.getLogger(__name__)

def compute_weighted_avg_for_year(student, year):
    marks = Mark.objects.filter(student=student, year=year).select_related('subject')
    total_score = 0.0
    total_coef = 0.0
    for m in marks:
        if m.term_average is None:
            continue
        coef = getattr(m.subject, 'coefficient', 1.0) or 1.0
        total_score += (m.term_average or 0) * coef
        total_coef += coef
    if total_coef:
        return total_score / total_coef
    return None

@transaction.atomic
def promote_students_for_year(year, pass_mark=10.0):
    """
    Promote students to their classroom.next_class if average >= pass_mark.
    Returns list of dicts with results for logging or display.
    """
    results = []
    for classroom in ClassRoom.objects.all():
        next_cls = classroom.next_class
        for student in Student.objects.filter(classroom=classroom):
            avg = compute_weighted_avg_for_year(student, year)
            if avg is None:
                # No marks → keep as repeater or mark for manual review
                student.repeater = True
                student.save()
                results.append({"student_id": student.id, "action": "no_marks", "avg": None})
                continue

            if avg >= pass_mark and next_cls:
                student.classroom = next_cls
                student.repeater = False
                student.save()
                results.append({"student_id": student.id, "action": "promoted", "avg": avg})
            else:
                student.repeater = True
                student.save()
                results.append({"student_id": student.id, "action": "repeat", "avg": avg})

    logger.info(f"Promotion run for year {year} complete, processed {len(results)} students")
    return results
