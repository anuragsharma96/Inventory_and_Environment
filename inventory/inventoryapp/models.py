from django.contrib.auth.models import AbstractUser
from django.db import models
import secrets
import djmoney
from djmoney.models.fields import MoneyField
from phonenumber_field.modelfields import PhoneNumberField

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('superuser', 'SuperUser')  # Superadmin is explicitly handled
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)
    login_key = models.CharField(max_length=100, unique=True, blank=True, null=True)  # Admin access key
    access_revoked = models.BooleanField(default=False)
    phonenumber = PhoneNumberField(blank=True, null=True, unique=True,default="+917807455055")


    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_groups",  # Avoid conflict with Django's default User model
        blank=True,
        help_text="The groups this user belongs to."
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions",  # Avoid conflict with Django's default User model
        blank=True,
        help_text="Specific permissions for this user."
    )

    def is_superadmin(self):
        return self.role == 'superuser' or self.is_superuser or self.role=="SuperUser"  # Corrected function to check superadmin status

    def save(self, *args, **kwargs):
        if self.role == 'admin' and not self.login_key:
            self.login_key = self.generate_unique_key()
        super().save(*args, **kwargs)

    def generate_unique_key(self):
        """Generate a unique login key for each Admin"""
        key = secrets.token_hex(16)  # 32-character secure key
        while CustomUser.objects.filter(login_key=key).exists():  # Ensure uniqueness
            key = secrets.token_hex(16)
        return key

