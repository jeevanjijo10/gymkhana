from django.db import models
from django.contrib.auth.models import User

class Member(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Paused', 'Paused')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)  # Allow NULL
    name = models.CharField(max_length=100)
    join_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')  # New field

    def __str__(self):
        return self.name


class GymClass(models.Model):
    name = models.CharField(max_length=100)
    trainer = models.ForeignKey('Trainer', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField()
    capacity = models.IntegerField(default=10)

    def __str__(self):
        return f"{self.name} - {self.date.strftime('%Y-%m-%d %H:%M')}"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    gym_class = models.ForeignKey(GymClass, on_delete=models.CASCADE, null=True, default=None)  # Temporary default
    booked_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.username} booked {self.gym_class.name}"

    

class Trainer(models.Model):
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    experience = models.IntegerField(help_text="Years of experience", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name    
    

class WorkoutRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to User
    bmi_category = models.CharField(max_length=50)
    bmi_value = models.FloatField()
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp

    def __str__(self):
        return f"{self.user.username} - {self.bmi_category} - {self.bmi_value}"


class WorkoutPlan(models.Model):
    recommendation = models.ForeignKey(WorkoutRecommendation, on_delete=models.CASCADE, related_name="workouts")
    day = models.IntegerField()  # Day 1 - 7
    workout = models.CharField(max_length=255)
    weight = models.CharField(max_length=50, blank=True, null=True)  # Some workouts may not have weights
    reps = models.CharField(max_length=50, blank=True, null=True)  # Some workouts may not have reps

    def __str__(self):
        return f"Day {self.day} - {self.workout}"
