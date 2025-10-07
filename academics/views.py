import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from .models import TeacherAssignment, Mark, Student, TermConfig
from django.contrib.auth.decorators import login_required
from .models import SubjectEnrollment
from .models import School
from .models import Teacher


@login_required
def index(request):
    if request.user.role == 'teacher':
        return render(request, 'academics/teacher_dashboard.html')
    return render(request, 'academics/index.html')

@login_required
def teacher_assignments(request):
    teacher = request.user
    assignments = TeacherAssignment.objects.filter(teacher=teacher).select_related('classroom','subject')
    data = [{"class_id": a.classroom.id, "class_name":a.classroom.name, "subject_id": a.subject.id, "subject": a.subject.name} for a in assignments]
    return JsonResponse(data, safe=False)

@login_required
def class_students(request, class_id):
    students = Student.objects.filter(classroom_id=class_id).values('id','first_name','last_name')
    return JsonResponse(list(students), safe=False)

@login_required
def get_marks(request):
    class_id = request.GET.get('class')
    subject_id = request.GET.get('subject')
    year = int(request.GET.get('year'))
    term = request.GET.get('term')
    # fetch marks for the class and subject
    students = Student.objects.filter(classroom_id=class_id)
    marks = Mark.objects.filter(student__in=students, subject_id=subject_id, year=year, term=term).values(
        'student_id','sequence1','sequence2','term_average','locked'
    )
    return JsonResponse(list(marks), safe=False)
@require_POST
@login_required
def bulk_save_marks(request):
    data = json.loads(request.body)
    teacher = request.user

    # verify teacher assignment
    if not TeacherAssignment.objects.filter(
        teacher=teacher,
        classroom_id=data['class_id'],
        subject_id=data['subject_id']
    ).exists():
        return JsonResponse({"detail": "Not assigned to this class/subject"}, status=403)

    # check if term is open
    if not TermConfig.objects.filter(year=data['year'], term=data['term'], is_open=True).exists():
        return JsonResponse({"detail": "Term submissions are closed"}, status=400)

    term_to_sequences = {
        'first': [1, 2],
        'second': [3, 4],
        'third': [5, 6],
    }
    sequences = term_to_sequences.get(data['term'], [1, 2])

    saved = []
    for row in data['data']:
        student = get_object_or_404(Student, id=row['student_id'], classroom_id=data['class_id'])
        mark, created = Mark.objects.get_or_create(
            student=student,
            subject_id=data['subject_id'],
            year=data['year'],
            term=data['term'],
            defaults={'teacher': teacher}
        )

        if mark.locked:
            continue

        # Dynamically update the right sequences for this term
        for seq in sequences:
            val = row.get(f'sequence{seq}')
            if val is not None:
                setattr(mark, f'sequence{seq}', val)

        mark.teacher = teacher
        mark.save()

        saved.append({"student_id": student.id, "term_average": mark.term_average})

    return JsonResponse({"saved": saved})


# admin-only open/close endpoint (simple)
# add these imports at the top of academics/views.py (if not already present)
from .models import TermConfig, Mark, DisciplineRecord
from .notifications import send_discipline_report
from .utils import promote_students_for_year
import logging

logger = logging.getLogger(__name__)

# replace or update the existing open_close_term view:
@require_POST
@login_required
def open_close_term(request):
    if not request.user.is_superuser and request.user.role != 'super_admin':
        return JsonResponse({"detail":"Forbidden"}, status=403)
    payload = json.loads(request.body)
    year = payload['year']
    term = payload['term']
    open_flag = payload['is_open']
    run_promotion = payload.get('run_promotion', False)  # optional flag
    pass_mark = payload.get('pass_mark', 10.0)

    cfg, created = TermConfig.objects.get_or_create(year=year, term=term)
    cfg.is_open = open_flag
    cfg.save()

    if not open_flag:
        # lock marks for the term
        Mark.objects.filter(year=year, term=term).update(locked=True)

        # send discipline reports to parents for records not yet sent
        discipline_qs = DisciplineRecord.objects.filter(year=year, term=term, sent_to_parent=False)
        for record in discipline_qs:
            try:
                send_discipline_report(record)
            except Exception:
                logger.exception("Error sending discipline report for record id %s", getattr(record, 'id', None))

        # run promotion either if asked or if closing the final term
        if run_promotion or term == 'third':
            try:
                promote_students_for_year(year, pass_mark=pass_mark)
            except Exception:
                logger.exception("Promotion run failed for year %s", year)

    return JsonResponse({"ok": True})



