from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields, validate
from marshmallow import ValidationError
from password import my_password    # <-- TODO Make sure to update w/your own 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:{my_password}@localhost/fitness_center_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)


### Member Model & Schema ###

class Member(db.Model):
    __tablename__ = 'Members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(320), unique=True)
    phone = db.Column(db.String(15))
    workout_sessions = db.relationship('WorkoutSession', backref='member')

class MemberSchema(ma.Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    age = fields.Integer(required=True, validate=validate.Range(min=13, min_inclusive=True))
    email = fields.String(required=False)
    phone = fields.String(required=False)

    class Meta:
        fields = (
            'name', 
            'age', 
            'email', 
            'phone', 
            'id'
            )

member_schema = MemberSchema()
members_schema = MemberSchema(many=True)


### WorkoutSession Model & Schema ###

class WorkoutSession(db.Model):
    __tablename__ = 'WorkoutSessions'
    session_id = db.Column(db.Integer, primary_key=True)
    session_date = db.Column(db.Date)
    session_time = db.Column(db.String(50))
    activity = db.Column(db.String(255))
    duration_minutes = db.Column(db.Integer)
    calories_burned = db.Column(db.Integer)
    member_id = db.Column(db.Integer, db.ForeignKey('Members.id'))

class WorkoutSessionSchema(ma.Schema):
    member_id = fields.Integer(required=False)
    session_date = fields.Date(required=True)
    session_time = fields.String(required=False)
    activity = fields.String(required=False)
    duration_minutes = fields.Integer(required=False)
    calories_burned = fields.Integer(required=False)

    class Meta:
        fields = (
            'member_id', 
            'session_date', 
            'session_time', 
            'activity', 
            'duration_minutes', 
            'calories_burned', 
            'session_id'
            )

workout_session_schema = WorkoutSessionSchema()
workout_sessions_schema = WorkoutSessionSchema(many=True)

# 'required=False' fields can have "" within the JSON body
# This ensures:
    # If the member is unsure what time of day OR activity they will be doing, it can be left empty and updated at a later date
    # When scheduling a session, the member may not know how long they will workout for OR how many calories are burned
    # If the member does not want to provide email or phone, they do not have to


### Member Routes & Methods ###

@app.route('/members', methods=['GET'])
def get_members():
    members = Member.query.all()
    return members_schema.jsonify(members)

@app.route('/members', methods=['POST'])
def add_member():
    try:
        member_data = member_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    new_member = Member(
        name = member_data['name'], 
        age = member_data['age'], 
        email = member_data['email'], 
        phone = member_data['phone']
    )
    db.session.add(new_member)
    db.session.commit()
    return jsonify({"message": "New member added successfully"}), 201

@app.route('/members/<int:id>', methods=['PUT'])
def update_member(id):
    member = Member.query.get_or_404(id)
    try:
        member_data = member_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    member.name = member_data['name']
    member.age = member_data['age']
    member.email = member_data['email']
    member.phone = member_data['phone']
    db.session.commit()
    return jsonify({"message": "Member details updated successfully"}), 200

@app.route('/members/<int:id>', methods=['DELETE'])
def delete_member(id):
    member = Member.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    return jsonify({"message": "Member removed successfully"}), 200


### WorkoutSession Routes & Methods ###

@app.route('/workout-sessions', methods=['GET'])
def get_workout_sessions():
    workout_sessions = WorkoutSession.query.all()
    return workout_sessions_schema.jsonify(workout_sessions)

@app.route('/workout-sessions', methods=['POST'])
def schedule_workout_session():
    try:
        workout_session_data = workout_session_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    new_session = WorkoutSession(
        member_id = workout_session_data['member_id'], 
        session_date = workout_session_data['session_date'], 
        session_time = workout_session_data['session_time'], 
        activity = workout_session_data['activity']
    )
    db.session.add(new_session)
    db.session.commit()
    return jsonify({"message": "New workout session scheduled successfully"}), 201

@app.route('/workout-sessions/<int:id>', methods=['PUT'])
def update_workout_session(id):
    workout_session = WorkoutSession.query.get_or_404(id)
    try:
        workout_session_data = workout_session_schema.load(request.json)
    except ValidationError as ve:
        return jsonify(ve.messages), 400
    
    workout_session.session_date = workout_session_data['session_date']
    workout_session.session_time = workout_session_data['session_time']
    workout_session.activity = workout_session_data['activity']
    workout_session.duration_minutes = workout_session_data['duration_minutes']
    workout_session.calories_burned = workout_session_data['calories_burned']
    db.session.commit()
    return jsonify({"message": "Workout session updated successfully"}), 200

@app.route('/workout-sessions/<int:id>', methods=['DELETE'])
def delete_workout_session(id):
    workout_session = WorkoutSession.query.get_or_404(id)
    db.session.delete(workout_session)
    db.session.commit()
    return jsonify({"message": "Session removed successfully"}), 200

@app.route('/workout-sessions/by-member-id', methods=['GET'])
def query_workout_sessions_by_member_id():
    member_id = request.args.get('member_id')
    workout_sessions = WorkoutSession.query.filter_by(member_id = member_id).all()
    if workout_sessions:
        return workout_sessions_schema.jsonify(workout_sessions)
    else:
        return jsonify({"message": f"No sessions or data found associated with Member ID: {member_id}"}), 404


# Initialize the database and create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)