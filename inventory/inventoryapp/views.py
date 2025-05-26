from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from .forms import EquipmentForm
from django.contrib.auth import login
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from .models import CustomUser, Equipment, Lab, Request, Access, AdminLog
from .forms import AdminCreationForm, EquipmentForm, AddLab
import re
import json
from django.db.models.signals import post_save
from .signals import create_or_update_equipment_from_lab

def home(request):
    return render(request, 'template.html')

# Render Inventory Page
@login_required
def inventory_list(request):
    if request.user.role in ['admin','SuperUser', 'superuser']or request.user.is_superuser:
        equipments = Equipment.objects.all()
##        labs = Lab.objects.all()
##        print("Equipment Data:", equipments)
        return render(request, 'template.html',{'equipments': equipments})# {'equipments': equipments, 'labs': labs})
    return redirect('home')

# Admin Places an Order (Triggers Email & Saves Timestamp)
@login_required
def place_order(request):
    if request.method == "POST":
        equipment_id = request.POST.get("equipment_id")
        equipment = get_object_or_404(Equipment, id=equipment_id)
        labid=request.POST.get("lab_id")
        lab=get_object_or_404(Lab,id=labid)
        tool_name=equipment.Tool_Name
        admin_email = request.user.email
        request_by=request.POSt.get("request_by")
        quantity=request.POST.get("quantity")
        superadmin_emails = list(CustomUser.objects.filter(is_superuser=True).values_list('email', flat=True))

        # Save Order with Timestamp
        order = Request.objects.create(
            Admin=request.user,
            Equipment=equipment,
            tool_name=tool_name,
            request_by=request_by,
            quantity=quantity,
            Type=equipment.Type,
            requested_at=timezone.now(),
            lab_name=labid.lab_name           
        )

        # Send Email Notification to SuperAdmin
        send_mail(
            "Equipment Order Request",
            f"Admin {request.user.username} has requested {equipment} on behalf of {request_by}.",
            "noreply@inventory.com",
            superadmin_emails,
            fail_silently=False,
        )
        AdminLog.objects.create(
    Admin=request.user,
    username=request.user.username,
    Email=request.user.email,
    Action=f"Requested order for {equipment}",
    TimeStamp=timezone.now()
)

        return JsonResponse({'message': 'Order placed successfully!', 'request_time': order.timezone.now()})

    return JsonResponse({'error': 'Invalid request'}, status=400)

# SuperAdmin Creates Admins
@login_required
def create_admin(request):
    if request.user.is_superuser or request.user.role=="SuperUser":
        if request.method == "POST":
            form = AdminCreationForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                previous_access_record = Access.objects.filter(Email=email).first()
                username=form.cleaned_data['username']
                role=form.cleaned_data['role']
                candidate_user=CustomUser.objects.filter(username=username).first()
                if role=="SuperUser":
                    CustomUser.objects.filter(username=username).update(is_superuser=True)
##                if previous_access_record or  (candidate_user and candidate_user.access_revoked):
##                    messages.info(request, f"User {email} and {username} was previously revoked. Reinstating status.")
##                    CustomUser.objects.filter(username=username).update(Admin=request.user,access_revoked=False,
##                                              Role=f"Reinstated as {role}")
####                if form.cleaned_data.get['username'] in CustomUser.objects.values_list('username',flat=True):
####                    return render(request, 'create_admin.html', {'entry_exists': True,'entered_username':form.username})
##                    AdminLog.objects.create(Admin=request.user,username=request.user.username,
##                                            Email=request.user.email,Action=f"Reinstated access for {username}",
##                                            TimeStamp=timezone.now())
##                    Access.objects.filter(username=username).update(Admin=request.user, Has_Access=True,Reinstated=True,Reinstated_at=timezone.now())
                else:
                    form.save()
                AdminLog.objects.create(
    Admin=request.user,
    username=request.user.username,
    Email=request.user.email,
    Action=f"Created new access record for {username}",
    TimeStamp=timezone.now()
)
                return redirect('admin_list')
        else:
            form = AdminCreationForm()
        return render(request, 'create_admin.html', {'form': form})
    return redirect('home')

