from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Main Screen - Dashboard (changed from medication_list)
    path('', views.dashboard_view, name='dashboard'),
    
    # Medications CRUD
    path('medications/', views.medication_list, name='med_list'),
    path('medications/add/', views.medication_create, name='med_add'),
    path('medications/edit/<int:pk>/', views.medication_update, name='med_edit'),
    path('medications/delete/<int:pk>/', views.medication_delete, name='med_delete'),

    # Dashboard (alternative path - still accessible via /dashboard/)
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),

    # API endpoints
    path('api/dashboard-data/', views.dashboard_data, name='dashboard_data'),
    path('api/log-dose/', views.log_dose, name='log_dose'),
    path('api/toggle-dose-status/', views.toggle_dose_status, name='toggle_dose_status'),
    path('api/mark-dose-taken/', views.mark_dose_taken, name='mark_dose_taken'),
    path('api/today-dose-logs/', views.get_today_dose_logs, name='today_dose_logs'),

    # Notifications
    path('get-vapid-public-key/', views.get_vapid_public_key, name='get_vapid_public_key'),
    path('save-subscription/', views.save_subscription, name='save_subscription'),

     # Google Calendar OAuth
    path('google/calendar/connect/', views.google_calendar_auth, name='google_calendar_auth'),
    path('google/calendar/callback/', views.google_calendar_callback, name='google_calendar_callback'),
    path('calendar/add-event/<int:med_id>/', views.add_event, name='add_event'),
    path('google-calendar/delete-event/<int:med_id>/', views.delete_event, name='delete_event'),
        
    # symptom APIs
    path('api/symptoms/', views.get_user_symptoms_api, name='get_symptoms'),
    path('api/symptoms/trends/', views.get_symptom_trends_api, name='symptom_trends'),
    path('api/symptoms/log/', views.log_symptom_manual_api, name='log_symptom'),
    
   # Chatbot endpoints
    path('chat/', views.ChatbotView.as_view(), name='chatbot'),
    path('chat/health/', views.ChatbotHealthView.as_view(), name='chatbot-health'),
    path('assistant/', views.chatbot_page, name='chatbot_page'),

]
