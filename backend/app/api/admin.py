from django.contrib import admin
from .models import LLMModel, Snippet, Run, Feedback


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Snippet)
class SnippetAdmin(admin.ModelAdmin):
    list_display = ("id", "language", "title")
    search_fields = ("title", "code")


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    list_display = ("id", "snippet", "model", "status", "latency_ms")
    list_filter = ("status", "model")
    search_fields = ("response_text", "complexity_reasoning", "error_message")


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "run", "score")
    search_fields = ("comment",)
