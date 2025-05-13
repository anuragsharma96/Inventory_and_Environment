"""
URL configuration for inventory project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from inventoryapp import views
from inventoryapp.views import home, inventory_list, add_equipment, add_lab, lab_autocomplete, lab_list,get_equipment_form

def redirect_admin():
    return redirect('/admin/login/')
urlpatterns = [
    path('',home,name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('inventoryapp.api_urls')),  # API routes
    path('create-admin/', views.create_admin, name='create_admin'),
    path('admin-list/', views.admin_list, name='admin_list'),
    path('lab_list/',lab_list,name='lab_list'),
    #path('manage-admins/', views.manage_admins, name='manage_admins'),
    path('inventory/', inventory_list, name='inventory_list'),
    path('place-order/', views.place_order, name='place_order'),
    path('add-lab/',add_lab,name='add_lab'),
    path('add-equipment/', add_equipment, name='add_equipment'),
    path("revoke-admin-access/", views.revoke_admin_access, name="revoke_admin_access"),
    path("reinstate-admin/", views.reinstate_admin, name="reinstate_admin"),
    path("promote/",views.promote,name="promote"),
    path('lab-autocomplete/', lab_autocomplete, name='lab-autocomplete'),
    path('issue_equipment/', views.issue_equipment, name='issue_equipment'),
    path('return_equipment/', views.return_equipment, name='return_equipment'),
    path('add_more_equipment/',views.get_equipment_form,name='get_equipment_form'),
]
