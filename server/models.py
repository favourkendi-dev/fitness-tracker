from datetime import date as date_cls

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates
from flask_sqlalchemy import SQLAlchemy

# I Created  the SQLAlchemy database instance
db = SQLAlchemy()


class Exercise(db.Model):
    # Stores all the exercises available in the application
    __tablename__ = 'exercises'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    equipment_needed = db.Column(db.Boolean, nullable=False, default=False)

    # One exercise can appear in many workout records
    workout_exercises = db.relationship(
        'WorkoutExercise',
        back_populates='exercise',
        cascade='all, delete-orphan'
    )

    # Makes it easy to access workouts for an exercise
    workouts = db.relationship(
        'Workout',
        secondary='workout_exercises',
        back_populates='exercises',
        viewonly=True
    )

    # Prevent empty names and duplicate exercise names
    __table_args__ = (
        CheckConstraint("length(name) > 0", name='ck_exercise_name_not_empty'),
        UniqueConstraint('name', name='uq_exercise_name'),
    )

    # These are the only exercise categories allowed
    ALLOWED_CATEGORIES = ('cardio', 'strength', 'flexibility', 'balance')

    # Check that the category entered is valid
    @validates('category')
    def validate_category(self, key, category):
        if category is None or category.lower() not in self.ALLOWED_CATEGORIES:
            raise ValueError(
                f"category must be one of {self.ALLOWED_CATEGORIES}"
            )
        return category.lower()

    # Clean and validate the exercise name
    @validates('name')
    def validate_name(self, key, name):
        if not name or not name.strip():
            raise ValueError("name must not be empty")
        if len(name) > 100:
            raise ValueError("name must be 100 characters or fewer")
        return name.strip()

    def __repr__(self):
        return f'<Exercise {self.id}: {self.name} ({self.category})>'


class Workout(db.Model):
    # Stores information about each workout session
    __tablename__ = 'workouts'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date_cls.today)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)

    # Connect workouts to their exercises
    workout_exercises = db.relationship(
        'WorkoutExercise',
        back_populates='workout',
        cascade='all, delete-orphan'
    )

    # Allows direct access to exercises in a workout
    exercises = db.relationship(
        'Exercise',
        secondary='workout_exercises',
        back_populates='workouts',
        viewonly=True
    )

    # Workout duration should always be greater than zero
    __table_args__ = (
        CheckConstraint('duration_minutes > 0', name='ck_workout_duration_positive'),
    )

    # Make sure the duration entered is valid
    @validates('duration_minutes')
    def validate_duration_minutes(self, key, value):
        if value is None or not isinstance(value, int) or value <= 0:
            raise ValueError("duration_minutes must be a positive integer")
        return value

    def __repr__(self):
        return f'<Workout {self.id} on {self.date}>'


class WorkoutExercise(db.Model):
    # This table links workouts and exercises together
    __tablename__ = 'workout_exercises'

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workouts.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    reps = db.Column(db.Integer)
    sets = db.Column(db.Integer)
    duration_seconds = db.Column(db.Integer)

    # Relationship back to the workout
    workout = db.relationship('Workout', back_populates='workout_exercises')

    # Relationship back to the exercise
    exercise = db.relationship('Exercise', back_populates='workout_exercises')

    # Prevent negative values from being stored
    __table_args__ = (
        CheckConstraint('reps IS NULL OR reps >= 0', name='ck_we_reps_nonnegative'),
        CheckConstraint('sets IS NULL OR sets >= 0', name='ck_we_sets_nonnegative'),
    )

    # Check that reps the sets and duration are not negative
    @validates('reps', 'sets', 'duration_seconds')
    def validate_non_negative(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} must be a non-negative integer")
        return value

    def __repr__(self):
        return (
            f'<WorkoutExercise {self.id} workout={self.workout_id} '
            f'exercise={self.exercise_id}>'
        )