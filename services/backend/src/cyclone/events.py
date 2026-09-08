import time
from src.realtime.events import RealtimeEvent, RealtimeEventType
from src.cyclone.contracts import CycloneIntelligence

def get_intelligence_events(intelligence: CycloneIntelligence):
    ts = int(time.time() * 1000)
    cyc_id = intelligence.cyclone_id
    events = []
    
    # CYCLONE_DETECTED
    if intelligence.identification.detected:
        evt = RealtimeEvent(
            event_type=RealtimeEventType.CYCLONE_DETECTED.value,
            payload={
                "cyclone_id": cyc_id,
                "confidence": intelligence.identification.confidence,
                "position": {
                    "lat": intelligence.prediction.current_position.lat if intelligence.prediction else 0.0,
                    "lon": intelligence.prediction.current_position.lon if intelligence.prediction else 0.0
                },
                "timestamp": intelligence.timestamp.isoformat()
            },
            timestamp=ts
        )
        events.append(evt)
        
    # CYCLONE_CLASSIFIED
    if intelligence.classification:
        evt = RealtimeEvent(
            event_type=RealtimeEventType.CYCLONE_CLASSIFIED.value,
            payload={
                "cyclone_id": cyc_id,
                "stage": intelligence.classification.stage,
                "confidence": intelligence.classification.confidence
            },
            timestamp=ts
        )
        events.append(evt)
        
    # CYCLONE_PREDICTION_UPDATED
    if intelligence.prediction:
        evt = RealtimeEvent(
            event_type=RealtimeEventType.CYCLONE_PREDICTION_UPDATED.value,
            payload={
                "cyclone_id": cyc_id,
                "predicted_path": [p.model_dump() for p in intelligence.prediction.predicted_path],
                "uncertainty": intelligence.prediction.uncertainty.model_dump(),
                "confidence": intelligence.prediction.confidence
            },
            timestamp=ts
        )
        events.append(evt)
        
    return events

def get_risk_updated_event(cyclone_id: str, risks: list):
    ts = int(time.time() * 1000)
    evt = RealtimeEvent(
        event_type=RealtimeEventType.CYCLONE_RISK_UPDATED.value,
        payload={
            "cyclone_id": cyclone_id,
            "risk_scores_by_zone": [
                {
                    "zone_id": r.zone_id,
                    "name": r.zone_name,
                    "risk": r.risk_level,
                    "score": r.risk_score,
                    "eta_hours": r.eta_hours
                } for r in risks
            ]
        },
        timestamp=ts
    )
    return evt
