from dj_rest_auth.serializers import UserDetailsSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

from userprofile.models import UserProfile, CustomUser


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('avatar', 'category')


class UserSerializer(UserDetailsSerializer):
    profile = UserProfileSerializer(source="userprofile")

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ('profile',)

    def update(self, instance, validated_data):
        userprofile_data = validated_data.pop('userprofile', {})

        # to access the 'company_name' field in here
        # company_name = userprofile_data.get('company_name')

        # update the userprofile fields
        userprofile_serializer = self.fields['profile']
        userprofile_instance = instance.userprofile
        userprofile_serializer.update(userprofile_instance, userprofile_data)

        instance = super().update(instance, validated_data)
        return instance


class CustomRegisterSerializer(RegisterSerializer):
    username = serializers.CharField(required=False, allow_blank=True)
    category = serializers.CharField(required=False)
    avatar = serializers.ImageField(required=False)

    def validate_email(self, email):
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already registered.")
        return email

    def save(self, request):
        self.validated_data['username'] = self.validated_data['email']

        user = super().save(request)

        UserProfile.objects.create(
            user=user,
            category=self.validated_data.get('category', None),
            avatar=self.validated_data.get('avatar', None)
        )
        return user
