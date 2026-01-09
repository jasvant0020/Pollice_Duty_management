# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from .models import User
from .decorators import role_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from app.models import User
from app.decorators import role_required
from django.db.models import Q
from app.utils.user_counts import get_admin_staff_counts
from django.db.models import Count
from app.models import SecurityCategory





# Dummy data for testing frontend
POLICE_PERSONNEL = [
    {'name': 'Bhanu Kumar', 'category': 'Inspector', 'status': 'Available'},
    {'name': 'Rudra Singh', 'category': 'Constable', 'status': 'Assigned'},
    {'name': 'Raju Rajput', 'category': 'SP', 'status': 'Available'},
    {'name': 'Aman Singh', 'category': 'Constable', 'status': 'Assigned'},
    {'name': 'Aniket Jha', 'category': 'SP', 'status': 'Available'},
]

VVIP_PERSONS = [
    {'name': 'Mr. President', 'category': 'High', 'location': 'City Hall'},
    {'name': 'Ambassador Lee', 'category': 'Medium', 'location': 'Embassy'},
    {'name': 'Mr. President', 'category': 'High', 'location': 'Sansad'},
    {'name': 'CM Yogi', 'category': 'Medium', 'location': 'National Park'},
]

role = [
    {'role': 'GD Munsi'},
    {'role': 'User'}
]

police_rank = [
    {'police_rank': 'Director General of Police (DGP)'},
    {'police_rank': 'Additional Director General of Police (ADGP)'},
    {'police_rank': 'Inspector General of Police (IGP)'},
    {'police_rank': 'Deputy Inspector General of Police (DIG)'},
    {'police_rank': 'Superintendent of Police (SP)'},
    {'police_rank': 'Additional Superintendent of Police (Addl SP)'},
    {'police_rank': 'Deputy Superintendent of Police (DSP) / Assistant Commissioner of Police (ACP)'},
    {'police_rank': 'Inspector'},  
    {'police_rank': 'Sub-Inspector (SI)'},
    {'police_rank': 'Assistant Sub-Inspector (ASI)'},
    {'police_rank': 'Head Constable (HC)'},
    {'police_rank': 'Constable'}
]


category = [
    {'category': 'X Security'},
    {'category': 'Y Security'},
    {'category': 'Y+ Security'},
    {'category': 'Z Security'},
    {'category': 'Z+ Security'},
    {'category': 'SPG Security'},  # Special Protection Group (highest level, for PM of India)
    {'category':'other'}
]


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Get user by email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, "Email not found!")
            return redirect("login")

        # Authenticate using username + password
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # ROLE BASED REDIRECTION
            if user.role == "developer":
                return redirect("admin:index")

            elif user.role in ["master_admin", "super_admin", "admin"]:
                return redirect("admin_dashboard")

            elif user.role == "gd_munsi":
                return redirect("dashboard")

            elif user.role == "field_staff":
                return redirect("user_profile")

            else:
                messages.error(request, "Unknown role assigned!")
                return redirect("login")

        else:
            messages.error(request, "Invalid credentials")
            return redirect("login")

    return render(request, "login_panel/login.html")

def logout_view(request):
    if request.method == 'POST':
        logout(request)
    messages.success(request,"you have been logged out successfully!")
    return redirect('login')


#------ Custom GD Munsi Panel Views ------
@login_required
def dashboard(request):
    role = request.user.role

    # Developer Dashboard
    if role == "developer":
        return render(request, "developer/dashboard.html", {
            "total_users": User.objects.count(),
            "master_admin_count": User.objects.filter(role="master_admin").count()
        })

    # Master Admin Dashboard
    if role == "master_admin":
        return render(request, "master_admin/dashboard.html", {
            "super_admin_count": User.objects.filter(role="super_admin").count(),
        })

    # Super Admin Dashboard
    if role == "super_admin":
        return render(request, "super_admin/dashboard.html", {
            "admin_count": User.objects.filter(role="admin", created_by=request.user).count(),
        })

    # Admin Dashboard
    if role == "admin":
        return render(request, "admin_panel/admin_dashboard.html", {
            "gd_munsi_count": User.objects.filter(role="gd_munsi", admin=request.user).count(),
            "field_staff_count": User.objects.filter(role="field_staff", admin=request.user).count(),
        })

    # GD Munsi Dashboard
    if role == "gd_munsi":
        return render(request, "GD_munsi_panel/dashboard.html", {
            "field_staff_count": User.objects.filter(gd_munsi=request.user).count(),
        })

    # Field Staff Dashboard
    if role == "field_staff":
        return render(request, "user_panel/user_profile.html", {
            "user_data": request.user
        })