# Admin Login
def admin_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        login_key = request.POST["login_key"]

        user = CustomUser.objects.filter(username=username).first()

        if user and user.role == 'admin' and user.check_password(password) and user.login_key == login_key:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'admin_login.html', {'error': "Invalid credentials or login key."})

    return render(request, 'admin_login.html')

# List Admins
@login_required
def admin_list(request):
    if request.user.is_superuser or request.user.role == "superuser" or request.user.role == "SuperUser":
        admins = CustomUser.objects.all()
        return render(request, 'admin_list.html', {'admins': admins})
    return redirect('home')

# Manage Admins (SuperAdmin Only)
@login_required
##def manage_admins(request):
##    if request.user.is_superuser() or request.user.role=="SuperUser":
##        admins = CustomUser.objects.all()
##        return render(request, 'admin_list.html', {'admins': admins})
##    return redirect('home')

# Add Equipment (With Lab Syncing & Duplicate Handling)
@login_required
def add_equipment(request):
    if request.user.is_superuser or request.user.role in ["SuperUser","superuser",str("Superuser").lower()]:

        if request.method == "POST":
            form = EquipmentForm(request.POST)
            if form.is_valid():
                tool_name = form.cleaned_data['Tool_Name']
                type = form.cleaned_data['Type']
                tool_cost=form.cleaned_data['Tool_Cost']
                section = form.cleaned_data['Section']
                quantity = form.cleaned_data['Quantity']
                lab_name = request.POST.get("lab_name")  # Get lab name from user input

                # Check if Lab exists
                lab = Lab.objects.filter(Name=lab_name).first()
                if not lab:
                    return JsonResponse({'error': 'Lab does not exist. Redirecting...'}, status=400)

                # Check if Equipment exists in Lab
                existing_equipment = Equipment.objects.filter(Tool_Name=tool_name, Lab=lab)
                if existing_equipment.exists():
                    reason = request.POST.get("reason_for_duplicate", "")
                    if not reason:
                        return JsonResponse({'error': 'Please provide a reason for adding duplicate equipment.'}, status=400)

                    # Save reason for duplicate addition
                    LabEquipment.objects.create(
                        lab=lab,
                        equipment=existing_equipment.first(),
                        quantity=quantity,
                        reason=reason
                    )
                else:
                    # Create new Equipment
                    new_equipment = Equipment.objects.create(
                        Tool_Name=tool_name,
                        Type=type,
                        Section=section,
                        Quantity=quantity,
                        Tool_Cost=tool_cost,
                        Lab=lab
                    )

                    # Link Equipment to Lab
                    LabEquipment.objects.create(
                        lab=lab,
                        equipment=new_equipment,
                        quantity=quantity
                    )
                AdminLog.objects.create(
    Admin=request.user,
    username=request.user.username,
    Email=request.user.email,
    TimeStamp=timezone.now(),
    Action=f"Placed order for {Equipment.Tool_Name}"
)

                return redirect("inventory_list")

        else:
            form = EquipmentForm()
        
        labs = Lab.objects.all()
        return render(request, "add_equipment.html", {"form": form, "labs": labs})
    else:
        return redirect("inventory_list")

