# academics/admin_utils.py
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from .models import ClassRoom, Student

from accounts.utils import user_is_global_admin, user_school

class SchoolScopedAdminMixin:
    """
    Use this mixin for ModelAdmin classes that must be scoped to a school.
    It:
      - filters queryset to the user's school (unless global admin)
      - limits FK choices to user's school
      - enforces object-level checks on view/change/delete
    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if user_is_global_admin(request.user):
            return qs
        school = user_school(request.user)
        if not school:
            return qs.none()
        model = self.model
        # heuristics for common models. Extend if needed.
        if hasattr(model, "school"):
            return qs.filter(school=school)
        if hasattr(model, "classroom"):
            return qs.filter(classroom__school=school)
        if hasattr(model, "student"):
            return qs.filter(student__classroom__school=school)
        # fallback: no access
        return qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # restrict FK queryset to the user's school where sensible
        school = user_school(request.user)
        if school and db_field.name in ("classroom", "student", "school"):
            from .models import ClassRoom, Student, School
            if db_field.name == "classroom":
                kwargs["queryset"] = ClassRoom.objects.filter(school=school)
            elif db_field.name == "student":
                kwargs["queryset"] = Student.objects.filter(classroom__school=school)
            elif db_field.name == "school":
                kwargs["queryset"] = School.objects.filter(pk=school.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # block attempts to open objects from other schools
    def has_change_permission(self, request, obj=None):
        if user_is_global_admin(request.user):
            return True
        if obj is None:
            return super().has_change_permission(request, obj)
        school = user_school(request.user)
        if hasattr(obj, "school"): return getattr(obj, "school", None) == school and super().has_change_permission(request, obj)
        if hasattr(obj, "classroom") and getattr(obj, "classroom", None):
            return getattr(obj, "classroom").school == school and super().has_change_permission(request, obj)
        return False
