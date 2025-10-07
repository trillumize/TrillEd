# TrillEd
School Management System - User Manual
Table of Contents
Introduction
System Overview
Getting Started
Global Admin Guide
School Admin Guide
Teacher Guide
Common Tasks
Troubleshooting

Introduction
This School Management System is a multi-tenant application that allows you to manage multiple schools from a single installation. Each school has its own isolated database, admin panel, and users.
Key Features
Multi-school management
Student records and enrollment
Teacher assignments
Marks and grades management
Report card generation
Discipline records
Class leaderboards

System Overview
User Roles
Global Admin


Creates and manages schools (tenants)
Access: http://localhost:8000/admin/ or your main domain
Can see all schools but cannot access individual school data
School Admin


Manages their specific school
Access: http://schoolname.localhost:8000/admin/
Full control over their school's data
Teacher


Manages assigned classes and subjects
Enters marks for students
Access: School-specific URLs
Student


Future functionality (not yet implemented)

Getting Started
System Requirements
Python 3.8+
PostgreSQL database
Django and django-tenants installed
Initial Setup
Start the server:

 python manage.py runserver


Create a Global Admin (first time only):

 python manage.py createsuperuser


Enter your email (used as username)
Set a secure password
Access Global Admin:


Go to http://localhost:8000/admin/
Login with your global admin credentials

Global Admin Guide
Creating a New School
Option 1: Using Django Admin (Recommended for beginners)
Login to Global Admin


URL: http://localhost:8000/admin/
Create Client (School)


Navigate to SCHOOLS → Clients
Click Add Client
Fill in:
Name: Full school name (e.g., "Benita College")
Schema name: Lowercase, no spaces (e.g., "benita")
Admin username: School admin login name (e.g., "benitadmin")
Admin email: Admin email address
Admin password: Strong password for school admin
On trial: Check if school is on trial period
Paid until: Set subscription end date (optional)
Click Save
Create Domain


Navigate to SCHOOLS → Domains
Click Add Domain
Fill in:
Domain: Subdomain for school (e.g., "benita.localhost")
Tenant: Select the school you just created
Is primary: Check this box
Click Save
Update Hosts File


Windows: C:\Windows\System32\drivers\etc\hosts
Mac/Linux: /etc/hosts
Add line: 127.0.0.1 benita.localhost
Option 2: Using Management Command (Faster)
Open terminal and run:
python manage.py create_school \
  --name "Benita College" \
  --schema benita \
  --domain benita.localhost \
  --username benitadmin \
  --password SecurePass123! \
  --email admin@benita.com \
  --trial

This creates everything in one command.
Managing Schools
List all schools:
python manage.py list_schools

View school details:
Go to SCHOOLS → Clients in Global Admin
Click on any school to view/edit
Delete a school:
Select school in Clients list
Click Delete (WARNING: This removes all school data permanently)

School Admin Guide
Logging In
Go to your school's admin URL: http://yourschool.localhost:8000/admin/
Enter your username and password (provided by Global Admin)
You'll see your school's admin dashboard
Initial School Setup
1. Add School Information
Navigate to ACADEMICS → Schools
Click Add School
Fill in:
Name (English): Your school's English name
Name (French): Your school's French name
Logo: Upload school logo (optional)
Registration Number: Official registration number
2. Create Classrooms
Navigate to ACADEMICS → Class Rooms
Click Add Class Room
Enter:
Name: e.g., "Form 1A", "Form 2B"
Next class: Select which class students move to (optional)
Repeat for all classes
3. Add Subjects
Navigate to ACADEMICS → Subjects
Click Add Subject
Enter:
Name: e.g., "Mathematics", "English", "French"
Coefficient: Subject weight (default: 1.0)
Repeat for all subjects
4. Add Teachers
Navigate to ACADEMICS → Teachers
Click Add Teacher
Fill in:
First Name
Last Name
Email
Employee ID (optional)
Click Save
A user account is automatically created with:
Username: firstname.lastname
Password: defaultpassword123 (teacher should change this)
5. Assign Teachers to Classes/Subjects
Navigate to ACADEMICS → Teacher Assignments
Click Add Teacher Assignment
Select:
Teacher
Classroom
Subject
Click Save
Note: Each subject in a class can only have one teacher
Managing Students
Adding Individual Students
Navigate to ACADEMICS → Students
Click Add Student
Fill in all details
Click Save
Bulk Upload Students
Go to ACADEMICS → Class Rooms
Find your class and click Upload Students
Upload CSV or Excel file with columns:
first_name (required)
last_name (required)
Other fields optional
Click Upload
Example CSV:
first_name,last_name,date_of_birth,gender
John,Doe,2008-05-15,Male
Jane,Smith,2008-08-22,Female

Managing Academic Terms
Navigate to ACADEMICS → Term Configs
Click Add Term Config
Set:
Year: e.g., 2025
Term: First, Second, or Third
Is open: Check to allow mark entry
Only one term should be "open" at a time
Viewing Student Reports
Individual Report Card:
Go to ACADEMICS → Students
Find student
Click Generate Report button
PDF report downloads automatically
Class Reports (Bulk):
Go to ACADEMICS → Class Rooms
Find your class
Click Generate Class Reports
ZIP file with all student reports downloads
Leaderboards
Go to ACADEMICS → Class Rooms
Click on Leaderboards link for your class
Select term (1st, 2nd, or 3rd)
View ranked students by average marks
Marks Overview
Go to ACADEMICS → Class Rooms
Click View Marks for a class
Filter by:
Subject
Year
Term
Sequence
Toggle between:
Student mode: Average across all subjects
Subject mode: Individual subject marks
Export to CSV if needed

