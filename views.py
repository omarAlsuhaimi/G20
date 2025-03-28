from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.contrib.gis.geos import Point
from django.db.models import Func, F, Value
from django.contrib.gis.db.models.functions import Distance as GISDistance
from .models import Ride, Typemultiplier, Surgearea
from .serializers import RideSerializer
from django.contrib.gis.db.models import PointField

class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer

    # -----------------------------------------
    # 🚗 Ride Request Endpoint
    # -----------------------------------------
    @action(detail=False, methods=['post'], url_path='request')
    def request_ride(self, request):
        try:
            lng1 = float(request.data['pickup_lng'])
            lat1 = float(request.data['pickup_lat'])
            lng2 = float(request.data['dropoff_lng'])
            lat2 = float(request.data['dropoff_lat'])
            rider_id = int(request.data['rider_id'])
            type_str = request.data.get('type')

            # Create pickup and dropoff Points
            pickup = Point(lng1, lat1, srid=4326)
            dropoff = Point(lng2, lat2, srid=4326)

            # 💡 Calculate distance between pickup and dropoff in km
            distance_km = round(pickup.distance(dropoff) * 100, 2)  # Approximate (1 deg ≈ 100 km)

            # 🌀 Detect surge area
            surge_areas = Surgearea.objects.annotate(
                surge_geom=Func(
                    F('longitude'),
                    F('latitude'),
                    function='ST_SetSRID',
                    template='ST_SetSRID(ST_MakePoint(%(expressions)s), 4326)',
                    output_field=PointField()
                ),
                dist=GISDistance(Value(pickup), Func(
                    F('longitude'),
                    F('latitude'),
                    function='ST_SetSRID',
                    template='ST_SetSRID(ST_MakePoint(%(expressions)s), 4326)',
                    output_field=PointField()
                ))
            ).filter(dist__lte=F('radius')).order_by('dist')

            detected_surge = surge_areas.first()
            surge_multiplier = float(detected_surge.multiplier) if detected_surge else 1.0

            # 🚘 Get vehicle type multiplier
            vehicle_type = Typemultiplier.objects.get(type=type_str)
            type_multiplier = float(vehicle_type.multiplier)
            rate_per_hour= 37.88
            # 💰 Price = distance × surge × type
            price = round(((distance_km/40)*rate_per_hour) * surge_multiplier * type_multiplier, 2)

            # 🛒 Create the ride
            ride = Ride.objects.create(
                rider_id=rider_id,
                pickup_location=pickup,
                drop_off_location=dropoff,
                distance=distance_km,
                surge=detected_surge,
                price=price,
                status='pending'
            )

            return Response(RideSerializer(ride).data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # -----------------------------------------
    # ✅ Accept Ride Endpoint
    # -----------------------------------------
    @action(detail=True, methods=['post'], url_path='accept')
    def accept_ride(self, request, pk=None):
        try:
            driver_id = int(request.data['driver_id'])

            with transaction.atomic():
                # Lock row to prevent race conditions
                ride = Ride.objects.select_for_update().get(pk=pk)
                if ride.status != 'pending':
                    raise Exception("Ride is already accepted or completed.")
                ride.driver_id = driver_id
                ride.status = 'accepted'
                ride.save()

            return Response({'message': 'Ride accepted successfully'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
