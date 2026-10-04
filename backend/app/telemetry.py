import logging
import os
from collections.abc import Iterable
from typing import Any

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.metrics import Observation
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.semconv.resource import ResourceAttributes

from app.config import settings

logger = logging.getLogger("uvicorn.telemetry")

_in_memory_span_exporter: InMemorySpanExporter | None = None
_in_memory_metric_reader: InMemoryMetricReader | None = None
_tracer_provider: TracerProvider | None = None
_meter_provider: MeterProvider | None = None
_instrumented_apps: set[int] = set()
_instrumented_engines: set[int] = set()

# Application Metric Instruments
_matches_created_counter: metrics.Counter | None = None
_score_updates_counter: metrics.Counter | None = None
_score_update_failures_counter: metrics.Counter | None = None

# Internal tracking for quick metadata introspection
_matches_created_count: int = 0
_score_updates_registered_count: int = 0
_score_update_failures_count: int = 0


def get_telemetry_resource() -> Resource:
    """Build OpenTelemetry Resource populated with service name, environment, and deployed version."""
    service_name = settings.SERVICE_NAME
    environment = settings.ENVIRONMENT
    deployed_version = settings.DEPLOYED_VERSION

    attributes: dict[str, Any] = {
        # Service Name
        ResourceAttributes.SERVICE_NAME: service_name,
        "service.name": service_name,
        "service_name": service_name,
        # Environment
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: environment,
        "deployment.environment": environment,
        "environment": environment,
        # Deployed Version
        ResourceAttributes.SERVICE_VERSION: deployed_version,
        "service.version": deployed_version,
        "deployed_version": deployed_version,
        "deployed.version": deployed_version,
    }

    return Resource.create(attributes)


def get_active_matches_count() -> int:
    """Query database for the current number of ongoing or active matches (IN_PROGRESS)."""
    try:
        from sqlalchemy import func, select

        from app.db.models import MatchDB
        from app.db.session import get_db_context
        from app.models.match import MatchStatus

        with get_db_context() as session:
            count = session.scalar(
                select(func.count(MatchDB.id)).where(
                    MatchDB.status == MatchStatus.IN_PROGRESS.value
                )
            )
            return int(count or 0)
    except Exception as e:
        logger.debug("Active matches count evaluation: %s", e)
        return 0


def _observe_active_matches(options: Any = None) -> Iterable[Observation]:
    """Callback for OpenTelemetry Observable Gauge measuring active live matches."""
    count = get_active_matches_count()
    yield Observation(
        count,
        {
            "environment": settings.ENVIRONMENT,
            "deployed_version": settings.DEPLOYED_VERSION,
        },
    )


def record_match_created(entity_type: str = "match") -> None:
    """
    Record creation of a match fixture or league.
    Includes environment and deployed version in telemetry attributes.
    """
    global _matches_created_count, _matches_created_counter
    _matches_created_count += 1
    if _matches_created_counter:
        _matches_created_counter.add(
            1,
            {
                "type": entity_type,
                "environment": settings.ENVIRONMENT,
                "deployed_version": settings.DEPLOYED_VERSION,
            },
        )


def record_score_update_registered(match_id: str | None = None) -> None:
    """
    Record successful submission of a live score or match event.
    Includes environment and deployed version in telemetry attributes.
    """
    global _score_updates_registered_count, _score_updates_counter
    _score_updates_registered_count += 1
    if _score_updates_counter:
        _score_updates_counter.add(
            1,
            {
                "environment": settings.ENVIRONMENT,
                "deployed_version": settings.DEPLOYED_VERSION,
                "status": "success",
            },
        )


def record_score_update_failure(
    reason: str = "validation_error", match_id: str | None = None
) -> None:
    """
    Record a failed score submission or validation error.
    Includes environment and deployed version in telemetry attributes.
    """
    global _score_update_failures_count, _score_update_failures_counter
    _score_update_failures_count += 1
    if _score_update_failures_counter:
        _score_update_failures_counter.add(
            1,
            {
                "environment": settings.ENVIRONMENT,
                "deployed_version": settings.DEPLOYED_VERSION,
                "reason": reason,
            },
        )


def get_application_metrics_summary() -> dict[str, int]:
    """Return dictionary summary of tracked application metrics."""
    return {
        "matches_created": _matches_created_count,
        "active_live_matches": get_active_matches_count(),
        "score_updates_registered": _score_updates_registered_count,
        "score_update_failures": _score_update_failures_count,
    }


def reset_application_metrics() -> None:
    """Reset application metrics counters (useful for unit testing isolation)."""
    global _matches_created_count, _score_updates_registered_count, _score_update_failures_count
    _matches_created_count = 0
    _score_updates_registered_count = 0
    _score_update_failures_count = 0


def get_telemetry_metadata() -> dict[str, Any]:
    """Return dictionary of current telemetry configuration, resource attributes, and application metrics."""
    service_name = settings.SERVICE_NAME
    environment = settings.ENVIRONMENT
    deployed_version = settings.DEPLOYED_VERSION
    enabled = settings.OTEL_ENABLED

    resource = get_telemetry_resource()
    resource_attrs = {str(k): str(v) for k, v in resource.attributes.items()}

    return {
        "service_name": service_name,
        "environment": environment,
        "deployed_version": deployed_version,
        "enabled": enabled,
        "resource_attributes": resource_attrs,
        "application_metrics": get_application_metrics_summary(),
    }


