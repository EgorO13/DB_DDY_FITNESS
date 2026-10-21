import psycopg2

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
        new_DB = """
DROP TABLE IF EXISTS
    pay_dock,
    plan,
    booking,
    contract,
    package,
    purchase,
    service,
    workout,
    product,
    visit,
    area,
    work_in_gym,
    staff,
    staff_role,
    sub,
    client,
    gym
CASCADE;

DROP TYPE IF EXISTS
    grade_enum,
    workout_enum,
    service_enum,
    product_enum,
    purchase_enum,
    contract_enum,
    booking_enum,
    sex_enum,
    payment_enum
CASCADE;


CREATE TYPE sex_enum AS ENUM (
    'male',
    'female'
);

CREATE TYPE grade_enum AS ENUM (
    'master',
    'expert',
    'top'
);

CREATE TYPE workout_enum AS ENUM (
    'individual',
    'group',
    'split'
);

CREATE TYPE service_enum AS ENUM (
    'sport massage',
    'SPA massage',
    'classic massage',
    'consultation'
);

CREATE TYPE product_enum AS ENUM (
    'workout',
    'service'
);

CREATE TYPE purchase_enum AS ENUM (
    'package',
    'contract',
    'booking'
);

CREATE TYPE contract_enum AS ENUM (
    'paid',
    'canceled',
    'in progress'
);

CREATE TYPE booking_enum AS ENUM (
    'recorded',
    'canceled',
    'visited'
);

CREATE TYPE payment_enum AS ENUM (
    'full',
    'installment'
);


CREATE TABLE gym (
    gym_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    address varchar(100) NOT NULL,
    phone char(12) NOT NULL UNIQUE
);


CREATE TABLE client (
    client_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name varchar(15) NOT NULL,
    last_name varchar(15) NOT NULL,
    passport char(10) NOT NULL UNIQUE,
    phone char(12) NOT NULL,
    sex sex_enum NOT NULL,
    birthday date NOT NULL
);


CREATE TABLE sub (
    sub_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sub_name varchar(20) NOT NULL UNIQUE,
    price decimal(8, 2) NOT NULL,
    individual_discount int NOT NULL DEFAULT 0,

    CONSTRAINT chk_sub_price
        CHECK (price > 0),

    CONSTRAINT chk_sub_discount
        CHECK (individual_discount BETWEEN 0 AND 100)
);


CREATE TABLE staff_role (
    staff_role_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name varchar(20) NOT NULL UNIQUE,
    grade grade_enum,
    workout_price decimal(8, 2),

    CONSTRAINT chk_workout_price
        CHECK (workout_price IS NULL OR workout_price > 0)
);


CREATE TABLE staff (
    staff_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    staff_role_id int NOT NULL REFERENCES staff_role(staff_role_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    first_name varchar(15) NOT NULL,
    last_name varchar(15) NOT NULL,
    passport char(10) NOT NULL UNIQUE,
    phone char(12) NOT NULL,
    birthday date NOT NULL
);


CREATE TABLE work_in_gym (
    gym_id int NOT NULL REFERENCES gym(gym_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    staff_id int NOT NULL REFERENCES staff(staff_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    PRIMARY KEY (gym_id, staff_id)
);


CREATE TABLE area (
    area_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    gym_id int NOT NULL REFERENCES gym(gym_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    area_name varchar(20) NOT NULL,

    CONSTRAINT uq_area_gym_name
        UNIQUE (gym_id, area_name)
);


CREATE TABLE visit (
    visit_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id int NOT NULL REFERENCES client(client_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    gym_id int NOT NULL REFERENCES gym(gym_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    visit_date date NOT NULL,
    entry_time time NOT NULL,
    exit_time time,

    CONSTRAINT chk_visit_time
        CHECK (exit_time IS NULL OR exit_time >= entry_time)
);


CREATE TABLE product (
    product_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    staff_id int NOT NULL REFERENCES staff(staff_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    area_id int NOT NULL REFERENCES area(area_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    product_date date NOT NULL,
    start_time time NOT NULL,
    duration_min int NOT NULL,
    price decimal(8, 2) NOT NULL,
    product_type product_enum NOT NULL,

    CONSTRAINT chk_product_duration
        CHECK (duration_min > 0),

    CONSTRAINT chk_product_price
        CHECK (price >= 0)
);


CREATE TABLE workout (
    product_id int PRIMARY KEY REFERENCES product(product_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    workout_type workout_enum NOT NULL,
    capacity smallint NOT NULL,

    CONSTRAINT chk_workout_capacity
        CHECK (
            (workout_type = 'individual' AND capacity = 1)
            OR
            (workout_type = 'split' AND capacity BETWEEN 2 AND 3)
            OR
            (workout_type = 'group' AND capacity >= 2)
        )
);


CREATE TABLE service (
    product_id int PRIMARY KEY REFERENCES product(product_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    service_type service_enum NOT NULL,
    description varchar(50)
);


CREATE TABLE purchase (
    purchase_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id int NOT NULL REFERENCES client(client_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    staff_id int NOT NULL REFERENCES staff(staff_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    purchase_type purchase_enum NOT NULL,
    purchase_date timestamp NOT NULL,
    all_price decimal(8, 2) NOT NULL,

    CONSTRAINT chk_purchase_price
        CHECK (all_price >= 0)
);


CREATE TABLE package (
    purchase_id int PRIMARY KEY REFERENCES purchase(purchase_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    amount int NOT NULL,
    price decimal(8, 2) NOT NULL,
    discount int NOT NULL DEFAULT 0,
    remainder int NOT NULL,

    CONSTRAINT chk_package_amount
        CHECK (amount > 0),

    CONSTRAINT chk_package_price
        CHECK (price > 0),

    CONSTRAINT chk_package_discount
        CHECK (discount IN (0, 3, 5, 10, 15)),

    CONSTRAINT chk_package_remainder
        CHECK (remainder BETWEEN 0 AND amount)
);


CREATE TABLE contract (
    purchase_id int PRIMARY KEY REFERENCES purchase(purchase_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    sub_id int NOT NULL REFERENCES sub(sub_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    date_start date NOT NULL,
    date_end date NOT NULL,
    payment_type payment_enum NOT NULL,
    status contract_enum NOT NULL,

    CONSTRAINT chk_contract_dates
        CHECK (date_end >= date_start)
);


CREATE TABLE booking (
    purchase_id int PRIMARY KEY REFERENCES purchase(purchase_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    product_id int NOT NULL REFERENCES product(product_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    package_purchase_id int REFERENCES package(purchase_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    date_booking timestamp NOT NULL,
    status booking_enum NOT NULL
);


CREATE TABLE plan (
    plan_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    purchase_id int NOT NULL REFERENCES contract(purchase_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    amount decimal(8, 2) NOT NULL,
    pay_date date NOT NULL,

    CONSTRAINT chk_plan_amount
        CHECK (amount > 0)
);


CREATE TABLE pay_dock (
    pay_dock_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    purchase_id int NOT NULL REFERENCES purchase(purchase_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    staff_id int NOT NULL REFERENCES staff(staff_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    payment_date date NOT NULL,
    payment_check int NOT NULL UNIQUE,
    price decimal(8, 2) NOT NULL,

    CONSTRAINT chk_payment_price
        CHECK (price > 0)
);
        """
        cursor.execute(new_DB)
        connection.commit()
        print("Commit")

except Exception as error:
    print("Error:", error)

finally:
    if connection:
        connection.close()
        print("End")
