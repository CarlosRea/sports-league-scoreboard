import logging
import os
from typing import Any

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
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
_tracer_provider: TracerProvider | None = None
_meter_provider: MeterProvider | None = None
_instrumented_apps: set[int] = set()
_instrumented_engines: set[int] = set()


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


def get_telemetry_metadata() -> dict[str, Any]:
    """Return dictionary of current telemetry configuration and resource attributes."""
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
    }


def get_in_memory_exporter() -> InMemorySpanExporter | None:
    """Return the active in-memory span exporter for testing or in-process verification."""
    return _in_memory_span_exporter


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
    Initialize OpenTelemetry tracing, metrics, and automatic instrumentation.
    Configures standard Resource attributes (service name, environment, deployed version)
    and attaches exporters.
    """
    global _in_memory_span_exporter, _tracer_provider, _meter_provider

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
        _meter_provider = MeterProvider(resource=resource)
        metrics.set_meter_provider(_meter_provider)

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
        "resource": resource,
    }
