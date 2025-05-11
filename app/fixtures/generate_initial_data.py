"""Generates random Events data for initial migrations"""

import hashlib
import json
import os
import random
import secrets

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("UTC")


def generate_password():
    """Helper to generate password hash"""
    password = "password123"
    salt = secrets.token_hex(12)
    iterations = 260000
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        iterations
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${pw_hash}"


def generate_fixtures():
    fixtures = []

    # Create users
    users = []
    for i in range(1, 11):
        user = {
            "model": "auth.user",
            "pk": i,
            "fields": {
                "username": f"user_{i}",
                "email": f"user_{i}@example.com",
                "password": generate_password(),
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            }
        }
        users.append(user)
        fixtures.append(user)

    # Create tags
    tags = []
    for i in range(1, 11):
        tag = {
            "model": "events.tag",
            "pk": i,
            "fields": {
                "name": f"Tag {i}"
            }
        }
        tags.append(tag)
        fixtures.append(tag)

    # Create 25 past events and 25 future events
    now = datetime.now(tz=TZ)
    events = []
    for i in range(1, 51):
        # Random date in future and past within a year
        if i <= 25:
            start_time = now - timedelta(days=random.randint(1, 365))
        else:
            start_time = now + timedelta(days=random.randint(1, 365))

        # pick organizer randomly
        organizer = random.choice(range(1, 11))

        event = {
            "model": "events.event",
            "pk": i,
            "fields": {
                "name": f"Event {i}",
                "description": f"Description for Event {i}",
                "start_time": start_time.isoformat(),
                "location": f"City {random.randint(1, 10)}",
                "available_seats": random.randint(10, 100),
                "status": "upcoming" if i > 25 else "completed",
                "organizer": organizer,
                "created_at": (now - timedelta(
                    days=random.randint(30, 365))).isoformat(),
                "tags": random.sample(
                    range(1, 11), random.randint(1, 3)
                ) if i % 3 == 0 else [],
                "search_vector": None
            }
        }
        events.append(event)
        fixtures.append(event)

    # Create reservations
    reservation_id = 1
    future_events = [e for e in events if
                     e['fields']['status'] == 'upcoming']

    # Track which events each user has already reserved
    user_reservations = {user_id: set() for user_id in range(1, 6)}

    for user_id in range(1, 6):
        # Get available events (not yet reserved by this user)
        available_events = [
            e for e in future_events
            if e['pk'] not in user_reservations[user_id]
        ]

        # Randomly select 3-5 events from available ones
        num_choices = min(random.randint(3, 5), len(available_events))
        if num_choices == 0:
            continue

        selected_events = random.sample(available_events, num_choices)

        for event in selected_events:
            event_id = event["pk"]
            if event_id in user_reservations[user_id]:
                continue

            reservation = {
                "model": "events.reservation",
                "pk": reservation_id,
                "fields": {
                    "user": user_id,
                    "event": event_id,
                    "status": "confirmed",
                    "created_at": (now - timedelta(
                        days=random.randint(1, 30))).isoformat()
                }
            }
            fixtures.append(reservation)
            user_reservations[user_id].add(event_id)
            reservation_id += 1

    # Create ratings
    rating_id = 1
    for user_id in range(1, 6):
        # get visited events
        past_events = [e for e in events if
                       e['fields']['status'] == 'completed']
        for event in random.sample(past_events, random.randint(2, 4)):
            rating = {
                "model": "events.rating",
                "pk": rating_id,
                "fields": {
                    "user": user_id,
                    "event": event["pk"],
                    "rating": random.randint(1, 5),
                    "comment": f"Comment from user {user_id} "
                               f"for event {event['pk']}",
                    "created_at": (now - timedelta(
                        days=random.randint(1, 30))).isoformat()
                }
            }
            fixtures.append(rating)
            rating_id += 1

    return fixtures


if __name__ == "__main__":
    data = generate_fixtures()
    filepath = os.path.join(os.path.dirname(__file__), "initial_data.json")
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

    print("initial_data.json created")
