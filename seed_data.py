from app import app, db, Arbitrator

# Sample arbitrator data
arbitrators = [
    {
        'name': 'John Smith',
        'specialization': 'Commercial Disputes',
        'experience_years': 15,
        'cases_handled': 200
    },
    {
        'name': 'Sarah Johnson',
        'specialization': 'International Arbitration',
        'experience_years': 20,
        'cases_handled': 300
    },
    {
        'name': 'Michael Chen',
        'specialization': 'Construction Disputes',
        'experience_years': 12,
        'cases_handled': 150
    },
    {
        'name': 'Elena Rodriguez',
        'specialization': 'Maritime Law',
        'experience_years': 18,
        'cases_handled': 250
    }
]

def seed_database():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Add sample arbitrators
        for arb_data in arbitrators:
            arbitrator = Arbitrator(**arb_data)
            db.session.add(arbitrator)
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database() 