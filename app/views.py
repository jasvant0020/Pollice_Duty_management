from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.shortcuts import render, redirect
from django.contrib import messages
from app.services.officer_stats import get_rank_status




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
    {'role': 'Admin'},
    {'role': 'GD Munsi'},
    {'role': 'User'}
]

rank = [
    {'rank': 'Director General of Police (DGP)'},
    {'rank': 'Additional Director General of Police (ADGP)'},
    {'rank': 'Inspector General of Police (IGP)'},
    {'rank': 'Deputy Inspector General of Police (DIG)'},
    {'rank': 'Superintendent of Police (SP)'},
    {'rank': 'Additional Superintendent of Police (Addl SP)'},
    {'rank': 'Deputy Superintendent of Police (DSP) / Assistant Commissioner of Police (ACP)'},
    {'rank': 'Inspector'},  
    {'rank': 'Sub-Inspector (SI)'},
    {'rank': 'Assistant Sub-Inspector (ASI)'},
    {'rank': 'Head Constable (HC)'},
    {'rank': 'Constable'},
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


#------ Custom GD Munsi Panel Views ------
def dashboard(request):
    context = {
        'role': 'Munsi',  # change to 'Admin' to test admin view
        'police_count': len(POLICE_PERSONNEL),
        'vvip_count': len(VVIP_PERSONS),
        'assignments_today': 2
    }
    return render(request, 'GD_munsi_panel/dashboard.html', context)


def police_list(request):
    context = {'police_personnel': POLICE_PERSONNEL}
    return render(request, 'GD_munsi_panel/police_list.html', context)


def vvip_list(request):
    context = {'vvip_persons': VVIP_PERSONS}
    return render(request, 'GD_munsi_panel/vvip_list.html', context)


def assign_duty(request):
    context = {
        'police_personnel': POLICE_PERSONNEL,
        'vvip_persons': VVIP_PERSONS
    }
    return render(request, 'GD_munsi_panel/assign_duty.html', context)

from django.shortcuts import render

#------ Custom Admin Panel Views ------
def admin_dashboard(request):
    return render(request, "admin_panel/admin_dashboard.html")
def manage(request):
    return render(request, "admin_panel/manage.html")
def police_hierarchy_table(request):
    context = {
        'rank_status': get_rank_status()
    }
    return render(request, 'admin_panel/police_hierarchy_table.html', context)
def manage_users(request):
    return render(request, "admin_panel/manage_users.html")
def manage_police_categories(request):
    return render(request, "admin_panel/manage_police_categories.html")
def manage_vvip_categories(request):
    return render(request, "admin_panel/manage_vvip_categories.html")


#----- Custom user Panel Views -----
def user_assign_duty(request):
    return render(request, "user_panel/user_assign_duty.html")
def request_application_box(request):
    return render(request, "user_panel/request_application_box.html")
def duty_history(request):
    return render(request, "user_panel/duty_history.html")
def Notifications(request):
    return render(request, "user_panel/Notifications.html")
def attendance_panel(request):
    return render(request, "user_panel/attendance_panel.html")
def user_profile(request):
    return render(request, "user_panel/user_profile.html")


# views.py
def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # If you use username instead of email:
        # user = authenticate(request, username=email, password=password)

        # If your User model uses email as username:
        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)

            # Redirect based on user role
            if user.role == "custom_admin":
                return redirect("admin_dashboard")   # Custom admin

            elif user.role == "gd_munsi":
                return redirect("dashboard")         # GD Munsi Panel

            else:
                return redirect("user_profile")      # Normal user panel

        else:
            messages.error(request, "Invalid credentials")

    return render(request, "login_panel/login.html")


#-------- CRUD opration by admin to manage user ---------
from django.shortcuts import render, redirect, get_object_or_404
from .models import Officer

def manage_users(request):
    officers = Officer.objects.all()
    return render(request, 'admin_panel/manage_users.html', {'officers': officers})

# Add User
def add_user(request):
    context = {
        'role': role,
        'rank': rank
    }

    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        gender = request.POST.get('gender')
        dob = request.POST.get('dob')

        selected_rank = request.POST.get('rank')
        selected_role = request.POST.get('role')

        # Basic password match validation
        if password != confirm_password:
            context['error'] = "Password and Confirm Password do not match."
            return render(request, 'admin_panel/add_user.html', context)

        # Create Officer record
        Officer.objects.create(
            name=name,
            email=email,
            password=password,  # (later you should hash this)
            gender=gender,
            dob=dob,
            rank=selected_rank,
            role=selected_role
        )

        return redirect('manage_users')

    return render(request, 'admin_panel/add_user.html', context)


