from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
)

health_schema = extend_schema(
    tags=["Health"],
    summary="Health check",
    description=(
        "Liveness check used by Render: returns 200 while the process is "
        "up. It doesn't check the database or Redis."
    ),
    auth=[],
    responses={
        200: OpenApiResponse(
            description="The server is running",
            examples=[OpenApiExample("OK", value={"status": "ok"})],
        ),
    },
)
