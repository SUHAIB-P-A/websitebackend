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

    plus_two_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="+2 Percentage"
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="City"
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
