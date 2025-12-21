"""
URL configuration for library_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Customize Admin Site
admin.site.site_header = 'UNIKL Library System'
admin.site.site_title = 'UNIKL Library System'
admin.site.index_title = 'Library Administration'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('books.urls')),
    path('accounts/', include('accounts.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler400 = 'library_project.views.bad_request'
handler403 = 'library_project.views.permission_denied'
handler404 = 'library_project.views.page_not_found'
handler500 = 'library_project.views.server_error'
