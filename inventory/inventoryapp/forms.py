from django import forms
from .models import CustomUser, Request, Equipment, Lab, LabEquipment

# Form for Creating Admins
class AdminCreationForm(forms.ModelForm):
    ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('superuser', 'SuperUser'),
]
    role=forms.ChoiceField(choices=ROLE_CHOICES)
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email','phonenumber', 'password','role']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Hash the password
        user.role = self.cleaned_data.get('role', 'admin')  # Assign the admin role
        if commit:
            user.save()
        return user

### Form for Admin Equipment Requests
##class RequestForm(forms.ModelForm):
##    class Meta:
##        model = Request
##        fields = ['Equipment', 'Type', 'Condition_Issued', 'Condition_Returned', 'Is_Returned']

# Refactored Lab Form (Now Independent)
class AddLab(forms.ModelForm):
    class Meta:
        model = Lab
        fields = ['Name','Tool_Name','Tool_Cost', 'Type', 'Section','Quantity']
    def save(self, commit=True):
        lab_instance = super().save(commit=False)
        if commit:
            lab_instance.save()
            # Create a corresponding Equipment entry
            Equipment.objects.create(
                Tool_Name=lab_instance.Tool_Name,
                Type=lab_instance.Type,
                Section=lab_instance.Section,
                Lab=lab_instance,  # Link to the newly created Lab
                Quantity=lab_instance.Quantity,
                Tool_Cost=lab_instance.Tool_Cost
            )
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            qs = Section.objects.all().order_by('category', 'name')
            # turn it into a normal list of (pk, name) and append our sentinel
            choices = [(sec.pk, sec.name) for sec in qs]
            choices.append(('__CREATE__', 'Create New Section…'))
            self.fields['Section'].choices = choices
        return lab_instance

# Refactored Equipment Form (Lab Can Be Typed)
class EquipmentForm(forms.ModelForm):
    lab_name = forms.CharField(required=True, help_text="Enter the Lab Name. If it doesn't exist, you'll be redirected to add it.")

    class Meta:
        model = Equipment
        fields = ['Tool_Name', 'Type', 'Section', 'Quantity',"Tool_Cost"]

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("Tool_Name")
        lab_name = cleaned_data.get("lab_name")

        # Check if Lab exists
        lab = Lab.objects.filter(Name=lab_name).first()

        if not lab:
            raise forms.ValidationError("This lab does not exist. You will be redirected to add it.")

        cleaned_data['lab'] = lab  # Assign lab to form

        # Check if Equipment already exists in this Lab
        if Equipment.objects.filter(Tool_Name=name, Lab=lab).exists():
            raise forms.ValidationError("This equipment already exists in this lab. Please provide a reason.")

        return cleaned_data

# New Form for LabEquipment (Handles Duplicate Equipment)
class LabEquipmentForm(forms.ModelForm):
    reason = forms.CharField(required=False, help_text="If adding the same equipment again, enter a reason.")
    class Meta:
        model = LabEquipment
        fields = ['lab', 'equipment', 'quantity', 'requested_by','reason']
class RequestForm(forms.ModelForm):
    class Meta:
        model=Request
        fields=['Username','Post','Tool_Name','Condition_Issued','Issued_By','IssuedQuantity',"Type","Section"]
            
class ReturnForm(forms.ModelForm):
    class Meta:
        model=Request
        fields=['Username','Post','Tool_Name','Condition_Returned','Returned_To','UserEmail','ReturnQuantity']            
