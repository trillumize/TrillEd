from django.contrib import admin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse, path
import pandas as pd
import io
import zipfile
from django.http import HttpResponse

from .models import ClassRoom, Subject, TeacherAssignment, Student, TermConfig, Mark
from .forms import StudentUploadForm

# ----------------------------
# ClassRoomAdmin - Upload Students + Generate Reports
# ----------------------------from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponse
from collections import defaultdict
import pandas as pd
import io, zipfile, csv

from .models import ClassRoom, Student, Mark, Subject
from .forms import StudentUploadForm

# admin.py
import datetime
from django.urls import reverse
from django.utils.html import format_html
from django.contrib import admin
from .models import ClassRoom



from django.contrib import admin
from .models import School

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name_en", "name_fr", "registration_number")

    def has_module_permission(self, request):
        from accounts.utils import user_is_global_admin
        return user_is_global_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)

@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'upload_students_link',
        'generate_class_reports_link',
        'marks_overview_link',
        'leaderboard_link',   # ✅ added column
    )

    # ----------------------------
    # Leaderboards Link
    # ----------------------------
    def leaderboard_link(self, obj):
        # ✅ Use current year dynamically
        current_year = datetime.date.today().year  

        try:
            first_term_url = reverse('academics:class_leaderboard', args=[obj.id, current_year, 'first'])
            second_term_url = reverse('academics:class_leaderboard', args=[obj.id, current_year, 'second'])
            third_term_url = reverse('academics:class_leaderboard', args=[obj.id, current_year, 'third'])
        except Exception:
            # fallback if reverse fails (e.g., no URL name yet)
            return "⚠️ Leaderboard URL not found"

        return format_html(
            '<a class="button" href="{}">1st Term</a> '
            '<a class="button" href="{}">2nd Term</a> '
            '<a class="button" href="{}">3rd Term</a>',
            first_term_url, second_term_url, third_term_url
        )

    leaderboard_link.short_description = "Leaderboards"

    
    # ----------------------------
    # Upload Students
    # ----------------------------
    def upload_students_link(self, obj):
        return format_html(
            '<a class="button" href="{}">Upload Students</a>',
            reverse('admin:academics_classroom_upload_students', args=[obj.id])
        )
    upload_students_link.short_description = 'Upload Students'

    def generate_class_reports_link(self, obj):
        return format_html(
            '<a class="button" href="{}">Generate Class Reports</a>',
            reverse('admin:academics_classroom_generate_reports', args=[obj.id])
        )
    generate_class_reports_link.short_description = 'Generate Reports'

    def marks_overview_link(self, obj):
        return format_html(
            '<a class="button" href="{}">View Marks</a>',
            reverse('admin:academics_classroom_marks_overview', args=[obj.id])
        )
    marks_overview_link.short_description = 'Marks Overview'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:classroom_id>/upload-students/',
                self.admin_site.admin_view(self.upload_students),
                name='academics_classroom_upload_students'
            ),
            path(
                '<int:classroom_id>/generate-reports/',
                self.admin_site.admin_view(self.generate_class_reports_view),
                name='academics_classroom_generate_reports'
            ),
            path(
                '<int:classroom_id>/marks-overview/',
                self.admin_site.admin_view(self.marks_overview),
                name='academics_classroom_marks_overview'
            ),
        ]
        return custom_urls + urls

    def upload_students(self, request, classroom_id):
        classroom = self.get_object(request, classroom_id)
        if request.method == "POST":
            form = StudentUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file = form.cleaned_data['file']
                try:
                    if file.name.endswith('.csv'):
                        df = pd.read_csv(file)
                    else:
                        df = pd.read_excel(file)
                except Exception as e:
                    self.message_user(request, f"Error reading file: {e}", level=messages.ERROR)
                    return redirect(request.path)

                required_cols = ['first_name', 'last_name']
                if not all(col in df.columns for col in required_cols):
                    self.message_user(
                        request,
                        "File must contain columns: first_name, last_name",
                        level=messages.ERROR
                    )
                    return redirect(request.path)

                for _, row in df.iterrows():
                    Student.objects.get_or_create(
                        first_name=row['first_name'].strip(),
                        last_name=row['last_name'].strip(),
                        classroom=classroom
                    )
                self.message_user(request, "Students uploaded successfully!", level=messages.SUCCESS)
                return redirect(f"../../{classroom_id}/change/")
        else:
            form = StudentUploadForm()

        return render(
            request,
            "admin/upload_students_form.html",
            {"form": form, "classroom": classroom}
        )

    def generate_class_reports_view(self, request, classroom_id):
        classroom = self.get_object(request, classroom_id)
        students = Student.objects.filter(classroom=classroom)
        from .views import generate_report_card

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for student in students:
                response = generate_report_card(request, student.id, 2025, 'first')
                zip_file.writestr(
                    f"{student.first_name}_{student.last_name}_report.pdf",
                    response.content
                )

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={classroom.name}_reports.zip'
        return response

    # ----------------------------
    # Marks Overview (NEW)
    # ----------------------------
    def marks_overview(self, request, classroom_id):
        classroom = self.get_object(request, classroom_id)

        # query params
        mode = request.GET.get('mode', 'student')  # 'student' or 'subject'
        subject_id = request.GET.get('subject')
        year = request.GET.get('year')
        term = request.GET.get('term')
        sequence_filter = request.GET.get('sequence')
        export_csv = request.GET.get('export') == 'csv'

        students = Student.objects.filter(classroom=classroom).order_by('last_name', 'first_name')

        marks_qs = Mark.objects.filter(student__classroom=classroom).select_related('student', 'subject')
        if subject_id:
            marks_qs = marks_qs.filter(subject_id=subject_id)
        if year:
            marks_qs = marks_qs.filter(year=year)
        if term:
            marks_qs = marks_qs.filter(term=term)

        marks_by_student = defaultdict(list)
        for m in marks_qs:
            marks_by_student[m.student_id].append(m)

        data = []

        if mode == 'subject':
            for st in students:
                for m in marks_by_student.get(st.id, []):
                    row = {
                        'student': f"{st.last_name} {st.first_name}",
                        'subject': m.subject.name if m.subject else '',
                        'seq1': m.sequence1 or '',
                        'seq2': m.sequence2 or '',
                        'seq3': m.sequence3 or '',
                        'seq4': m.sequence4 or '',
                        'seq5': m.sequence5 or '',
                        'seq6': m.sequence6 or '',
                    }
                    if sequence_filter and not row.get(f'seq{sequence_filter}'):
                        continue
                    data.append(row)
        else:
            for st in students:
                sums = [0.0] * 7
                counts = [0] * 7
                for m in marks_by_student.get(st.id, []):
                    for i in range(1, 7):
                        val = getattr(m, f'sequence{i}', None)
                        if val not in (None, ''):
                            try:
                                v = float(val)
                            except Exception:
                                v = None
                            if v is not None:
                                sums[i] += v
                                counts[i] += 1
                row = {'student': f"{st.last_name} {st.first_name}"}
                for i in range(1, 7):
                    row[f'seq{i}'] = round(sums[i] / counts[i], 2) if counts[i] else ''
                if sequence_filter and not row.get(f'seq{sequence_filter}'):
                    continue
                data.append(row)

        subjects = Subject.objects.filter(mark__student__classroom=classroom).distinct()
        years = Mark.objects.filter(student__classroom=classroom).values_list('year', flat=True).distinct()
        terms = Mark.objects.filter(student__classroom=classroom).values_list('term', flat=True).distinct()

        # CSV export
        if export_csv:
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            headers = ['Student']
            if mode == 'subject':
                headers.append('Subject')
            headers += [f"Sequence {i}" for i in range(1, 6 + 1)]
            writer.writerow(headers)
            for row in data:
                out = [row['student']]
                if mode == 'subject':
                    out.append(row.get('subject', ''))
                out += [row.get(f'seq{i}', '') for i in range(1, 7)]
                writer.writerow(out)
            resp = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
            resp['Content-Disposition'] = f'attachment; filename="{classroom.name}_marks_overview.csv"'
            return resp

        return render(
            request,
            "admin/marks_overview.html",
            {
                "classroom": classroom,
                "data": data,
                "mode": mode,
                "subjects": subjects,
                "years": sorted(list(set(years))),
                "terms": sorted(list(set(terms))),
                "selected_subject": int(subject_id) if subject_id else None,
                "selected_year": year,
                "selected_term": term,
                "sequence_filter": sequence_filter,
            }
        )

   

