from django.urls import path
from .views import *

urlpatterns = [
    path("rooms/", ChatRoomListView.as_view()),
    path("rooms/create/", CreateChatRoomView.as_view()),
    path("rooms/<int:room_id>/messages/", MessageListView.as_view()),
    path("rooms/<int:room_id>/status/", RoomStatusView.as_view()),
    path("rooms/<int:room_id>/send/", SendMessageView.as_view()),
    path("rooms/<int:room_id>/delete/", DeleteRoomView.as_view()),
    path("rooms/<int:room_id>/toggle/", ToggleRoomActiveView.as_view()),
]
