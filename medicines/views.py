from .models import Medication, DoseLog, PushSubscription, GoogleCredentials,OTP
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.base_user import BaseUserManager
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
import json
from datetime import date, datetime, timedelta

from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from django.core.mail import send_mail
import random
import string
from django.utils.crypto import get_random_string

# Google API imports
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow



from .models import UserProfile, Appointment, User

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django import forms


logger = logging.getLogger(__name__)


# ===========================
# INTERNAL HELPER FUNCTIONS (UPDATED)
# ===========================

def _delete_google_events(user, event_ids):
    """Internal helper to safely delete a list of Google Calendar events."""
    if not event_ids:
        return 0
        
    try:
        creds_obj = GoogleCredentials.objects.get(user=user)
        creds = Credentials(
            token=creds_obj.access_token,
            refresh_token=creds_obj.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=creds_obj.client_id,
            client_secret=creds_obj.client_secret,
            scopes=["https://www.googleapis.com/auth/calendar.events"]
        )
    except GoogleCredentials.DoesNotExist:
        # Cannot delete without credentials
        return 0

    service = build('calendar', 'v3', credentials=creds)
    deleted_count = 0
    
    for event_id in event_ids:
        try:
            # Note: For recurring events, deleting the master event deletes all instances.
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            deleted_count += 1
        except Exception as e:
            # Log the error but continue trying to delete other events
            # Errors can occur if an event was manually deleted by the user.
            print(f"Error deleting event {event_id} during update/delete: {e}")
            
    return deleted_count