# ----------------------------
# SubjectAdmin
# ----------------------------
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'coefficient')

# ----------------------------
# TeacherAssignmentAdmin
# ----------------------------

# ----------------------------
# TermConfigAdmin
# ----------------------------
@admin.register(TermConfig)
class TermConfigAdmin(admin.ModelAdmin):
    list_display = ('year', 'term', 'is_open')
    list_filter = ('year', 'term')

# ----------------------------
# MarkAdmin
# ----------------------------
#@admin.register(Mark)
#class MarkAdmin(admin.ModelAdmin):
 #   list_display = (
  #      'student', 'subject', 'year', 'term',
   #     'sequence_display1', 'sequence_display2',
    #    'sequence_display3', 'sequence_display4',
     #   'sequence_display5', 'sequence_display6',
      #  'term_average', 'teacher', 'locked'
    #)
    #list_filter = ('year', 'term', 'subject', 'student__classroom')
    #search_fields = ('student__first_name', 'student__last_name', 'subject__name')

    # --------------------------
    # Prevent editing
    # --------------------------
    #def has_add_permission(self, request):
     #   return False   # prevent adding

    #def has_change_permission(self, request, obj=None):
     #   return False   # prevent editing

    #def has_delete_permission(self, request, obj=None):
     #   return False   # prevent deletion

    # --------------------------
    # Sequence display columns
    # --------------------------
    #def sequence_display1(self, obj):
     #   return obj.sequence1 if obj.term == 'first' else ''
    #sequence_display1.short_description = "Sequence 1"

    #def sequence_display2(self, obj):
     #   return obj.sequence2 if obj.term == 'first' else ''
    #sequence_display2.short_description = "Sequence 2"

    #def sequence_display3(self, obj):
     #   return obj.sequence3 if obj.term == 'second' else ''
    #sequence_display3.short_description = "Sequence 3"

    #def sequence_display4(self, obj):
     #   return obj.sequence4 if obj.term == 'second' else ''
    #sequence_display4.short_description = "Sequence 4"

    #def sequence_display5(self, obj):
     #   return obj.sequence5 if obj.term == 'third' else ''
    #sequence_display5.short_description = "Sequence 5"

    #def sequence_display6(self, obj):
     #   return obj.sequence6 if obj.term == 'third' else ''
    #sequence_display6.short_description = "Sequence 6"

