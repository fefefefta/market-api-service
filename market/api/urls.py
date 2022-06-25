from django.urls import path

from .views import import_units, show_unit, delete_unit, sales


urlpatterns = [
    path('import/', import_units, name='import_unit'),
    path('nodes/<obj_id>/', show_unit, name='show_unit'),
    path('delete/<obj_id>/', delete_unit, name='delete_unit'),
    path('sales/', sales, name='sales'),

]