class Section(models.Model):
    CATEGORY_CHOICES = [
    ('et', 'ET'),
    ('beauty', 'Beauty'),
    ('stitch', 'Stitch'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    name     = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.get_category_display()} – {self.name}"

class Lab(models.Model):
##    SECTION_CHOICES = [
##        [
##            ('Create New Section'),('Create New Section')
##            ],
##    ('et', [
##        ('Electrical Technician', 'Electrical Technician'),
##        ('CCTV', 'CCTV'),
##        ('Solar', 'Solar'),
##        ('Motor Starter', 'Motor Starter'),
##        ('Cabling Technician', 'Cabling Technician'),
##        ('EV Charging', 'EV Charging'),
##        ('Energy Meter', 'Energy Meter'),
##    ]),
##    ('beauty', [
##        ('Skin', 'Skin'),
##        ('Hair', 'Hair'),
##        ('Nails', 'Nails'),
##        ('Makeup', 'Makeup'),
##    ]),
##    ('stitch', [
##        ('Basic', 'Basic'),
##        ('Advanced', 'Advanced'),
##        ('Knitting', 'Knitting'),
##    ]),
##]

    Name = models.CharField(max_length=100, unique=False)  # Ensuring unique Lab names
    LabId=models.IntegerField(null=False,blank=False, unique=False,default=1)
    Tool_Name=models.CharField(max_length=255,unique=False,null=True,blank=True,default=1)
    Type = models.CharField(max_length=20, choices=[('fixed', 'Fixed'), ('consumable', 'Consumable')])
    Section = models.ForeignKey('Section',on_delete=models.PROTECT,related_name='labs')
    Quantity=models.IntegerField(null=True, blank=True)
    Tool_Cost=MoneyField(max_digits=20,decimal_places=2,default_currency='INR',blank=False,default=0,null=False)
    Equipment = models.ManyToManyField('Equipment', through='LabEquipment',related_name='labs')

    def __str__(self):
        return self.Name


class Equipment(models.Model):
    Tool_Name = models.CharField(max_length=100,null=False,unique=False)
    Type = models.CharField(max_length=20, choices=[('fixed', 'Fixed'), ('consumable', 'Consumable')])
    Section = models.ForeignKey('Section',on_delete=models.PROTECT,related_name='equipment')
##    Section = models.CharField(max_length=100, choices=Lab.SECTION_CHOICES)  # Ensure consistency with Lab
    Lab = models.ForeignKey('Lab', on_delete=models.CASCADE,related_name='Equipments')# One-to-Many relation with Lab
    Lab_Name=models.CharField(max_length=100, unique=False) 
    Quantity = models.IntegerField(null=True, blank=True)
    Tool_Cost=MoneyField(max_digits=20,decimal_places=2,default_currency='INR',blank=False,default=0,null=False)
    Total_Cost=MoneyField(max_digits=12, decimal_places=2, default_currency='INR', editable=False,default=0)
    Issued_Quantity = models.IntegerField(null=True, blank=True)
    Issued = models.BooleanField(default=False)
    Ordered_Date = models.DateTimeField(auto_now_add=True)# Timestamp for when equipment was added

    def save(self, *args, **kwargs):
        self.Total_Cost = self.Quantity * self.Tool_Cost
        return(super().save(*args, **kwargs))

    def __str__(self):
        return f"{self.Tool_Name} in {self.Lab.Name} ({self.Quantity})"


class LabEquipment(models.Model):
    """
    This model tracks equipment assignments to labs, including timestamps and reasons for duplicate entries.
    """
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    lab_name=models.CharField(max_length=100,null=False, blank=False)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    tool_name=models.CharField(max_length=255,null=False, default=False)
    quantity = models.PositiveIntegerField(default=1)
    reason = models.TextField(blank=True, null=True)  # Store reason for duplicate equipment
    requested_by=models.CharField(max_length=100,null=False,default=False)
    requested_at = models.DateTimeField(auto_now_add=True)  # Timestamp when equipment is added

    def __str__(self):
        return f"{self.equipment.Tool_Name} in {self.lab.Name} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Sync Equipment Quantity with LabEquipment
        self.equipment.Quantity = self.quantity
        self.equipment.save()


class Request(models.Model):
    """
    This model tracks requests made for equipment, including timestamps.
    """
    Admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    Issued_By=models.CharField(max_length=150,null=False,blank=False)
    Username=models.CharField(max_length=150,null=False,blank=False)
    Post=models.CharField(max_length=100,choices=[('student','Student'),('trainer','Trainer')])
    Authorized_By=models.CharField(max_length=250,null=True,blank=True)
    UserEmail=models.EmailField(unique=False,null=False)
    Equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    Tool_Name=models.CharField(max_length=150,null=False,blank=False)
    Type = models.CharField(max_length=20, choices=[('fixed', 'Fixed'), ('consumable', 'Consumable')])
    Section = models.ForeignKey('Section',on_delete=models.PROTECT,related_name='request')
    #Section = models.CharField(max_length=100, choices=Lab.SECTION_CHOICES)
    IssuedQuantity=models.IntegerField(default=0,null=True)
    Issued_Date = models.DateTimeField(auto_now_add=True)  # Track when issued
    Return_Date = models.DateTimeField(blank=True, null=True,auto_now_add=True)
    Returned_To=models.CharField(max_length=150,null=False,blank=False)
    Condition_Issued = models.TextField()
    Condition_Returned = models.TextField(blank=True, null=True)
    Is_Returned = models.BooleanField(default=False)
    ReturnQuantity=models.IntegerField(default=0,null=True)

    def __str__(self):
        return f"Request by {self.Username}, {self.Post} for {self.Equipment.Tool_Name}"
    
    def delete(self, *args, **kwargs):
        """Before deleting, store user details in Access"""
        if hasattr(self, 'access_record'):
            self.access_record.store_deleted_user_data()
        super().delete(*args, **kwargs)

class AdminLog(models.Model):
    """
    This model logs all admin actions for auditing.
    """
    Admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE,default="N/A")
    username= models.CharField(max_length=150,null=True,blank=True)
    Email = models.EmailField(unique=False,default="demo@ciimcm.org",null=False)
    Action = models.TextField()  # Description of the action performed
    TimeStamp = models.DateTimeField(auto_now_add=True)  # Auto-set timestamp

    def __str__(self):
        return f"{self.Admin.username} - {self.Action}"
    
    def save(self, *args, **kwargs):
        self.Email = self.Admin.email  # Ensure email is updated before saving
        super().save(*args, **kwargs)

class Access(models.Model):
    Admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    username= models.CharField(max_length=150,null=True,blank=True)
    Email = models.EmailField(unique=True,default="demo@ciimcm.org",null=False)
    PhoneNumber=PhoneNumberField()
    Has_Access = models.BooleanField(default=True)
    Reason_Revoked = models.TextField(blank=True, null=True)
    revoked_at = models.DateTimeField(null=True,blank=True)
    Reinstated=models.BooleanField(null=True,blank=True)
    Reinstated_at=models.DateTimeField(null=True,blank=True)

    def save(self, *args, **kwargs):
        self.Email = self.Admin.email  # Ensure email is updated before saving
        super().save(*args, **kwargs)
