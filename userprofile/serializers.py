from allauth.account.models import EmailAddress
from dj_rest_auth.serializers import UserDetailsSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

from userprofile.models import CustomUser


class UserSerializer(UserDetailsSerializer):
    avatar = serializers.ImageField(allow_null=True, required=False)
    is_verified = serializers.BooleanField(source='get_email_verified', read_only=True)

    class Meta(UserDetailsSerializer.Meta):
        model = CustomUser
        fields = UserDetailsSerializer.Meta.fields + ('avatar','is_verified')

    def get_email_verified(self, obj):
        # Get the email address linked to the user
        email_address = EmailAddress.objects.filter(user=obj, primary=True).first()
        if email_address:
            return email_address.verified
        return False

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['is_verified'] = self.get_email_verified(instance)

        request = self.context.get('request', None)

        if request and instance.avatar:
            representation['avatar'] = request.build_absolute_uri(instance.avatar.url)

        return representation

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