def get_in_memory_exporter() -> InMemorySpanExporter | None:
    """Return the active in-memory span exporter for testing or in-process verification."""
    return _in_memory_span_exporter


def get_in_memory_metric_reader() -> InMemoryMetricReader | None:
    """Return the active in-memory metric reader for testing or in-process verification."""
    return _in_memory_metric_reader


def get_tracer(name: str = "sports-league-scoreboard") -> trace.Tracer:
    """Return an OpenTelemetry Tracer instance."""
    return trace.get_tracer(name)


def get_meter(name: str = "sports-league-scoreboard") -> metrics.Meter:
    """Return an OpenTelemetry Meter instance."""
    return metrics.get_meter(name)


def _server_request_hook(span: Any, scope: dict) -> None:
    """Enrich HTTP spans with service name, environment, and deployed version attributes."""
    if span and span.is_recording():
        span.set_attribute("service.name", settings.SERVICE_NAME)
        span.set_attribute("environment", settings.ENVIRONMENT)
        span.set_attribute("deployment.environment", settings.ENVIRONMENT)
        span.set_attribute("deployed_version", settings.DEPLOYED_VERSION)
        span.set_attribute("service.version", settings.DEPLOYED_VERSION)


def setup_telemetry(app: FastAPI | None = None, engine: Any = None) -> dict[str, Any]:
    """
    Initialize OpenTelemetry tracing, metrics, application meters, and automatic instrumentation.
    Configures standard Resource attributes (service name, environment, deployed version)
    and attaches exporters and application metric counters/gauges.
    """
    global _in_memory_span_exporter, _in_memory_metric_reader
    global _tracer_provider, _meter_provider
    global _matches_created_counter, _score_updates_counter, _score_update_failures_counter

    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry is disabled via configuration.")
        return {"enabled": False}

    resource = get_telemetry_resource()

    if _tracer_provider is None:
        _tracer_provider = TracerProvider(resource=resource)
        _in_memory_span_exporter = InMemorySpanExporter()
        _tracer_provider.add_span_processor(SimpleSpanProcessor(_in_memory_span_exporter))

        # Check for OTLP exporter endpoint
        otlp_endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
        if otlp_endpoint:
            logger.info("Configuring OTLP HTTP trace exporter to %s", otlp_endpoint)
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            _tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Check for console trace exporter
        if os.getenv("OTEL_TRACES_EXPORTER", "").strip().lower() == "console":
            _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

        trace.set_tracer_provider(_tracer_provider)

    if _meter_provider is None:
        readers: list[Any] = []
        _in_memory_metric_reader = InMemoryMetricReader()
        readers.append(_in_memory_metric_reader)

        otlp_endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT
        if otlp_endpoint:
            # Derive metrics endpoint (e.g. http://host:4318/v1/metrics or same base)
            metrics_endpoint = os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT")
            if not metrics_endpoint:
                if "/v1/traces" in otlp_endpoint:
                    metrics_endpoint = otlp_endpoint.replace("/v1/traces", "/v1/metrics")
                else:
                    metrics_endpoint = f"{otlp_endpoint.rstrip('/')}/v1/metrics"
            logger.info("Configuring OTLP HTTP metric exporter to %s", metrics_endpoint)
            otlp_metric_exporter = OTLPMetricExporter(endpoint=metrics_endpoint)
            readers.append(
                PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=15000)
            )

        _meter_provider = MeterProvider(resource=resource, metric_readers=readers)
        metrics.set_meter_provider(_meter_provider)

        # Initialize Application Metrics Instruments
        meter = _meter_provider.get_meter("scoreboard-application-metrics")
        _matches_created_counter = meter.create_counter(
            name="matches_created_total",
            unit="{matches}",
            description="Total matches or leagues created",
        )
        _score_updates_counter = meter.create_counter(
            name="score_updates_registered_total",
            unit="{updates}",
            description="Total score and match event updates submitted",
        )
        _score_update_failures_counter = meter.create_counter(
            name="score_update_failures_total",
            unit="{failures}",
            description="Total failed score submissions or validation errors",
        )
        meter.create_observable_gauge(
            name="active_live_matches",
            callbacks=[_observe_active_matches],
            unit="{matches}",
            description="Currently ongoing or active live matches",
        )

    # Instrument FastAPI application if provided
    if app is not None and id(app) not in _instrumented_apps:
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=_tracer_provider,
            meter_provider=_meter_provider,
            server_request_hook=_server_request_hook,
        )
        _instrumented_apps.add(id(app))
        logger.info(
            "OpenTelemetry FastAPI instrumented (service: %s, env: %s, version: %s)",
            settings.SERVICE_NAME,
            settings.ENVIRONMENT,
            settings.DEPLOYED_VERSION,
        )

    # Instrument SQLAlchemy database engine if provided
    if engine is not None and id(engine) not in _instrumented_engines:
        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            tracer_provider=_tracer_provider,
        )
        _instrumented_engines.add(id(engine))
        logger.info("OpenTelemetry SQLAlchemy engine instrumented.")

    return {
        "enabled": True,
        "tracer_provider": _tracer_provider,
        "meter_provider": _meter_provider,
        "in_memory_exporter": _in_memory_span_exporter,
        "in_memory_metric_reader": _in_memory_metric_reader,
        "resource": resource,
    }