# Add Lab (Without Equipment Form Embedded)
@login_required
def add_lab(request):
    if request.user.is_superuser or request.user.role in ["SuperUser","superuser",str("Superuser").lower()]:
        if request.method == "POST":
            form = AddLab(request.POST)
            if form.is_valid():
                post_save.disconnect(create_or_update_equipment_from_lab, sender=Lab)

                form.save()
                post_save.connect(create_or_update_equipment_from_lab, sender=Lab)
                equipment_pattern = re.compile(r'^Tool_Name_(\d+)$')
                equipment_indices = []
                
                # Find all indices from the tool_name fields
                for key in request.POST:
                    match = equipment_pattern.match(key)
                    if match:
                        equipment_indices.append(match.group(1))
                
                # Optionally sort indices if order is important
                equipment_indices.sort(key=lambda x: int(x))

                if request.POST.get('Name') not in Lab.Name:
                    labnum=next(reversed(Lab.LabId))
                    labnum+=1
                for index in equipment_indices:
                    if request.POST.get(f'Section_{index}')=="Create New Section":
                        tool_name = request.POST.get(f'Tool_Name_{index}')
                        type_field = request.POST.get(f'Type_{index}')
                        quantity = request.POST.get(f'Quantity_{index}')
                        tool_cost = request.POST.get(f'Tool_Cost_0_{index}')
                        tool_cost_currency=request.POST.get(f'Tool_Cost_1_{index}')
                        section=request.POST.get(r'^newsection(\d+)$')
                        SECTION.create(category=request.POST.get(r'^catinp(\d+)$'),name=section)
                        Lab.objects.create(Name=request.POST.get('Name'),Tool_Name= tool_name, Type= type_field, Section=section,
            Quantity= quantity, Tool_Cost= tool_cost, Tool_Cost_currency=tool_cost_currency)
                    # For each equipment block, extract the data using the index
                    else:
                        tool_name = request.POST.get(f'Tool_Name_{index}')
                        type_field = request.POST.get(f'Type_{index}')
                        section = request.POST.get(f'Section_{index}')
                        quantity = request.POST.get(f'Quantity_{index}')
                        tool_cost = request.POST.get(f'Tool_Cost_0_{index}')
                        tool_cost_currency=request.POST.get(f'Tool_Cost_1_{index}')
                        Lab.objects.create(Name=request.POST.get('Name'),
                        Tool_Name= tool_name, Type= type_field, Section=section,
                Quantity= quantity, Tool_Cost= tool_cost, Tool_Cost_currency=tool_cost_currency)
##                    equipment_list.append({
##                        "Tool_Name": tool_name,
##                        "Type": type_field,
##                        "Section": section,
##                        "Quantity": quantity,
##                        "Tool_Cost": tool_cost
##                    })
##                for i in equipment_list:
##                    form.append.save()
##                    messages.success(request, "Lab added successfully!")
                AdminLog.objects.create(
        Admin=request.user,
        username=request.user.username,
        Email=request.user.email,
        Action=f"Lab {Lab.Name} added",
        TimeStamp=timezone.now()
    )
                return redirect('lab_list')
        else:
            form = AddLab()

        return render(request, "add_lab.html", {"form": form})

# List Labs
def lab_list(request):
    labs = Lab.objects.all()
    return render(request, 'lab_list.html', {'labs': labs})

# Revoke Admin Access
@login_required
def revoke_admin_access(request):
    if request.user.is_superuser or request.user.role in ["SuperUser","superuser",str("Superuser").lower()]:
        if request.method == "POST":
            admin_id = request.POST.get("admin_id")
            reason = request.POST.get("reason")

            try:
                admin_user = CustomUser.objects.get(id=admin_id)
        ##            if admin_user.access_revoked!=True:
        ##                admin_user.access_revoked=
                if admin_user.is_superuser==True or admin_user.role in ["SuperUser","superuser","superuser".lower()]:
                    admin_user.is_superuser=False
                admin_user.role="Revoked"
                admin_user.access_revoked=True
                admin_user.save()
        ##            adm_user, created= CustomUser.objects.get_or_create(user=admin_user)
        ##            adm_user.role="Revoked"
        ##            adm_user.access_revoked=True
        ##            adm_user.save()
                access_record, created = Access.objects.get_or_create(Admin=admin_user)

                # Update existing record instead of creating a duplicate
                access_record.Has_Access = False
                access_record.Reason_Revoked = reason
                access_record.revoked_at=timezone.now()
                access_record.save()
                messages.success(request, f"Access revoked for {admin_user.username}")
                AdminLog.objects.create(
        Admin=request.user,
        username=request.user.username,
        Email=request.user.email,
        Action=f"Admin access revoked for {admin_user.username}",
        TimeStamp=timezone.now()
        ).save()
            except CustomUser.DoesNotExist:
                messages.error(request, "Admin not found")

            return redirect("admin_list")

