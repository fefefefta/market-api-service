from django.urls import path

from .views import import_units


urlpatterns = [
    path('import/', import_units, name='import'),
]