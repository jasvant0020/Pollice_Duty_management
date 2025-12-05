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
    {'police_rank': 'Constable'},
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
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # ROLE BASED REDIRECTION
            if user.role == "developer":
                return redirect("admin:index")  # Use Django admin for developer

            elif user.role == "master_admin":
                return redirect("admin_dashboard")  # You can create dedicated dashboard later

            elif user.role == "super_admin":
                return redirect("admin_dashboard")

            elif user.role == "admin":
                return redirect("admin_dashboard")

            elif user.role == "gd_munsi":
                return redirect("dashboard")  # Munsi dashboard

            elif user.role == "field_staff":
                return redirect("user_profile")

            else:
                messages.error(request, "Unknown role assigned!")
                return redirect("login")

        else:
            messages.error(request, "Invalid credentials")
            return redirect("login")

    return render(request, "login_panel/login.html")


#------ Custom GD Munsi Panel Views ------
@role_required(["gd_munsi"])
def dashboard(request):
    context = {
        'role': 'Munsi',  # change to 'Admin' to test admin view
        'police_count': len(POLICE_PERSONNEL),
        'vvip_count': len(VVIP_PERSONS),
        'assignments_today': 2
    }
    return render(request, 'GD_munsi_panel/dashboard.html', context)

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
    return render(request, "admin_panel/admin_dashboard.html")

@role_required(["admin"])
def manage(request):
    return render(request, "admin_panel/manage.html")

@role_required(["admin"])
def police_hierarchy_table(request):
    return render(request, 'admin_panel/police_hierarchy_table.html')

@role_required(["admin"])
def manage_users(request):
    return render(request, "admin_panel/manage_users.html")

@role_required(["admin"])
def manage_security_categories(request):
    return render(request, "admin_panel/manage_security_categories.html")

@role_required(["admin"])
def manage_vvip(request):
    return render(request, "admin_panel/manage_vvip.html")

@role_required(["admin"])
def add_vvip(request):
    return render(request, "admin_panel/add_vvip.html")

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
@role_required(["admin"])
def manage_users(request):
    return render(request, 'admin_panel/manage_users.html')

@role_required(["admin", "super_admin"])
def add_user(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        gender = request.POST.get("gender")
        dob = request.POST.get("dob")
        role = request.POST.get("role")
        password = request.POST.get("password")

        user = User(
            username=email,
            email=email,
            first_name=name,
            role=role,
            created_by=request.user,   # AUTO SET
        )

        # --- Hierarchy rules ---
        if request.user.role == "admin":
            # Admin creates GD Munsi or Field staff
            if role == "gd_munsi":
                user.admin = request.user  # One admin → one GD Munsi
            elif role == "field_staff":
                gd_munsi_id = request.POST.get("gd_munsi_id")
                if gd_munsi_id:
                    gd_munsi = User.objects.get(id=gd_munsi_id)
                    user.gd_munsi = gd_munsi
                    user.admin = request.user  # also connect to the admin

        elif request.user.role == "gd_munsi":
            # GD Munsi creates only field staff
            if role == "field_staff":
                user.gd_munsi = request.user
                user.admin = request.user.admin  # connect back to parent admin

        elif request.user.role == "super_admin":
            # Super admin creates only admins
            pass  # no extra linkage needed

        elif request.user.role == "master_admin":
            # Master admin creates only super admins
            pass

        elif request.user.role == "developer":
            # Developer creates master admin
            pass

        user.set_password(password)
        user.save()

        return redirect("user_list")  # adjust as needed

    context = {
        "gd_munsi_list": User.objects.filter(role="gd_munsi"),
        "admin_list": User.objects.filter(role="admin"),
    }
    return render(request, "add_user.html", context)

@role_required(["admin"])
def edit_user(request, user_id):
    return render(request, 'admin_panel/edit_user.html')

@role_required(["admin"])
def delete_user(request, user_id):
    return redirect("manage_users")


#-------- CRUD opration by admin to Manage Police Categories ---------
@role_required(["admin"])
def manage_police_categories(request):
    return render(request, "admin_panel/manage_police_categories.html")

@role_required(["admin"])
def add_security_category(request):
    return render(request, 'admin_panel/add_security_category.html')

@role_required(["admin"])
def edit_security_category(request, category_id):
    return render(request, 'admin_panel/edit_security_category.html')

@role_required(["admin"])
def delete_security_category(request, category_id):
    return redirect('manage_police_categories')






def list_users(request):

    user = request.user

    if user.role == "developer":
        users = User.objects.all()

    elif user.role == "master_admin":
        users = User.objects.filter(role="super_admin")

    elif user.role == "super_admin":
        users = User.objects.filter(created_by=user)

    elif user.role == "admin":
        users = User.objects.filter(admin=user)

    elif user.role == "gd_munsi":
        users = User.objects.filter(gd_munsi=user)

    elif user.role == "field_staff":
        users = User.objects.filter(id=user.id)

    context = {
        "users": users,
    }

    return render(request, "user_list.html", context)





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