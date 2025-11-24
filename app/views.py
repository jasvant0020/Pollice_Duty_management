from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

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

#------Custom GD Munsi Panel Views------
def dashboard(request):
    context = {
        'role': 'Munsi',  # change to 'Admin' to test admin view
        'police_count': len(POLICE_PERSONNEL),
        'vvip_count': len(VVIP_PERSONS),
        'assignments_today': 2
    }
    return render(request, 'dashboard.html', context)


def police_list(request):
    context = {'police_personnel': POLICE_PERSONNEL}
    return render(request, 'police_list.html', context)


def vvip_list(request):
    context = {'vvip_persons': VVIP_PERSONS}
    return render(request, 'vvip_list.html', context)


def assign_duty(request):
    context = {
        'police_personnel': POLICE_PERSONNEL,
        'vvip_persons': VVIP_PERSONS
    }
    return render(request, 'assign_duty.html', context)

from django.shortcuts import render

#------Custom Admin Panel Views------
def admin_dashboard(request):
    return render(request, "admin_panel/admin_dashboard.html")

def manage_users(request):
    return render(request, "admin_panel/manage_users.html")

def manage_police_categories(request):
    return render(request, "admin_panel/manage_police_categories.html")

def manage_vvip_categories(request):
    return render(request, "admin_panel/manage_vvip_categories.html")


def user_dashboard(request):
        # ----- Dummy User -----
    user = {
        "full_name": "Officer Rohan Sharma",
        "rank": "Constable",
        "badge_number": "45231",
        "station": "Sector 14 Police Station"
    }

    # ----- Dummy Current Duty -----
    current_duty = {
        "location": "City Center Road",
        "partner": {"name": "Officer Rahul Singh"},
        "start_time": "10:00 AM",
        "end_time": "4:00 PM",
        "status": "Active",
    }

    # ----- Dummy Duty History -----
    duty_history = [
        {
            "date": "18 Nov 2025",
            "location": "Highway 21",
            "partner": {"name": "Officer Meena"},
            "status": "Completed",
        },
        {
            "date": "17 Nov 2025",
            "location": "Bus Stand Sector 5",
            "partner": {"name": "Officer Arjun"},
            "status": "Completed",
        },
    ]

    # ----- Dummy Notifications -----
    notifications = [
        {"text": "New duty assigned for tomorrow at 8 AM."},
        {"text": "Your leave request from 15 Nov approved."},
    ]

    # ----- Dummy Attendance -----
    attendance = {
        "checkin": "09:55 AM",
        "checkout": None,  # Means pending
    }

    context = {
        "user": user,
        "current_duty": current_duty,
        "duty_history": duty_history,
        "notifications": notifications,
        "attendance": attendance,
    }
    return render(request, "user_panel/user_dashboard.html",current_duty)

#-----Custom user Panel Views-----
def user_base(request):
    return render(request, "user_panel/user_base.html")
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