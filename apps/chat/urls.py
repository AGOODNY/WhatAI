from django.urls import path
from .views import *

urlpatterns = [
    path("rooms/", ChatRoomListView.as_view()),
    path("rooms/create/", CreateChatRoomView.as_view()),
    path("rooms/<int:room_id>/messages/", MessageListView.as_view()),
]