from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from sessions_app.models import Session
from sessions_app.serializers import SessionSerializer
from accounts.permissions import IsCreator, IsSessionOwner

class PublicSessionListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        sessions = Session.objects.all().select_related('creator')
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)

class PublicSessionDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        session = get_object_or_404(Session.objects.select_related('creator'), pk=pk)
        serializer = SessionSerializer(session)
        return Response(serializer.data)

class CreatorSessionListView(APIView):
    permission_classes = [IsCreator]

    def get(self, request):
        sessions = Session.objects.filter(creator=request.user).select_related('creator')
        serializer = SessionSerializer(sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SessionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreatorSessionDetailView(APIView):
    permission_classes = [IsCreator, IsSessionOwner]

    def get_object(self, pk):
        session = get_object_or_404(Session, pk=pk)
        self.check_object_permissions(self.request, session)
        return session

    def get(self, request, pk):
        session = self.get_object(pk)
        serializer = SessionSerializer(session)
        return Response(serializer.data)

    def patch(self, request, pk):
        session = self.get_object(pk)
        serializer = SessionSerializer(session, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        session = self.get_object(pk)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
