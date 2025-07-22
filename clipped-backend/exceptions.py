from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from schemas.error import ErrorResponse


def register_exception_handlers(app: FastAPI):
    """
    Register global exception handlers for the FastAPI app.
    """
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        payload = ErrorResponse(
            status_code=exc.status_code,
            error=str(exc.detail)
        )
        return JSONResponse(status_code=exc.status_code, content=payload.dict())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Combine all validation errors into a single detail string
        details = "; ".join([f"{err['loc']}: {err['msg']}" for err in exc.errors()])
        payload = ErrorResponse(
            status_code=422,
            error="Validation Error",
            details=details
        )
        return JSONResponse(status_code=422, content=payload.dict())

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # TODO: add logging
        payload = ErrorResponse(
            status_code=500,
            error="Internal Server Error",
            details=str(exc)
        )
        return JSONResponse(status_code=500, content=payload.dict())
