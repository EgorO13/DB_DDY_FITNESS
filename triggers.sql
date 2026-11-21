/*
Первый триггер предназначен для автоматического формирования плана оплат при оформлении абонемента с рассрочкой.
При создании договора абонемента сроком 12 месяцев с разбивкой оплаты на части система должна автоматически
сформировать записи плана оплаты по каждому месяцу рассрочки. Размер каждого платежа рассчитывается на основании
общей стоимости абонемента, количества месяцев рассрочки и установленного коэффициента надбавки: при рассрочке
до 6 месяцев применяется коэффициент 10%, при рассрочке более 6 месяцев — 15%. Все сформированные платежи должны
быть связаны с соответствующим договором абонемента.
*/
CREATE OR REPLACE FUNCTION fn_generate_installment_plan()
RETURNS TRIGGER AS $$
DECLARE
    v_total_price decimal(8, 2);
    v_m_percent decimal(5, 2);
    v_single_payment decimal(8, 2);
    v_duration_days int;
    i int;
BEGIN
    IF NEW.payment_type = 'installment' THEN
        v_duration_days := NEW.date_end - NEW.date_start;

        IF v_duration_days < 365 THEN
            RAISE EXCEPTION 'Рассрочка доступна только для абонементов сроком на 12 месяцев.';
        END IF;

        IF NEW.installment_months IS NULL OR NEW.installment_months < 2 OR NEW.installment_months > 12 THEN
            RAISE EXCEPTION 'Укажите корректное количество месяцев рассрочки (от 2 до 12) в поле installment_months.';
        END IF;

        SELECT all_price INTO v_total_price
        FROM purchase
        WHERE purchase_id = NEW.purchase_id;

        IF NEW.installment_months <= 6 THEN
            v_m_percent := 10.0;
        ELSE
            v_m_percent := 15.0;
        END IF;

        v_single_payment := ROUND((v_total_price / NEW.installment_months) * (1 + v_m_percent / 100.0), 2);

        FOR i IN 0..(NEW.installment_months - 1) LOOP
            INSERT INTO plan (purchase_id, amount, pay_date)
            VALUES (
                NEW.purchase_id,
                v_single_payment,
                (NEW.date_start + (i * INTERVAL '1 month'))::date
            );
        END LOOP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_contract_installment_plan ON contract;
CREATE TRIGGER trg_contract_installment_plan
AFTER INSERT ON contract
FOR EACH ROW
EXECUTE FUNCTION fn_generate_installment_plan();

/*
Примеры запросов:
1) Успех, рассрочка на 6 месяцев
WITH new_pur AS (
    INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price)
    VALUES (1, 1, 'contract', NOW(), 30000.00)
    RETURNING purchase_id
)
INSERT INTO contract (purchase_id, sub_id, date_start, date_end, payment_type, installment_months, status)
SELECT purchase_id, 1, '2026-12-01', '2027-12-01', 'installment', 6, 'in progress'
FROM new_pur;
SELECT * FROM plan WHERE purchase_id = (SELECT MAX(purchase_id) FROM contract);

2) Успех, рассрочка на 12 месяцев
WITH new_pur AS (
    INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price)
    VALUES (2, 1, 'contract', NOW(), 36000.00)
    RETURNING purchase_id
)
INSERT INTO contract (purchase_id, sub_id, date_start, date_end, payment_type, installment_months, status)
SELECT purchase_id, 1, '2026-12-01', '2027-12-01', 'installment', 12, 'in progress'
FROM new_pur;
SELECT * FROM plan WHERE purchase_id = (SELECT MAX(purchase_id) FROM contract);

3) Ошибка, рассрочка на 6 месяцев
WITH bad_pur AS (
    INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price)
    VALUES (1, 1, 'contract', NOW(), 15000.00)
    RETURNING purchase_id
)
INSERT INTO contract (purchase_id, sub_id, date_start, date_end, payment_type, installment_months, status)
SELECT purchase_id, 1, '2026-12-01', '2027-06-01', 'installment', 6, 'in progress'
FROM bad_pur;
*/

