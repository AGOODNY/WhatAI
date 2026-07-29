from django.urls import path

from .views import (
    GomokuRespondView,
    IdiomRespondView,
    IdiomStartView,
    PoetryRespondView,
    PoetryStartView,
)


urlpatterns = [
    path("gomoku/respond/", GomokuRespondView.as_view()),
    path("idiom/start/", IdiomStartView.as_view()),
    path("idiom/respond/", IdiomRespondView.as_view()),
    path("poetry/start/", PoetryStartView.as_view()),
    path("poetry/respond/", PoetryRespondView.as_view()),
]
