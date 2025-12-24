from django.db import models
from django.core.validators import RegexValidator


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
        unique=True,
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

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
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

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Enquiry"
        verbose_name_plural = "Enquiries"

    def __str__(self):
        return f"{self.name} - {self.phone}"
