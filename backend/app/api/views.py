import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from .models import LLMModel, Snippet, Run, Feedback
from .serializers import (
    LLMModelSerializer,
    SnippetCreateSerializer,
    SnippetDetailSerializer,
    RunSerializer,
    RunCreateSerializer,
    FeedbackSerializer,
)
from ai.registry import get_client_for_model


# Utility: ensure some defaults exist if table is empty (no users/admin assumed)
DEFAULT_MODELS = [
    "openai:gpt-4o-mini",
    "openai:gpt-3.5",
    "anthropic:claude-3-haiku",
    "mock:demo",
]


class ModelsListView(APIView):
    def get(self, request):
        if not LLMModel.objects.exists():
            LLMModel.objects.bulk_create(
                [LLMModel(name=name, is_active=True) for name in DEFAULT_MODELS],
                ignore_conflicts=True,
            )
        qs = LLMModel.objects.filter(is_active=True).order_by("name")
        return Response(LLMModelSerializer(qs, many=True).data, status=200)


class SnippetListCreateView(generics.ListCreateAPIView):
    """
    GET /api/v1/snippets/?limit=20  -> recent N snippets (ordered by id desc)
    POST /api/v1/snippets/          -> create snippet (unchanged behavior)
    """
    queryset = Snippet.objects.all()

    def get_queryset(self):
        try:
            limit = int(self.request.query_params.get("limit", 20))
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(limit, 100))  # cap to 100 for safety
        return Snippet.objects.order_by("-id")[:limit]

    def get_serializer_class(self):
        if self.request.method == "GET":
            from .serializers import SnippetListItemSerializer
            return SnippetListItemSerializer
        # POST
        return SnippetCreateSerializer


class SnippetDetailView(generics.RetrieveAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetDetailSerializer
    lookup_field = "pk"


class RunCreateView(APIView):
    """
    Create a single run for (snippet, model).
    Calls the appropriate LLM client adapter, normalizes response, persists Run.
    """

    def post(self, request):
        s = RunCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        snippet = s.validated_data["snippet"]
        llm_model = s.validated_data["llm_model"]

        client = get_client_for_model(llm_model.name)
        started = time.perf_counter()
        try:
            result = client.explain(
                language=snippet.language,
                snippet=snippet.code,
                want_tests=bool((snippet.options_json or {}).get("tests", True)),
            )
            latency_ms = int((time.perf_counter() - started) * 1000)

            run = Run.objects.create(
                snippet=snippet,
                model=llm_model,
                status=Run.STATUS_OK,
                response_text=result.get("explanation", "") or "",
                complexity_time=(result.get("complexity") or {}).get("time", "") or "",
                complexity_space=(result.get("complexity") or {}).get("space", "") or "",
                complexity_reasoning=(result.get("complexity") or {}).get("reasoning", "") or "",
                latency_ms=latency_ms,
            )
            return Response(RunSerializer(run).data, status=status.HTTP_201_CREATED)

        except client.RateLimitedError as e:  # type: ignore[attr-defined]
            latency_ms = int((time.perf_counter() - started) * 1000)
            run = Run.objects.create(
                snippet=snippet,
                model=llm_model,
                status=Run.STATUS_RATE_LIMITED,
                response_text="",
                complexity_time="",
                complexity_space="",
                complexity_reasoning="",
                latency_ms=latency_ms,
                error_code="RATE_LIMITED",
                error_message=str(e),
            )
            return Response(RunSerializer(run).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            latency_ms = int((time.perf_counter() - started) * 1000)
            run = Run.objects.create(
                snippet=snippet,
                model=llm_model,
                status=Run.STATUS_ERROR,
                response_text="",
                complexity_time="",
                complexity_space="",
                complexity_reasoning="",
                latency_ms=latency_ms,
                error_code="UNEXPECTED_ERROR",
                error_message=str(e),
            )
            return Response(RunSerializer(run).data, status=status.HTTP_201_CREATED)


class FeedbackUpsertView(APIView):
    """
    One feedback per run. Upsert behavior.
    """

    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            return Response(FeedbackSerializer(obj).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