/*
Второй триггер обеспечивает контроль количества участников групповых занятий. Перед добавлением клиента
в список участников групповой тренировки необходимо проверить, не превышает ли текущее количество записанных
клиентов максимально допустимое число участников для данного занятия. В случае отсутствия свободных мест
операция записи должна быть отменена с выдачей сообщения об ошибке. Изменение количества участников после
достижения лимита запрещается.
*/
CREATE OR REPLACE FUNCTION fn_check_group_workout_capacity()
RETURNS TRIGGER AS $$
DECLARE
    v_workout_type workout_enum;
    v_capacity smallint;
    v_current_count int;
BEGIN
    IF NEW.status = 'canceled' THEN
        RETURN NEW;
    END IF;

    SELECT w.workout_type, w.capacity
    INTO v_workout_type, v_capacity
    FROM workout w
    WHERE w.product_id = NEW.product_id;

    IF FOUND AND v_workout_type = 'group' THEN
        SELECT COUNT(*) INTO v_current_count
        FROM booking
        WHERE product_id = NEW.product_id AND status IN ('recorded', 'visited') AND purchase_id <> COALESCE(NEW.purchase_id, -1);
        IF v_current_count >= v_capacity THEN
            RAISE EXCEPTION 'Запись невозможна: достигнут лимит участников (%) для групповой тренировки ID %.', v_capacity, NEW.product_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_booking_group_capacity ON booking;
CREATE TRIGGER trg_booking_group_capacity
BEFORE INSERT OR UPDATE ON booking
FOR EACH ROW
EXECUTE FUNCTION fn_check_group_workout_capacity();
/*
Примеры запросов:
1) Подготовка: создание групповой тренировки с лимитом 2 человека
WITH new_prod AS (
    INSERT INTO product (staff_id, area_id, product_date, start_time, duration_min, price, product_type)
    VALUES (1, 1, '2026-12-20', '18:00:00', 60, 800.00, 'workout')
    RETURNING product_id
)
INSERT INTO workout (product_id, workout_type, capacity)
SELECT product_id, 'group', 2 FROM new_prod
RETURNING product_id;

2) Успех, запись 1-го и 2-го клиентов (заполнение лимита)
WITH p1 AS (
    INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price)
    VALUES (1, 1, 'booking', NOW(), 800.00)
    RETURNING purchase_id
)
INSERT INTO booking (purchase_id, product_id, date_booking, status)
SELECT purchase_id, (SELECT MAX(product_id) FROM workout), NOW(), 'recorded' FROM p1;

WITH p2 AS (
    INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price)
    VALUES (2, 1, 'booking', NOW(), 800.00)
    RETURNING purchase_id
)
INSERT INTO booking (purchase_id, product_id, date_booking, status)
SELECT purchase_id, (SELECT MAX(product_id) FROM workout), NOW(), 'recorded' FROM p2;

3) Ошибка, попытка записать 3-го клиента сверх лимита (INSERT)
WITH p3 AS (
    INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price)
    VALUES (3, 1, 'booking', NOW(), 800.00)
    RETURNING purchase_id
)
INSERT INTO booking (purchase_id, product_id, date_booking, status)
SELECT purchase_id, (SELECT MAX(product_id) FROM workout), NOW(), 'recorded' FROM p3;

4) Ошибка, попытка активировать отмененную бронь при заполненной группе (UPDATE)
WITH p4 AS (
    INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price)
    VALUES (4, 1, 'booking', NOW(), 800.00)
    RETURNING purchase_id
)
INSERT INTO booking (purchase_id, product_id, date_booking, status)
SELECT purchase_id, (SELECT MAX(product_id) FROM workout), NOW(), 'canceled' FROM p4;

UPDATE booking
SET status = 'recorded'
WHERE purchase_id = (SELECT MAX(purchase_id) FROM booking);
*/