from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse
from .models import Student, Mark

from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse



# academics/views.py

from django.shortcuts import render
from .models import TeacherAssignment
from django.shortcuts import render, get_object_or_404, redirect
from .models import TeacherAssignment, Student, Mark, TermConfig
from django.contrib.auth.decorators import login_required

#@login_required
#def teacher_dashboard(request):
 #   assignments = TeacherAssignment.objects.filter(teacher=request.user)
   # return render(request, "academics/teacher_dashboard.html", {"assignments": assignments})


# academics/views.py

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            if user.role == 'teacher':
                return redirect('academics:teacher_dashboard')
            elif user.role in ['global_admin', 'school_admin']:
                return redirect('admin:index')
            else:
                return redirect('academics:index')
        else:
            messages.error(request, "Invalid username or password")
    
    return render(request, "academics/login.html")


@login_required
def teacher_dashboard(request):
    if request.user.role != 'teacher':
        messages.error(request, "Access denied. Teacher access only.")
        return redirect('academics:login')
    
    teacher, created = Teacher.objects.get_or_create(
        user=request.user,
        defaults={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email
        }
    )
    
    assignments = TeacherAssignment.objects.filter(teacher=teacher)
    
    return render(request, "academics/teacher_dashboard.html", {
        "teacher": teacher,
        "assignments": assignments
    })



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import TeacherAssignment, TermConfig, Mark, Student
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import TeacherAssignment, TermConfig, Mark, Student
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import TeacherAssignment, TermConfig, Mark, Student

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import TeacherAssignment, Student, Mark, TermConfig, Competency



from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages




@login_required
def enter_marks(request, assignment_id):
    assignment = get_object_or_404(TeacherAssignment, id=assignment_id)

    # ✅ Detect if senior class (Form 4+)
    is_senior_class = False
    try:
        class_label = assignment.classroom.name.strip().lower()  # e.g. "Form 4"
        if class_label.startswith("form"):
            form_number = int(class_label.split()[1])
            if form_number >= 4:
                is_senior_class = True
    except Exception:
        pass

    # ✅ Student list logic
    if is_senior_class:
        # Only those explicitly enrolled (teacher must select)
        enrolled_students = SubjectEnrollment.objects.filter(
            teacher_assignment=assignment
        ).values_list("student_id", flat=True)
        students = Student.objects.filter(id__in=enrolled_students)
    else:
        # Junior classes: include all students in the class
        students = Student.objects.filter(classroom=assignment.classroom)

    # ✅ Term and editability
    current_term = TermConfig.objects.filter(is_open=True).last()
    editable = bool(current_term and current_term.is_open)

    # ✅ Map term → sequences
    term_to_sequences = {
        'first': [1, 2],
        'second': [3, 4],
        'third': [5, 6],
    }
    sequences = term_to_sequences.get(
        current_term.term if current_term else 'first',
        [1, 2]
    )

    # ✅ Existing marks
    marks_qs = Mark.objects.filter(
        student__classroom=assignment.classroom,
        subject=assignment.subject,
    )
    if current_term:
        marks_qs = marks_qs.filter(
            year=current_term.year,
            term=current_term.term
        )
    marks_dict = {m.student.id: m for m in marks_qs}

    # ✅ Competencies
    competences_qs = Competency.objects.filter(
        subject=assignment.subject,
        classroom=assignment.classroom,
        teacher=request.user,
        sequence__in=sequences
    )
    competences_dict = {c.sequence: c.description for c in competences_qs}

    # ✅ Handle form submission
    if request.method == "POST" and editable:
        # --- Save marks ---
        for student in students:
            mark = marks_dict.get(student.id)
            if not mark:
                mark = Mark.objects.create(
                    student=student,
                    subject=assignment.subject,
                    teacher=request.user,
                    year=current_term.year,
                    term=current_term.term
                )
                marks_dict[student.id] = mark

            for seq in sequences:
                val = request.POST.get(f"seq{seq}_{student.id}")
                if val != "" and val is not None:
                    setattr(mark, f'sequence{seq}', float(val))
            mark.teacher = request.user
            mark.save()

        # --- Save competencies ---
        for seq in sequences:
            comp_text = request.POST.get(f"comp{seq}")
            if comp_text is not None:
                comp_text = comp_text.strip()
                comp_obj, created = Competency.objects.get_or_create(
                    subject=assignment.subject,
                    classroom=assignment.classroom,
                    teacher=request.user,
                    sequence=seq,
                    defaults={'description': comp_text}
                )
                if not created:
                    comp_obj.description = comp_text
                    comp_obj.save()

        return redirect("academics:enter_marks", assignment_id=assignment.id)

    # ✅ Render page
    return render(request, "academics/teacher_marks.html", {
        "assignment": assignment,
        "students": students,
        "marks": marks_dict,
        "competences": competences_dict,
        "editable": editable,
        "sequences": sequences,
        "is_senior_class": is_senior_class,
    })








