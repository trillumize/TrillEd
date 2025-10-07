from django.urls import path
from . import views
from .views import class_leaderboard

app_name = 'academics'

urlpatterns = [
    # ---------- Teacher Pages ----------
    path('', views.index, name='index'),  # Teacher dashboard redirect
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/assignments/', views.teacher_assignments, name='teacher_assignments'),
    path('class/<int:class_id>/students/', views.class_students, name='class_students'),
    path('marks/bulk_save/', views.bulk_save_marks, name='bulk_save_marks'),
    path('marks/', views.get_marks, name='get_marks'),
    path('term/open_close/', views.open_close_term, name='open_close_term'),
    path('enter-marks/<int:assignment_id>/', views.enter_marks, name='enter_marks'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path("report/<int:student_id>/<int:year>/<str:term>/", views.preview_report_card, name="preview_report"),

    path("report-pdf/<int:student_id>/<str:term>/", views.generate_report_card, name="report_pdf"),
    path("select-students/<int:assignment_id>/", views.select_students, name="select_students"),
    path("student/<int:student_id>/progress/", views.student_progress_view, name="student_progress_view"),
    path("student/<int:student_id>/progress-data/", views.student_progress_data, name="student_progress_data"),


    path('classroom/<int:classroom_id>/leaderboard/<int:year>/<str:term>/', views.class_leaderboard, name='class_leaderboard'),
    path('student/<int:student_id>/progress/data/', views.student_progress_data, name='student_progress_data'),
    path('student/<int:student_id>/progress/', views.student_progress_view, name='student_progress'),
    path('students/search/', views.search_students, name='search_students'),
    path(
        'academics/leaderboard/<int:classroom_id>/<int:year>/<str:term>/',
        class_leaderboard,
        name='class_leaderboard'
    ),

    # ---------- Super Admin Pages ----------
    # Dashboard to view all students and generate report cards
    path(
        'superadmin/report-dashboard/<int:year>/<str:term>/',
        views.superadmin_report_dashboard,
        name='superadmin_report_dashboard'
    ),

    # Generate single student PDF report card
    path(
        'report-card/<int:student_id>/<int:year>/<str:term>/',
        views.generate_report_card,
        name='generate_report_card'
    ),
]
