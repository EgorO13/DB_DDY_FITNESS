import psycopg2
import random
import string
from datetime import date, datetime, timedelta


def gen_random_string(length: int) -> str:
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(length))


def gen_random_number_str(length: int) -> str:
    digits = string.digits
    return "".join(random.choice(digits) for _ in range(length))


def gen_random_phone() -> str:
    digits = "".join(random.choice(string.digits) for _ in range(10))
    return f"+7{digits}"


def gen_random_enum(enum_list: list) -> str:
    if not enum_list:
        return None
    return random.choice(enum_list)


def make_gyms_data(count: int) -> list:
    data = []
    for _ in range(count):
        data.append((f"City-{gen_random_string(5)}", gen_random_phone()))
    return data


def make_clients_data(count: int) -> list:
    data = []
    sex_options = ["male", "female"]
    for _ in range(count):
        birth_date = date(
            random.randint(1980, 2005),
            random.randint(1, 12),
            random.randint(1, 28),
        )
        data.append(
            (
                gen_random_string(10),
                gen_random_string(10),
                gen_random_number_str(10),
                gen_random_phone(),
                gen_random_enum(sex_options),
                birth_date,
            )
        )
    return data


def make_subs_data(count: int) -> list:
    data = []
    for i in range(count):
        name = f"Sub-{gen_random_string(5)}-{i}"
        price = round(random.uniform(1000.00, 9999.00), 2)
        discount = random.choice([0, 5, 10, 15])
        data.append((name, price, discount))
    return data


def make_roles_data(count: int) -> list:
    data = []
    grade_options = ["master", "expert", "top"]
    for i in range(count):
        name = f"Role-{gen_random_string(5)}-{i}"
        grade = gen_random_enum(grade_options)
        price = round(random.uniform(500.00, 5000.00), 2)
        data.append((name, grade, price))
    return data


def make_staff_data(count: int, role_ids: list) -> list:
    data = []
    for _ in range(count):
        birth_date = date(
            random.randint(1975, 2002),
            random.randint(1, 12),
            random.randint(1, 28),
        )
        data.append(
            (
                gen_random_string(10),
                gen_random_string(10),
                gen_random_number_str(10),
                gen_random_phone(),
                birth_date,
                random.choice(role_ids),
            )
        )
    return data


def make_work_in_gym_data(gym_ids: list, staff_ids: list) -> list:
    data = set()
    pairs_count = min(15, len(gym_ids) * len(staff_ids))
    while len(data) < pairs_count:
        data.add((random.choice(gym_ids), random.choice(staff_ids)))
    return list(data)


def make_areas_data(count: int, gym_ids: list) -> list:
    data = []
    area_names = ["Gym Floor", "Pool", "SPA", "Crossfit", "Yoga Room"]
    used_pairs = set()
    for _ in range(count):
        gym_id = random.choice(gym_ids)
        name = random.choice(area_names)
        while (gym_id, name) in used_pairs:
            gym_id = random.choice(gym_ids)
            name = random.choice(area_names)
        used_pairs.add((gym_id, name))
        data.append((gym_id, name))
    return data


def make_visit_data(count: int, client_ids: list, gym_ids: list) -> list:
    data = []
    for _ in range(count):
        v_date = date(2026, random.randint(1, 10), random.randint(1, 28))
        entry = f"{random.randint(7, 21):02d}:{random.randint(0, 59):02d}:00"
        exit = f"{random.randint(22, 23):02d}:{random.randint(0, 59):02d}:00"
        data.append(
            (
                random.choice(client_ids),
                random.choice(gym_ids),
                v_date,
                entry,
                exit,
            )
        )
    return data


def make_product_data(count: int, staff_ids: list, area_ids: list) -> list:
    data = []
    types = ["workout", "service"]
    for _ in range(count):
        p_date = date(2026, random.randint(10, 12), random.randint(1, 28))
        start = f"{random.randint(8, 20):02d}:00:00"
        duration = random.choice([45, 60, 90])
        price = round(random.uniform(1000.00, 5000.00), 2)
        data.append(
            (
                random.choice(staff_ids),
                random.choice(area_ids),
                p_date,
                start,
                duration,
                price,
                random.choice(types),
            )
        )
    return data


def make_purchase_data(count: int, client_ids: list, staff_ids: list) -> list:
    data = []
    types = ["package", "contract", "booking"]
    for _ in range(count):
        p_date = datetime(2026, 10, random.randint(1, 14), random.randint(9, 18), 0, 0)
        price = round(random.uniform(2000.00, 9000.00), 2)
        data.append(
            (
                random.choice(client_ids),
                random.choice(staff_ids),
                random.choice(types),
                p_date,
                price,
            )
        )
    return data


connection = None

