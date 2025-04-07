from app import app, db, Arbitrator

# Real arbitrator data
arbitrators = [
    {
        'name': 'Donald M. McRae',
        'specialization': 'International Law',
        'experience_years': 30,
        'cases_handled': 50
    },
    {
        'name': 'Kristian Jervell',
        'specialization': 'Investment Arbitration',
        'experience_years': 25,
        'cases_handled': 40
    },
    {
        'name': 'Vaughan Lowe',
        'specialization': 'Public International Law',
        'experience_years': 35,
        'cases_handled': 60
    },
    {
        'name': 'Marius Emberland',
        'specialization': 'International Dispute Resolution',
        'experience_years': 20,
        'cases_handled': 30
    }
]

def seed_database():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Add arbitrators
        for arb_data in arbitrators:
            arbitrator = Arbitrator(**arb_data)
            db.session.add(arbitrator)
        
        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database() 