from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.contrib.gis.geos import Point

from psycopg2 import extensions


from .models import Ride
from .serializers import RideSerializer

# Register adapter so PostGIS can handle Django Point objects correctly
def adapt_point(point):
    return extensions.AsIs("ST_GeomFromText('%s', 4326)" % point.wkt)

extensions.register_adapter(Point, adapt_point)

class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer

    # ---------------------------
    # 🚗 Ride Request Endpoint
    # ---------------------------
    @action(detail=False, methods=['post'], url_path='request')
    def request_ride(self, request):
        try:
            lng1 = float(request.data['pickup_lng'])
            lat1 = float(request.data['pickup_lat'])
            lng2 = float(request.data['dropoff_lng'])
            lat2 = float(request.data['dropoff_lat'])
            rider_id = int(request.data['rider_id'])

            from django.contrib.gis.geos import GEOSGeometry
            pickup = GEOSGeometry(f'POINT({lng1} {lat1})', srid=4326)
            dropoff = GEOSGeometry(f'POINT({lng2} {lat2})', srid=4326)

            ride = Ride.objects.create(
                rider_id=rider_id,
                pickup_location=pickup,
                drop_off_location=dropoff,
                status='pending'
            )

            return Response(RideSerializer(ride).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    # ---------------------------
    # ✅ Ride Accept Endpoint
    # ---------------------------
    @action(detail=True, methods=['post'], url_path='accept')
    def accept_ride(self, request, pk=None):
        try:
            driver_id = int(request.data['driver_id'])

            with transaction.atomic():
                # Lock the ride row to avoid double acceptance
                ride = Ride.objects.select_for_update().get(pk=pk)
                ride.assign_driver(driver_id)  # Calls the method inside your Ride model

            return Response({'message': 'Ride accepted successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
