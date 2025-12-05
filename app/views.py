# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from .models import CustomUser





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

#------ Custom Admin Panel Views ------
def admin_dashboard(request):
    return render(request, "admin_panel/admin_dashboard.html")
def manage(request):
    return render(request, "admin_panel/manage.html")
def police_hierarchy_table(request):
    return render(request, 'admin_panel/police_hierarchy_table.html')
def manage_users(request):
    return render(request, "admin_panel/manage_users.html")
def manage_security_categories(request):
    return render(request, "admin_panel/manage_security_categories.html")
def manage_vvip(request):
    return render(request, "admin_panel/manage_vvip.html")
def add_vvip(request):
    return render(request, "admin_panel/add_vvip.html")
def edit_vvip(request, vvip_id):
    return render(request, "admin_panel/edit_vvip.html")
def delete_vvip(request, vvip_id):
    return redirect('manage_vvip_categories')


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


#-------- CRUD opration by admin to manage user ---------

def manage_users(request):
    return render(request, 'admin_panel/manage_users.html')
def add_user(request):
    return render(request, "admin_panel/add_user.html")
def edit_user(request, user_id):
    return render(request, 'admin_panel/edit_user.html')
def delete_user(request, user_id):
    return redirect("manage_users")


#-------- CRUD opration by admin to Manage Police Categories ---------
def manage_police_categories(request):
    return render(request, "admin_panel/manage_police_categories.html")
def add_security_category(request):
    return render(request, 'admin_panel/add_security_category.html')
def edit_security_category(request, category_id):
    return render(request, 'admin_panel/edit_security_category.html')
def delete_security_category(request, category_id):
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