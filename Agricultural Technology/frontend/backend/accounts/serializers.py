from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    business_name = serializers.CharField(write_only=True, required=False)
    address = serializers.CharField(write_only=True)
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = User
        fields = ['phone_number', 'full_name', 'role', 'password', 'business_name', 'address', 'latitude', 'longitude']

    def create(self, validated_data):
        profile_data = {
            'business_name': validated_data.pop('business_name', ''),
            'address': validated_data.pop('address', ''),
            'latitude': validated_data.pop('latitude', 23.8103),
            'longitude': validated_data.pop('longitude', 90.4125),
        }
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, **profile_data)
        return user


class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['full_name'] = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        data['full_name'] = self.user.full_name
        return data