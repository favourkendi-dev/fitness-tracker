from datetime import date
from pathlib import Path

from flask import Flask, request, jsonify, make_response, render_template, redirect, url_for
from flask_migrate import Migrate
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from models import db, Exercise, Workout, WorkoutExercise
from schemas import (
    exercise_schema, exercises_schema,
    workout_schema, workouts_schema,
    workout_exercise_schema,
)

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{BASE_DIR / "app.db"}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'fitness-tracker-dev-secret'

migrate = Migrate(app, db)
db.init_app(app)


def seed_sample_data_if_needed():
    if Exercise.query.count() == 0 and Workout.query.count() == 0:
        sample_exercises = [
            Exercise(name='Push Up', category='strength', equipment_needed=False),
            Exercise(name='Squat', category='strength', equipment_needed=False),
            Exercise(name='Running', category='cardio', equipment_needed=False),
            Exercise(name='Yoga Flow', category='flexibility', equipment_needed=False),
        ]
        db.session.add_all(sample_exercises)
        db.session.commit()

        workout = Workout(date=date(2026, 7, 1), duration_minutes=45, notes='Morning strength session')
        db.session.add(workout)
        db.session.commit()

        db.session.add_all([
            WorkoutExercise(workout_id=workout.id, exercise_id=sample_exercises[0].id, reps=15, sets=3),
            WorkoutExercise(workout_id=workout.id, exercise_id=sample_exercises[2].id, duration_seconds=1800),
        ])
        db.session.commit()


with app.app_context():
    db.create_all()
    seed_sample_data_if_needed()


# html views

@app.route('/', methods=['GET'])
def home():
    workouts = Workout.query.order_by(Workout.date.desc()).all()
    exercises = Exercise.query.order_by(Exercise.name).all()
    return render_template('index.html', workouts=workouts, exercises=exercises)


@app.route('/dashboard/workouts', methods=['GET'])
def html_workouts():
    workouts = Workout.query.order_by(Workout.date.desc()).all()
    return render_template('workouts.html', workouts=workouts)


@app.route('/dashboard/workouts/new', methods=['GET'])
def new_workout_page():
    return render_template('workout_form.html', workout=None, errors=None)


@app.route('/dashboard/workouts/new', methods=['POST'])
def create_workout_page():
    try:
        workout = Workout(
            date=date.fromisoformat(request.form['date']),
            duration_minutes=int(request.form['duration_minutes']),
            notes=request.form.get('notes') or None,
        )
        db.session.add(workout)
        db.session.commit()
    except Exception as exc:
        return render_template('workout_form.html', workout=None, errors=[str(exc)]), 400

    return redirect(url_for('html_workout_detail', id=workout.id))


@app.route('/dashboard/workouts/<int:id>', methods=['GET'])
def html_workout_detail(id):
    workout = db.session.get(Workout, id)
    if not workout:
        return make_response("Workout not found", 404)
    return render_template('workout_detail.html', workout=workout, exercises=Exercise.query.order_by(Exercise.name).all())


@app.route('/dashboard/workouts/<int:workout_id>/link-exercise', methods=['POST'])
def link_exercise_to_workout_page(workout_id):
    workout = db.session.get(Workout, workout_id)
    if not workout:
        return make_response("Workout not found", 404)

    exercise_id = request.form.get('exercise_id')
    if not exercise_id:
        return redirect(url_for('html_workout_detail', id=workout.id))

    exercise = db.session.get(Exercise, int(exercise_id))
    if not exercise:
        return make_response("Exercise not found", 404)

    existing = WorkoutExercise.query.filter_by(workout_id=workout.id, exercise_id=exercise.id).first()
    if not existing:
        workout_exercise = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=exercise.id,
            reps=request.form.get('reps', type=int),
            sets=request.form.get('sets', type=int),
            duration_seconds=request.form.get('duration_seconds', type=int),
        )
        db.session.add(workout_exercise)
        db.session.commit()

    return redirect(url_for('html_workout_detail', id=workout.id))


@app.route('/dashboard/exercises', methods=['GET'])
def html_exercises():
    exercises = Exercise.query.order_by(Exercise.name).all()
    return render_template('exercises.html', exercises=exercises)


@app.route('/dashboard/exercises/new', methods=['GET'])
def new_exercise_page():
    return render_template('exercise_form.html', exercise=None, errors=None)


@app.route('/dashboard/exercises/new', methods=['POST'])
def create_exercise_page():
    try:
        exercise = Exercise(
            name=request.form['name'],
            category=request.form['category'],
            equipment_needed=request.form.get('equipment_needed') == 'on',
        )
        db.session.add(exercise)
        db.session.commit()
    except Exception as exc:
        return render_template('exercise_form.html', exercise=None, errors=[str(exc)]), 400

    return redirect(url_for('html_exercise_detail', id=exercise.id))


@app.route('/dashboard/exercises/<int:id>', methods=['GET'])
def html_exercise_detail(id):
    exercise = db.session.get(Exercise, id)
    if not exercise:
        return make_response("Exercise not found", 404)
    return render_template('exercise_detail.html', exercise=exercise)