def lab_autocomplete(request):
    if 'term' in request.GET:
        labs = Lab.objects.filter(name__icontains=request.GET.get('term'))
        lab_list = list(labs.values_list('name', flat=True))
        return JsonResponse(lab_list, safe=False)
    return JsonResponse([], safe=False)

#reinstate access
@login_required
def reinstate_admin(request):
        if request.user.is_superuser or request.user.role in ["SuperUser","superuser",str("Superuser").lower()]:
            if request.method=="POST":
                admin_id=request.POST.get("adm_id")
                email=request.POST.get("email")
                phone=request.POST.get("phone")
                is_staff=request.POST.get("is_staff")
                role=request.POST.get("role")
                try:
                    admin_user=CustomUser.objects.get(id=admin_id)
                    admin_user.email=email
                    admin_user.phonenumber=phone
                    if is_staff==True or is_staff=="True":
                        admin_user.is_staff=True
                    admin_user.access_revoked=False
                    admin_user.role=f"Reinstated as {role}"
                    admin_user.save()
                    access_record, created=Access.objects.get_or_create(Admin=admin_user)
                    access_record.Has_Access = True
                    access_record.Reinstated_at=timezone.now()
                    access_record.Reinstated=True
                    access_record.save()
                    messages.success(request, f"Access reinstated for {admin_user.username} as {admin_user.role}.")
                    AdminLog.objects.create(
        Admin=request.user,
        username=request.user.username,
        Email=request.user.email,
        Action=f"Admin access reinstated for {admin_user.username}",
        TimeStamp=timezone.now()
        ).save()
                finally:
                    return redirect("admin_list")
#promote access
@login_required
def promote(request):
    if request.user.is_superuser or request.user.role in ["SuperUser","superuser",str("Superuser").lower()]:
        if request.method=="POST":
            admin_id=request.POST.get("admid")
        try:
            admin_user=CustomUser.objects.get(id=admin_id)
            admin_user.role="SuperUser"
            admin_user.is_superuser=True
            admin_user.save()
            access_record, created=Access.objects.get_or_create(Admin=admin_user)
            access_record.Has_Access = True
            access_record.Promoted = True
            access_record.promoted_at=timezone.now()
            access_record.save()
            messages.success(request,f"Access promoted for {admin_user.username} as {admin_user.role}.")
            AdminLog.objects.create(Admin=request.user,username=request.user.username,Email=request.user.email,
                                   Action=f"Admin access promoted for {admin_user.username}", TimeStamo=timezone.now()).save()
        finally:
            return redirect("admin_list")
@login_required
def issue_equipment(request):
    # Always fetch the list of equipment for the form
    equipment_list = Equipment.objects.all()

    if request.method == "POST":
        # Process the form submission
        equipment = get_object_or_404(Equipment, id=request.POST["equipment_id"])
        req = Request.objects.create(
            Admin=request.user,
            Issued_By=request.POST["issued_by"],
            Username=request.POST["username"],
            Post=request.POST["post"],
            UserEmail=request.POST["user_email"],
            #Equipment=equipment,
            Tool_Name=equipment.Tool_Name,
            Type=equipment.Type,
            Section=equipment.Section,
            IssuedQunatity=request.POST["quantity"],
            Condition_Issued=request.POST["condition_issued"]
        )
        # Use Django messages to show a one‐time success message
        messages.success(request, "Equipment issued successfully!")
        AdminLog.objects.create(
        Admin=request.user,
        username=request.user.username,
        Email=request.user.email,
        Action=f"{username} issued {Tool_Name} to {Username}",
        TimeStamp=timezone.now()
        ).save()
        # After POST, redirect to GET (Post/Redirect/Get pattern)
        return redirect('issue_equipment')

    # If GET (or any other method), render the form
    return render(request, "request.html", {
        "equipment_list": equipment_list
    })
