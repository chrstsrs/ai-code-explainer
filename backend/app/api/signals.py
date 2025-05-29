# backend/app/api/signals.py
import os
from django.db.models.signals import post_migrate
from django.dispatch import receiver


def _seed_list():
    raw = os.getenv("SEED_LLM_MODELS", "mock:demo")  # default: only mock
    return [x.strip() for x in raw.split(",") if x.strip()]


@receiver(post_migrate)
def seed_llm_models(sender, **kwargs):
    from .models import LLMModel
    try:
        for name in _seed_list():
            LLMModel.objects.get_or_create(name=name,
                                           defaults={"is_active": True})
        # Optionally: deactivate anything NOT in the list to keep things tidy
        keep = set(_seed_list())
        for m in LLMModel.objects.exclude(name__in=keep):
            if m.is_active:
                m.is_active = False
                m.save(update_fields=["is_active"])
    except Exception:
        # Never break migrations due to seeding
        pass