def _create_google_events(user, med, service=None):
    """
    Internal helper to create recurring Google Calendar events for a medication.
    Returns: list of new Google Event IDs (master recurring event IDs).
    """
    new_event_ids = []
    
    try:
        if not service:
            creds_obj = GoogleCredentials.objects.get(user=user)
            creds = Credentials(
                token=creds_obj.access_token,
                refresh_token=creds_obj.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=creds_obj.client_id,
                client_secret=creds_obj.client_secret,
                scopes=["https://www.googleapis.com/auth/calendar.events"]
            )
            service = build('calendar', 'v3', credentials=creds)
    except GoogleCredentials.DoesNotExist:
        raise
    
    # Logic for recurrence (RCULE) based on frequency
    # Assuming 'daily' is a valid value for med.frequency
    if med.frequency == 'daily':
        # Default recurrence is daily, indefinitely.
        # You could also add an UNTIL date (e.g., 1 year from now) for performance.
        recurrence_rule = 'RRULE:FREQ=DAILY'
    elif med.frequency == 'weekly':
        # You might need a more complex form for weekly, but for simplicity, we use the rule.
        # Real-world app may need a field for 'day of week'.
        recurrence_rule = 'RRULE:FREQ=WEEKLY'
    else:
        # If frequency is not recognized, default to daily for 30 days
        until_date = (date.today() + timedelta(days=30)).strftime('%Y%m%dT000000Z')
        recurrence_rule = f'RRULE:FREQ=DAILY;UNTIL={until_date}' 
    
    today = timezone.localdate()

    for t_str in med.times:
        time_obj = datetime.strptime(t_str, "%H:%M").time()
        # Events must start from the earliest time possible today in the user's timezone (Asia/Kolkata)
        start_datetime_local = datetime.combine(today, time_obj)
        start_datetime = timezone.make_aware(start_datetime_local)
        
        # End time is 30 minutes later
        end_datetime = start_datetime + timedelta(minutes=30) 

        event = {
            'summary': f'Medication: {med.pill_name} ({med.dosage} mg)',
            'description': f'Time to take your {med.pill_name} dose.',
            'start': {'dateTime': start_datetime.isoformat(), 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': end_datetime.isoformat(), 'timeZone': 'Asia/Kolkata'},
            # Add the recurrence rule to make it a recurring event
            'recurrence': [recurrence_rule],
        }

        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        new_event_ids.append(created_event.get('id'))

    return new_event_ids


def signup_view(request):
    """
    Renders the signup page gateway.
    Handles GET requests to show UI (Manual form + Google Button).
    Google initiation happens directly via the template tag.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, "medicines/signup.html")

def otp_signup_request(request):
    """Step 1: Get manual form data and send OTP. Targeted by form action."""
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email', '').lower()
        password = request.POST.get('password')
        
        # 1. Validation before logic execution
        if not all([username, email, password]):
            messages.error(request, "All magical fields are required!")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('signup')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered. Try Logging in.")
            return redirect('login') 

        # 2. Generate and Save OTP Registry
        otp_code = OTP.generate_otp()
        OTP.objects.update_or_create(email=email, defaults={'otp_code': otp_code})
        
        # 3. Secure Session Storage
        request.session['reg_username'] = username
        request.session['reg_email'] = email
        request.session['reg_password'] = password 

        # 4. Email Delivery
        try:
            send_mail(
                'MediMimes: Verification Code',
                f'Your magic code: {otp_code}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
            )
            messages.success(request, f"Verification code sent to {email}.")
            return redirect('otp_verify')
        except Exception:
            messages.error(request, "Courier failed. Check email settings.")
            return redirect('signup')

    return redirect('signup')

def otp_verify(request):
    """Step 2: Verify OTP and complete secure user registration."""
    email = request.session.get('reg_email')
    username = request.session.get('reg_username')
    raw_password = request.session.get('reg_password')

    if not email:
        messages.error(request, "Session expired. Please start registration again.")
        return redirect('otp_signup_request')

    if request.method == "POST":
        submitted_otp = request.POST.get('otp_code')
        
        try:
            otp_entry = OTP.objects.get(email=email)
        except OTP.DoesNotExist:
            return redirect('otp_signup_request')

        if not otp_entry.is_valid():
            messages.error(request, "The code has expired.")
            otp_entry.delete()
            return redirect('otp_signup_request')

        if submitted_otp == otp_entry.otp_code:
            
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=raw_password # Auto-hashed by Django
            )
            user.save()
            
            # 3. Clean up session and log in
            otp_entry.delete()
            del request.session['reg_username']
            del request.session['reg_email']
            del request.session['reg_password']
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Registration successful! Welcome to MediMimes.")
            return redirect('dashboard') 

        else:
            messages.error(request, "Invalid verification code.")
    
    return render(request, "medicines/otp_verify.html", {'email': email})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        intended_role = request.POST.get('intended_role') # Capture the selection
        
        user = authenticate(request, username=username, password=password)
        if user:
            
            try:
                actual_role = user.profile.role
            except Exception:
                actual_role = 'user' # Fallback for base users

            # Verification Logic
            if intended_role == 'admin' and not (user.is_superuser or actual_role == 'admin'):
                messages.error(request, "Access Denied. You are not an authorized Overseer.")
            elif intended_role == 'doctor' and actual_role != 'doctor':
                messages.error(request, "Access Denied. You are not an authorized Healer.")
            else:
                login(request, user)
                messages.success(request, f"Welcome, {user.username}! You have entered as a {intended_role}.")
                
                # Dynamic Redirect based on role success
                if intended_role == 'doctor':
                    return redirect('doctor_dashboard')
                elif intended_role == 'admin':
                    return redirect('overwatch')
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid key or username')
            
    return render(request, 'medicines/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')



@login_required
def medication_list(request):
    meds = Medication.objects.filter(user=request.user)

    meds_data = []
    for med in meds:
        times_list = med.times if isinstance(med.times, list) else [] 
        meds_data.append({
            "pill_name": med.pill_name,
            "dosage": med.dosage,
            "times": times_list,
            "frequency": med.frequency,
            "times_per_day": med.times_per_day
        })
    
    meds_data_json = json.dumps(meds_data, cls=DjangoJSONEncoder)

    return render(request, 'medicines/medication_list.html', {
        'meds': meds,
        "VAPID_PUBLIC_KEY": settings.VAPID_PUBLIC_KEY,
        "meds_data_json": meds_data_json
    })


@login_required
def medication_create(request):
    if request.method == "POST":
        pill_name = request.POST.get("pill_name")
        dosage = request.POST.get("dosage")
        frequency = request.POST.get("frequency_type")
        times_per_day = int(request.POST.get("times_per_day", 1))
        times = request.POST.getlist("times")

        if not pill_name or not dosage or not times:
            messages.error(request, "Please fill all required fields.")
            return redirect('med_add')

        Medication.objects.create(
            user=request.user,
            pill_name=pill_name,
            dosage=int(dosage),
            frequency=frequency,
            times_per_day=times_per_day,
            times=times,
            # google_event_ids defaults to [] here
        )
        messages.success(request, f"{pill_name} added successfully!")
        return redirect('med_list')

    return render(request, "medicines/medication_form.html", {"med": None})


@login_required
def medication_update(request, pk):
    med = get_object_or_404(Medication, pk=pk, user=request.user)
    
    # Store old data before POST processing
    old_times = med.times 
    old_frequency = med.frequency
    old_event_ids = med.google_event_ids # Capture old list of IDs

    if request.method == 'POST':
        submitted_times = request.POST.getlist('times')
        
        # 1. Update medication object fields
        med.pill_name = request.POST.get('pill_name')
        med.dosage = request.POST.get('dosage')
        new_frequency = request.POST.get('frequency_type')
        
        med.frequency = new_frequency
        med.times = submitted_times
        med.times_per_day = len(submitted_times) 
        
        # Basic validation check
        if med.times_per_day == 0:
            messages.error(request, 'At least one time is required.')
            return render(request, 'medicines/medication_form.html', {'med': med})
            
        # Determine if calendar event action is required
        schedule_changed = (submitted_times != old_times) or (new_frequency != old_frequency)
        
        # 2. Handle Calendar Deletion if schedule changed AND events existed
        if old_event_ids and schedule_changed:
            _delete_google_events(request.user, old_event_ids)
            # Clear the IDs locally before saving the new med data
            med.google_event_ids = []


        try:
            # 3. Save the medication changes
            med.save()
            
            # 4. Handle Calendar Re-creation (UPDATED to use helper function)
            # Re-create events only if the schedule changed AND the medication was previously synced (had old IDs).
            if old_event_ids and schedule_changed:
                try:
                    new_event_ids = _create_google_events(request.user, med)

                    # Save the new IDs back to the medication object
                    med.google_event_ids = new_event_ids
                    med.save(update_fields=['google_event_ids'])
                    messages.info(request, f"Google Calendar events were updated for the new schedule ({len(new_event_ids)} recurring events created).")

                except GoogleCredentials.DoesNotExist:
                    messages.warning(request, "Google Calendar schedule was updated, but events were not re-added (credentials missing).")
                except Exception as e:
                    print(f"Calendar Re-creation Error: {e}")
                    messages.warning(request, "Google Calendar events could not be re-added due to an API error.")
                

            messages.success(request, f"{med.pill_name} updated successfully!")
            return redirect('med_list')
            
        except Exception as e:
            print(f"Database Save Error: {e}")
            messages.error(request, f'Save failed due to a system error.')
            return render(request, 'medicines/medication_form.html', {'med': med})
    
    return render(request, 'medicines/medication_form.html', {'med': med})


@login_required
def medication_delete(request, pk):
    med = get_object_or_404(Medication, pk=pk, user=request.user)
    
    # 1. Delete Google Calendar Events first, if any (NEW)
    if med.google_event_ids:
        deleted_count = _delete_google_events(request.user, med.google_event_ids)
        if deleted_count > 0:
             messages.info(request, f"Removed {deleted_count} linked Google Calendar event(s).")
             
    # 2. Delete the Medication object
    med.delete()
    messages.success(request, "Medication deleted successfully!")
    return redirect('med_list')


@csrf_exempt
def save_subscription(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            subscription = PushSubscription(
                user=request.user,  
                endpoint=data['endpoint'],
                p256dh=data['p256dh'],  
                auth=data['auth']
            )
            subscription.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error saving subscription: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'})


@login_required
def get_vapid_public_key(request):
    return JsonResponse({'vapid_public_key': settings.VAPID_PUBLIC_KEY})


# ===========================
# DASHBOARD VIEWS
# ===========================
@login_required
def dashboard_view(request):
    meds = Medication.objects.filter(user=request.user)
    today = date.today()
    now = timezone.now()

    dose_data = []
    for med in meds:
        # Safety check: Ensure med.times is a list before iterating
        times_list = med.times if isinstance(med.times, list) else [] 
        
        for t_str in times_list:
            t_obj = datetime.strptime(t_str, "%H:%M").time()
            scheduled_dt = timezone.make_aware(datetime.combine(today, t_obj))
            
            # ALWAYS create DoseLog entry to ensure we have an ID
            dose_log, created = DoseLog.objects.get_or_create(
                user=request.user,
                medication=med,
                scheduled_time=scheduled_dt,
                defaults={'status': 'pending'}
            )
            
            # Auto-mark as missed if time has passed and still pending
            if dose_log.status == 'pending' and scheduled_dt < now:
                dose_log.status = 'missed'
                dose_log.save()
            
            dose_data.append({
                'med_id': med.id,
                'pill_name': med.pill_name,
                'time': t_str,
                'status': dose_log.status,
                'dose_log_id': dose_log.id 
            })

    # --- PRIMARY CHANGE FOR SEQUENTIAL ORDER ---
    # Sort dose_data by time string (e.g., "08:00" comes before "12:00")
    dose_data.sort(key=lambda x: x['time']) 
    # -------------------------------------------

    # Calculate adherence
    total_doses = len(dose_data)
    taken_doses = sum(1 for d in dose_data if d['status'] == 'taken')
    missed_doses = sum(1 for d in dose_data if d['status'] == 'missed')
    adherence = round((taken_doses / total_doses) * 100, 1) if total_doses else 0

    # Calculate streak
    streak = 0
    # Use a set of all unique medications to calculate expected doses per day
    all_meds = Medication.objects.filter(user=request.user)
    
    for i in range(30):
        day = today - timedelta(days=i)
        day_start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(day, datetime.max.time()))
        
        # We need to consider all possible scheduled doses for that day
        expected_doses_count = sum(len(m.times) for m in all_meds if isinstance(m.times, list))
        
        # Check the logs for that specific day
        day_logs = DoseLog.objects.filter(
            user=request.user, 
            # Note: scheduled_time is used to track the *intended* date
            scheduled_time__range=(day_start, day_end) 
        )

        taken_doses_count = day_logs.filter(status='taken').count()
        
        # A perfect day means all expected doses for that day were taken
        if expected_doses_count > 0 and taken_doses_count == expected_doses_count:
            streak += 1
        else:
            break

    # Next dose
    next_dose_time = "--:--"
    # Iterate over the sorted dose_data for the nearest upcoming dose
    for d in dose_data:
        dose_time_obj = datetime.strptime(d['time'], "%H:%M").time()
        scheduled_dt = timezone.make_aware(datetime.combine(today, dose_time_obj))
        if scheduled_dt > now and d['status'] == 'pending':
            next_dose_time = d['time']
            break

    # Weekly adherence data
    weekly_adherence = []
    week_days = []
    for i in range(6, -1, -1): # Last 7 days including today
        day = today - timedelta(days=i)
        week_days.append(day.strftime('%a'))
        
        day_start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(day, datetime.max.time()))
        
        day_logs = DoseLog.objects.filter(
            user=request.user, 
            scheduled_time__range=(day_start, day_end)
        )
        
        expected_doses = sum(len(m.times) for m in all_meds if isinstance(m.times, list))
        taken_doses_for_day = day_logs.filter(status='taken').count()
        
        day_adherence = round((taken_doses_for_day / expected_doses) * 100, 1) if expected_doses > 0 else 0
        weekly_adherence.append(day_adherence)

    context = {
        'meds': meds,
        'dose_data': dose_data,
        'dose_data_json': json.dumps(dose_data),
        'adherence': adherence,
        'streak': streak,
        'next_dose': next_dose_time,
        'total_doses': total_doses,
        'taken_doses': taken_doses,
        'missed_doses': missed_doses,
        'weekly_adherence_json': json.dumps(weekly_adherence),
        'week_days_json': json.dumps(week_days),
    }
    return render(request, "medicines/dashboard.html", context)

# ===========================
# TOGGLE DOSE STATUS
# ===========================
@login_required
@csrf_exempt
def toggle_dose_status(request):
    """Simple toggle between taken/missed"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            dose_log_id = data.get('dose_log_id')
            new_status = data.get('status')  # 'taken' or 'missed'
            
            # Safety check - ensure dose_log_id is valid
            if not dose_log_id:
                return JsonResponse({'status': 'error', 'message': 'Missing dose log ID'})
            
            try:
                dose_log_id = int(dose_log_id)  # Convert to integer
            except (ValueError, TypeError):
                return JsonResponse({'status': 'error', 'message': 'Invalid dose log ID'})
            
            dose_log = DoseLog.objects.get(id=dose_log_id, user=request.user)
            
            # Update status
            dose_log.status = new_status
            if new_status == 'taken':
                dose_log.timestamp = timezone.now()
            
            dose_log.save()
            
            return JsonResponse({
                'status': 'success',
                'new_status': dose_log.status
            })
            
        except DoseLog.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Dose not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'})

@login_required
def dashboard_data(request):
    meds = Medication.objects.filter(user=request.user)
    today = date.today()

    dose_data = []
    for med in meds:
        # Safety check: Ensure med.times is a list before iterating
        times_list = med.times if isinstance(med.times, list) else [] 
        for t_str in times_list:
            t_obj = datetime.strptime(t_str, "%H:%M").time()
            scheduled_dt = timezone.make_aware(datetime.combine(today, t_obj))
            try:
                log = DoseLog.objects.get(user=request.user, medication=med, scheduled_time=scheduled_dt)
                status = log.status
            except DoseLog.DoesNotExist:
                status = 'pending'
            dose_data.append({
                'med_id': med.id,
                'pill_name': med.pill_name,
                'time': t_str,
                'status': status
            })

    taken_count = sum(1 for d in dose_data if d['status'] == 'taken')
    missed_count = sum(1 for d in dose_data if d['status'] == 'missed')
    pending_count = sum(1 for d in dose_data if d['status'] == 'pending')

    return JsonResponse({
        'dose_data': dose_data,
        'taken_count': taken_count,
        'missed_count': missed_count,
        'pending_count': pending_count,
        'total_doses': len(dose_data)
    })


# ===========================
# DOSE LOG AJAX 
# ===========================
@login_required
@csrf_exempt
def log_dose(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            med = Medication.objects.get(id=data['med_id'], user=request.user)
            dose_time = datetime.strptime(data['time'], "%H:%M").time()
            scheduled_dt = timezone.make_aware(datetime.combine(date.today(), dose_time))
            status = 'taken' if data.get('taken', True) else 'missed'

            DoseLog.objects.update_or_create(
                user=request.user,
                medication=med,
                scheduled_time=scheduled_dt,
                defaults={'status': status}
            )
            return JsonResponse({'status': 'success', 'message': 'Dose logged successfully'})
        except Medication.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Medication not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# ===========================
# MARK DOSE TAKEN (For push notification action)
# ===========================
@login_required
@csrf_exempt
def mark_dose_taken(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            dose_log = DoseLog.objects.get(
                id=data['dose_log_id'],
                user=request.user  # Security: ensure user owns this dose log
            )
            dose_log.status = 'taken'
            dose_log.timestamp = timezone.now()  # Update timestamp to when taken
            dose_log.save()
            
            return JsonResponse({
                'status': 'success', 
                'message': f'{dose_log.medication.pill_name} marked as taken'
            })
            
        except DoseLog.DoesNotExist:
            return JsonResponse({
                'status': 'error', 
                'message': 'Dose log not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'status': 'error', 
        'message': 'Invalid request method'
    }, status=405)


# ===========================
# GET TODAY'S DOSE LOGS
# ===========================
@login_required
def get_today_dose_logs(request):
    today = date.today()
    today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    dose_logs = DoseLog.objects.filter(
        user=request.user,
        scheduled_time__range=(today_start, today_end)
    ).select_related('medication')
    
    logs_data = []
    for log in dose_logs:
        logs_data.append({
            'id': log.id,
            'medication_name': log.medication.pill_name,
            'scheduled_time': log.scheduled_time.strftime('%H:%M'),
            'status': log.status,
            'taken_time': log.timestamp.strftime('%H:%M') if log.status == 'taken' else None
        })
    
    return JsonResponse({'dose_logs': logs_data})


# ===========================
# GOOGLE CALENDAR INTEGRATION
# ===========================

# --------------------------------------
# Step 1: Authenticate with Google OAuth
# --------------------------------------
@login_required
def google_calendar_auth(request):
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
                "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar.events"],
        redirect_uri=request.build_absolute_uri(reverse('google_calendar_callback'))
    )
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # ensures refresh_token is returned
    )
    return redirect(auth_url)