@login_required
def return_equipment(request):
    if request.method == "POST":
        equipment = get_object_or_404(Equipment, id=request.POST["equipment_id"])
        req = Request.objects.create(
            Admin=request.user,
        Returned_to=request.POST["returned_to"],
        Username=request.POST["username"],
        Post=request.POST["post"],
        UserEmail=request.POST["user_email"],
        ReturnedQuantity=request.POST['quantity'],
        #Equipment=equipment,
        Tool_Name=equipment.Tool_Name,
        Type=equipment.Type,
        Section=equipment.Section,
        Condition_Returned=request.POST["condition_returne"]
        )
        # Use Django messages to show a one‐time success message
        messages.success(request, "Equipment issued successfully!")
        AdminLog.objects.create(
        Admin=request.user,
        username=request.user.username,
        Email=request.user.email,
        Action=f"{Username} returned {Tool_Name} to {username}",
        TimeStamp=timezone.now()
        ).save()
        # After POST, redirect to GET (Post/Redirect/Get pattern)
        return redirect('unreturned_equipment', username=req.Username)

    # GET method: render the return form
    equipment_list = Equipment.objects.all()  # Make sure to define this
    return render(request, "return.html", {
        "equipment_list": equipment_list
    })

@login_required
def adminlog():
    return(request,'adminlog.html')

@require_GET
def get_equipment_form(request):
    index = request.GET.get('index', '0')
    form = AddLab()
    form.fields.pop('Name', None)
    # Grab choices
    section_choices = form.fields['Section'].choices
    type_choices = form.fields['Type'].choices
    # ---- begin: MoneyField rendering hack ----
    # Grab the MoneyWidget (a MultiWidget under the hood)
    money_widget = form.fields['Tool_Cost'].widget
    # Get the raw value out of the bound field (a Money instance or None)
    bound_value = form['Tool_Cost'].value()
    # Decompress it into [amount, currency]
    parts = money_widget.decompress(bound_value)
    # Now render each subwidget with a custom name/id
    tool_cost_html = []
    for slot, widget in enumerate(money_widget.widgets):
        if slot == 0:
            name = f"Tool_Cost_0{index}"      # the decimal amount
        else:
            name = f"Tool_Cost_1{index}"    # the currency select
        tool_cost_html.append(
            widget.render(name=name,
                          value=parts[slot],
                          attrs={'id': name})
        )
    tool_cost_html = "\n".join(tool_cost_html)
    # ---- end MoneyField hack ----
    html = f"""
        <div class="equipment-block">
            <label for='Tool_Name_{index}'>Tool Name</label>
            <input type="text" id="Tool_Name{index}" name="Tool_Name{index}" value="{form['Tool_Name'].value() or ''}"><br>

            <label for='Type_{index}'>Type</label>
            <select name="Type{index}">
    """
 
    for val, label in type_choices:
        html += f"<option value='{val}'>{label}</option>"
    html += "</select>"
    html += f"""
            <label for='Section_{index} id="Section{index}"'>Section</label>
            <select name="Section{index}">
    """
    for val, label in section_choices:
        html += f"<option value='{val}'>{label}</option>"
    html += "</select>"
    html += f"""
            <label for='Quantity_{index}'>Quantity</label>
            <input class="Quantity" type="number" name="Quantity_{index}" id="Quantity_{index}" value="{form['Quantity'].value() or ''}">
            <label for='Tool_Cost_{index}'>Tool Cost</label><label for="Tool_Cost_1{index}"></label>
            {tool_cost_html}
            
            <hr>
        </div>
    """
    return JsonResponse({'form_html': html})
