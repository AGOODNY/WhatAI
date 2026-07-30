from django.urls import path

from .views import PersonaDetailView, PersonaListCreateView


urlpatterns = [
    path("", PersonaListCreateView.as_view()),
    path("<int:persona_id>/", PersonaDetailView.as_view()),
]
