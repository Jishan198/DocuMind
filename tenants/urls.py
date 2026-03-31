from django.urls import path
from . import views

urlpatterns = [
    path('', views.OrganizationCreateView.as_view(), name='org-create'),
    path('detail/', views.OrganizationDetailView.as_view(), name='org-detail'),
    path('members/', views.MemberListView.as_view(), name='member-list'),
    path('members/invite/', views.MemberInviteView.as_view(), name='member-invite'),
]