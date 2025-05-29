from rest_framework import serializers
from .models import LLMModel, Snippet, Run, Feedback


class LLMModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMModel
        fields = ["id", "name", "is_active"]


class SnippetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snippet
        fields = ["id", "language", "code", "options_json", "title"]


class SnippetListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snippet
        fields = ["id", "language", "title"]


class FeedbackSerializer(serializers.ModelSerializer):
    run = serializers.PrimaryKeyRelatedField(
        queryset=Run.objects.all(), validators=[])

    class Meta:
        model = Feedback
        fields = ["run", "score", "comment"]

    def create(self, validated_data):
        # Upsert (one feedback per run)
        run = validated_data["run"]
        obj, _ = Feedback.objects.update_or_create(
            run=run,
            defaults={
                "score": validated_data["score"],
                "comment": validated_data.get("comment"),
            },
        )
        return obj

class RunSerializer(serializers.ModelSerializer):
    model = LLMModelSerializer(read_only=True)
    feedback = FeedbackSerializer(read_only=True)

    class Meta:
        model = Run
        fields = [
            "id",
            "snippet",
            "model",
            "status",
            "response_text",
            "complexity_time",
            "complexity_space",
            "complexity_reasoning",
            "latency_ms",
            "error_code",
            "error_message",
            "feedback",
        ]


class RunCreateSerializer(serializers.Serializer):
    snippetId = serializers.IntegerField()
    modelId = serializers.IntegerField()

    def validate(self, attrs):
        # Attach instances for use in the view
        try:
            attrs["snippet"] = Snippet.objects.get(pk=attrs["snippetId"])
        except Snippet.DoesNotExist:
            raise serializers.ValidationError({"snippetId": "Snippet not found."})
        try:
            attrs["llm_model"] = LLMModel.objects.get(pk=attrs["modelId"], is_active=True)
        except LLMModel.DoesNotExist:
            raise serializers.ValidationError({"modelId": "Model not found or inactive."})
        return attrs


class SnippetDetailSerializer(serializers.ModelSerializer):
    runs = RunSerializer(many=True, read_only=True)

    class Meta:
        model = Snippet
        fields = ["id", "language", "code", "options_json", "title", "runs"]
