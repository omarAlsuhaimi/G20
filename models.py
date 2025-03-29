from django.db import models


from django.contrib.gis.db import models


class Driver(models.Model):
    driver_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    phone_num = models.CharField(unique=True, max_length=15)
    email = models.CharField(unique=True, max_length=150, blank=True, null=True)
    license = models.CharField(unique=True, max_length=50)
    status = models.CharField(max_length=20)
    longitude = models.FloatField()
    latitude = models.FloatField()
    vehicle = models.ForeignKey('Vehicle', models.DO_NOTHING, blank=True, null=True)
    current_location = models.PointField()

    class Meta:
        managed = False
        db_table = 'driver'


class Ride(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
    ]

    ride_id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=20)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    distance_traveled = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    distance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rider = models.ForeignKey('Rider', models.DO_NOTHING)
    driver = models.ForeignKey('Driver', models.DO_NOTHING, blank=True, null=True)
    surge = models.ForeignKey('Surgearea', models.DO_NOTHING, blank=True, null=True)
    pickup_location = models.PointField()
    drop_off_location = models.PointField()
    route = models.LineStringField()

    class Meta:
        managed = True
        db_table = 'ride'

  


class Rider(models.Model):
    rider_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    phone_num = models.CharField(unique=True, max_length=15)
    email = models.CharField(unique=True, max_length=150, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rider'


class SpatialRefSys(models.Model):
    srid = models.IntegerField(primary_key=True)
    auth_name = models.CharField(max_length=256, blank=True, null=True)
    auth_srid = models.IntegerField(blank=True, null=True)
    srtext = models.CharField(max_length=2048, blank=True, null=True)
    proj4text = models.CharField(max_length=2048, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'spatial_ref_sys'


class Suitabledriver(models.Model):
    ride = models.OneToOneField(Ride, models.DO_NOTHING,
                                primary_key=True)
    driver = models.ForeignKey(Driver, models.DO_NOTHING)
    response = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'suitabledriver'
        unique_together = (('ride', 'driver'),)


class Surgearea(models.Model):
    surge_id = models.AutoField(primary_key=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    name = models.CharField(max_length=100, blank=True, null=True)
    radius = models.FloatField()
    multiplier = models.DecimalField(max_digits=5, decimal_places=2)
    location = models.PointField()

    class Meta:
        managed = False
        db_table = 'surgearea'


class Typemultiplier(models.Model):
    type = models.CharField(primary_key=True, max_length=50)
    multiplier = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'typemultiplier'


class Vehicle(models.Model):
    vehicle_id = models.AutoField(primary_key=True)
    make = models.IntegerField(blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    plate_number = models.CharField(unique=True, max_length=20)
    model = models.CharField(max_length=50, blank=True, null=True)
    type = models.ForeignKey(Typemultiplier, models.DO_NOTHING, db_column='type')

    class Meta:
        managed = False
        db_table = 'vehicle'