# helpers

def workout_to_dict(workout, include_exercise_details=False):
    data = workout_schema.dump(workout)
    if include_exercise_details:
        data['exercises'] = [
            {
                'workout_exercise_id': we.id,
                'exercise_id': we.exercise.id,
                'name': we.exercise.name,
                'category': we.exercise.category,
                'equipment_needed': we.exercise.equipment_needed,
                'reps': we.reps,
                'sets': we.sets,
                'duration_seconds': we.duration_seconds,
            }
            for we in workout.workout_exercises
        ]
    else:
        data['exercises'] = [e.name for e in workout.exercises]
    return data


def exercise_to_dict(exercise):
    data = exercise_schema.dump(exercise)
    data['workouts'] = [w.id for w in exercise.workouts]
    return data


# My workout routes

@app.route('/workouts', methods=['GET'])
def get_workouts():
    workouts = Workout.query.all()
    return jsonify([workout_to_dict(w) for w in workouts]), 200


@app.route('/workouts/<int:id>', methods=['GET'])
def get_workout(id):
    workout = db.session.get(Workout, id)
    if not workout:
        return make_response(jsonify({'error': 'Workout not found'}), 404)
    return jsonify(workout_to_dict(workout, include_exercise_details=True)), 200


@app.route('/workouts', methods=['POST'])
def create_workout():
    json_data = request.get_json() or {}

    try:
        data = workout_schema.load(json_data)
    except ValidationError as err:
        return make_response(jsonify({'errors': err.messages}), 400)

    try:
        workout = Workout(
            date=data['date'],
            duration_minutes=data['duration_minutes'],
            notes=data.get('notes'),
        )
        db.session.add(workout)
        db.session.commit()
    except (ValueError, IntegrityError) as err:
        db.session.rollback()
        return make_response(jsonify({'errors': [str(err)]}), 400)

    return jsonify(workout_to_dict(workout)), 201


@app.route('/workouts/<int:id>', methods=['DELETE'])
def delete_workout(id):
    workout = db.session.get(Workout, id)
    if not workout:
        return make_response(jsonify({'error': 'Workout not found'}), 404)

    db.session.delete(workout)
    db.session.commit()
    return make_response(jsonify({}), 204)


# Exercise routes

@app.route('/exercises', methods=['GET'])
def get_exercises():
    exercises = Exercise.query.all()
    return jsonify([exercise_schema.dump(e) for e in exercises]), 200


@app.route('/exercises/<int:id>', methods=['GET'])
def get_exercise(id):
    exercise = db.session.get(Exercise, id)
    if not exercise:
        return make_response(jsonify({'error': 'Exercise not found'}), 404)
    return jsonify(exercise_to_dict(exercise)), 200


@app.route('/exercises', methods=['POST'])
def create_exercise():
    json_data = request.get_json() or {}

    try:
        data = exercise_schema.load(json_data)
    except ValidationError as err:
        return make_response(jsonify({'errors': err.messages}), 400)

    try:
        exercise = Exercise(
            name=data['name'],
            category=data['category'],
            equipment_needed=data['equipment_needed'],
        )
        db.session.add(exercise)
        db.session.commit()
    except (ValueError, IntegrityError) as err:
        db.session.rollback()
        return make_response(jsonify({'errors': [str(err)]}), 400)

    return jsonify(exercise_schema.dump(exercise)), 201


@app.route('/exercises/<int:id>', methods=['DELETE'])
def delete_exercise(id):
    exercise = db.session.get(Exercise, id)
    if not exercise:
        return make_response(jsonify({'error': 'Exercise not found'}), 404)

    db.session.delete(exercise)
    db.session.commit()
    return make_response(jsonify({}), 204)


# workout Exercise route

@app.route(
    '/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises',
    methods=['POST']
)
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.session.get(Workout, workout_id)
    exercise = db.session.get(Exercise, exercise_id)

    if not workout or not exercise:
        return make_response(jsonify({'error': 'Workout or Exercise not found'}), 404)

    # Prevent duplicate exercise-workout links
    existing = WorkoutExercise.query.filter_by(workout_id=workout.id, exercise_id=exercise.id).first()
    if existing:
        return make_response(jsonify({'error': 'Exercise already linked to this workout'}), 409)

    json_data = request.get_json() or {}

    try:
        data = workout_exercise_schema.load(json_data)
    except ValidationError as err:
        return make_response(jsonify({'errors': err.messages}), 400)

    try:
        workout_exercise = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=exercise.id,
            reps=data.get('reps'),
            sets=data.get('sets'),
            duration_seconds=data.get('duration_seconds'),
        )
        db.session.add(workout_exercise)
        db.session.commit()
    except (ValueError, IntegrityError) as err:
        db.session.rollback()
        return make_response(jsonify({'errors': [str(err)]}), 400)

    return jsonify(workout_exercise_schema.dump(workout_exercise)), 201


if __name__ == '__main__':
    app.run(port=5555, debug=True)
