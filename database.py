from config import *

DDL_SCRIPT = """
DROP TABLE IF EXISTS pay_dock, plan, booking, contract, package, purchase, service, workout, product, visit, area, work_in_gym, staff, staff_role, sub, client, gym CASCADE;
DROP TYPE IF EXISTS grade_enum, workout_enum, service_enum, product_enum, purchase_enum, contract_enum, booking_enum, sex_enum, payment_enum CASCADE;

CREATE TYPE sex_enum AS ENUM ('male', 'female');
CREATE TYPE grade_enum AS ENUM ('master', 'expert', 'top');
CREATE TYPE workout_enum AS ENUM ('individual', 'group', 'split');
CREATE TYPE service_enum AS ENUM ('sport massage', 'SPA massage', 'classic massage', 'consultation');
CREATE TYPE product_enum AS ENUM ('workout', 'service');
CREATE TYPE purchase_enum AS ENUM ('package', 'contract', 'booking');
CREATE TYPE contract_enum AS ENUM ('paid', 'canceled', 'in progress');
CREATE TYPE booking_enum AS ENUM ('recorded', 'canceled', 'visited');
CREATE TYPE payment_enum AS ENUM ('full', 'installment');

CREATE TABLE gym (gym_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, address varchar(100) NOT NULL, phone char(12) NOT NULL UNIQUE);
CREATE TABLE client (client_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, first_name varchar(15) NOT NULL, last_name varchar(15) NOT NULL, passport char(10) NOT NULL UNIQUE, phone char(12) NOT NULL, sex sex_enum NOT NULL, birthday date NOT NULL);
CREATE TABLE sub (sub_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, sub_name varchar(20) NOT NULL UNIQUE, price decimal(8, 2) NOT NULL, CONSTRAINT chk_sub_price CHECK (price > 0));
CREATE TABLE staff_role (staff_role_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, role_name varchar(20) NOT NULL UNIQUE, grade grade_enum, workout_price decimal(8, 2), CONSTRAINT chk_workout_price CHECK (workout_price IS NULL OR workout_price > 0));
CREATE TABLE staff (staff_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, staff_role_id int NOT NULL REFERENCES staff_role(staff_role_id) ON DELETE RESTRICT ON UPDATE CASCADE, first_name varchar(15) NOT NULL, last_name varchar(15) NOT NULL, passport char(10) NOT NULL UNIQUE, phone char(12) NOT NULL, birthday date NOT NULL);
CREATE TABLE work_in_gym (gym_id int NOT NULL REFERENCES gym(gym_id) ON DELETE CASCADE ON UPDATE CASCADE, staff_id int NOT NULL REFERENCES staff(staff_id) ON DELETE CASCADE ON UPDATE CASCADE, PRIMARY KEY (gym_id, staff_id));
CREATE TABLE area (area_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, gym_id int NOT NULL REFERENCES gym(gym_id) ON DELETE RESTRICT ON UPDATE CASCADE, area_name varchar(20) NOT NULL, CONSTRAINT uq_area_gym_name UNIQUE (gym_id, area_name));
CREATE TABLE visit (visit_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, client_id int NOT NULL REFERENCES client(client_id) ON DELETE RESTRICT ON UPDATE CASCADE, gym_id int NOT NULL REFERENCES gym(gym_id) ON DELETE RESTRICT ON UPDATE CASCADE, visit_date date NOT NULL, entry_time time NOT NULL, exit_time time, CONSTRAINT chk_visit_time CHECK (exit_time IS NULL OR exit_time >= entry_time));
CREATE TABLE product (product_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, staff_id int NOT NULL REFERENCES staff(staff_id) ON DELETE RESTRICT ON UPDATE CASCADE, area_id int NOT NULL REFERENCES area(area_id) ON DELETE RESTRICT ON UPDATE CASCADE, product_date date NOT NULL, start_time time NOT NULL, duration_min int NOT NULL, price decimal(8, 2) NOT NULL, product_type product_enum NOT NULL, CONSTRAINT chk_product_duration CHECK (duration_min > 0), CONSTRAINT chk_product_price CHECK (price >= 0));
CREATE TABLE workout (product_id int PRIMARY KEY REFERENCES product(product_id) ON DELETE CASCADE ON UPDATE CASCADE, workout_type workout_enum NOT NULL, capacity smallint NOT NULL, CONSTRAINT chk_workout_capacity CHECK ((workout_type = 'individual' AND capacity = 1) OR (workout_type = 'split' AND capacity BETWEEN 2 AND 3) OR (workout_type = 'group' AND capacity >= 2)));
CREATE TABLE service (product_id int PRIMARY KEY REFERENCES product(product_id) ON DELETE CASCADE ON UPDATE CASCADE, service_type service_enum NOT NULL, description varchar(50));
CREATE TABLE purchase (purchase_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, client_id int NOT NULL REFERENCES client(client_id) ON DELETE RESTRICT ON UPDATE CASCADE, staff_id int NOT NULL REFERENCES staff(staff_id) ON DELETE RESTRICT ON UPDATE CASCADE, purchase_type purchase_enum NOT NULL, purchase_date timestamp NOT NULL, all_price decimal(8, 2) NOT NULL, CONSTRAINT chk_purchase_price CHECK (all_price >= 0));
CREATE TABLE package (purchase_id int PRIMARY KEY REFERENCES purchase(purchase_id) ON DELETE CASCADE ON UPDATE CASCADE, amount int NOT NULL, price decimal(8, 2) NOT NULL, discount int NOT NULL DEFAULT 0, remainder int NOT NULL, CONSTRAINT chk_package_amount CHECK (amount > 0), CONSTRAINT chk_package_price CHECK (price > 0), CONSTRAINT chk_package_discount CHECK (discount IN (0, 3, 5, 10, 15)), CONSTRAINT chk_package_remainder CHECK (remainder BETWEEN 0 AND amount));
CREATE TABLE contract (purchase_id int PRIMARY KEY REFERENCES purchase(purchase_id) ON DELETE CASCADE ON UPDATE CASCADE, sub_id int NOT NULL REFERENCES sub(sub_id) ON DELETE RESTRICT ON UPDATE CASCADE, date_start date NOT NULL, date_end date NOT NULL, payment_type payment_enum NOT NULL, installment_months int, status contract_enum NOT NULL, CONSTRAINT chk_contract_dates CHECK (date_end >= date_start),
    CONSTRAINT chk_contract_installment CHECK (
        (payment_type = 'full' AND installment_months IS NULL) OR 
        (payment_type = 'installment' AND installment_months BETWEEN 2 AND 12)
    )
);
CREATE TABLE booking (purchase_id int PRIMARY KEY REFERENCES purchase(purchase_id) ON DELETE CASCADE ON UPDATE CASCADE, product_id int NOT NULL REFERENCES product(product_id) ON DELETE RESTRICT ON UPDATE CASCADE, package_purchase_id int REFERENCES package(purchase_id) ON DELETE RESTRICT ON UPDATE CASCADE, date_booking timestamp NOT NULL, status booking_enum NOT NULL);
CREATE TABLE plan (plan_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, purchase_id int NOT NULL REFERENCES contract(purchase_id) ON DELETE CASCADE ON UPDATE CASCADE, amount decimal(8, 2) NOT NULL, pay_date date NOT NULL, CONSTRAINT chk_plan_amount CHECK (amount > 0));
CREATE TABLE pay_dock (pay_dock_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, purchase_id int NOT NULL REFERENCES purchase(purchase_id) ON DELETE RESTRICT ON UPDATE CASCADE, staff_id int NOT NULL REFERENCES staff(staff_id) ON DELETE RESTRICT ON UPDATE CASCADE, payment_date date NOT NULL, payment_check int NOT NULL UNIQUE, price decimal(8, 2) NOT NULL, CONSTRAINT chk_payment_price CHECK (price > 0));
"""

