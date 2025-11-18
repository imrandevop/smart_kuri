from django.urls import path
from .views import CreateChitAPIView

urlpatterns = [
    path('api/chits/', CreateChitAPIView.as_view(), name='create-chit'),
]