try:
    connection = psycopg2.connect(
        host="localhost",
        database="ddy_fitness",
        user="postgres",
        password="261022",
        port="5432",
    )

    with connection.cursor() as cursor:
        gym_ids = []
        insert_gym = "INSERT INTO gym (address, phone) VALUES (%s, %s) RETURNING gym_id;"
        for item in make_gyms_data(10):
            cursor.execute(insert_gym, item)
            print(item)
            gym_ids.append(cursor.fetchone()[0])

        client_ids = []
        insert_client = "INSERT INTO client (first_name, last_name, passport, phone, sex, birthday) VALUES (%s, %s, %s, %s, %s, %s) RETURNING client_id;"
        for item in make_clients_data(10):
            cursor.execute(insert_client, item)
            print(item)
            client_ids.append(cursor.fetchone()[0])

        sub_ids = []
        insert_sub = "INSERT INTO sub (sub_name, price, individual_discount) VALUES (%s, %s, %s) RETURNING sub_id;"
        for item in make_subs_data(10):
            cursor.execute(insert_sub, item)
            print(item)
            sub_ids.append(cursor.fetchone()[0])

        role_ids = []
        insert_role = "INSERT INTO staff_role (role_name, grade, workout_price) VALUES (%s, %s, %s) RETURNING staff_role_id;"
        for item in make_roles_data(10):
            cursor.execute(insert_role, item)
            print(item)
            role_ids.append(cursor.fetchone()[0])

        staff_ids = []
        insert_staff = "INSERT INTO staff (first_name, last_name, passport, phone, birthday, staff_role_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING staff_id;"
        for item in make_staff_data(10, role_ids):
            cursor.execute(insert_staff, item)
            print(item)
            staff_ids.append(cursor.fetchone()[0])

        insert_work_gym = "INSERT INTO work_in_gym (gym_id, staff_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;"
        cursor.executemany(insert_work_gym, make_work_in_gym_data(gym_ids, staff_ids))

        area_ids = []
        insert_area = "INSERT INTO area (gym_id, area_name) VALUES (%s, %s) RETURNING area_id;"
        for item in make_areas_data(10, gym_ids):
            cursor.execute(insert_area, item)
            print(item)
            area_ids.append(cursor.fetchone()[0])

        insert_visit = "INSERT INTO visit (client_id, gym_id, visit_date, entry_time, exit_time) VALUES (%s, %s, %s, %s, %s);"
        cursor.executemany(insert_visit, make_visit_data(10, client_ids, gym_ids))

        product_records = []
        insert_product = "INSERT INTO product (staff_id, area_id, product_date, start_time, duration_min, price, product_type) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING product_id, product_type;"
        for item in make_product_data(15, staff_ids, area_ids):
            cursor.execute(insert_product, item)
            print(item)
            product_records.append(cursor.fetchone())

        insert_workout = "INSERT INTO workout (product_id, workout_type, capacity) VALUES (%s, %s, %s);"
        insert_service = "INSERT INTO service (product_id, service_type, description) VALUES (%s, %s, %s);"

        workout_enums = ["individual", "split", "group"]
        service_enums = ["sport massage", "SPA massage", "classic massage", "consultation"]
        workout_ids = []

        for p_id, p_type in product_records:
            if p_type == "workout":
                w_type = random.choice(workout_enums)
                capacity = 1 if w_type == "individual" else (
                    random.randint(2, 3) if w_type == "split" else random.randint(4, 20))
                item = (p_id, w_type, capacity)
                cursor.execute(insert_workout, item)
                print(item)
                workout_ids.append(p_id)
            else:
                s_type = random.choice(service_enums)
                item = (p_id, s_type, gen_random_string(15))
                cursor.execute(insert_service, item)
                print(item)

        purchase_records = []
        insert_purchase = "INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price) VALUES (%s, %s, %s, %s, %s) RETURNING purchase_id, purchase_type, all_price;"
        for item in make_purchase_data(20, client_ids, staff_ids):
            cursor.execute(insert_purchase, item)
            print(item)
            purchase_records.append(cursor.fetchone())

        insert_package = "INSERT INTO package (purchase_id, amount, price, discount, remainder) VALUES (%s, %s, %s, %s, %s);"
        insert_contract = "INSERT INTO contract (purchase_id, sub_id, date_start, date_end, payment_type, status) VALUES (%s, %s, %s, %s, %s, %s);"
        insert_booking = "INSERT INTO booking (purchase_id, product_id, package_purchase_id, date_booking, status) VALUES (%s, %s, %s, %s, %s);"

        package_ids = []
        contract_ids = []

        for pur_id, pur_type, price in purchase_records:
            if pur_type == "package":
                amount = random.choice([5, 10, 20])
                discount = random.choice([0, 3, 5, 10, 15])
                cursor.execute(insert_package, (pur_id, amount, price, discount, amount))
                package_ids.append(pur_id)
            elif pur_type == "contract":
                sub_id = random.choice(sub_ids)
                d_start = date(2026, 10, 14)
                d_end = d_start + timedelta(days=random.choice([30, 90, 365]))
                p_type = random.choice(["full", "installment"])
                status = random.choice(["paid", "canceled", "in progress"])
                cursor.execute(insert_contract, (pur_id, sub_id, d_start, d_end, p_type, status))
                contract_ids.append((pur_id, price, p_type))
            else:
                prod_id = random.choice([p[0] for p in product_records])
                pack_id = random.choice(package_ids) if package_ids and random.choice([True, False]) else None
                b_status = random.choice(["recorded", "canceled", "visited"])
                b_date = datetime(2026, 10, 15, 12, 0, 0)
                cursor.execute(insert_booking, (pur_id, prod_id, pack_id, b_date, b_status))

        insert_plan = "INSERT INTO plan (purchase_id, amount, pay_date) VALUES (%s, %s, %s);"
        for c_id, price, p_type in contract_ids:
            if p_type == "installment":
                part = round(price / 2, 2)
                cursor.execute(insert_plan, (c_id, part, date(2026, 10, 14)))
                cursor.execute(insert_plan, (c_id, part, date(2026, 11, 14)))

        insert_pay_dock = "INSERT INTO pay_dock (purchase_id, staff_id, payment_date, payment_check, price) VALUES (%s, %s, %s, %s, %s);"
        pay_dock_counter = 100001
        for pur_id, pur_type, price in purchase_records:
            cursor.execute(insert_pay_dock, (pur_id, random.choice(staff_ids), date(2026, 10, 14), pay_dock_counter, price))
            pay_dock_counter += 1

        connection.commit()
        print("Commit")

except Exception as error:
    print("Error:", error)

finally:
    if connection:
        connection.close()
        print("End")
