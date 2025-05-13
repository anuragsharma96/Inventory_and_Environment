from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Equipment, CustomUser
from .serializers import EquipmentSerializer, AdminSerializer

class InventoryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        inventory = Equipment.objects.all()
        serializer = EquipmentSerializer(inventory, many=True)
        return Response(serializer.data)

class AdminAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        admins = CustomUser.objects.filter(role='admin')
        serializer = AdminSerializer(admins, many=True)
        return Response(serializer.data)
