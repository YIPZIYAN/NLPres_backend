from dj_rest_auth.serializers import UserDetailsSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

from userprofile.models import CustomUser


class UserSerializer(UserDetailsSerializer):
    category = serializers.CharField(allow_null=True, required=False)
    avatar = serializers.ImageField(allow_null=True, required=False)

    class Meta(UserDetailsSerializer.Meta):
        model = CustomUser
        fields = UserDetailsSerializer.Meta.fields + ('category', 'avatar')

    def update(self, instance, validated_data):
        category = validated_data.pop('category', None)
        avatar = validated_data.pop('avatar', None)

        if category is not None:
            instance.category = category
        if avatar is not None:
            instance.avatar = avatar

        instance = super().update(instance, validated_data)
        instance.save()

        return instance


class CustomRegisterSerializer(RegisterSerializer):
    username = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, email):
        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email is already registered.")
        return email

    def save(self, request):
        self.validated_data['username'] = self.validated_data['email']

        user = super().save(request)

        return user
