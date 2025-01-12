from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API URLs for video processing (handled in video_processing.urls)
    path('api/videos/', include('video_processing.urls')),  # Ensure video_processing/urls.py is set up correctly

    # Default home page for frontend (if you have a single-page app)
    path('', TemplateView.as_view(template_name='index.html')),  # Serve an index template for frontend

    # Optional: If you need other specific URLs, you can add them here
]

# This line will ensure that media files are served correctly in development mode.
# This should only be used in development, and you should configure a proper static/media file server in production.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
