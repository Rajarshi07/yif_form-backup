from django.urls import path
from firstapp import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth.views import LogoutView
app_name = "firstapp"

urlpatterns = [
    path('', views.index, name = "index"),
    path('<str:state>/events/', views.event_page, name = "events"),
    path('other_states/', views.other_states, name = "other_states"),
    path('events/<str:event_name>', views.event_details, name = "event_details"),
    # path('events/<str:event_name>/register', views.main_form, name = "main_form"),
    # path('society_leads_login', views.society_leads_login, name = "admin_login"),
    path('special_admin_login/', views.admin_login, name = "admin_login"),
    path('export_user_xls/', views.export_users_xls, name = "download_xls"),
    # path('paytm_gateway/', views.paytm_gateway, name = "paytm_gateway"),
    path('email_test/', views.email_test, name = 'email_test'),
    path('email_test/<str:event_name>', views.send_email, name = "send email"),
    path('eventsedit/<id>/', views.detail_view ),
    path('eventsedit/<id>/update', views.update_view ),
    path('eventscreate/', views.create_view),
    path('eventsedit/',views.EventsList.as_view()),
    path('accounts/login/',RedirectView.as_view(url='/special_admin_login/', permanent=False)),
    path('logout/',LogoutView.as_view(next_page="/"),name='logout')
]

urlpatterns = urlpatterns + static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)

