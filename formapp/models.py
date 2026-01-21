from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password

class Staff(models.Model):
    name = models.CharField(max_length=100, verbose_name="Staff Name")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    login_id = models.CharField(max_length=50, unique=True, verbose_name="Login ID")
    password = models.CharField(max_length=255, verbose_name="Password")  # Stored as hash
    active_status = models.BooleanField(default=True, verbose_name="Active Status")
    role = models.CharField(max_length=10, default='staff', verbose_name="Role")
    
    # Profile Fields
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Phone Number")
    secondary_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Secondary Phone")
    email_secondary = models.EmailField(blank=True, null=True, verbose_name="Secondary Email") # Optional but good to have? Requirement didn't ask, skipping.
    
    gender = models.CharField(max_length=10, blank=True, null=True, verbose_name="Gender")
    dob = models.DateField(blank=True, null=True, verbose_name="Date of Birth")
    profile_image = models.TextField(blank=True, null=True, verbose_name="Profile Image (Base64)")
    official_photo = models.TextField(blank=True, null=True, verbose_name="Official Staff Photo (Base64)") # Admin managed
    
    designation = models.CharField(max_length=100, blank=True, null=True, verbose_name="Designation")
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name="Department") # User didn't explicitly ask but it was in the UI code I saw earlier. I'll add it for completeness if I saw it.
    address = models.TextField(blank=True, null=True, verbose_name="Address") # Detailed address
    date_of_joining = models.DateField(blank=True, null=True, verbose_name="Date of Joining")
    
    created_at = models.DateTimeField(auto_now_add=True)

    # StudentCount can be calculated dynamically...
    # ...

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    @property
    def student_count(self):
        # Count only active/assigned students?
        return self.assigned_students.count() + self.assigned_enquiries.count()

    def __str__(self):
        return f"{self.name} ({self.login_id})"

class StaffDocument(models.Model):
    staff = models.ForeignKey(Staff, related_name='documents', on_delete=models.CASCADE)
    document_name = models.CharField(max_length=255, verbose_name="Document Name")
    file = models.FileField(upload_to='staff_documents/', verbose_name="File")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_name} - {self.staff.name}"

class CollectionForm(models.Model):
    first_name = models.CharField(
        max_length=100,
        verbose_name="First Name"
    )

    last_name = models.CharField(
        max_length=100,
        verbose_name="Last Name"
    )

    email = models.EmailField(
        verbose_name="Email Address"
    )

    phone_number = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message="Enter a valid 10-digit mobile number"
            )
        ],
        verbose_name="Phone Number"
    )

    dob = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date of Birth"
    )

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Others', 'Others'),
    ]
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        verbose_name="Gender"
    )

    QUALIFICATION_CHOICES = [
        ('10th Standard', '10th Standard'),
        ('12th Standard', '12th Standard'),
        ('Diploma', 'Diploma'),
        ("Bachelor's Degree", "Bachelor's Degree"),
        ("Master's Degree", "Master's Degree"),
    ]
    highest_qualification = models.CharField(
        max_length=50,
        choices=QUALIFICATION_CHOICES,
        null=True,
        blank=True,
        verbose_name="Highest Qualification"
    )

    year_of_passing = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Year of Passing"
    )

    aggregate_percentage = models.CharField(
        max_length=10,
        verbose_name="Aggregate Percentage%/CGPA",
        null=True,
        blank=True
    )

    # Legacy field - keeping for backward compatibility if needed, or we can reuse/remove.
    # The requirement asks for "Aggregate Percentage%/CGPA". I'll use the new field for clarity.
    plus_two_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="+2 Percentage",
        null=True,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="City"
    )

    follow_up_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Follow Up Date"
    )



    course_selected = models.CharField(
        max_length=100,
        verbose_name="Course Selected",
        blank=True,
        null=True
    )

    colleges_selected = models.TextField(
        verbose_name="Colleges Selected",
        blank=True,
        null=True
    )

    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Extra Data"
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )

    assigned_staff = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_students',
        verbose_name="Assigned Staff"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Follow Up', 'Follow Up'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        verbose_name="Status"
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="Is Read"
    )

    viewed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Viewed At"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['assigned_staff']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_read', 'status']),  # Composite for common filters
        ]
        verbose_name = "Collection Form Entry"
        verbose_name_plural = "Collection Form Entries"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Enquiry(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Full Name"
    )

    email = models.EmailField(
        verbose_name="Email Address",
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message="Enter a valid 10-digit mobile number"
            )
        ],
        verbose_name="Mobile Number"
    )

    location = models.CharField(
        max_length=100,
        verbose_name="Location",
        blank=True,
        null=True
    )

    message = models.TextField(
        verbose_name="Query / Message",
        blank=True,
        null=True
    )

    assigned_staff = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_enquiries',
        verbose_name="Assigned Staff"
    )

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Connected', 'Connected'),
        ('Follow Up', 'Follow Up'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        verbose_name="Status"
    )

    follow_up_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Follow Up Date"
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="Is Read"
    )

    viewed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Viewed At"
    )



    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['assigned_staff']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_read', 'status']),  # Composite for common filters
        ]
        verbose_name = "Enquiry"
        verbose_name_plural = "Enquiries"

    def __str__(self):
        return f"{self.name} - {self.phone}"