##@require_GET
##def addjs(request):
##    js= '''<script>
##const sect=document.getElementById("Section{index}"};
##        const labPatterns = {
##            et: [
##                /^Electrician(\d*)$/,
##                /^Electric(\d*)$/,
##                /^ET(\d*)$/,
##                /^ET_Lab(\d*)$/,
##                /^ET_Lab_(\d*)$/,
##                /^ET lab(\d*)$/,
##                /^ET_lab_(\d*)$/,
##                /^ET_lab$/
##            ],
##            stitch: [
##                /^Stitchingand Tailoring(\d*)$/, /^Stitching&Tailoring(\d*)$/, /^Stitching & Tailoring(\d*)$/, /^Stitching_and_Tailoring(\d*)$/,
##                /^Stitching_&_Tailoring(\d*)$/, /^S&T(\d*)$/, /^S_&_T(\d*)$/, /^Stitching(\d*)$/, /^Tailoring(\d*)$/
##            ],
##            beauty: [/^Beauty and Wellness(\d*)$/, /^ Beauty&Wellness(\d*)$/, /^Beauty & Wellness(\d*)$/, /^Beauty_and_Wellness(\d*)$/, /^B&W(\d*)$/,
##                /^Beauty_&_Wellness(\d*)$/, /^B & W(\d*)$/, /^Beauty(\d*)$/],
##        };
##        const sectionChoices =
##        {
##            et: [
##                { value: 'Electrical Technician', text: 'Electrical Technician' },
##                { value: 'CCTV', text: 'CCTV' },
##                { value: 'Solar', text: 'Solar' },
##                { value: 'Motor Starter', text: 'Motor Starter' },
##                { value: 'Cabling Technician', text: 'Cabling Technician' },
##                { value: 'EV Charging', text: 'EV Charging' },
##                { value: 'Energy Meter', text: 'Energy Meter' },
##                { value: "Create New Section", text: "Create New Section" }
##            ],
##            beauty: [{ value: 'Skin', text: 'Skin' }, { value: 'Hair', text: 'Hair' }, { value: 'Nails', text: 'Nails' }, { value: 'Makeup', text: 'Makeup' },
##            { value: "Create New Section", text: "Create New Section" }],
##            stitch: [{ value: 'Basic', text: 'Basic' }, { value: 'Advanced', text: 'Advanced' }, { value: 'Knitting', text: 'Knitting' },
##            { value: "Create New Section", text: "Create New Section" }]
##        };
##        document.addEventListener('DOMContentLoaded', () => {
##            const nameInput = document.getElementById('id_Name');
##            ////const sectionSelect = document.getElementById("Section{index}');
##            const originalOptions = Array.from(sectionSelect.options).map(opt => ({ value: opt.value, text: opt.text }));
##
##            function setOptions(opts) {
##                sect.innerHTML = '';
##                opts.forEach(({ value, text }) => {
##                    sect.appendChild(new Option(text, value));
##                });
##            }
##
##            nameInput.addEventListener('input', () => {
##                const name = nameInput.value.trim();
##
##                let matchedCategory = null;
##                if (labPatterns.et.some(rx => rx.test(name))) {
##                    matchedCategory = 'et';
##                } else if (labPatterns.stitch.some(rx => rx.test(name))) {
##                    matchedCategory = 'stitch';
##                } else if (labPatterns.beauty.some(rx => rx.test(name))) {
##                    matchedCategory = 'beauty';
##                }
##
##                if (matchedCategory) {
##                    setOptions(sectionChoices[matchedCategory]);
##                }
##                else {
##                    setOptions(originalOptions); // fallback if nothing matches
##                }
##            });
##
##        sect.forEach((select, index) => {
##            console.log("select running");
##            select.addEventListener("change", (event) => {
##                if (sect.value == "Create New Section" || sect.value == "New – New Section") {
##                    console.log(sect.value);
##                    let catlab = document.createElement("label");
##                    catlab.id = "catlab" + index;
##                    catlab.name = "catlab" + index;
##                    catlab.textContent = "Lab Category";
##                    let b = document.getElementById("Quantity_{index}");
##                    b.insertAdjacentElement('beforebegin', catlab);
##                    let catInp = document.createElement("input");
##                    catInp.setAttribute("id", "catinp" + index);
##                    catInp.setAttribute("name", "catinp" + index);
##                    catInp.value = nameInput.value.trim();
##                    catlab.insertAdjacentElement('afterend', catInp);
##                    let valLab = document.createElement("label");
##                    valLab.textContent = "Section";
##                    catInp.insertAdjacentElement('afterend', valLab);
##                    let valInp = document.createElement("input");
##                    valInp.setAttribute("id", "newsection" + index);
##                    valInp.setAttribute("name", "catinp" + index);
##                    valInp.value = "";
##                    valLab.insertAdjacentElement('afterend', valInp);
##                    ind++;
##                }
##            });
##        });
##        </script>'''
##    return JsonResponse({'form_html':js})

