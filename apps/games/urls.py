from django.urls import path

from .views import GomokuRespondView


urlpatterns = [
    path("gomoku/respond/", GomokuRespondView.as_view()),
]

