from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

class BookingError(Exception):
    def __init__(self, detail, status_code=status.HTTP_409_CONFLICT):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)

def custom_exception_handler(exc, context):
    if isinstance(exc, BookingError):
        return Response({"detail": exc.detail}, status=exc.status_code)
        
    response = exception_handler(exc, context)
    
    if response is not None:
        # Standardize error message payload to {"detail": "..."} format if necessary
        if isinstance(response.data, dict) and "detail" not in response.data:
            first_val = list(response.data.values())[0]
            if isinstance(first_val, list) and len(first_val) > 0:
                response.data = {"detail": str(first_val[0])}
            else:
                response.data = {"detail": str(first_val)}
                
    return response
