from django.shortcuts import render

# Create your views here.

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

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

def admin_dashboard(request):
    return render(request, "admin_panel/admin_dashboard.html")

def manage_users(request):
    return render(request, "admin_panel/manage_users.html")

def manage_police_categories(request):
    return render(request, "admin_panel/manage_police_categories.html")

def manage_vvip_categories(request):
    return render(request, "admin_panel/manage_vvip_categories.html")
