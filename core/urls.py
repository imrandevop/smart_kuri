from django.urls import path
from .views import CreateChitAPIView, AddMemberAPIView

urlpatterns = [
    path('api/chits/', CreateChitAPIView.as_view(), name='create-chit'),
    path('api/members/', AddMemberAPIView.as_view(), name='add-member'),
]
