from django.urls import path
from .views import VideoUploadView, video_status

urlpatterns = [
    path('upload/', VideoUploadView.as_view(), name='video-upload'),
    path('status/<int:video_id>/', video_status, name='video_status'),
]
