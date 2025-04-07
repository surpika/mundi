from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///arbitrators.db'
db = SQLAlchemy(app)

class Arbitrator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(200))
    experience_years = db.Column(db.Integer)
    cases_handled = db.Column(db.Integer)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/arbitrators')
def get_arbitrators():
    arbitrators = Arbitrator.query.all()
    return jsonify([{
        'id': a.id,
        'name': a.name,
        'specialization': a.specialization,
        'experience_years': a.experience_years,
        'cases_handled': a.cases_handled
    } for a in arbitrators])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 