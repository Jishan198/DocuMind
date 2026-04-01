from django.urls import path
from . import views
from config.health import health_check

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_view, name='upload'),
    path('chat/', views.chat_view, name='chat'),
    path('upload/document/', views.upload_document, name='upload_document'),
    path('documents/list/', views.document_list_partial, name='document_list_partial'),
    path('audit/', views.audit_log_view, name='audit_log'),
    path('health/', health_check, name='health_check'),
]