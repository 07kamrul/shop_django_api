from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, ValueError):
        return Response({"message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, PermissionError):
        return Response({"message": str(exc)}, status=status.HTTP_403_FORBIDDEN)

    return Response(
        {"message": "An internal error occurred."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