# ----------------------------
# StudentAdmin
# ----------------------------
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'get_classroom', 'generate_report_link', 'progress_link')
    list_filter = ('classroom',)
    search_fields = ('first_name', 'last_name', 'admission_no', 'parent_contact', 'parent_name')

    def get_classroom(self, obj):
        return obj.classroom.name
    get_classroom.short_description = 'Class'

    def generate_report_link(self, obj):
        url = reverse('academics:generate_report_card', args=[obj.id, 2025, 'first'])
        return format_html('<a class="button" href="{}">Generate Report</a>', url)
    generate_report_link.short_description = 'Report Card'


    def progress_link(self, obj):
        url = reverse('academics:student_progress_view', args=[obj.id])
        return format_html('<a class="button" href="{}">Progress</a>', url)
    progress_link.short_description = 'Progress'


def marks_overview(self, request, classroom_id):
    classroom = self.get_object(request, classroom_id)
    # basic query params
    mode = request.GET.get('mode', 'student')  # 'student' or 'subject'
    subject_id = request.GET.get('subject')
    year = request.GET.get('year')
    term = request.GET.get('term')
    sequence_filter = request.GET.get('sequence')  # '1'..'6' or None
    export_csv = request.GET.get('export') == 'csv'

    # students in the classroom
    students = Student.objects.filter(classroom=classroom).order_by('last_name', 'first_name')

    # base marks queryset limited to this classroom
    marks_qs = Mark.objects.filter(student__classroom=classroom)
    if subject_id:
        marks_qs = marks_qs.filter(subject_id=subject_id)
    if year:
        marks_qs = marks_qs.filter(year=year)
    if term:
        marks_qs = marks_qs.filter(term=term)
    marks_qs = marks_qs.select_related('student', 'subject')

    # group marks by student for fast lookup
    marks_by_student = defaultdict(list)
    for m in marks_qs:
        marks_by_student[m.student_id].append(m)

    data = []  # rows that will be rendered or exported

    if mode == 'subject':
        # one row per (student, subject)
        for st in students:
            for m in marks_by_student.get(st.id, []):
                row = {
                    'student_id': st.id,
                    'student': f"{st.last_name} {st.first_name}",
                    'subject': m.subject.name if m.subject else '',
                    'seq1': m.sequence1 if getattr(m, 'sequence1', None) not in (None, '') else '',
                    'seq2': m.sequence2 if getattr(m, 'sequence2', None) not in (None, '') else '',
                    'seq3': m.sequence3 if getattr(m, 'sequence3', None) not in (None, '') else '',
                    'seq4': m.sequence4 if getattr(m, 'sequence4', None) not in (None, '') else '',
                    'seq5': m.sequence5 if getattr(m, 'sequence5', None) not in (None, '') else '',
                    'seq6': m.sequence6 if getattr(m, 'sequence6', None) not in (None, '') else '',
                }
                # apply sequence filter if requested
                if sequence_filter and not row.get(f'seq{sequence_filter}'):
                    continue
                data.append(row)
    else:
        # student mode — average across subjects for each sequence
        for st in students:
            sums = [0.0] * 7   # index 1..6
            counts = [0] * 7
            for m in marks_by_student.get(st.id, []):
                for i in range(1, 7):
                    val = getattr(m, f'sequence{i}', None)
                    if val not in (None, ''):
                        try:
                            v = float(val)
                        except Exception:
                            v = None
                        if v is not None:
                            sums[i] += v
                            counts[i] += 1
            row = {
                'student_id': st.id,
                'student': f"{st.last_name} {st.first_name}",
            }
            for i in range(1, 7):
                if counts[i]:
                    row[f'seq{i}'] = round(sums[i] / counts[i], 2)
                else:
                    row[f'seq{i}'] = ''
            if sequence_filter and not row.get(f'seq{sequence_filter}'):
                continue
            data.append(row)

    # lists for the filter dropdowns in the template
    subjects = Subject.objects.filter(mark__student__classroom=classroom).distinct()
    years = Mark.objects.filter(student__classroom=classroom).values_list('year', flat=True).distinct()
    terms = Mark.objects.filter(student__classroom=classroom).values_list('term', flat=True).distinct()

    # CSV export
    if export_csv:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        headers = ['Student']
        if mode == 'subject':
            headers.append('Subject')
        headers += [f"Sequence {i}" for i in range(1, 7)]
        writer.writerow(headers)
        for row in data:
            out = [row['student']]
            if mode == 'subject':
                out.append(row.get('subject', ''))
            out += [row.get(f'seq{i}', '') for i in range(1, 7)]
            writer.writerow(out)
        resp = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
        resp['Content-Disposition'] = f'attachment; filename="{classroom.name}_marks_overview.csv"'
        return resp

    context = {
        'classroom': classroom,
        'data': data,
        'mode': mode,
        'subjects': subjects,
        'years': sorted(list(set(years))),
        'terms': sorted(list(set(terms))),
        'selected_subject': int(subject_id) if subject_id else None,
        'selected_year': year,
        'selected_term': term,
        'sequence_filter': sequence_filter,
    }
    return render(request, "admin/marks_overview.html", context)




