import pytest
from src.cyclone.risk_engine import haversine_km

def test_haversine_distance():
    # Puri
    lat1, lon1 = 19.8135, 85.8312
    # Somewhere else
    lat2, lon2 = 20.2961, 85.8245 # Bhubaneswar
    
    dist = haversine_km(lat1, lon1, lat2, lon2)
    assert 50 <= dist <= 60 # Approx 53km
