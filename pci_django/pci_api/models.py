from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class APIUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class APIUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = APIUserManager()

    class Meta:
        db_table = 'pci_users'

    def __str__(self):
        return self.email
        

class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        DECLINED = 'DECLINED', 'Declined'

    transaction_ref = models.CharField(max_length=64, unique=True, db_index=True)
    pan_encrypted = models.TextField()  # Store encrypted PAN as hex string
    expiry_encrypted = models.TextField()  # Store encrypted expiry as hex string
    pan_masked = models.CharField(max_length=24)  # Masked PAN for display (e.g., "**** **** **** 1234")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    email = models.EmailField(max_length=254)
    owner = models.ForeignKey(APIUser, on_delete=models.CASCADE, related_name='transactions')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


    class Meta:
        db_table = 'pci_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email'], name='idx_tx_email'),
            models.Index(fields=['status'], name='idx_tx_status'),
        ]

    def __str__(self):
        return f"Transaction {self.transaction_ref} - {self.pan_masked} - {self.amount}"



