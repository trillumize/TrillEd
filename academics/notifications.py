# academics/notifications.py
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_sms_placeholder(phone, message):
    """
    Replace with real SMS provider (Twilio, Africa's Talking, etc.)
    For now we just log the SMS so you can test locally.
    """
    logger.info(f"[SMS PLACEHOLDER] To: {phone}\n{message}")
    return True

def build_discipline_message(student, record):
    return (
        f"Dear {student.parent_name or 'Parent'},\n\n"
        f"Discipline summary for {student.first_name} {student.last_name} — {record.term.capitalize()} {record.year}:\n\n"
        f"- Unjustified absences: {record.unjustified_absences}\n"
        f"- Justified absences: {record.justified_absences}\n"
        f"- Lateness: {record.lateness}\n"
        f"- Punishment hours: {record.punishment_hours}\n"
        f"- Warning: {'Yes' if record.warning else 'No'}\n"
        f"- Reprimand: {'Yes' if record.reprimand else 'No'}\n"
        f"- Suspension: {'Yes' if record.suspension else 'No'}\n"
        f"- Dismissal: {'Yes' if record.dismissal else 'No'}\n\n"
        f"Remarks: {record.remark or 'None'}\n\n"
        f"Regards,\n{getattr(settings, 'SCHOOL_NAME', 'School Admin')}"
    )

def send_discipline_report(record):
    """
    Send discipline summary to parent_email (email) and parent_contact (SMS placeholder).
    This function sets record.sent_to_parent = True after attempting sends to avoid duplicates.
    """
    student = record.student
    message = build_discipline_message(student, record)

    success = False

    # Email
    if student.parent_email:
        try:
            send_mail(
                subject=f"Discipline Report — {student.first_name} {student.last_name} — {record.term} {record.year}",
                message=message,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
                recipient_list=[student.parent_email],
                fail_silently=False,
            )
            logger.info(f"Discipline email sent to {student.parent_email}")
            success = True
        except Exception as e:
            logger.exception(f"Failed to send discipline email to {student.parent_email}: {e}")

    # SMS placeholder
    if student.parent_contact:
        try:
            send_sms_placeholder(student.parent_contact, message)
            success = True
        except Exception as e:
            logger.exception(f"Failed to send discipline SMS to {student.parent_contact}: {e}")

    # mark as sent to avoid duplicates
    if success:
        record.sent_to_parent = True
        record.save(update_fields=['sent_to_parent'])
