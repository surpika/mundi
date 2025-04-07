from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import time
import json
from arbitrator_finder import search_arbitrator_cases

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///arbitrators.db'
db = SQLAlchemy(app)

# Add your JusMundi API key here
API_KEY = "your_api_key_here"  # TODO: Move to environment variable

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

@app.route('/api/conflicts/<int:arbitrator_id>')
def get_conflicts(arbitrator_id):
    arbitrator = Arbitrator.query.get_or_404(arbitrator_id)
    
    try:
        # Call the arbitrator finder script
        results = search_arbitrator_cases(API_KEY, arbitrator.name, max_cases=10)
        
        if not results:
            return jsonify({
                'status': 'no_results',
                'message': f'No results found for arbitrator {arbitrator.name}'
            })

        # Format the results for display
        formatted_results = []
        for individual in results:
            cases_info = []
            for case in individual.get('cases', []):
                case_info = {
                    'title': case['title'],
                    'reference': case['reference'],
                    'organization': case['organization'],
                    'status': case['status'],
                    'dates': f"{case['startDate']} - {case['endDate']}",
                    'parties': [f"{p['name']} ({p['role']})" for p in case['parties']]
                }
                cases_info.append(case_info)

            formatted_results.append({
                'name': individual['name'],
                'details': individual['details'],
                'cases': cases_info
            })

        return jsonify({
            'status': 'success',
            'arbitrator': arbitrator.name,
            'results': formatted_results
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001) 