# --------------------------------------
# Step 2: Handle OAuth Callback
# --------------------------------------
@login_required
def google_calendar_callback(request):
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
                "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar.events"],
        redirect_uri=request.build_absolute_uri(reverse('google_calendar_callback'))
    )
    flow.fetch_token(authorization_response=request.build_absolute_uri())
    credentials = flow.credentials

    defaults = {
        "access_token": credentials.token,
        "client_id": settings.GOOGLE_CALENDAR_CLIENT_ID,
        "client_secret": settings.GOOGLE_CALENDAR_CLIENT_SECRET,
    }

    if credentials.refresh_token:
        defaults["refresh_token"] = credentials.refresh_token

    GoogleCredentials.objects.update_or_create(
        user=request.user,
        defaults=defaults
    )

    messages.success(request, "Google Calendar connected successfully! You can now sync your medication schedule.")
    return redirect('dashboard')


# --------------------------------------
# Step 3: Add Medication Event(s) (UPDATED for recurrence)
# --------------------------------------
@login_required
def add_event(request, med_id=None):
    med = get_object_or_404(Medication, id=med_id, user=request.user)

    # Check if events are already linked
    if med.google_event_ids:
        return JsonResponse({'status': 'error', 'message': f"Events are already linked to this medication. Delete them first if you want to re-add."}, status=400)


    try:
        # Calls the helper function to create recurring events
        new_event_ids = _create_google_events(request.user, med)

        # Save ALL newly created master event IDs to the medication object
        med.google_event_ids = new_event_ids
        med.save(update_fields=['google_event_ids'])

    except GoogleCredentials.DoesNotExist:
        # Return JSON error for AJAX handling
        return JsonResponse({'status': 'error', 'message': "Please connect your Google Calendar first."}, status=401)
    except Exception as e:
        print(f"Calendar Add Event Error: {e}")
        return JsonResponse({'status': 'error', 'message': f"An API error occurred: {e}"}, status=500)

    # Success JSON Response
    return JsonResponse({
        'status': 'ok', 
        'message': f"Successfully created {len(new_event_ids)} recurring calendar event(s).",
        'count': len(new_event_ids)
    })


