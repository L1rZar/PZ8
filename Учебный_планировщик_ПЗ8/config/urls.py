from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include


def healthz(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path('admin/', admin.site.urls),
    path('api/', include('planner.api_urls')),
    path('', include('planner.urls')),
]
