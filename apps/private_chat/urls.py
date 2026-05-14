from django.urls import path

from .views import *

urlpatterns = [

    path(
        "rooms/",
        PrivateRoomListView.as_view()
    ),

    path(
        "rooms/create/",
        CreatePrivateRoomView.as_view()
    ),

    path(
        "rooms/<int:room_id>/messages/",
        PrivateMessageListView.as_view()
    ),

    path(
        "rooms/<int:room_id>/send/",
        SendPrivateMessageView.as_view()
    ),
]