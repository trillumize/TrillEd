from .models import School

def school_context(request):
    # Fetch the first school (or you can handle multi-school setups later)
    school = School.objects.first()
    return {"school": school}
