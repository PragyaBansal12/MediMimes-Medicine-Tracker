import os
import joblib
from django.conf import settings

_model = None

def get_adherence_model():
    global _model
    if _model is None:
        model_path = os.path.join(settings.BASE_DIR, 'medicines', 'ml_model', 'adherence_model.pkl')
        _model = joblib.load(model_path)
    return _model
