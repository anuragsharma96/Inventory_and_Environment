from django.db import migrations

OLD_CHOICES = {
    'et': [
        'Electrical Technician', 'CCTV', 'Solar', 'Motor Starter',
        'Cabling Technician', 'EV Charging', 'Energy Meter',
    ],
    'beauty': ['Skin', 'Hair', 'Nails', 'Makeup'],
    'stitch': ['Basic', 'Advanced', 'Knitting'],
    'New': ['New Section',]
}


def forwards(apps, schema_editor):
    Section = apps.get_model('inventoryapp', 'Section')
    for cat, names in OLD_CHOICES.items():
        for name in names:
            Section.objects.get_or_create(category=cat, name=name)


class Migration(migrations.Migration):
    dependencies = [
        ('inventoryapp', '0016_section_alter_equipment_section_alter_lab_section_and_more'),
    ]
    operations = [
        migrations.RunPython(forwards),
    ]
