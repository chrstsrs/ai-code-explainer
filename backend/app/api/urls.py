from django.urls import path
from .views import (
    ModelsListView,
    SnippetListCreateView,
    SnippetDetailView,
    RunCreateView,
    FeedbackUpsertView,
)

urlpatterns = [
    path("v1/models/", ModelsListView.as_view(), name="models-list"),
    path("v1/snippets/", SnippetListCreateView.as_view(), name="snippets-list-create"),
    path("v1/snippets/<int:pk>/", SnippetDetailView.as_view(), name="snippets-detail"),
    path("v1/runs/", RunCreateView.as_view(), name="runs-create"),
    path("v1/feedback/", FeedbackUpsertView.as_view(), name="feedback-upsert"),
]