def user_logout(request):
    logout(request)
    return redirect('academics:login')  # redirect to namespaced login









@login_required
def superadmin_report_dashboard(request, year, term):
    if not request.user.is_superuser and request.user.role != 'super_admin':
        return HttpResponse('Forbidden', status=403)

    students = Student.objects.all().select_related('classroom')
    return render(request, 'academics/superadmin_report_dashboard.html', {
        "students": students,
        "year": year,
        "term": term
    })



# views.py
from django.shortcuts import render, get_object_or_404
from .models import Student, Mark


from statistics import mean
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Student, Mark, DisciplineRecord


from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from statistics import mean
from .models import Student, Mark, DisciplineRecord


@login_required
def preview_report_card(request, student_id, year, term):
    # Only allow superusers and school_admins
    if not (request.user.is_superuser or request.user.role == 'school_admin'):
        return HttpResponse('Access denied. Only school admins can view report cards.', status=403)

    # --- Fetch student and marks ---
    student = get_object_or_404(Student, id=student_id)
    marks = Mark.objects.filter(student=student, year=year, term=term).select_related('subject')

    # --- Compute total score and total coefficient ---
    total_score = sum((m.term_average or 0) * m.subject.coefficient for m in marks)
    total_coef = sum(m.subject.coefficient for m in marks if m.term_average is not None)
    term_average = total_score / total_coef if total_coef else None
    school = School.objects.first() 
    
    # --- Class statistics ---
    passed_count = sum(1 for m in marks if m.term_average and m.term_average >= 10)
    class_average = mean([m.term_average for m in marks if m.term_average is not None]) if marks else 0
    min_score = min([m.term_average for m in marks if m.term_average is not None], default=0)
    max_score = max([m.term_average for m in marks if m.term_average is not None], default=0)

    # --- Determine overall grade ---
    def get_overall_grade(avg):
        if avg is None:
            return "-"
        if avg < 5: return "F"
        if avg < 10: return "E"
        if avg < 14: return "D"
        if avg < 17: return "C"
        if avg < 20: return "B"
        return "A"

    overall_grade = get_overall_grade(term_average)

    # --- Success rate ---
    total_students = Student.objects.filter(classroom=student.classroom).count()
    success_rate = (passed_count / total_students * 100) if total_students else 0

    # --- Discipline record ---
    discipline = DisciplineRecord.objects.filter(student=student, term=term, year=year).first()

    # --- Tick logic for student performance ---
    cvwa = cwa = caa = cna = ca_tick = ""
    if overall_grade == "A":
        cvwa = "✔"
    elif overall_grade == "B":
        cwa = "✔"
    elif overall_grade == "C":
        caa = "✔"
    elif overall_grade == "D":
        ca_tick = "✔"
    else:
        cna = "✔"

    # --- Context for template ---
    context = {
        "student": student,
        "marks": marks,
        "year": year,
        "term": term,
        "total_score": round(total_score, 2),
        "term_average": round(term_average, 2) if term_average else None,
        "class_average": round(class_average, 2) if class_average else None,
        "passed_count": passed_count,
        "min_score": min_score,
        "max_score": max_score,
        "overall_grade": overall_grade,
        "success_rate": round(success_rate, 1),
        "class_master": "________",
        "cvwa": cvwa,
        "cwa": cwa,
        "caa": caa,
        "cna": cna,
        "ca_tick": ca_tick,
        "coef": total_coef,
        "discipline": discipline,
        "school": school
    }
    return render(request, "academics/report_template.html", context)



