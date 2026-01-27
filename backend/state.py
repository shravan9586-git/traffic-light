# ==========================================
# SHARED STATE (Data Store)
# ==========================================

# 1. HUBS DATA (Existing Logic)
HUBS = {
    "hub1": { "name": "Main Junction", "traffic": 20 },
    "hub2": { "name": "Highway Exit", "traffic": 35 }
}

# 2. USERS DATABASE (New Logic)
# Format: "username": { "password": "...", "role": "...", "created_by": "...", "login_time": float }
# Default Admin user pehle se hai
USERS_DB = {
    "admin": {
        "password": "admin123",
        "role": "admin",
        "created_by": "system",
        "login_time": None
    }
}

# 3. ONLINE USERS SET (Existing Logic)
USERS_ONLINE = set()