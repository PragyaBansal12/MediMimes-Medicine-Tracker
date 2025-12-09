from datetime import datetime, timedelta
from medicines.models import DoseLog, Medication

def extract_features(user, medication):
    # 1. Past adherence rate for this medication
    logs = DoseLog.objects.filter(user=user, medication=medication)
    total = logs.count()
    taken = logs.filter(status='taken').count()
    past_adherence_rate = taken / total if total > 0 else 1.0

    # 2. Lifestyle routine (taken all doses in last 4 days?)
    four_days_ago = datetime.now() - timedelta(days=4)
    recent_logs = logs.filter(scheduled_time__gte= four_days_ago)
    if recent_logs.exists():
        lifestyle_routine = 1 if recent_logs.filter(status='taken').count() >= 0.8*recent_logs.count() else 0
    else:
        lifestyle_routine = 0

    # 3. Dose complexity = how many times per day
    dose_complexity = medication.times_per_day

    # 4. Time of day (based on next scheduled dose)
    next_dose = logs.filter(scheduled_time__gte=datetime.now()).order_by('scheduled_time').first()
    if next_dose:
        hour = next_dose.scheduled_time.hour
    else:
        hour = 8  # fallback: morning

    if 5 <= hour < 12:
        time_of_day = "Morning"
    elif 12 <= hour < 17:
        time_of_day = "Afternoon"
    elif 17 <= hour < 21:
        time_of_day = "Evening"
    else:
        time_of_day = "Night"

    # 5. One-hot encoding for time_of_day
    time_features = {
        'Morning': 1 if time_of_day == 'Morning' else 0,
        'Afternoon': 1 if time_of_day == 'Afternoon' else 0,
        'Evening': 1 if time_of_day == 'Evening' else 0,
        'Night': 1 if time_of_day == 'Night' else 0,
    }

    # Final feature set
    features = {
        'dose_complexity': dose_complexity,
        'past_adherence_rate': past_adherence_rate,
        'lifestyle_routine': lifestyle_routine,
        **time_features
    }

    return features