# --------------------------------------
# Step 4: Delete Medication Event
# --------------------------------------
@login_required
@require_POST
def delete_event(request, med_id=None):
    med = get_object_or_404(Medication, id=med_id, user=request.user)
    
    # Check the new list field
    if not med.google_event_ids:
        return JsonResponse({'status': 'error', 'message': "No linked Google Calendar events found."}, status=400)

    # Use the helper function to delete events
    deleted_count = _delete_google_events(request.user, med.google_event_ids)
    
    # Clear the field after deletion attempts
    med.google_event_ids = []
    med.save(update_fields=['google_event_ids'])

    # Success JSON Response
    return JsonResponse({
        'status': 'ok', 
        'message': f"Successfully deleted {deleted_count} linked Google Calendar recurring event(s)!"
    })


@csrf_exempt
def chatbot_view(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            user_input = body.get('message', '')

            bot_response = get_chatbot_response(user_input)

            return JsonResponse({'response': bot_response})
        except Exception as e:
            return JsonResponse({'response': f'Error: {str(e)}'})
    return JsonResponse({'response': 'Invalid request method'}, status=400)

def get_patient_stats(user):
    """A systematic calculation tool to pull data logs for standard patient review."""
    from datetime import date, timedelta
    logs = DoseLog.objects.filter(user=user)
    total = logs.count()
    taken = logs.filter(status='taken').count()
    adherence = round((taken / total) * 100, 1) if total else 0

    # Detailed medical history for doctor reflection
    detailed_history = logs.order_by('-scheduled_time')[:10] 

    return {
        'adherence': adherence,
        'detailed_history': detailed_history
    }

@login_required
def doctor_list(request):
    """Lists all available doctors for the patient to choose from."""
    doctors = UserProfile.objects.filter(role='doctor')
    return render(request, 'medicines/doctor_list.html', {'doctors': doctors})

@login_required
def book_appointment(request, doctor_id):
    """The form where patients enter their problem details."""
    doctor_user = get_object_or_404(User, id=doctor_id)
    if request.method == "POST":
        problem = request.POST.get('problem')
        details = request.POST.get('details')
        
        Appointment.objects.create(
            patient=request.user,
            doctor=doctor_user,
            problem=problem,
            patient_details=details
        )
        return render(request, 'medicines/booking_sent.html', {'doctor': doctor_user})
    
    return render(request, 'medicines/booking_form.html', {'doctor': doctor_user})


# medicines/views.py

@login_required
def doctor_dashboard(request):
    """Refined dashboard to audit all patient statuses (Pending/Accepted/Rejected)."""
    # 1. Authorize the Doctor Registry
    try:
        profile = request.user.profile
        if profile.role != 'doctor':
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        return redirect('dashboard')

    # 2. Fetch Incoming Requests (Only Pending)
    # These include health statistics badges for clinical review
    requests = Appointment.objects.filter(doctor=request.user, status='pending')
    for appt in requests:
        appt.patient_stats = get_patient_stats(appt.patient)

    # 3. Fetch Full Systematic Archive (Exclude Pending)
    # This automatically includes processed 'accepted' and 'rejected' records
    processed_history = Appointment.objects.filter(doctor=request.user).exclude(status='pending').order_by('-created_at')

    context = {
        'doctor_profile': profile,
        'requests': requests,
        'history': processed_history,
    }
    return render(request, 'medicines/doctor_dashboard.html', context)
@login_required
def respond_to_request(request, appt_id, action):
    """Doctor logic to confirm or deny an audience."""
    # Security: Ensure this appointment belongs to the logged-in doctor
    appt = get_object_or_404(Appointment, id=appt_id, doctor=request.user)
    
    if action == 'accept':
        appt.status = 'accepted'
        messages.success(request, f"Confirmed audience with patient {appt.patient.username} ✨")
    elif action == 'reject':
        appt.status = 'rejected'
        messages.warning(request, "Request declined.")
    
    appt.save()
    return redirect('doctor_dashboard')



@login_required
def patient_requests(request):
    """View for patients to track the status of their magic requests."""
    # Fetch all appointments made by the logged-in patient
    my_requests = Appointment.objects.filter(patient=request.user).order_by('-created_at')
    
    return render(request, 'medicines/patient_requests.html', {'appointments': my_requests})

# medicines/views.py

@login_required
def admin_overwatch(request):
    """A master dashboard for the Admin to see all realm appointments."""
    # Security: Ensure only authorized Admins can enter
    try:
        if request.user.profile.role != 'admin' and not request.user.is_superuser:
            messages.error(request, "Access Denied. Admin oversight only!")
            return redirect('dashboard')
    except Exception:
        return redirect('dashboard')

    # Fetch every single appointment in the realm
    all_appointments = Appointment.objects.all().order_by('-created_at')
    
    return render(request, 'medicines/admin_overwatch.html', {'appointments': all_appointments})

class AdminDoctorCreationForm(forms.Form):
    """Form used by the Admin to create a new Doctor account."""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Unique Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Login Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Temporary Password'}))
    specialty = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'e.g., General Medicine'}))
    age = forms.IntegerField(min_value=18, widget=forms.NumberInput(attrs={'placeholder': 'Doctor Age'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Full Address'}))
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


@login_required
def admin_authorize_doctor(request):
    """
    Handles the Admin's creation of a new Doctor (Role 1).
    """
    # Security: Only Admins can access
    try:
        if request.user.profile.role != 'admin' and not request.user.is_superuser:
            messages.error(request, "Access Denied. Admin privileges required!")
            return redirect('dashboard')
    except Exception:
        return redirect('dashboard')

    form = AdminDoctorCreationForm()

    if request.method == 'POST':
        form = AdminDoctorCreationForm(request.POST)
        if form.is_valid():
            # 1. Create User (Password is auto-hashed securely)
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            user.save()

            # 2. Create the Doctor's UserProfile and set all details and the 'doctor' role
            UserProfile.objects.create(
                user=user,
                role='doctor',
                specialty=form.cleaned_data['specialty'],
                # Note: If you want to use age/address, you must add these fields to your UserProfile model in models.py first.
            )

            messages.success(request, f"Doctor {user.username} successfully created. They can now log in.")
            return redirect('overwatch')

    # For both GET and invalid POST
    return render(request, 'medicines/doctor_authorization_form.html', {'form': form})

from .models import Symptom 
@login_required
@require_http_methods(["GET"])
def get_user_symptoms_api(request):
    try:
        user = request.user
        days = int(request.GET.get('days', 7))
        limit = int(request.GET.get('limit', 50))
        
        # Get queryset
        symptoms_qs = Symptom.objects.filter(user=user)
        
        # Filter by days if specified
        if days and days > 0:
            cutoff_date = timezone.now() - timedelta(days=days)
            symptoms_qs = symptoms_qs.filter(timestamp__gte=cutoff_date)
        
        # Apply limit and order
        symptoms = symptoms_qs.order_by('-timestamp')[:limit]
        
        # Convert to list of dicts using model's to_dict() method
        symptoms_list = [symptom.to_dict() for symptom in symptoms]
        
        return JsonResponse({
            "success": True,
            "symptoms": symptoms_list,
            "count": len(symptoms_list),
            "days": days
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)

from django.db.models import Count
@login_required
@require_http_methods(["GET"])
def get_symptom_trends_api(request):
    try:
        user = request.user
        days = int(request.GET.get('days', 30))
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Get symptoms in timeframe
        symptoms = Symptom.objects.filter(
            user=user,
            timestamp__gte=cutoff_date
        )
        
        # Get symptom frequency
        symptom_frequency = (
            symptoms.values('symptom')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Get severity distribution
        severity_distribution = (
            symptoms.exclude(severity__isnull=True)
            .values('severity')
            .annotate(count=Count('id'))
            .order_by('severity')
        )
        
        # Convert to list/dict
        symptom_freq_list = [
            {"symptom": item['symptom'], "count": item['count']}
            for item in symptom_frequency
        ]
        
        severity_dict = {
            item['severity']: item['count']
            for item in severity_distribution
        }
        
        return JsonResponse({
            "success": True,
            "trends": {
                "days_analyzed": days,
                "total_symptoms": symptoms.count(),
                "symptom_frequency": symptom_freq_list,
                "severity_distribution": severity_dict
            }
        })
            
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def log_symptom_manual_api(request):
    """
    API to manually log a symptom using Django ORM.
    URL: /api/symptoms/log/
    Method: POST
    Body: {"symptom": "headache", "severity": "mild"}
    
    Matches your Symptom model (no duration field).
    """
    try:
        data = json.loads(request.body)
        user = request.user
        
        symptom_text = data.get('symptom', '').strip()
        severity = data.get('severity')
        
        if not symptom_text:
            return JsonResponse({
                "success": False,
                "error": "Symptom is required"
            }, status=400)
        
        # Validate severity
        if severity and severity not in ['mild', 'moderate', 'severe']:
            severity = None
        
        # Create symptom record (no duration field in your model)
        symptom = Symptom.objects.create(
            user=user,
            symptom=symptom_text[:500],
            severity=severity
        )
        
        # Cleanup old entries (keep only last 50 entries and 7 days)
        cleanup_old_symptoms(user.id)
        
        return JsonResponse({
            "success": True,
            "id": symptom.id,
            "message": "Symptom logged successfully"
        })
            
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        }, status=500)


def cleanup_old_symptoms(user_id: int):
    """
    Clean up old symptom logs for a user.
    Keeps only last 50 entries and last 7 days.
    Uses Django ORM.
    """
    try:
        from django.utils import timezone
        
        # Get cutoff time (7 days ago)
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # 1. Delete entries older than 7 days
        deleted_old = Symptom.objects.filter(
            user_id=user_id,
            timestamp__lt=seven_days_ago
        ).delete()[0]
        
        # 2. Keep only the 50 most recent entries
        # Get IDs of the 50 most recent symptoms
        recent_ids = Symptom.objects.filter(
            user_id=user_id
        ).order_by('-timestamp').values_list('id', flat=True)[:50]
        
        # Delete symptoms not in recent_ids
        deleted_excess = Symptom.objects.filter(
            user_id=user_id
        ).exclude(id__in=recent_ids).delete()[0]
        
        if deleted_old > 0 or deleted_excess > 0:
            import logging
            logger = logging.getLogger(_name_)
            logger.info(f"Cleaned up symptoms for user {user_id}: {deleted_old} old, {deleted_excess} excess")
            
    except Exception as e:
        import logging
        logger = logging.getLogger(_name_)
        logger.error(f"Failed to cleanup old symptoms: {e}")
        

try:
    from chatbot.utils import chatbot
except ImportError:
    chatbot = None

from django.utils.decorators import method_decorator
@method_decorator(csrf_exempt, name='dispatch')
class ChatbotView(APIView):
    """
    Simple chatbot endpoint.
    """
    def post(self, request):
        """
        Handle chatbot messages.
        Expected JSON:
        {
            "message": "user message here",
            "user_id": "optional_user_id",
            "context": {}  # optional context
        }
        """
        if chatbot is None:
            return Response(
                {"error": "Chatbot module not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Get request data
        data = request.data
        
        # Validate
        message = data.get('message', '').strip()
        if not message:
            return Response(
                {"error": "Message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = request.user.id
        if not user_id:
            user_id = data.get("user_id")
        context = data.get('context', {})
        
        # Process with chatbot
        try:
            result = chatbot.process(
                user_input=message,
                user_id=user_id,
                context=context
            )
            
            # Add request metadata
            result['request_id'] = request.id if hasattr(request, 'id') else None
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Chatbot view error: {e}")
            return Response(
                {
                    "success": False,
                    "response": "An error occurred while processing your message.",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class ChatbotHealthView(APIView):
    """Health check endpoint for chatbot"""
    def get(self, request):
        if chatbot is None:
            return Response(
                {"status": "unavailable", "message": "Chatbot module not loaded"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            # Try to initialize to check health
            chatbot.initialize()
            return Response({
                "status": "healthy",
                "message": "Chatbot is ready"
            })
        except Exception as e:
            return Response({
                "status": "unhealthy",
                "message": f"Chatbot initialization failed: {str(e)}"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
def chatbot_page(request):
    return render(request, "medicines/chatbot.html")