Teacher Guide
Accessing the System
Teachers log in at the same URL as school admin:
URL: http://yourschool.localhost:8000/admin/
Username: firstname.lastname (e.g., john.doe)
Password: defaultpassword123 (change immediately)
Changing Your Password
Click your username in top-right corner
Click Change Password
Enter old password and new password twice
Click Save
Entering Student Marks
Navigate to ACADEMICS → Marks
Filter by your subject and class
For each student:
Enter marks for sequences (1-6, depending on term)
Marks are out of 20
System automatically calculates averages
Click Save
Mark Entry Rules:
First Term: Sequences 1 & 2
Second Term: Sequences 3 & 4
Third Term: Sequences 5 & 6
Average is calculated automatically
Locked marks cannot be edited (contact admin)
Grading Scale
18-20: A (Excellent)
14-17: C (Good)
10-14: D (Fair)
5-10: E (Weak)
0-5: F (Very Poor)
Managing Discipline Records
Navigate to ACADEMICS → Discipline Records
Select student
Record:
Absences (justified/unjustified)
Lateness incidents
Punishment hours
Sanctions (warnings, suspensions, etc.)
Add remarks if needed
Use WhatsApp link to notify parents

Common Tasks
Promoting Students to Next Class
Navigate to ACADEMICS → Class Rooms
Edit current class
Set Next class field to the promotion class
Save
At year end, run promotion (feature to be implemented)
Generating Report Cards
Single Student:
ACADEMICS → Students → [Select Student] → Generate Report button

Entire Class:
ACADEMICS → Class Rooms → [Select Class] → Generate Class Reports

Reports include:
Student information
All subject marks and averages
Term average and rank
Grade and remarks
Discipline records
Teacher comments (if configured)
Tracking Student Progress
Go to ACADEMICS → Students
Find student
Click Progress button
View:
All terms' marks
Trend graphs
Subject performance
Historical data
Managing Discipline
Recording Incidents:
ACADEMICS → Discipline Records → Add

Notifying Parents:
Open discipline record
Click WhatsApp link
Message auto-populates
Send via WhatsApp Web
Exporting Data
Student List (CSV):
Go to Students list
Use export function (top right)
Marks Overview (CSV):
Go to Class Rooms → View Marks
Apply filters
Click Export CSV

Troubleshooting
Cannot Access School Admin Panel
Problem: "No tenant for hostname" error
Solution:
Check domain exists in Global Admin
Verify hosts file entry
Restart Django server
Clear browser cache
Login Fails for School Admin
Problem: "Please enter correct email and password"
Solution:
Verify you're using username, not email
Check you're on correct domain (school.localhost, not localhost)
Reset password via Django shell if needed:
 python manage.py shell
 from django_tenants.utils import schema_contextfrom accounts.models import Userwith schema_context('yourschool'):    user = User.objects.get(username='schooladmin')    user.set_password('NewPassword123!')    user.save()


Marks Not Saving
Problem: Marks don't save or disappear
Solution:
Check term is "open" in Term Config
Verify mark is not locked
Check you're assigned to that subject/class
Ensure mark is between 0-20
Cannot Upload Students
Problem: CSV upload fails
Solution:
Verify file has first_name and last_name columns
Check for special characters in names
Use UTF-8 encoding
Remove empty rows
Report Card Generation Fails
Problem: PDF doesn't generate
Solution:
Ensure student has marks entered
Check term config exists
Verify all required data is complete
Check server logs for errors
Domain Already Exists Error
Problem: Can't create new school with domain
Solution:
Check if domain already registered
Use different subdomain
Delete old domain if no longer needed

Best Practices
Security
Change default passwords immediately
Use strong passwords (minimum 8 characters, mix of letters, numbers, symbols)
Don't share admin credentials
Log out after each session
Regularly backup your database
Data Entry
Enter marks before term ends
Lock marks after finalization to prevent changes
Verify student information is complete
Keep discipline records up to date
Generate reports at end of each term
System Maintenance
Regularly backup database
Archive old academic years
Update student photos
Review and update teacher assignments each year
Clean up inactive user accounts

Support & Contact
For technical issues:
Check this manual first
Review error messages carefully
Contact your system administrator
Keep detailed notes of issues
For feature requests:
Document what you need
Explain the use case
Contact system administrator

Appendix: Command Reference
Management Commands
Create school:
python manage.py create_school --name "School Name" --schema schoolname --domain schoolname.localhost --username admin --password Pass123!

List schools:
python manage.py list_schools

Run migrations:
python manage.py migrate

Create global superuser:
python manage.py createsuperuser

Start server:
python manage.py runserver


Version History
v1.0 - Initial release
Multi-tenant support
Student/Teacher management
Marks and grading system
Report card generation
Discipline tracking

Last Updated: October 2025



