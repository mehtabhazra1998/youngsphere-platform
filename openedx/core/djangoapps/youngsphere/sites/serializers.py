from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from opaque_keys.edx.locator import CourseLocator
from rest_framework import serializers
from organizations import api as organizations_api
from organizations.models import Organization

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.youngsphere.sites.tasks import clone_course
from .models import AlternativeDomain, School, Class, Section, Course, UserMiniProfile, UserSectionMapping
from .utils import sass_to_dict, dict_to_sass, bootstrap_site


class SASSDictField(serializers.DictField):
    def to_internal_value(self, data):
        return dict_to_sass(data)

    def to_representation(self, value):
        return sass_to_dict(value)


class SiteConfigurationSerializer(serializers.ModelSerializer):
    values = serializers.DictField()
    #YoungSphere Later Stages
    #sassVariables = serializers.ListField(source='sass_variables')
    #pageElements = serializers.DictField(source='page_elements')

    class Meta:
        model = SiteConfiguration
        fields = ('id', 'values')

    def update(self, instance, validated_data):
        object = super(SiteConfigurationSerializer, self).update(instance, validated_data)
        return object


class SiteConfigurationListSerializer(SiteConfigurationSerializer):
    class Meta(SiteConfigurationSerializer.Meta):
        fields = ('id', 'name', 'domain')


class AlternativeDomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlternativeDomain
        fields = ('id', 'domain', 'site')


class SiteSerializer(serializers.ModelSerializer):
    configuration = SiteConfigurationSerializer(read_only=True)
    alternativeDomain = AlternativeDomainSerializer(source='alternative_domain', read_only=True)
    customDomainStatus = serializers.SerializerMethodField('custom_domain_status', read_only=True)

    class Meta:
        model = Site
        fields = ('id', 'name', 'domain', 'configuration', 'alternativeDomain', 'customDomainStatus')

    def create(self, validated_data):
        site = super(SiteSerializer, self).create(validated_data)
        organization, site, user = bootstrap_site(site)
        return site

    def custom_domain_status(self, obj):
        if not hasattr(obj, 'alternative_domain'):
            return 'inactive'
        return 'active' if obj.alternative_domain.is_tahoe_domain() else 'inactive'


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'short_name', 'edx_uuid')

    def create(self, validated_data):
        return organizations_api.add_organization(**validated_data)


class RegistrationSerializer(serializers.Serializer):
    site = SiteSerializer()
    organization = OrganizationSerializer()
    user_email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False)
    initial_values = serializers.DictField(required=False)

    def create(self, validated_data):
        site_data = validated_data.pop('site')
        site = Site.objects.create(**site_data)
        organization_data = validated_data.pop('organization')
        user_email = validated_data.pop('user_email', None)
        organization, site, user = bootstrap_site(site, organization_data, user_email)
        site_configuration = site.configuration
        initial_values = validated_data.get('initial_values', {})
        if initial_values:
            site_configuration.values['SITE_NAME'] = site.domain
            site_configuration.values['platform_name'] = initial_values.get('platform_name')
            site_configuration.values['logo_positive'] = initial_values.get('logo_positive')
            site_configuration.values['logo_negative'] = initial_values.get('logo_negative')
            site_configuration.values['primary-font'] = initial_values.get('font')
            site_configuration.values['accent-font'] = 'Delius Unicase'
            site_configuration.values['page_status'] = {
                'about': True,
                'blog': True,
                'contact': True,
                'copyright': True,
                'donate': False,
                'embargo': False,
                'faq': True,
                'help': True,
                'honor': True,
                'jobs': False,
                'news': True,
                'press': True,
                'privacy': True,
                'tos': True
            }
            #YoungSphere Later stages
            # site_configuration.set_sass_variables({
            #     '$brand-primary-color': initial_values.get('primary_brand_color'),
            #     '$base-text-color': initial_values.get('base_text_color'),
            #     '$cta-button-bg': initial_values.get('cta_button_bg'),
            #     '$primary-font-name': '"{}"'.format(initial_values.get('font')),
            #     '$accent-font-name': '"Delius Unicase"',
            # })
            site_configuration.save()

        # clone course
        if settings.CLONE_COURSE_FOR_NEW_SIGNUPS:
            source_course_locator = CourseLocator.from_string(settings.COURSE_TO_CLONE)
            destination_course_locator = CourseLocator(organization.name, 'My first course', '2017')
            clone_course.apply_async(
                (unicode(source_course_locator), unicode(destination_course_locator), user.id),
                queue="edx.core.cms.high"
            )
        return {
            'site': site,
            'organization': organization,
            'user_email': user_email,
            'password': 'hashed',
            'initial_values': initial_values,
        }


class AlternativeDomainSerializer(serializers.ModelSerializer):
    site = serializers.PrimaryKeyRelatedField(queryset=Site.objects.all())

    class Meta:
        model = AlternativeDomain
        fields = ('id', 'site', 'domain')

    def create(self, validated_data):
        """
        Allow only one alternative domain per Site model.
        """
        domain, created = AlternativeDomain.objects.get_or_create(
            site=validated_data.get('site', None),
            defaults={'domain': validated_data.get('domain', None)})
        if not created:
            domain.domain = validated_data.get('domain', None)
            domain.save()
        return domain

class SchoolSerializer(serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(queryset=Organization.objects.all(), slug_field='name')
    class Meta:
        model = School
        fields = ('id','organization', 'schoolname', 'principal', 'email', 'contact_number', 'address', 'website', 'board')

class ClassSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())

    class Meta:
        model = Class
        fields = ('id','organization','class_level', 'display_name', 'num_sections')

class SectionSerializer(serializers.ModelSerializer):
    section_class = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all())

    class Meta:
        model = Section
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    course_class = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all())
    course_section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())

    class Meta:
        model = Course
        fields = '__all__'

class UserMiniProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = UserMiniProfile
        fields = '__all__'

class UserSectionMappingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    section = serializers.PrimaryKeyRelatedField(queryset=Section.objects.all())

    class Meta:
        model = UserSectionMapping
        fields = '__all__'