from .models import Competency, DisciplineRecord

# ----------------------------
# CompetencyAdmin
# ----------------------------
@admin.register(Competency)
class CompetencyAdmin(admin.ModelAdmin):
    list_display = ('subject', 'description')
    list_filter = ('subject',)
    search_fields = ('description',)

# ----------------------------
# DisciplineRecordAdmin
# ----------------------------
# academics/admin.py
from django.contrib import admin
from .models import DisciplineRecord
from .notifications import send_discipline_report


#@admin.register(DisciplineRecord)
#class DisciplineRecordAdmin(admin.ModelAdmin):
    #list_display = (
        #"student", "year", "term",
       # "unjustified_absences", "justified_absences",
      #  "lateness", "punishment_hours",
     #   "sent_to_parent",   # ✅ Show if report was sent
    #)
    #list_filter = ("year", "term", "student__classroom")
    #search_fields = ("student__first_name", "student__last_name")

    #actions = ["send_to_parents"]

    # ✅ Custom admin action
    #def send_to_parents(self, request, queryset):
        #sent = 0
        #skipped = 0
        #for record in queryset:
            #if not record.sent_to_parent:  # avoid duplicates
           #     send_discipline_report(record)
          #      sent += 1
         #   else:
        #        skipped += 1

       # self.message_user(
      #      request,
     #       f"✅ {sent} report(s) sent. ⏭️ {skipped} skipped (already sent)."
    #    )

   # send_to_parents.short_description = "📤 Send discipline reports to parents"
