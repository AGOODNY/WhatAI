from django.urls import path

from .views import GomokuRespondView, IdiomRespondView, IdiomStartView


urlpatterns = [
    path("gomoku/respond/", GomokuRespondView.as_view()),
    path("idiom/start/", IdiomStartView.as_view()),
    path("idiom/respond/", IdiomRespondView.as_view()),
]
