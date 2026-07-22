from marshmallow import Schema, fields, validate, validates, validates_schema, ValidationError


# Handles validation and serialization for exercises
class ExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100, error="name must be 1-100 characters")
    )
    category = fields.String(
        required=True,
        validate=validate.OneOf(
            ['cardio', 'strength', 'flexibility', 'balance'],
            error="category must be one of: cardio, strength, flexibility, balance"
        )
    )
    equipment_needed = fields.Boolean(required=True)

    # Make sure the exercise name isn't just spaces
    @validates('name')
    def validate_name_not_blank(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("name cannot be blank")


# Handles workout data
class WorkoutSchema(Schema):
    id = fields.Integer(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="duration_minutes must be greater than 0")
    )
    notes = fields.String(required=False, allow_none=True)


# Handles the relationship between workouts and exercises
class WorkoutExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    workout_id = fields.Integer(dump_only=True)
    exercise_id = fields.Integer(dump_only=True)
    reps = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0, error="reps must be 0 or greater")
    )
    sets = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0, error="sets must be 0 or greater")
    )
    duration_seconds = fields.Integer(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0, error="duration_seconds must be 0 or greater")
    )

    # Require at least one workout measurement
    @validates_schema
    def validate_at_least_one_metric(self, data, **kwargs):
        if not any(data.get(f) is not None for f in ('reps', 'sets', 'duration_seconds')):
            raise ValidationError(
                "at least one of reps, sets, or duration_seconds is required",
                field_name='_schema'
            )


# Single and multiple object schemas
exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True)

workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)

workout_exercise_schema = WorkoutExerciseSchema()
workout_exercises_schema = WorkoutExerciseSchema(many=True)