from django.contrib import admin
from django.utils.html import format_html
from .models import DisciplineRecord
from .notifications import build_discipline_message
import urllib.parse

@admin.register(DisciplineRecord)
class DisciplineRecordAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'year', 'term',
        'unjustified_absences', 'justified_absences',
        'lateness', 'punishment_hours',
        'whatsapp_link',  # ✅ Added WhatsApp link
    )
    list_filter = ('year', 'term', 'student__classroom')
    search_fields = ('student__first_name', 'student__last_name')

    def whatsapp_link(self, obj):
        student = obj.student
        phone = student.parent_contact
        if not phone:
            return "No contact"

        # Remove non-digit characters
        phone = ''.join(filter(str.isdigit, phone))

        # Ensure it has Cameroon country code
        if not phone.startswith("237"):
            phone = "237" + phone[-9:]  # last 9 digits of local number

        # Build message
        message = build_discipline_message(student, obj)

        # URL-encode message
        encoded_message = urllib.parse.quote(message)

        # WhatsApp link
        url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_message}"
        return format_html('<a href="{}" target="_blank">Send WhatsApp</a>', url)

    whatsapp_link.short_description = "WhatsApp"






# academics/admin.py  (inside your SchoolAdmin)
from django import forms
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model

class CreateSchoolAdminForm(forms.Form):
    username = forms.CharField()
    email = forms.EmailField(required=False)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)

def get_urls(self):
    urls = super().get_urls()
    custom = [
        path('<int:school_id>/create-school-admin/', self.admin_site.admin_view(self.create_school_admin), name='academics_school_create_school_admin'),
    ]
    return custom + urls

def create_school_admin(self, request, school_id):
    school = self.get_object(request, school_id)
    if request.method == "POST":
        form = CreateSchoolAdminForm(request.POST)
        if form.is_valid():
            User = get_user_model()
            u = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data.get('first_name', ''),
                last_name=form.cleaned_data.get('last_name', ''),
                password=form.cleaned_data['password'],
            )
            # flags: staff but NOT superuser
            u.is_staff = True
            # your user model or profile field:
            if hasattr(u, 'is_school_admin'):
                u.is_school_admin = True
                u.school = school
            else:
                # if using profile
                u.profile.is_school_admin = True
                u.profile.school = school
                u.profile.save()
            u.save()
            messages.success(request, "School admin created")
            return redirect(reverse("admin:academics_school_change", args=[school_id]))
    else:
        form = CreateSchoolAdminForm()
    return render(request, "admin/create_school_admin.html", {"form": form, "school": school})













from django.contrib import admin
from .models import Teacher, TeacherAssignment, ClassRoom, Subject, Student

# -------------------
# Teacher admin
# -------------------
from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Teacher

# ----------------------------
# Custom form for TeacherAdmin
# ----------------------------

# ----------------------------
# TeacherAdmin
# ----------------------------
# academics/admin.py


# academics/admin.py

from django.contrib import admin
from django import forms
from django.db import connection
from .models import Teacher, TeacherAssignment

class TeacherAdminForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Set initial password for this teacher"
    )
    
    class Meta:
        model = Teacher
        exclude = ('user',)
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if len(password) < 6:
            raise forms.ValidationError("Password must be at least 6 characters")
        return password


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    form = TeacherAdminForm
    list_display = ("first_name", "last_name", "email", "employee_id", "username_display")
    search_fields = ("first_name", "last_name", "email", "employee_id")
    
    def username_display(self, obj):
        if obj.user:
            return obj.user.username
        return "-"
    username_display.short_description = "Username"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only when creating new teacher
            password = form.cleaned_data.get('password')
            
            # ✅ Import the TENANT user model (not GlobalSuperAdmin)
            from accounts.models import User  # This is the tenant User model
            
            # Create username from name
            username = f"{obj.first_name.lower()}.{obj.last_name.lower()}"
            
            # Check if username exists, add number if needed
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            # ✅ Create tenant user with role field
            user = User.objects.create_user(
                username=username,
                first_name=obj.first_name,
                last_name=obj.last_name,
                email=obj.email,
                password=password,
                role="teacher"  # ✅ Now this works because accounts.User has role field
            )
            
            obj.user = user
        
        super().save_model(request, obj, form, change)
















# -------------------
# TeacherAssignment admin
# -------------------
@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ("teacher", "classroom", "subject")
    list_filter = ("classroom", "subject", "teacher")
    search_fields = ("teacher__first_name", "teacher__last_name", "classroom__name", "subject__name")











# ============================================
# Hide Recent Actions with CSS
# ============================================
from django.shortcuts import render
from django.db import connection

_original_index = admin.site.index

def custom_index(request, extra_context=None):
    response = _original_index(request, extra_context)
    
    # Inject CSS to hide recent actions in tenant schemas
    if connection.schema_name != 'public':
        # Render the response first
        response.render()
        
        # Then modify the content
        hide_css = b'<style>#recent-actions-module { display: none !important; }</style></head>'
        response.content = response.content.replace(b'</head>', hide_css)
    
    return response

admin.site.index = custom_index








from .models import FeeStructure, FeePayment, StudentFeeStatus

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'fee_type', 'amount', 'classroom', 'academic_year', 'term', 'is_mandatory', 'is_active')
    list_filter = ('academic_year', 'term', 'fee_type', 'is_active', 'classroom')
    search_fields = ('name',)
    list_editable = ('is_active',)

@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_structure', 'amount_paid', 'payment_date', 'payment_method', 'reference_number')
    list_filter = ('payment_date', 'payment_method', 'fee_structure')
    search_fields = ('student__first_name', 'student__last_name', 'reference_number')
    readonly_fields = ('recorded_by', 'created_at')
    date_hierarchy = 'payment_date'
    
    def save_model(self, request, obj, form, change):
        if not obj.recorded_by:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)
        
        # Update student fee status
        status, created = StudentFeeStatus.objects.get_or_create(
            student=obj.student,
            academic_year=obj.fee_structure.academic_year,
            term=obj.fee_structure.term or 'first'
        )
        
        # Recalculate totals
        total_paid = FeePayment.objects.filter(
            student=obj.student,
            fee_structure__academic_year=status.academic_year,
            fee_structure__term=status.term
        ).aggregate(total=models.Sum('amount_paid'))['total'] or 0
        
        status.total_paid = total_paid
        status.update_balance()

@admin.register(StudentFeeStatus)
class StudentFeeStatusAdmin(admin.ModelAdmin):
    list_display = ('student', 'academic_year', 'term', 'total_fees', 'total_paid', 'balance', 'payment_status')
    list_filter = ('academic_year', 'term', 'student__classroom')
    search_fields = ('student__first_name', 'student__last_name')
    readonly_fields = ('balance', 'last_updated')
    
    def payment_status(self, obj):
        if obj.balance <= 0:
            return format_html('<span style="color: green;">Paid</span>')
        elif obj.total_paid > 0:
            return format_html('<span style="color: orange;">Partial</span>')
        else:
            return format_html('<span style="color: red;">Unpaid</span>')
    payment_status.short_description = 'Status'
    
    actions = ['send_fee_reminder']
    
    def send_fee_reminder(self, request, queryset):
        """Send fee reminders to parents"""
        count = 0
        for status in queryset:
            if status.balance > 0:
                # You can implement WhatsApp/Email notification here
                count += 1
        self.message_user(request, f"Sent {count} fee reminders")
    send_fee_reminder.short_description = "Send fee reminders to parents"
