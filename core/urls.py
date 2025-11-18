from django.urls import path
from .views import CreateChitAPIView, AddMemberAPIView, JoinChitAPIView

urlpatterns = [
    path('api/chits/', CreateChitAPIView.as_view(), name='create-chit'),
    path('api/members/', AddMemberAPIView.as_view(), name='add-member'),
    path('api/chit/join/', JoinChitAPIView.as_view(), name='join-chit'),
]
