from dj_rest_auth.serializers import UserDetailsSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

from userprofile.models import CustomUser


class UserSerializer(UserDetailsSerializer):
    avatar = serializers.ImageField(allow_null=True, required=False)

    class Meta(UserDetailsSerializer.Meta):
        model = CustomUser
        fields = UserDetailsSerializer.Meta.fields + ('avatar',)

    def update(self, instance, validated_data):
        avatar = validated_data.pop('avatar', None)

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


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_current_password(self, value):
        if not self.instance.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, data):
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        if new_password != confirm_password:
            raise serializers.ValidationError("New passwords do not match.")

        if self.instance.check_password(new_password):
            raise serializers.ValidationError("New password cannot be the same as the current password.")

        return data

    def save(self):
        self.instance.set_password(self.validated_data['new_password'])
        self.instance.save()
        return self.instance
