from django.db import models
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL



# academics/models.py
from django.db import models

class School(models.Model):
    name_en = models.CharField(max_length=255, verbose_name="English name")
    name_fr = models.CharField(max_length=255, verbose_name="French name")
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name_en


class ClassRoom(models.Model):
    name = models.CharField(max_length=100)  # e.g. "Form 2A"
    next_class = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="previous_class"
    )  # link to the class into which students are promoted

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=150)
    coefficient = models.FloatField(default=1.0)
    def __str__(self): return self.name

#class TeacherAssignment(models.Model):
 #   teacher = models.ForeignKey(
  #      User,
   #     limit_choices_to={'role': 'teacher'},
    #    on_delete=models.CASCADE
    #)
    #classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    #subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    #class Meta:
     #   unique_together = ('classroom', 'subject')  # <== ✅ change here

    #def __str__(self):
     #   return f"{self.teacher} → {self.classroom} ({self.subject})"

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = settings.AUTH_USER_MODEL

# -------------------
# Teacher
# -------------------
from accounts.models import User  # tenant-specific user
# academics/models.py - Update Teacher model
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    employee_id = models.CharField(max_length=50, blank=True, null=True)

    # ❌ REMOVE the save() method - we'll handle it in admin instead

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# -------------------
# TeacherAssignment
# -------------------
class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    classroom = models.ForeignKey("ClassRoom", on_delete=models.CASCADE)
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("classroom", "subject")

    def __str__(self):
        return f"{self.teacher} → {self.classroom} ({self.subject})"


class Student(models.Model):
    admission_no = models.CharField(max_length=50, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    date_of_birth = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=150, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    photo = models.ImageField(upload_to="student_photos/", null=True, blank=True)
    parent_name = models.CharField(max_length=150, null=True, blank=True)
    parent_contact = models.CharField(max_length=50, null=True, blank=True)  # phone
    parent_email = models.EmailField(null=True, blank=True)  # <-- NEW
    repeater = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"




# models.py
class TermConfig(models.Model):
    TERM_CHOICES = (('first','First'),('second','Second'),('third','Third'))
    year = models.IntegerField()
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    is_open = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('year','term')  # Removed 'sequence'

    def __str__(self):
        return f"{self.year} - {self.term}"
class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(
        User,
        limit_choices_to={'role': 'teacher'},
        on_delete=models.SET_NULL,
        null=True
    )
    year = models.IntegerField()
    term = models.CharField(
        max_length=10,
        choices=(('first', 'First'), ('second', 'Second'), ('third', 'Third'))
    )

    # ✅ Marks only
    sequence1 = models.FloatField(null=True, blank=True)
    sequence2 = models.FloatField(null=True, blank=True)
    sequence3 = models.FloatField(null=True, blank=True)
    sequence4 = models.FloatField(null=True, blank=True)
    sequence5 = models.FloatField(null=True, blank=True)
    sequence6 = models.FloatField(null=True, blank=True)

    # ✅ Computed fields
    term_average = models.FloatField(null=True, blank=True)
    locked = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'subject', 'year', 'term')

    def save(self, *args, **kwargs):
        # Compute average for the right term
        seqs = []
        if self.term == 'first':
            seqs = [self.sequence1, self.sequence2]
        elif self.term == 'second':
            seqs = [self.sequence3, self.sequence4]
        elif self.term == 'third':
            seqs = [self.sequence5, self.sequence6]

        valid_seqs = [s for s in seqs if s is not None]
        if valid_seqs:
            self.term_average = sum(valid_seqs) / len(valid_seqs)

        super().save(*args, **kwargs)

    # ✅ Automatic remark from average
    def get_remark(self):
        if self.term_average is None:
            return "No marks yet"
        if self.term_average < 5:
            return "Very poor, needs serious work"
        elif self.term_average < 10:
            return "Weak, must improve"
        elif self.term_average < 14:
            return "Fair, keep trying"
        elif self.term_average < 17:
            return "Good work, continue"
        else:
            return "Excellent, keep it up"

    # ✅ Letter grade from average
    def get_grade(self):
        if self.term_average is None:
            return "-"
        if self.term_average < 5:
            return "F"
        if self.term_average < 10:
            return "E"
        if self.term_average < 14:
            return "D"
        if self.term_average < 17:
            return "C"
        return "A"



