import pprint
import os
import pickle
import pandas as pd
from django.shortcuts import render
from sklearn.preprocessing import LabelEncoder
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from datetime import timedelta
from .models import Member, GymClass, Booking, Trainer, WorkoutRecommendation, WorkoutPlan
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from datetime import timedelta
from django.utils.timezone import now
from .models import Member
# Define base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define file paths
model_path = os.path.join(BASE_DIR, "myapp", "model.pkl")
encoder_path = os.path.join(BASE_DIR, "myapp", "label_encoder.pkl")
gym_path = os.path.join(BASE_DIR, "myapp", "Gymworkout.csv")

# Load gym workout data
gymworkout = pd.read_csv(gym_path)

# Load trained model and encoder
try:
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(encoder_path, "rb") as f:
        encoder = pickle.load(f)
except Exception as e:
    print(f"Error loading model or encoder: {e}")
    model, encoder = None, None


#Home index page 
def home(request):
    return render(request, 'index.html')




#recommendation page
def recommend(request):
    if request.method == 'POST':
        try:
            # Validate form data
            weight = request.POST.get('weight')
            height = request.POST.get('height')
            age = request.POST.get('age')
            gender = request.POST.get('gender')
            
            if not all([weight, height, age, gender]):
                return render(request, 'recommend.html', {'error': 'All fields are required.'})
            
            # Convert values
            w = float(weight)
            h = float(height)  # Convert height to meters
            age = int(age)
            
            if age < 16 or age > 60:
                return render(request, 'recommend.html', {'error': 'Workout recommendations are only available for ages 16-60.'})
            
            # Calculate BMI
            bmi = w / (h * h)
            
            if not model or not encoder:
                return render(request, 'recommend.html', {'error': 'Model is not available. Please try again later.'})
            
            # Prepare input data for the model
            input_data = pd.DataFrame({'Weight': [w], 'Height': [h], 'BMI': [bmi], 'Age': [age]})
            
            # Predict BMI category
            predicted_bmi_category = model.predict(input_data)
            predicted_bmi_encoded = encoder.inverse_transform(predicted_bmi_category)
            predicted_bmi_category = predicted_bmi_encoded[0]
            
            # Normalize category names
            predicted_bmi_category = predicted_bmi_category.strip().lower()
            gender = gender.strip().lower()
            
            # Normalize DataFrame columns
            gymworkout["BMI Case"] = gymworkout["BMI Case"].str.strip().str.lower()
            gymworkout["Gender"] = gymworkout["Gender"].str.strip().str.lower()
            
            # Debugging print
            print("Unique BMI Cases in CSV:", gymworkout["BMI Case"].unique())
            print("Unique Gender Values in CSV:", gymworkout["Gender"].unique())
            print("Predicted BMI Category:", predicted_bmi_category)
            print("User Gender Input:", gender)
            
            # Filter workout plan based on BMI category and gender
            filtered_df = gymworkout[
                (gymworkout["BMI Case"] == predicted_bmi_category) &
                (gymworkout["Gender"] == gender)
            ]
            
            print("Filtered DataFrame:")
            print(filtered_df)
            
            recommendations = []
            if not filtered_df.empty:
                for _, row in filtered_df.iterrows():
                    day_plan = {}
                    for i in range(1, 8):  # Loop from Day 1 to Day 7
                        day_plan[f"Day {i} Workout"] = row.get(f"Day {i} - Workout", "N/A")
                        day_plan[f"Day {i} Weight"] = row.get(f"Day {i} - Weight", "N/A")
                        day_plan[f"Day {i} Reps"] = row.get(f"Day {i} - Reps", "N/A")
                    recommendations.append(day_plan)
            
            print("Final Recommendations Data:")
            pprint.pprint(recommendations)
            
            restructure_data = restructure_workout_data(recommendations)
            
            return render(request, 'result.html', {
                'recommendations': restructure_data,  # Now a list of tuples
                'bmi_category': predicted_bmi_category,
                'bmi': round(bmi, 2),
                'age': age,
                'gender': gender,
            })
        
        except ValueError:
            return render(request, 'recommend.html', {'error': 'Invalid input values. Please enter numeric values correctly.'})
        except Exception as e:
            print(f"Error: {e}")
            return render(request, 'recommend.html', {'error': 'An unexpected error occurred. Please try again later.'})

    return render(request, 'recommend.html')



