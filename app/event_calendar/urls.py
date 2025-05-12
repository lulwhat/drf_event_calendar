from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, \
    TokenRefreshView, TokenVerifyView

from events.views import UserLoginView, UserRegisterView

urlpatterns = [
    # Authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(),
         name='token_verify'),
    path('api/user/login', UserLoginView.as_view(), name='user_login'),
    path('api/user/register', UserRegisterView.as_view(),
         name='user_register'),

    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'),
         name='swagger-ui'),
    path('api/', include('events.urls')),
    path('api/', include('notifications.urls')),
    path('api-auth/', include('rest_framework.urls')),
]
