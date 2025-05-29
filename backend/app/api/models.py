from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class LLMModel(models.Model):
    """
    Registry of available models. Provider is embedded in `name`, e.g.:
    - "openai:gpt-4o-mini"
    - "openai:gpt-3.5"
    - "anthropic:claude-3-haiku"
    - "mock:demo"
    """
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Snippet(models.Model):
    language = models.CharField(max_length=32, default="python")
    code = models.TextField()
    options_json = models.JSONField(null=True, blank=True)
    title = models.CharField(max_length=120, null=True, blank=True)

    def __str__(self):
        return self.title or f"Snippet #{self.pk}"


class Run(models.Model):
    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    STATUS_TIMEOUT = "timeout"
    STATUS_RATE_LIMITED = "rate_limited"

    STATUS_CHOICES = [
        (STATUS_OK, "OK"),
        (STATUS_ERROR, "Error"),
        (STATUS_TIMEOUT, "Timeout"),
        (STATUS_RATE_LIMITED, "Rate limited"),
    ]

    snippet = models.ForeignKey(Snippet, on_delete=models.CASCADE, related_name="runs")
    model = models.ForeignKey(LLMModel, on_delete=models.PROTECT, related_name="runs")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OK)

    # Normalized response fields
    response_text = models.TextField(blank=True, default="")
    complexity_time = models.CharField(max_length=32, blank=True, default="")
    complexity_space = models.CharField(max_length=32, blank=True, default="")
    complexity_reasoning = models.TextField(blank=True, default="")

    # Telemetry / errors
    latency_ms = models.IntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=64, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Run #{self.pk} ({self.model.name})"


class Feedback(models.Model):
    run = models.OneToOneField(Run, on_delete=models.CASCADE, related_name="feedback")
    score = models.IntegerField(validators=[MinValueValidator(-100), MaxValueValidator(100)])
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Feedback for run #{self.run_id}: {self.score}"
