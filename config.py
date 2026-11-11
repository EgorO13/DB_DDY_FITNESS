import psycopg2
import random
import string
from datetime import date, datetime, timedelta

DB_PARAMS = {
    "host": "localhost",
    "database": "ddy_fitness",
    "user": "postgres",
    "password": "261022",
    "port": "5432"
}

WORKOUT_ENUMS = ["individual", "split", "group"]
SERVICE_ENUMS = ["sport massage", "SPA massage", "classic massage", "consultation"]
AREA_NAMES = ["Gym Floor", "Pool", "SPA", "Crossfit", "Yoga Room"]
SEX_OPTIONS = ["male", "female"]
SUB_TYPES = ["Light", "Smart", "Infinity"]
GRADES = ["master", "expert", "top"]

def get_connection():
    return psycopg2.connect(**DB_PARAMS)

def gen_random_string(length: int) -> str:
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(length))

def gen_random_number_str(length: int) -> str:
    digits = string.digits
    return "".join(random.choice(digits) for _ in range(length))

def gen_random_phone() -> str:
    digits = "".join(random.choice(string.digits) for _ in range(10))
    return f"+7{digits}"

def make_gyms_data(count: int) -> list:
    return [(f"City-{gen_random_string(5)}", gen_random_phone()) for _ in range(count)]

def make_clients_data(count: int) -> list:
    data = []
    for _ in range(count):
        birth_date = date(random.randint(1980, 2005), random.randint(1, 12), random.randint(1, 28))
        data.append((gen_random_string(10), gen_random_string(10), gen_random_number_str(10), gen_random_phone(), random.choice(SEX_OPTIONS), birth_date))
    return data

def make_subs_data() -> list:
    return [(name, round(random.uniform(2000.00, 5000.00), 2)) for name in SUB_TYPES]

def make_roles_data(count: int) -> list:
    return [(f"Role-{gen_random_string(5)}-{i}", random.choice(GRADES), round(random.uniform(1500.00, 4000.00), 2)) for i in range(count)]

def make_staff_data(count: int, role_ids: list) -> list:
    data = []
    for _ in range(count):
        birth_date = date(random.randint(1975, 2002), random.randint(1, 12), random.randint(1, 28))
        data.append((gen_random_string(10), gen_random_string(10), gen_random_number_str(10), gen_random_phone(), birth_date, random.choice(role_ids)))
    return data

def make_work_in_gym_data(gym_ids: list, staff_ids: list) -> list:
    data = set()
    for staff_id in staff_ids:
        data.add((random.choice(gym_ids), staff_id))
    pairs_count = min(25, len(gym_ids) * len(staff_ids))
    while len(data) < pairs_count:
        data.add((random.choice(gym_ids), random.choice(staff_ids)))
    return list(data)

def make_areas_data(count: int, gym_ids: list) -> list:
    data = []
    used_pairs = set()
    for _ in range(count):
        gym_id = random.choice(gym_ids)
        name = random.choice(AREA_NAMES)
        while (gym_id, name) in used_pairs:
            gym_id = random.choice(gym_ids)
            name = random.choice(AREA_NAMES)
        used_pairs.add((gym_id, name))
        data.append((gym_id, name))
    return data
