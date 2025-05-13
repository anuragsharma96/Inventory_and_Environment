from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import CustomUser, AdminLog, Access, Lab, Equipment, LabEquipment
from django.db.utils import IntegrityError  # Import IntegrityError
from django.contrib.auth.signals import user_logged_in

@receiver(post_save, sender=CustomUser)
def create_access_entry(sender, instance, created, **kwargs):
    """
    Ensure every new user has an entry in the Access table.
    """
    if created:
        Access.objects.create(
            Admin=instance,
            Email=instance.email,
            PhoneNumber=instance.phonenumber,
            Has_Access=True,
            username=instance.username,
            revoked_at=None
        )

@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
    AdminLog.objects.create(
        Admin=user,
        username=user.username,
        Email=user.email,
        Action="Logged in"
    )

@receiver(post_save, sender=CustomUser)
def update_email_in_logs(sender, instance, **kwargs):
    # Update email in AdminLog table
    AdminLog.objects.filter(Admin=instance).update(Email=instance.email)
    AdminLog.objects.filter(Admin=instance).update(username=instance.username)


    # Update email in Access table
    Access.objects.filter(Admin=instance).update(Email=instance.email)
    Access.objects.filter(Admin=instance).update(username=instance.username)
    Access.objects.filter(Admin=instance).update(PhoneNumber=instance.phonenumber)

@receiver(pre_delete, sender=CustomUser)
def store_access_record_before_deletion(sender, instance, **kwargs):
    access_record, created = Access.objects.get_or_create(
        Admin=instance,
        defaults={"Has_Access": False, "Reason_Revoked": "Access revoked before deletion"}
    )
    access_record.save()
##    if access_record.Has_Access==False:
##        CustomUser.objects.filter(pk=instance.pk).update(pk.access_revoked=True)

@receiver(post_save, sender=Lab)
def create_or_update_equipment_from_lab(sender, instance, created, **kwargs):
    print("Lab post_save signal triggered for:", instance.Name)
    if not created:
        return
    if not instance.Tool_Name:
        return
    equipment_defaults = {
        'Quantity': instance.Quantity if instance.Quantity is not None else 0,
        'Tool_Cost': instance.Tool_Cost if instance.Tool_Cost is not None else 0,
    }
    try:
        equipment, eq_created = Equipment.objects.get_or_create(
            Tool_Name=instance.Tool_Name,
            Type=instance.Type,
            Section=instance.Section,
            Lab=instance,
            Lab_Name=instance.Lab_Name,
            defaults=equipment_defaults
        )
        if eq_created:
            print("Created new Equipment for Lab:", instance.Name)
        else:
            # If you want to update even on subsequent saves, update the record:
            equipment.Quantity = instance.Quantity
            equipment.Tool_Cost = instance.Tool_Cost
            equipment.save(update_fields=['Quantity', 'Tool_Cost'])
            print("Updated Equipment for Lab:", instance.Name)
    except Exception as e:
        print("Error in Lab signal:", e)
@receiver(post_save, sender=Equipment)
def link_equipment_and_update_lab(sender, instance, created, **kwargs):
    """
    When a new Equipment is added (via the Add Equipment form), ensure it is linked
    in the LabEquipment table and update the corresponding Lab fields if required.
    """
    if not created:
        return
    if not instance.Tool_Name:
        return
    if created:
        # Create the linking record in LabEquipment with the quantity from Equipment.
        LabEquipment.objects.get_or_create(
            lab=instance.Lab,
            equipment=instance,
            defaults={'quantity': instance.Quantity}
        )
        # OPTIONAL: Update the Lab's fields with Equipment data.
        # Adjust the condition if you only want to update when Lab fields are empty or need syncing.
        lab = instance.Lab
        updated = False
        if lab.Tool_Name != instance.Tool_Name:
            lab.Tool_Name = instance.Tool_Name
            updated = True
        if lab.Type != instance.Type:
            lab.Type = instance.Type
            updated = True
        if lab.Section != instance.Section:
            lab.Section = instance.Section
            updated = True
        if lab.Quantity != instance.Quantity:
            lab.Quantity = instance.Quantity
            updated = True
        if lab.Tool_Cost != instance.Tool_Cost:
            lab.Tool_Cost = instance.Tool_Cost
            updated = True
        if updated:
            lab.save(update_fields=['Tool_Name', 'Type', 'Section', 'Quantity', 'Tool_Cost'])