@login_required
def generate_report_card(request, student_id, year, term):
    # Only allow superusers and school_admins
    if not (request.user.is_superuser or request.user.role == 'school_admin'):
        return HttpResponse('Access denied. Only school admins can generate report cards.', status=403)

    student = get_object_or_404(Student, id=student_id)
    marks = Mark.objects.filter(student=student, year=year, term=term).select_related('subject')

    # --- Compute extra context ---
    total_score = sum((m.term_average or 0) * m.subject.coefficient for m in marks)
    total_coef = sum(m.subject.coefficient for m in marks if m.term_average is not None)
    term_average = total_score / total_coef if total_coef else None

    passed_count = sum(1 for m in marks if m.term_average and m.term_average >= 10)
    class_average = mean([m.term_average for m in marks if m.term_average is not None]) if marks else 0
    min_score = min([m.term_average for m in marks if m.term_average is not None], default=0)
    max_score = max([m.term_average for m in marks if m.term_average is not None], default=0)

    # overall grade
    def get_overall_grade(avg):
        if avg is None:
            return "-"
        if avg < 5: return "F"
        if avg < 10: return "E"
        if avg < 14: return "D"
        if avg < 17: return "C"
        if avg < 20: return "A"
    overall_grade = get_overall_grade(term_average)

    # success rate
    total_students = Student.objects.filter(classroom=student.classroom).count()
    success_rate = (passed_count / total_students * 100) if total_students else 0

    context = {
        "student": student,
        "marks": marks,
        "year": year,
        "term": term,
        "total_score": round(total_score, 2),
        "term_average": round(term_average, 2) if term_average else None,
        "class_average": round(class_average, 2) if class_average else None,
        "passed_count": passed_count,
        "min_score": min_score,
        "max_score": max_score,
        "overall_grade": overall_grade,
        "success_rate": round(success_rate, 1),
        "class_master": "________",
        "ca": "-",
    }

    html_string = render_to_string('academics/report_template.html', context)
    pdf = HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=report_{student.admission_no}_{term}_{year}.pdf'
    return response









from django.shortcuts import get_object_or_404
from .models import ClassRoom, Student, Mark
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404
from .models import ClassRoom, Student, Mark

