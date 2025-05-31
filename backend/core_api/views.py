from rest_framework.response import Response
from core_api.serializers import BikeSerializer
from .models import Bike, APIKey
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from ratelimit import limits, sleep_and_retry

def api_key_required(view_func):
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("ApiKey "):
            return Response({"error": "Missing or Invalid Authorization Header"}, status=status.HTTP_403_FORBIDDEN)

        api_key = auth_header.split(" ")[1]
        if not APIKey.objects.filter(key=api_key).exists():
            return Response({"error": "Invalid API Key"}, status=status.HTTP_403_FORBIDDEN)

        return view_func(request, *args, **kwargs)
    return wrapper



@sleep_and_retry
@limits(calls=10, period=1)
@api_view(['GET'])
def get_bikes(request, id=None, category=None):
    if id is not None:
        try:
            bike = Bike.objects.get(id=id)
            serializer = BikeSerializer(bike)
            return Response(serializer.data)
        except Bike.DoesNotExist:
            return Response({"error": "Bike not found"}, status=status.HTTP_404_NOT_FOUND)

    elif category is not None:
        bikes = Bike.objects.filter(category__iexact=category)
        serializer = BikeSerializer(bikes, many=True)
        return Response(serializer.data)

    else:
        bikes = Bike.objects.all()
        serializer = BikeSerializer(bikes, many=True)
        return Response(serializer.data)


@api_view(['POST'])
@api_key_required
@csrf_exempt
def post_bikes(request):
    serializer = BikeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