def reset_and_fill_db():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(DDL_SCRIPT)
            gym_ids = []
            for item in make_gyms_data(10):
                cursor.execute("INSERT INTO gym (address, phone) VALUES (%s, %s) RETURNING gym_id;", item)
                gym_ids.append(cursor.fetchone()[0])
            client_ids = []
            for item in make_clients_data(10):
                cursor.execute("INSERT INTO client (first_name, last_name, passport, phone, sex, birthday) VALUES (%s, %s, %s, %s, %s, %s) RETURNING client_id;", item)
                client_ids.append(cursor.fetchone()[0])
            sub_info = {}
            for name, price in make_subs_data():
                cursor.execute("INSERT INTO sub (sub_name, price) VALUES (%s, %s) RETURNING sub_id;", (name, price))
                sub_info[cursor.fetchone()[0]] = {"name": name, "price": price}
            role_info = {}
            for name, grade, price in make_roles_data(10):
                cursor.execute("INSERT INTO staff_role (role_name, grade, workout_price) VALUES (%s, %s, %s) RETURNING staff_role_id;", (name, grade, price))
                role_info[cursor.fetchone()[0]] = price
            staff_info = {}
            for item in make_staff_data(10, list(role_info.keys())):
                cursor.execute("INSERT INTO staff (first_name, last_name, passport, phone, birthday, staff_role_id) VALUES (%s, %s, %s, %s, %s, %s) RETURNING staff_id;", item)
                staff_info[cursor.fetchone()[0]] = role_info[item[5]]
            cursor.executemany("INSERT INTO work_in_gym (gym_id, staff_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", make_work_in_gym_data(gym_ids, list(staff_info.keys())))
            area_ids = []
            for item in make_areas_data(10, gym_ids):
                cursor.execute("INSERT INTO area (gym_id, area_name) VALUES (%s, %s) RETURNING area_id;", item)
                area_ids.append(cursor.fetchone()[0])
            product_records = []
            insert_product = "INSERT INTO product (staff_id, area_id, product_date, start_time, duration_min, price, product_type) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING product_id, product_type, price, staff_id;"
            for i in range(50):
                st_id = random.choice(list(staff_info.keys()))
                base_price = staff_info[st_id]
                p_date = date(2026, random.randint(1, 12), random.randint(1, 28))
                start = f"{random.randint(8, 20):02d}:00:00"
                duration = random.choice([45, 60, 90])
                if i % 2 == 0:
                    w_type = random.choice(WORKOUT_ENUMS)
                    calc_price = base_price if w_type == "individual" else (round(float(base_price) * 0.8, 2) if w_type == "split" else round(float(base_price) * 0.4, 2))
                    capacity = 1 if w_type == "individual" else (random.randint(2, 3) if w_type == "split" else random.randint(4, 20))
                    cursor.execute(insert_product, (st_id, random.choice(area_ids), p_date, start, duration, calc_price, "workout"))
                    res = cursor.fetchone()
                    product_records.append({"id": res[0], "type": res[1], "price": float(res[2]), "date": p_date})
                    cursor.execute("INSERT INTO workout (product_id, workout_type, capacity) VALUES (%s, %s, %s);", (res[0], w_type, capacity))
                else:
                    calc_price = round(random.uniform(1000.00, 5000.00), 2)
                    cursor.execute(insert_product, (st_id, random.choice(area_ids), p_date, start, duration, calc_price, "service"))
                    res = cursor.fetchone()
                    product_records.append({"id": res[0], "type": res[1], "price": float(res[2]), "date": p_date})
                    cursor.execute("INSERT INTO service (product_id, service_type, description) VALUES (%s, %s, %s);", (res[0], random.choice(SERVICE_ENUMS), gen_random_string(15)))
            package_ids = []
            client_active_infinity = set()
            pay_dock_counter = 100001
            for _ in range(60):
                c_id = random.choice(client_ids)
                st_id = random.choice(list(staff_info.keys()))
                pur_type = random.choice(["package", "contract", "booking"])
                p_date_dt = datetime(2026, random.randint(1, 12), random.randint(1, 28), random.randint(9, 18), 0, 0)
                if pur_type == "package":
                    amount = random.choice([5, 10, 15, 20])
                    discount = {5: 3, 10: 5, 15: 10, 20: 15}[amount]
                    total_price = round((float(staff_info[st_id]) * amount) * (1 - discount / 100), 2)
                    cursor.execute("INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price) VALUES (%s, %s, %s, %s, %s) RETURNING purchase_id, purchase_type, all_price;", (c_id, st_id, pur_type, p_date_dt, total_price))
                    pur_id, _, final_price = cursor.fetchone()
                    cursor.execute("INSERT INTO package (purchase_id, amount, price, discount, remainder) VALUES (%s, %s, %s, %s, %s);", (pur_id, amount, final_price, discount, amount))
                    package_ids.append(pur_id)
                    cursor.execute("INSERT INTO pay_dock (purchase_id, staff_id, payment_date, payment_check, price) VALUES (%s, %s, %s, %s, %s);", (pur_id, st_id, p_date_dt.date(), pay_dock_counter, final_price))
                    pay_dock_counter += 1
                elif pur_type == "contract":
                    sub_id = random.choice(list(sub_info.keys()))
                    duration_days = random.choice([30, 90, 180, 365])
                    d_start = p_date_dt.date()
                    p_type = "installment" if duration_days == 365 else "full"
                    N = random.choice([3, 4, 6, 12]) if p_type == "installment" else None
                    multipliers = {30: 1, 90: 2.7, 180: 5.0, 365: 9.0}
                    calculated_sub_price = round(float(sub_info[sub_id]["price"]) * multipliers[duration_days], 2)
                    cursor.execute("INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price) VALUES (%s, %s, %s, %s, %s) RETURNING purchase_id, purchase_type, all_price;", (c_id, st_id, pur_type, p_date_dt, calculated_sub_price))
                    pur_id, _, final_price = cursor.fetchone()
                    cursor.execute("INSERT INTO contract (purchase_id, sub_id, date_start, date_end, payment_type, installment_months, status) VALUES (%s, %s, %s, %s, %s, %s, %s);", (pur_id, sub_id, d_start, d_start + timedelta(days=duration_days), p_type, N, "paid"))
                    if sub_info[sub_id]["name"] == "Infinity":
                        client_active_infinity.add(c_id)
                    if p_type == "installment":
                        single_payment = round((float(final_price) / N) * (1 + (10 if N <= 6 else 15) / 100), 2)
                        for month in range(N):
                            cursor.execute("INSERT INTO plan (purchase_id, amount, pay_date) VALUES (%s, %s, %s);", (pur_id, single_payment, d_start + timedelta(days=30 * month)))
                            cursor.execute("INSERT INTO pay_dock (purchase_id, staff_id, payment_date, payment_check, price) VALUES (%s, %s, %s, %s, %s);", (pur_id, st_id, d_start + timedelta(days=30 * month), pay_dock_counter, single_payment))
                            pay_dock_counter += 1
                    else:
                        cursor.execute("INSERT INTO pay_dock (purchase_id, staff_id, payment_date, payment_check, price) VALUES (%s, %s, %s, %s, %s);", (pur_id, st_id, d_start, pay_dock_counter, final_price))
                        pay_dock_counter += 1
                else:
                    prod = random.choice(product_records)
                    pack_id = random.choice(package_ids) if (package_ids and random.choice([True, False])) else None
                    if pack_id:
                        final_price = 0.00
                    else:
                        final_price = prod["price"]
                        if c_id in client_active_infinity and prod["type"] == "workout":
                            cursor.execute("SELECT workout_type FROM workout WHERE product_id = %s;", (prod["id"],))
                            w_row = cursor.fetchone()
                            if w_row and w_row[0] == "individual":
                                final_price = round(prod["price"] * 0.93, 2)
                    cursor.execute("INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price) VALUES (%s, %s, %s, %s, %s) RETURNING purchase_id, purchase_type, all_price;", (c_id, st_id, pur_type, p_date_dt, final_price))
                    pur_id, _, final_price = cursor.fetchone()
                    cursor.execute("INSERT INTO booking (purchase_id, product_id, package_purchase_id, date_booking, status) VALUES (%s, %s, %s, %s, %s);", (pur_id, prod["id"], pack_id, p_date_dt, "visited"))
                    cursor.execute("INSERT INTO visit (client_id, gym_id, visit_date, entry_time, exit_time) VALUES (%s, %s, %s, '09:00:00', '11:00:00');", (c_id, random.choice(gym_ids), prod["date"]))
                    if final_price > 0:
                        cursor.execute("INSERT INTO pay_dock (purchase_id, staff_id, payment_date, payment_check, price) VALUES (%s, %s, %s, %s, %s);", (pur_id, st_id, p_date_dt.date(), pay_dock_counter, final_price))
                        pay_dock_counter += 1
            conn.commit()
            print("Commit")
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    reset_and_fill_db()