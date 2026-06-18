import datetime
from zoneinfo import ZoneInfo
from backend.data.weather_service import weather_service
from backend.data.hyderabad_attractions import ATTRACTIONS

class LiveCrowdService:
    def __init__(self):
        # We store the original crowd_probs to allow resetting or consistent updates
        self.original_probs = {a.id: dict(a.crowd_probs) for a in ATTRACTIONS}

    async def update_live_crowds(self):
        # 1. Get current time in IST
        ist = ZoneInfo("Asia/Kolkata")
        now = datetime.datetime.now(ist)
        
        is_weekend = now.weekday() >= 5
        hour = now.hour
        
        if 6 <= hour < 12:
            time_slot = "morning"
        elif 12 <= hour < 17:
            time_slot = "afternoon"
        else:
            time_slot = "evening"

        # 2. Get live weather
        condition, prob_rain = await weather_service.get_live_weather()
        
        # 3. Compute global modifiers
        weekend_mult = 1.4 if is_weekend else 1.0
        
        weather_mult_indoor = 1.0
        weather_mult_outdoor = 1.0
        
        if condition == "rain":
            weather_mult_outdoor = 0.3
            weather_mult_indoor = 1.3
        elif condition == "sunny":
            weather_mult_outdoor = 1.2
            weather_mult_indoor = 0.9

        # 4. Update the global ATTRACTIONS list
        avg_crowd = 0.0
        for a in ATTRACTIONS:
            base_prob = self.original_probs[a.id].get(time_slot, 0.5)
            
            # Apply modifiers
            mult = weekend_mult
            if a.weather_sensitivity > 0.5: # mostly outdoor
                mult *= weather_mult_outdoor
            else:
                mult *= weather_mult_indoor
                
            new_prob = min(0.99, base_prob * mult)
            
            # Mutate the current timeslot to the new calculated probability
            # We also slightly elevate the other timeslots to reflect a busy day
            for ts in ["morning", "afternoon", "evening"]:
                if ts == time_slot:
                    a.crowd_probs[ts] = round(new_prob, 2)
                else:
                    a.crowd_probs[ts] = round(min(0.99, self.original_probs[a.id].get(ts, 0.5) * weekend_mult), 2)
                    
            avg_crowd += new_prob

        avg_crowd /= len(ATTRACTIONS)
        
        day_str = "Weekend" if is_weekend else "Weekday"
        time_str = now.strftime("%I:%M %p")
        
        if avg_crowd > 0.7:
            status = "High"
        elif avg_crowd > 0.4:
            status = "Moderate"
        else:
            status = "Low"

        return {
            "message": f"Crowds: {status} ({day_str} {time_str}, {condition.capitalize()})",
            "avg_crowd": round(avg_crowd, 2),
            "details": f"Time slot: {time_slot}, Weather: {condition}, Rain Prob: {prob_rain*100}%"
        }

live_crowd_service = LiveCrowdService()