#fn to restructure dict value to structured format to display it in frontend
def restructure_workout_data(data):
    structured_data = {
        "Day": [],
        "Workout": [],
        "Weight": [],
        "Reps": []
    }
    
    if not data:
        return []
    
    for key in data[0].keys():
        parts = key.split()
        day = parts[1]
        category = parts[2]
        
        if f"Day {day}" not in structured_data["Day"]:
            structured_data["Day"].append(f"Day {day}")
        
        if category == "Workout":
            structured_data["Workout"].append(data[0][key])
        elif category == "Weight":
            structured_data["Weight"].append(data[0][key])
        elif category == "Reps":
            structured_data["Reps"].append(data[0][key])
    
    return list(zip(structured_data["Day"], structured_data["Workout"], structured_data["Weight"], structured_data["Reps"]))



#fn to save recommended workout plan basd on user
def save_workout_plan(request):
    if request.method == 'POST':
        user = request.user
        bmi_category = request.POST.get('bmi_category')
        bmi = float(request.POST.get('bmi'))
        age = int(request.POST.get('age'))
        gender = request.POST.get('gender')

        # Check if the user already has a saved recommendation
        recommendation, created = WorkoutRecommendation.objects.get_or_create(
            user=user,
            defaults={
                'bmi_category': bmi_category,
                'bmi_value': bmi,
                'age': age,
                'gender': gender
            }
        )

        # If recommendation already exists, update it
        if not created:
            recommendation.bmi_category = bmi_category
            recommendation.bmi_value = bmi
            recommendation.age = age
            recommendation.gender = gender
            recommendation.save()

            # Delete old workouts before adding new ones
            WorkoutPlan.objects.filter(recommendation=recommendation).delete()

        # Add new workout plans
        for i in range(1, 8):  # Loop from Day 1 to Day 7
            workout = request.POST.get(f'day_{i}_workout', 'N/A')
            weight = request.POST.get(f'day_{i}_weight', 'N/A')
            reps = request.POST.get(f'day_{i}_reps', 'N/A')

            WorkoutPlan.objects.create(
                recommendation=recommendation,
                day=i,
                workout=workout,
                weight=weight,
                reps=reps
            )

        return redirect('dashboard')  # Redirect to dashboard after saving

    return redirect('recommend')



#retrive saved workout plan 
@login_required
def saved_workout_plan(request):
    try:
        # Fetch the latest workout recommendation for the user
        saved_recommendation = WorkoutRecommendation.objects.filter(user=request.user).order_by('-created_at').first()

        if saved_recommendation:
            # Fetch associated workout plans
            workouts = WorkoutPlan.objects.filter(recommendation=saved_recommendation).order_by('day')
        else:
            workouts = None

    except WorkoutRecommendation.DoesNotExist:
        saved_recommendation = None
        workouts = None

    return render(request, 'saved_workout_plan.html', {
        'saved_recommendation': saved_recommendation,
        'workouts': workouts
    })


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# login form
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('/admin/')  # Redirect admins to Django admin panel
            else:
                return redirect('dashboard')  # Redirect members to index page
        else:
            messages.error(request, "Invalid username or password")
    
    return render(request, "login.html")


#registration form
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create the Member instance for the user
            join_date = now().date()
            expiry_date = join_date + timedelta(days=30)  # Auto-calculate expiry date

            Member.objects.create(
                user=user,
                name=user.username,
                join_date=join_date,
                expiry_date=expiry_date,
                status="Active"
            )

            login(request, user)  # Log in the user automatically
            return redirect('dashboard')  # Redirect to homepage or another page
    else:
        form = UserCreationForm()
    
    return render(request, "register.html", {"form": form})








#dashboard after logged in

@login_required
def dashboard(request):
    # Fetch user data
    member = Member.objects.get(user=request.user)
    bookings = Booking.objects.filter(user = request.user)
    trainers = Trainer.objects.all()
    classes = GymClass.objects.all()

    return render(request, 'dashboard.html', {
        'member': member,
        'bookings': bookings,
        'trainers': trainers,
        'classes' : classes
    })




#fn to book a class
@login_required
def book_class(request, class_id):
    gym_class = get_object_or_404(GymClass, id=class_id)
    
    # Check if the class is full
    if Booking.objects.filter(gym_class=gym_class).count() >= gym_class.capacity:
        messages.error(request, "Class is full")
    
    # Check if user already booked this class
    elif Booking.objects.filter(user=request.user, gym_class=gym_class).exists():
        messages.error(request, "Already Booked")

    else:

        Booking.objects.create(user=request.user, gym_class=gym_class)
        messages.success(request , "class booked!")
    return redirect('dashboard')


#fn to cancel a class
@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    booking.delete()

    messages.error(request, "Class cancelled")
    return redirect('dashboard')


#retriv booked classes for users
@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, 'my_bookings.html', {'bookings': bookings})




#retrive all trainer lists
def trainer_list(request):
    trainers = Trainer.objects.all()
    return render(request, 'trainer_list.html', {'trainers': trainers})



#logout fn
def logoutView(request):
    logout(request)
    return redirect('home')
    