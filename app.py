# app.py
from flask import Flask, render_template, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import threading
import time
import json
import os

app = Flask(__name__, static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///buses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Ensure the markers directory exists
os.makedirs('static/markers', exist_ok=True)

# Database Model
class BusPosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    bearing = db.Column(db.Float)
    speed = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    route_id = db.Column(db.String(50))
    trip_id = db.Column(db.String(50))
    current_status = db.Column(db.Integer)
    wheelchair_accessible = db.Column(db.Boolean)
    license_plate = db.Column(db.String(50))
    
    def to_dict(self):
        return {
            'vehicle_id': self.vehicle_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'bearing': self.bearing,
            'speed': self.speed,
            'timestamp': self.timestamp.isoformat(),
            'route_id': self.route_id,
            'trip_id': self.trip_id,
            'current_status': self.current_status,
            'wheelchair_accessible': self.wheelchair_accessible,
            'license_plate': self.license_plate
        }

# Create database tables
with app.app_context():
    db.create_all()

def fetch_bus_data():
    api_url = 'https://nextrip-public-api.azure-api.net/octranspo/gtfs-rt-vp/beta/v1/VehiclePositions'
    headers = {
        'Ocp-Apim-Subscription-Key': os.getenv('OCP_APIM_SUBSCRIPTION_KEY'),
        'Cache-Control': 'no-cache'
    }
    
    while True:
        try:
            response = requests.get(api_url, headers=headers, params={'format': 'json'})
            data = response.json()
            
            with app.app_context():
                # Clear old entries
                BusPosition.query.delete()
                
                # Add new entries
                for entity in data.get('Entity', []):
                    if entity.get('Vehicle'):
                        vehicle = entity['Vehicle']
                        vehicle_info = vehicle.get('Vehicle', {})
                        position = vehicle.get('Position', {})
                        trip = vehicle.get('Trip', {})
                        
                        bus = BusPosition(
                            vehicle_id=vehicle_info.get('Id'),
                            latitude=position.get('Latitude'),
                            longitude=position.get('Longitude'),
                            bearing=position.get('Bearing'),
                            speed=position.get('Speed'),
                            route_id=trip.get('RouteId') if trip else None,
                            trip_id=trip.get('TripId') if trip else None,
                            current_status=vehicle.get('CurrentStatus'),
                            wheelchair_accessible=bool(vehicle_info.get('WheelchairAccessible')),
                            license_plate=vehicle_info.get('LicensePlate')
                        )
                        db.session.add(bus)
                
                db.session.commit()
                
        except Exception as e:
            print(f"Error fetching data: {e}")
            
        time.sleep(30)  # Wait 30 seconds before next update

# Start the background thread for data fetching
fetch_thread = threading.Thread(target=fetch_bus_data, daemon=True)
fetch_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/buses')
def get_buses():
    buses = BusPosition.query.all()
    return jsonify([bus.to_dict() for bus in buses])

if __name__ == '__main__':
    app.run(debug=True)