# Fitness Tracker API

A Flask REST API for tracking workouts and exercises. Users can create, view,
and delete workouts and exercises, and attach exercises to a workout with
specific reps, sets, and duration.

## Project Description

This API models three resources:

- **Exercise** — `id`, `name`, `category`, `equipment_needed`
- **Workout** — `id`, `date`, `duration_minutes`, `notes`
- **WorkoutExercise** (join table) — `id`, `workout_id`, `exercise_id`, `reps`, `sets`, `duration_seconds`

**Relationships**

- A `WorkoutExercise` belongs to a `Workout` and belongs to an `Exercise`
- A `Workout` has many `WorkoutExercises` and has many `Exercises` through `WorkoutExercises`
- An `Exercise` has many `WorkoutExercises` and has many `Workouts` through `WorkoutExercises`

Validation is enforced at three levels:

| Level              | Examples                                                                 |
|--------------------|---------------------------------------------------------------------------|
| Table constraints  | `exercises.name` is unique and non-empty; `workouts.duration_minutes > 0`; `workout_exercises.reps/sets >= 0` |
| Model validations  | `Exercise.category` restricted to an allowed list; `Exercise.name`/`Workout.duration_minutes` type/blank checks |
| Schema validations  | `category` must be one of an allowed set; `duration_minutes` must be > 0; at least one of `reps`/`sets`/`duration_seconds` required when linking an exercise to a workout |

## Installation

1. Clone the repo and move into it:
   ```bash
   git clone https://github.com/favourkendi-dev/fitness-tracker.git
   cd fitness-tracker-api
   ```
2. Install dependencies with pipenv:
   ```bash
   pipenv install
   pipenv shell
   ```
3. Move into the `server/` directory (all Flask commands are run from here):
   ```bash
   cd server
   ```
4. Initialize, migrate, and upgrade the database:
   ```bash
   export FLASK_APP=app.py      
   flask db init
   flask db migrate -m "create exercises, workouts, workout_exercises tables"
   flask db upgrade head
   ```
5. Seed the database with example data:
   ```bash
   python seed.py
   ```

## Running the App

From the `server/` directory:

```bash
python app.py
```

The API runs at `http://localhost:5555`.

## Endpoints

| Method | Route                                                              | Description                                                        |
|--------|---------------------------------------------------------------------|----------------------------------------------------------------------|
| GET    | `/workouts`                                                        | List all workouts                                                   |
| GET    | `/workouts/<id>`                                                   | Show a single workout, including its associated exercises with reps/sets/duration |
| POST   | `/workouts`                                                        | Create a workout. Body: `{ "date": "YYYY-MM-DD", "duration_minutes": int, "notes": str }` |
| DELETE | `/workouts/<id>`                                                   | Delete a workout (also deletes its associated `WorkoutExercises`)    |
| GET    | `/exercises`                                                       | List all exercises                                                   |
| GET    | `/exercises/<id>`                                                  | Show a single exercise and the ids of workouts it's used in         |
| POST   | `/exercises`                                                       | Create an exercise. Body: `{ "name": str, "category": str, "equipment_needed": bool }` |
| DELETE | `/exercises/<id>`                                                  | Delete an exercise (also deletes its associated `WorkoutExercises`)  |
| POST   | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Add an exercise to a workout. Body: `{ "reps": int, "sets": int, "duration_seconds": int }` (at least one required) |

### Allowed exercise categories

`cardio`, `strength`, `flexibility`, `balance`

## Tech Stack

- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Marshmallow
- SQLite