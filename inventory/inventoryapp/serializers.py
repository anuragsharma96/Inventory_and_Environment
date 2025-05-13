from rest_framework import serializers
from .models import Equipment, CustomUser

class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ['id', 'tool_name', 'type', 'issued']

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'login_key']