@role_required(["gd_munsi"])
def police_list(request):
    context = {'police_personnel': POLICE_PERSONNEL}
    return render(request, 'GD_munsi_panel/police_list.html', context)

@role_required(["gd_munsi"])
def vvip_list(request):
    context = {'vvip_persons': VVIP_PERSONS}
    return render(request, 'GD_munsi_panel/vvip_list.html', context)

@role_required(["gd_munsi"])
def assign_duty(request):
    context = {
        'police_personnel': POLICE_PERSONNEL,
        'vvip_persons': VVIP_PERSONS
    }
    return render(request, 'GD_munsi_panel/assign_duty.html', context)

#------ Custom Admin Panel Views ------
@role_required(["admin"])
def admin_dashboard(request):
    admin_user = request.user

    # Get all counts from utility
    staff_counts = get_admin_staff_counts(request.user)

    context = {
        **staff_counts,   # unpack counts
    }
    return render(request, "admin_panel/admin_dashboard.html", context)

@role_required(["admin"])
def manage(request):
    return render(request, "admin_panel/manage.html")

@role_required(["admin"])
def police_hierarchy_table(request):
    admin_user = request.user

    # Fetch only ranks that exist in DB for this admin
    rank_qs = (
        User.objects
        .filter(
            admin=admin_user,
            rank__isnull=False
        )
        .exclude(rank="")
        .values("rank")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    rank_status = []

    for r in rank_qs:
        count = r["count"]

        # Dynamic status logic
        if count >= 10:
            status = "Healthy"
            badge_color = "green"
        elif count >= 5:
            status = "Moderate"
            badge_color = "yellow"
        else:
            status = "Critical"
            badge_color = "red"

        rank_status.append({
            "rank": r["rank"],
            "count": count,
            "status": status,
            "badge_color": badge_color,
        })

    context = {
        "rank_status": rank_status
    }

    return render(request, "admin_panel/police_hierarchy_table.html", context)


@role_required(["admin", "Admin"])
def manage_users(request):
    admin_user = request.user

    # Get all officers related to this admin
    officers = User.objects.filter(
        Q(role="gd_munsi", admin=admin_user) |             # GD Munsis under this admin
        Q(role="field_staff", gd_munsi__admin=admin_user) |  # Field staff under GD Munsis of this admin
        Q(created_by=admin_user)                             # Users directly created by admin
    ).distinct().order_by('role', 'username')

    # Debugging: print all officers in console
    print("Total officers:", officers.count())
    for o in officers:
        print(f"{o.username} | role: {o.role} | admin: {o.admin} | gd_munsi: {o.gd_munsi} | created_by: {o.created_by}")

    return render(request, "admin_panel/manage_users.html", {"officers": officers})

# @role_required(["admin"])
# def manage_security_categories(request):
#     return render(request, "admin_panel/manage_security_categories.html")

@role_required(["admin"])
def manage_vvip(request):
    return render(request, "admin_panel/manage_vvip.html")

from app.models import User, SecurityCategory
from django.contrib.auth.hashers import make_password
from django.contrib import messages

@role_required(["admin"])
def add_vvip(request):

    categories = SecurityCategory.objects.filter(admin=request.user)
    context = {
            "category": categories,   # 👈 pass to template
        }

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        gender = request.POST.get("gender")
        dob = request.POST.get("dob")

        designation = request.POST.get("designation")
        custom_designation = request.POST.get("custom_designation")
        category_id = request.POST.get("category")  # 👈 selected category

        final_designation = (
            custom_designation if designation == "other" else designation
        )

        category_obj = SecurityCategory.objects.get(
            id=category_id,
            admin=request.user  # 🔒 security check
        )

        User.objects.create(
            username=email,
            email=email,
            password=make_password(password),
            first_name=name,
            gender=gender.lower(),
            dob=dob or None,
            rank=final_designation,
            role="vvip",
            admin=request.user,
            created_by=request.user,
            category=category_obj  # 👈 assign category
        )

        messages.success(request, "VVIP created successfully")
        return redirect("manage_vvip")

    return render(request,"admin_panel/add_vvip.html",context)

@role_required(["admin"])
def edit_vvip(request, vvip_id):
    return render(request, "admin_panel/edit_vvip.html")

@role_required(["admin"])
def delete_vvip(request, vvip_id):
    return redirect('manage_vvip_categories')


#----- Custom user Panel Views -----
@role_required(["field_staff"])
def user_assign_duty(request):
    return render(request, "user_panel/user_assign_duty.html")

@role_required(["field_staff"])
def request_application_box(request):
    return render(request, "user_panel/request_application_box.html")

@role_required(["field_staff"])
def duty_history(request):
    return render(request, "user_panel/duty_history.html")

@role_required(["field_staff"])
def Notifications(request):
    return render(request, "user_panel/Notifications.html")

@role_required(["field_staff"])
def attendance_panel(request):
    return render(request, "user_panel/attendance_panel.html")

@role_required(["field_staff"])
def user_profile(request):
    return render(request, "user_panel/user_profile.html")


#-------- CRUD opration by admin to manage user ---------
@role_required(["developer", "master_admin", "super_admin", "admin", "gd_munsi"])
def add_user(request):

    user = request.user
    context = {
        'police_rank':police_rank,
    }

    # -----------------------------------------------------
    # 1️⃣ Determine allowed roles for the logged-in user
    # -----------------------------------------------------
    if user.role == "developer":
        allowed_roles = ["master_admin"]

    elif user.role == "master_admin":
        allowed_roles = ["super_admin"]

    elif user.role == "super_admin":
        allowed_roles = ["admin"]

    elif user.role == "admin":
        if User.objects.filter(role="gd_munsi", admin=user).exists():
            allowed_roles = ["field_staff"]
        else:
            allowed_roles = ["gd_munsi", "field_staff"]

    elif user.role == "gd_munsi":
        allowed_roles = ["field_staff"]

    else:
        allowed_roles = []

    context["allowed_roles"] = allowed_roles

    # -----------------------------------------------------
    # 2️⃣ Provide GD Munsi list only when needed
    # -----------------------------------------------------
    if user.role == "admin":
        context["gd_munsi_list"] = User.objects.filter(role="gd_munsi", admin=user)

    elif user.role == "gd_munsi":
        context["gd_munsi_list"] = [user]   # force assign to itself

    else:
        context["gd_munsi_list"] = []

    # -----------------------------------------------------
    # 3️⃣ Handle user creation
    # -----------------------------------------------------
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        gender = request.POST.get("gender")
        dob = request.POST.get("dob")
        rank = request.POST.get("rank")
        role = request.POST.get("role")
        password = request.POST.get("password")

        # -----------------------------------------------------
        # ❌ BLOCK MULTIPLE GD CREATION BY SAME ADMIN
        # -----------------------------------------------------
        if user.role == "admin" and role == "gd_munsi":
            gd_exists = User.objects.filter(
                role="gd_munsi",
                admin=user
            ).exists()

            if gd_exists:
                messages.error(
                    request,
                    "You already have a GD Munsi. Only one GD Munsi is allowed per Admin."
                )
                return redirect("manage_users")


        new_user = User(
            username=email,
            email=email,
            first_name=name,
            phone=phone,
            gender=gender,
            dob=dob,
            role=role,
            rank=rank,
            created_by=request.user,
        )


        # HIERARCHY LOGIC
        if user.role == "admin":
            if role == "gd_munsi":
                new_user.admin = user  

            elif role == "field_staff":
                gd_id = request.POST.get("gd_munsi_id")
                if gd_id:
                    gm = User.objects.get(id=gd_id)
                    new_user.gd_munsi = gm
                    new_user.admin = user

        elif user.role == "gd_munsi":
            if role == "field_staff":
                new_user.gd_munsi = user
                new_user.admin = user.admin

        # Higher hierarchy don't need linking
        new_user.set_password(password)
        new_user.save()

        if role == "field_staff":
            messages.success(request, f"{name} has been added as an Field Staff successfully!")
            return redirect("manage_users")
        elif role == "gd_munsi":
            messages.success(request, f"{name} has been added as a GD Munsi successfully!")
            return redirect("manage_users")

        # return redirect("admin_panel/user_list")

    return render(request, "admin_panel/add_user.html", context)

@role_required(["developer", "master_admin", "super_admin", "admin", "gd_munsi"])
def edit_user(request, user_id):

    user = request.user                          # logged in user
    officer = User.objects.get(id=user_id)       # user being edited
    context = {
        'police_rank':police_rank,
    }

    # -----------------------------------------------------
    # Determine allowed roles based on logged-in user
    # -----------------------------------------------------
    if user.role == "developer":
        allowed_roles = ["master_admin"]

    elif user.role == "master_admin":
        allowed_roles = ["super_admin"]

    elif user.role == "super_admin":
        allowed_roles = ["admin"]

    elif user.role == "admin":
        if officer.role == "gd_munsi":
            allowed_roles = ["gd_munsi"]
        else:
            allowed_roles = ["field_staff"]

    elif user.role == "gd_munsi":
        allowed_roles = ["field_staff"]

    else:
        allowed_roles = []

    context["role"] = allowed_roles
    context["officer"] = officer

    # -----------------------------------------------------
    # Provide GD Munsi dropdown logic
    # -----------------------------------------------------
    if user.role == "admin":
        context["gd_munsi_list"] = User.objects.filter(role="gd_munsi", admin=user)

    elif user.role == "gd_munsi":
        context["gd_munsi_list"] = [user]

    else:
        context["gd_munsi_list"] = []

    # -----------------------------------------------------
    # Handle UPDATE
    # -----------------------------------------------------
    if request.method == "POST":
        officer.first_name = request.POST.get("name")
        officer.email = request.POST.get("email")
        officer.username = request.POST.get("email")
        officer.gender = request.POST.get("gender")
        officer.dob = request.POST.get("dob")
        officer.rank = request.POST.get("rank")
        officer.phone = request.POST.get("phone")

        new_role = request.POST.get("role")

        # -----------------------------------------------------
        # ❌ BLOCK MULTIPLE GD ASSIGNMENT ON EDIT
        # -----------------------------------------------------
        if user.role == "admin" and new_role == "gd_munsi":
            gd_exists = User.objects.filter(
                role="gd_munsi",
                admin=user
            ).exclude(id=officer.id).exists()

            if gd_exists:
                messages.error(
                    request,
                    "You already have a GD Munsi. Cannot assign another."
                )
                return redirect("edit_user", user_id=user_id)


        # ----------------------------
        # Password Update
        # ----------------------------
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password:
            if password == confirm_password:
                officer.set_password(password)
            else:
                messages.error(request, "Passwords do not match!")
                return redirect("edit_user", user_id=user_id)

        # ----------------------------
        # Hierarchy Logic
        # ----------------------------
        if user.role == "admin":

            if new_role == "gd_munsi":
                officer.gd_munsi = None
                officer.admin = user

            elif new_role == "field_staff":
                gd_id = request.POST.get("gd_munsi_id")
                if gd_id:
                    gm = User.objects.get(id=gd_id)
                    officer.gd_munsi = gm
                    officer.admin = user

        elif user.role == "gd_munsi":
            if new_role == "field_staff":
                officer.gd_munsi = user
                officer.admin = user.admin

        # Update role last
        officer.role = new_role

        officer.save()

        if officer.role == "field_staff":
            messages.success(request, f"{officer.first_name} as {officer.role} has been updated successfully!")
            return redirect("manage_users")
        elif officer.role == "gd_munsi":
            messages.success(request, f"{officer.first_name} as {officer.role} has been updated successfully!")
            return redirect("manage_users")
        # messages.success(request, "User updated successfully!")
        # return redirect("manage_users")

    return render(request, "admin_panel/edit_user.html", context)


@role_required(["admin"])
def delete_user(request, user_id):
    return redirect("manage_users")


#-------- CRUD opration by admin to Manage Police Categories ---------
@role_required(["admin"])
def manage_security_categories(request):
    categories = SecurityCategory.objects.filter(admin_id=request.user.id).order_by("-created_at")

    return render(request,"admin_panel/manage_security_categories.html",{"categories": categories})


@role_required(["admin"])
def add_security_category(request):

    context = {
        'police_rank':police_rank,
        'category' :category,
    }

    # 🔐 Only categories created by THIS admin
    # categories = SecurityCategory.objects.filter(admin=request.user)

    if request.method == "POST":

        category_name = request.POST.get("category_name")
        custom_category = request.POST.get("custom_category", "").strip()

        # Handle custom category
        if category_name == "other":
            category_name = custom_category

        if not category_name:
            messages.error(request, "Category name is required.")
            return redirect(request.path)

        # Prevent duplicate category for same admin
        if SecurityCategory.objects.filter(
            name__iexact=category_name,
            admin_id=request.user.id
        ).exists():
            messages.error(request, "This category already exists.")
            return redirect(request.path)

        personnel_by_rank = {}
        total_personnel = 0

        # Collect rank-wise data
        for key, value in request.POST.items():
            if key.startswith("rank_") and value:
                try:
                    count = int(value)
                    if count > 0:
                        rank_name = key.replace("rank_", "")
                        personnel_by_rank[rank_name] = count
                        total_personnel += count
                except ValueError:
                    continue

        if total_personnel == 0:
            messages.error(
                request,
                "Please enter personnel for at least one rank."
            )
            return redirect(request.path)

        # ✅ Create category (admin-owned)
        SecurityCategory.objects.create(
            name=category_name,
            personnel_by_rank=personnel_by_rank,
            total_personnel=total_personnel,
            admin_id=request.user.id
        )

        messages.success(request,"Security category added successfully.")
        return redirect("manage_security_categories")

    return render(request,"admin_panel/add_security_category.html",context)

@role_required(["admin"])
def edit_security_category(request, category_id):

    category = get_object_or_404(
        SecurityCategory,
        id=category_id,
        admin=request.user   # 🔐 admin scoped
    )

    if request.method == "POST":
        personnel_by_rank = {}
        total_personnel = 0

        for key, value in request.POST.items():
            if key.startswith("rank_") and value:
                try:
                    count = int(value)
                    if count > 0:
                        rank_name = key.replace("rank_", "")
                        personnel_by_rank[rank_name] = count
                        total_personnel += count
                except ValueError:
                    continue

        if total_personnel == 0:
            messages.error(request, "At least one rank is required.")
            return redirect(request.path)

        category.personnel_by_rank = personnel_by_rank
        category.total_personnel = total_personnel
        category.save()

        messages.success(request, "Security category updated successfully.")
        return redirect("manage_security_categories")

    context = {
        "category": category,
        "police_rank": police_rank,  # all available ranks
    }
    return render(request, "admin_panel/edit_security_category.html", context)


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@role_required(["admin"])
def delete_security_category(request, category_id):
    category = get_object_or_404(
        SecurityCategory,
        id=category_id,
        admin=request.user   # 🔐 admin scoped
    )

    if request.method == "POST":
        category.delete()
        messages.success(request, "Security category deleted successfully.")
        return redirect("manage_security_categories")

    # ❌ Do not allow GET delete
    messages.error(request, "Invalid delete request.")
    return redirect("manage_security_categories")










#----- firebase push notification -----
def showFirebaseJS(request):
    data='importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-app.js");' \
         'importScripts("https://www.gstatic.com/firebasejs/8.2.0/firebase-messaging.js"); ' \
         'var firebaseConfig = {' \
         '        apiKey: "AIzaSyCEVCeD8QbdOFG1MMk0LKi6FNAoGY3cL9E",' \
         '        authDomain: "push-notification-cc870.firebaseapp.com",' \
         '        databaseURL: "",' \
         '        projectId: "push-notification-cc870",' \
         '        storageBucket: "push-notification-cc870.firebasestorage.app",' \
         '        messagingSenderId: "595457578638",' \
         '        appId: "1:595457578638:web:42a5525e4f017186e4dbdf",' \
         '        measurementId: "G-E476M6ETBE"' \
         ' };' \
         'firebase.initializeApp(firebaseConfig);' \
         'const messaging=firebase.messaging();' \
         'messaging.setBackgroundMessageHandler(function (payload) {' \
         '    console.log(payload);' \
         '    const notification=JSON.parse(payload);' \
         '    const notificationOption={' \
         '        body:notification.body,' \
         '        icon:notification.icon' \
         '    };' \
         '    return self.registration.showNotification(payload.notification.title,notificationOption);' \
         '});'

    return HttpResponse(data,content_type="text/javascript")