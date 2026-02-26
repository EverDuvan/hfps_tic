from .models import SystemSettings

def system_settings(request):
    """
    Context processor to make the active System Settings available to all templates.
    """
    return {
        'system_settings': SystemSettings.load()
    }
