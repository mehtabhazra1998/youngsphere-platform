from django.conf import settings
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter
from .api import SiteConfigurationViewSet, SiteViewSet, FileUploadView, SiteCreateView, \
    UsernameAvailabilityView, DomainAvailabilityView, CustomDomainView, DomainSwitchView, \
    SchoolView, ClassView, SectionView, CourseView, UserMiniProfileView, UserSectionMappingView, SchoolProfile, \
    TeacherProfile, TeacherNewProfile, NewClassView, NewSectionView, StudentProfile, StudentNewProfile

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'site-configurations', SiteConfigurationViewSet)
router.register(r'sites', SiteViewSet)
router.register(r'school', SchoolView )
router.register(r'Course', CourseView )
router.register(r'userminiprofile', UserMiniProfileView )
router.register(r'usersection', UserSectionMappingView )

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
urlpatterns = [
    url(r'^upload_file/', FileUploadView.as_view()),
    url(r'^username/{}/'.format(settings.USERNAME_PATTERN), UsernameAvailabilityView.as_view()),
    url(r'^domain/(?P<subdomain>[\w.@+-]+)/', DomainAvailabilityView.as_view()),
    url(r'^custom_domain/', CustomDomainView.as_view()),
    url(r'^domain_switch/', DomainSwitchView.as_view()),
    url(r'^register/', SiteCreateView.as_view()),
    url(r'^schoolprofile/{}/'.format(settings.USERNAME_PATTERN), SchoolProfile.as_view()),
    url(r'^teacher/(?P<pk>[0-9]+)/', TeacherProfile.as_view()),
    url(r'^teacher/', TeacherNewProfile.as_view()),
    url(r'^class/(?P<pk>[0-9]+)/', ClassView.as_view()),
    url(r'^class/', NewClassView.as_view()),
    url(r'^section/(?P<pk>[0-9]+)/', SectionView.as_view()),
    url(r'^section/', NewSectionView.as_view()),
    url(r'^student/(?P<pk>[0-9]+)/', StudentProfile.as_view()),
    url(r'^student/', StudentNewProfile.as_view()),

    url(r'^', include(router.urls)),
]