class Competency(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)  # <- match class name
    teacher = models.ForeignKey(User, limit_choices_to={'role': 'teacher'}, on_delete=models.CASCADE)
    sequence = models.IntegerField()  # 1,2,3...
    description = models.TextField()

    class Meta:
        unique_together = ('subject', 'classroom', 'teacher', 'sequence')

    def __str__(self):
        return f"{self.subject.name} - {self.classroom.name} - {self.teacher.username} Seq {self.sequence}"




class DisciplineRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    year = models.IntegerField()
    term = models.CharField(
        max_length=10,
        choices=(('first','First'),('second','Second'),('third','Third'))
    )

    unjustified_absences = models.IntegerField(default=0)
    justified_absences = models.IntegerField(default=0)
    lateness = models.IntegerField(default=0)
    punishment_hours = models.IntegerField(default=0)

    warning = models.BooleanField(default=False)
    reprimand = models.BooleanField(default=False)
    suspension = models.BooleanField(default=False)
    dismissal = models.BooleanField(default=False)

    remark = models.TextField(null=True, blank=True)

    # Prevent duplicate sends
    sent_to_parent = models.BooleanField(default=False)  # <-- NEW

    class Meta:
        unique_together = ('student','year','term')

    def __str__(self):
        return f"Discipline {self.student} - {self.year} {self.term}"

# models.py
from django.db import models

class Leaderboard(models.Model):
    class Meta:
        verbose_name = "Leaderboard"
        verbose_name_plural = "Leaderboards"

    def __str__(self):
        return "Leaderboard"




# academics/models.py
class SubjectEnrollment(models.Model):
    teacher_assignment = models.ForeignKey("TeacherAssignment", on_delete=models.CASCADE)
    student = models.ForeignKey("Student", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("teacher_assignment", "student")

    def __str__(self):
        return f"{self.student} in {self.teacher_assignment.subject} ({self.teacher_assignment.classroom})"






class FeeStructure(models.Model):
    """Define fee types and amounts"""
    FEE_TYPES = (
        ('tuition', 'Tuition'),
        ('registration', 'Registration'),
        ('books', 'Books'),
        ('uniform', 'Uniform'),
        ('transport', 'Transport'),
        ('exam', 'Examination'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=100)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, null=True, blank=True, help_text="Leave blank for school-wide fees")
    academic_year = models.IntegerField()
    term = models.CharField(max_length=10, choices=(('first','First'),('second','Second'),('third','Third')), blank=True)
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['academic_year', 'term', 'fee_type']
    
    def __str__(self):
        return f"{self.name} - {self.amount} ({self.academic_year})"


class FeePayment(models.Model):
    """Record individual fee payments"""
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('mobile', 'Mobile Money'),
        ('cheque', 'Cheque'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.PROTECT)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=100, blank=True, help_text="Cheque/Transfer reference")
    remarks = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.student} - {self.amount_paid} ({self.payment_date})"


class StudentFeeStatus(models.Model):
    """Track fee status per student per term"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    academic_year = models.IntegerField()
    term = models.CharField(max_length=10, choices=(('first','First'),('second','Second'),('third','Third')))
    total_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'academic_year', 'term')
        ordering = ['-academic_year', '-term']
    
    def update_balance(self):
        """Recalculate balance"""
        self.balance = self.total_fees - self.total_paid
        self.save()
    
    def __str__(self):
        return f"{self.student} - {self.academic_year} {self.term} (Balance: {self.balance})"



