# Edit User
def edit_user(request, user_id):
    officer = get_object_or_404(Officer, id=user_id)
    context = {
        'officer': officer,
        'role': role,
        'rank': rank
    }

    if request.method == "POST":
        # Update basic fields
        officer.name = request.POST.get('name')
        officer.email = request.POST.get('email')
        officer.gender = request.POST.get('gender')
        officer.dob = request.POST.get('dob')
        officer.rank = request.POST.get('rank')
        officer.role = request.POST.get('role')

        # Update password only if provided and matches confirm
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password:
            if password == confirm_password:
                officer.password = password  # Later you can hash it
            else:
                context['error'] = "Password and Confirm Password do not match."
                return render(request, 'admin_panel/edit_user.html', context)

        officer.save()
        return redirect('manage_users')

    return render(request, 'admin_panel/edit_user.html', context)


# Delete User
def delete_user(request, user_id):
    officer = get_object_or_404(Officer, id=user_id)
    officer.delete()
    return redirect('manage_users')
    


#-------- CRUD opration by admin to Manage Police Categories ---------

from django.shortcuts import render, redirect, get_object_or_404
from .models import SecurityCategory, Officer

def manage_police_categories(request):
    categories = SecurityCategory.objects.all()
    return render(request, "admin_panel/manage_police_categories.html", {'categories': categories})


def add_security_category(request):
    ranks = Officer.objects.values_list('rank', flat=True).distinct()
    
    context = {
        'ranks': ranks,
        'category': category  # Make sure 'category' is defined earlier
    }

    if request.method == "POST":
        selected_category = request.POST.get('category_name')
        custom_category = request.POST.get('custom_category')
        category_name = custom_category.strip() if custom_category else selected_category

        # --- VALIDATION: Duplicate category check ---
        if category_name:
            if SecurityCategory.objects.filter(name__iexact=category_name).exists():
                messages.error(request, f"Category '{category_name}' already exists!")
                return redirect('add_security_category')

        # --- Decide final category name ---
        if selected_category == "other" and custom_category:
            name = custom_category
        else:
            name = selected_category

        # --- Collect personnel by rank ---
        personnel_by_rank = {}
        for rank in ranks:
            count = request.POST.get(rank, '0')  # default to 0 if empty
            try:
                count = int(count)
            except ValueError:
                count = 0
            if count > 0:  # only save ranks with personnel > 0
                personnel_by_rank[rank] = count

        # --- Calculate total personnel ---
        total_personnel = sum(personnel_by_rank.values())

        # --- Save to DB ---
        SecurityCategory.objects.create(
            name=name,
            total_personnel=total_personnel,
            personnel_by_rank=personnel_by_rank
        )

        messages.success(request, f"Category '{name}' added successfully!")
        return redirect('manage_police_categories')

    return render(request, 'admin_panel/add_security_category.html', context)


def edit_security_category(request, category_id):
    category = get_object_or_404(SecurityCategory, id=category_id)
    ranks = Officer.objects.values_list('rank', flat=True).distinct()

    context = {
        'category': category,
        'ranks': ranks
    }

    if request.method == "POST":
        category.name = request.POST.get('name')

        # Collect personnel by rank, only save ranks with >0 personnel
        personnel_by_rank = {}
        for rank in ranks:
            count = request.POST.get(rank, '0')
            try:
                count = int(count)
            except ValueError:
                count = 0
            if count > 0:
                personnel_by_rank[rank] = count

        # Update total personnel from non-zero ranks
        category.total_personnel = sum(personnel_by_rank.values())
        category.personnel_by_rank = personnel_by_rank
        category.save()

        messages.success(request, f"Category '{category.name}' updated successfully!")
        return redirect('manage_police_categories')

    return render(request, 'admin_panel/edit_security_category.html', context)


def delete_security_category(request, category_id):
    category = get_object_or_404(SecurityCategory, id=category_id)
    category.delete()
    messages.success(request, f"' {category.name} ' deleted successfully!")
    return redirect('manage_police_categories')






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