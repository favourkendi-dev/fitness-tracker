#!/usr/bin/env python3

from datetime import date

from app import app
from models import db, Exercise, Workout, WorkoutExercise

# Run everything inside the Flask application context
with app.app_context():
    print("Creating database tables...")
    db.create_all()

    # Remove old records before adding new ones
    print("Clearing existing data...")
    WorkoutExercise.query.delete()
    Workout.query.delete()
    Exercise.query.delete()
    db.session.commit()

    # Create sample exercises
    print("Seeding exercises...")
    push_up = Exercise(name="Push Up", category="strength", equipment_needed=False)
    squat = Exercise(name="Squat", category="strength", equipment_needed=False)
    running = Exercise(name="Running", category="cardio", equipment_needed=False)
    deadlift = Exercise(name="Deadlift", category="strength", equipment_needed=True)
    yoga_flow = Exercise(name="Yoga Flow", category="flexibility", equipment_needed=False)

    db.session.add_all([push_up, squat, running, deadlift, yoga_flow])
    db.session.commit()

    # Create a few workout sessions
    print("Seeding workouts...")
    workout_1 = Workout(date=date(2026, 7, 1), duration_minutes=45, notes="Morning strength session")
    workout_2 = Workout(date=date(2026, 7, 3), duration_minutes=30, notes="Easy recovery run")
    workout_3 = Workout(date=date(2026, 7, 5), duration_minutes=60, notes="Full body + mobility")

    db.session.add_all([workout_1, workout_2, workout_3])
    db.session.commit()

    # Connect exercises with the workouts
    print("Linking exercises to workouts...")
    links = [
        WorkoutExercise(workout_id=workout_1.id, exercise_id=push_up.id, reps=15, sets=3),
        WorkoutExercise(workout_id=workout_1.id, exercise_id=squat.id, reps=12, sets=4),
        WorkoutExercise(workout_id=workout_2.id, exercise_id=running.id, duration_seconds=1800),
        WorkoutExercise(workout_id=workout_3.id, exercise_id=deadlift.id, reps=8, sets=5),
        WorkoutExercise(workout_id=workout_3.id, exercise_id=yoga_flow.id, duration_seconds=900),
    ]
    db.session.add_all(links)
    db.session.commit()

    print("Seeding complete!")