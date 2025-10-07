from django.conf import settings

def user_is_global_admin(user):
    if user.is_superuser:
        return True
    if getattr(user, "is_global_admin", False):
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and getattr(profile, "is_global_admin", False))

def user_school(user):
    # return None for global admin, else School instance or None
    if user_is_global_admin(user):
        return None
    if getattr(user, "school", None):
        return user.school
    profile = getattr(user, "profile", None)
    return getattr(profile, "school", None)
