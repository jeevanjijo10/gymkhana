

from django.contrib import admin
from .models import Member, GymClass, Booking,Trainer, WorkoutPlan, WorkoutRecommendation

admin.site.register(Member)
admin.site.register(GymClass)
admin.site.register(Booking)
admin.site.register(Trainer)
admin.site.register(WorkoutPlan)
admin.site.register(WorkoutRecommendation)

