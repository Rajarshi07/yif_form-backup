from django.urls import path
from firstapp import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "firstapp"

urlpatterns = [
    path('', views.index, name = "index"),
    path('<str:state>/events/', views.event_page, name = "events"),
    path('other_states/', views.other_states, name = "other_states"),
    path('events/<str:event_name>', views.event_details, name = "event_details"),
    path('events/<str:event_name>/register', views.main_form, name = "main_form"),
    path('society_leads_login', views.society_leads_login, name = "admin_login"),
    path('admin_login/', views.admin_login, name = "admin_login"),
    path('export_user_xls/', views.export_users_xls, name = "download_xls"),
    path('paytm_gateway/', views.paytm_gateway, name = "paytm_gateway"),
]

urlpatterns = urlpatterns + static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)