@login_required
@user_passes_test(lambda u: u.is_superuser)
def class_leaderboard(request, classroom_id, year, term):
    classroom = get_object_or_404(ClassRoom, id=classroom_id)
    students = Student.objects.filter(classroom=classroom)

    ranking = []
    for s in students:
        marks = Mark.objects.filter(student=s, year=year, term=term).select_related('subject')
        total_score = 0.0
        total_coef = 0.0
        for m in marks:
            if m.term_average is None:
                continue
            coef = getattr(m.subject, 'coefficient', 1.0) or 1.0
            total_score += (m.term_average or 0) * coef
            total_coef += coef
        avg = (total_score / total_coef) if total_coef else 0.0
        ranking.append({
            "student": s,
            "gender": s.gender or "",
            "avg": round(avg, 2)
        })

    ranking_sorted = sorted(ranking, key=lambda x: x['avg'], reverse=True)
    for i, item in enumerate(ranking_sorted, start=1):
        item['position'] = i

    # 📊 Extra stats
    avgs = [r['avg'] for r in ranking_sorted if r['avg'] > 0]
    male_avgs = [r['avg'] for r in ranking_sorted if (r['gender'] or "").lower() == "male" and r['avg'] > 0]
    female_avgs = [r['avg'] for r in ranking_sorted if (r['gender'] or "").lower() == "female" and r['avg'] > 0]

    context = {
        "classroom": classroom,
        "ranking": ranking_sorted,
        "year": year,
        "term": term,
        "class_avg": round(sum(avgs) / len(avgs), 2) if avgs else 0,
        "male_avg": round(sum(male_avgs) / len(male_avgs), 2) if male_avgs else 0,
        "female_avg": round(sum(female_avgs) / len(female_avgs), 2) if female_avgs else 0,
        "total_students": len(ranking_sorted),
        "total_males": sum(1 for r in ranking_sorted if (r['gender'] or "").lower() == "male"),
        "total_females": sum(1 for r in ranking_sorted if (r['gender'] or "").lower() == "female"),
    }

    return render(request, "academics/class_leaderboard.html", context)




from django.http import JsonResponse

@login_required
def student_progress_data(request, student_id):
    from .models import Student, Mark
    student = get_object_or_404(Student, id=student_id)

    # distinct (year, term) pairs for which marks exist
    pairs = list(Mark.objects.filter(student=student).values_list('year', 'term').distinct())
    pairs = sorted(pairs)  # (year, term) tuples sort reasonably

    data = []
    for year, term in pairs:
        marks_qs = Mark.objects.filter(student=student, year=year, term=term).select_related('subject')
        total_score = 0.0
        total_coef = 0.0
        for m in marks_qs:
            if m.term_average is None:
                continue
            coef = getattr(m.subject, 'coefficient', 1.0) or 1.0
            total_score += (m.term_average or 0) * coef
            total_coef += coef
        avg = (total_score / total_coef) if total_coef else None
        label = f"{term.capitalize()} {year}"
        data.append({"label": label, "avg": round(avg,2) if avg is not None else None})
    return JsonResponse(data, safe=False)

@login_required
def student_progress_view(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, "academics/student_progress.html", {"student": student})



from django.db.models import Q
from django.http import JsonResponse

@login_required
def search_students(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse([], safe=False)
    qs = Student.objects.filter(
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q) |
        Q(admission_no__icontains=q) |
        Q(parent_contact__icontains=q)
    )[:50]
    results = [
        {
            "id": s.id,
            "name": f"{s.first_name} {s.last_name}",
            "admission_no": s.admission_no,
            "parent_contact": s.parent_contact,
            "classroom": s.classroom.name
        } for s in qs
    ]
    return JsonResponse(results, safe=False)


# academics/views.py
@login_required
def select_students(request, assignment_id):
    assignment = get_object_or_404(TeacherAssignment, id=assignment_id)
    all_students = Student.objects.filter(classroom=assignment.classroom)
    enrolled_students = Student.objects.filter(
        subjectenrollment__teacher_assignment=assignment
    )

    if request.method == "POST":
        selected_ids = request.POST.getlist("students")

        # remove old enrollments not selected
        SubjectEnrollment.objects.filter(teacher_assignment=assignment).exclude(
            student_id__in=selected_ids
        ).delete()

        # add newly selected enrollments
        for sid in selected_ids:
            SubjectEnrollment.objects.get_or_create(
                teacher_assignment=assignment,
                student_id=sid,
            )

        return redirect("academics:enter_marks", assignment_id=assignment.id)

    return render(request, "academics/select_students.html", {
        "assignment": assignment,
        "all_students": all_students,
        "enrolled_students": enrolled_students,
    })
