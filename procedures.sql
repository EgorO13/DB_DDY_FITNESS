/*
Первая процедура предназначена для создания новой групповой тренировки. Процедура принимает идентификатор
инструктора, идентификатор зоны проведения, дату и временной интервал занятия, а также список идентификаторов
клиентов, желающих принять участие в тренировке. Перед созданием записи процедура должна проверить доступность
инструктора и зоны на заданное время, а также убедиться, что количество участников не превышает допустимый лимит.
При выполнении всех условий формируется запись групповой тренировки с привязкой инструктора, зоны и списка
участников. В случае нарушения хотя бы одного условия процедура завершает выполнение с информативным сообщением об ошибке.
*/
CREATE OR REPLACE PROCEDURE sp_create_group_workout(
    p_instructor_id int,
    p_area_id int,
    p_date date,
    p_start_time time,
    p_duration_min int,
    p_capacity smallint,
    p_client_ids int[],
    p_admin_id int DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_end_time time;
    v_conflict_exists boolean;
    v_clients_count int;
    v_base_price decimal(8, 2);
    v_workout_price decimal(8, 2);
    v_product_id int;
    v_purchase_id int;
    v_client_id int;
    v_has_infinity boolean;
    v_registrar_id int;
BEGIN
    v_end_time := p_start_time + (p_duration_min * INTERVAL '1 minute');
    v_clients_count := COALESCE(array_length(p_client_ids, 1), 0);
    v_registrar_id := COALESCE(p_admin_id, p_instructor_id);

    IF p_capacity < 2 THEN
        RAISE EXCEPTION 'Вместимость групповой тренировки должна быть не менее 2 человек.';
    END IF;

    IF v_clients_count > p_capacity THEN
        RAISE EXCEPTION 'Количество переданных клиентов (%) превышает лимит группы (%).', v_clients_count, p_capacity;
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM product
        WHERE staff_id = p_instructor_id
          AND product_date = p_date
          AND p_start_time < (start_time + (duration_min * INTERVAL '1 minute'))
          AND v_end_time > start_time
    ) INTO v_conflict_exists;

    IF v_conflict_exists THEN
        RAISE EXCEPTION 'Инструктор (ID %) уже занят в указанный временной интервал (% - %).', p_instructor_id, p_start_time, v_end_time;
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM product
        WHERE area_id = p_area_id
          AND product_date = p_date
          AND p_start_time < (start_time + (duration_min * INTERVAL '1 minute'))
          AND v_end_time > start_time
    ) INTO v_conflict_exists;

    IF v_conflict_exists THEN
        RAISE EXCEPTION 'Зона проведения (ID %) занята в указанный временной интервал (% - %).', p_area_id, p_start_time, v_end_time;
    END IF;

    SELECT COALESCE(sr.workout_price, 1000.00) INTO v_base_price
    FROM staff s
    JOIN staff_role sr ON s.staff_role_id = sr.staff_role_id
    WHERE s.staff_id = p_instructor_id;

    v_workout_price := ROUND(v_base_price * 0.4, 2);

    INSERT INTO product (staff_id, area_id, product_date, start_time, duration_min, price, product_type)
    VALUES (p_instructor_id, p_area_id, p_date, p_start_time, p_duration_min, v_workout_price, 'workout')
    RETURNING product_id INTO v_product_id;

    INSERT INTO workout (product_id, workout_type, capacity)
    VALUES (v_product_id, 'group', p_capacity);

    IF v_clients_count > 0 THEN
        FOREACH v_client_id IN ARRAY p_client_ids LOOP
            SELECT EXISTS (
                SELECT 1 FROM contract c
                JOIN purchase p ON c.purchase_id = p.purchase_id
                JOIN sub s ON c.sub_id = s.sub_id
                WHERE p.client_id = v_client_id
                  AND s.sub_name = 'Infinity'
                  AND c.status = 'paid'
                  AND p_date BETWEEN c.date_start AND c.date_end
            ) INTO v_has_infinity;

            INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price)
            VALUES (
                v_client_id,
                v_registrar_id,
                'booking',
                CURRENT_TIMESTAMP,
                CASE WHEN v_has_infinity THEN 0.00 ELSE v_workout_price END
            )
            RETURNING purchase_id INTO v_purchase_id;

            INSERT INTO booking (purchase_id, product_id, package_purchase_id, date_booking, status)
            VALUES (v_purchase_id, v_product_id, NULL, CURRENT_TIMESTAMP, 'recorded');
        END LOOP;
    END IF;
END;
$$;

/*
Примеры запросов для первой процедуры (sp_create_group_workout):
1) Успех, создание групповой тренировки на 5 мест и запись клиентов ID 1, 2, 3
CALL sp_create_group_workout(
    p_instructor_id => 1,
    p_area_id => 1,
    p_date => '2026-12-25',
    p_start_time => '14:00:00',
    p_duration_min => 60,
    p_capacity => 5::smallint,
    p_client_ids => ARRAY[1, 2, 3],
    p_admin_id => 2
);

2) Ошибка, инструктор занят в пересекающийся временной интервал (14:30 - 15:30)
CALL sp_create_group_workout(
    p_instructor_id => 1,
    p_area_id => 2,
    p_date => '2026-12-25',
    p_start_time => '14:30:00',
    p_duration_min => 60,
    p_capacity => 5::smallint,
    p_client_ids => ARRAY[4, 5],
    p_admin_id => 2
);

3) Ошибка, зона проведения занята другим инструктором в это же время
CALL sp_create_group_workout(
    p_instructor_id => 3,
    p_area_id => 1,
    p_date => '2026-12-25',
    p_start_time => '14:00:00',
    p_duration_min => 60,
    p_capacity => 5::smallint,
    p_client_ids => ARRAY[4, 5],
    p_admin_id => 2
);

4) Ошибка, количество переданных клиентов превышает лимит группы (3 клиента при лимите 2)
CALL sp_create_group_workout(
    p_instructor_id => 3,
    p_area_id => 2,
    p_date => '2026-12-26',
    p_start_time => '12:00:00',
    p_duration_min => 60,
    p_capacity => 2::smallint,
    p_client_ids => ARRAY[1, 2, 3],
    p_admin_id => 2
);
*/



/*
Вторая процедура предназначена для переноса персональной тренировки. Процедура получает идентификаторы
тренера и клиента, а также старое и новое время проведения тренировки. Перед переносом выполняется проверка
доступности тренера и отсутствия у клиента других тренировок в новом временном интервале. Если конфликтов
не выявлено, время тренировки обновляется с сохранением всех остальных параметров. В противном случае
процедура отклоняет перенос, фиксируя причину невозможности изменения расписания.
*/
CREATE OR REPLACE PROCEDURE sp_reschedule_personal_workout(
    p_trainer_id int,
    p_client_id int,
    p_old_date date,
    p_old_start_time time,
    p_new_date date,
    p_new_start_time time
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_product_id int;
    v_area_id int;
    v_duration_min int;
    v_new_end_time time;
    v_conflict_exists boolean;
BEGIN
    SELECT pr.product_id, pr.area_id, pr.duration_min
    INTO v_product_id, v_area_id, v_duration_min
    FROM product pr
    JOIN workout w ON pr.product_id = w.product_id
    JOIN booking b ON pr.product_id = b.product_id
    JOIN purchase pu ON b.purchase_id = pu.purchase_id
    WHERE pr.staff_id = p_trainer_id AND pu.client_id = p_client_id AND pr.product_date = p_old_date
      AND pr.start_time = p_old_start_time AND w.workout_type = 'individual' AND b.status = 'recorded';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Перенос отклонен: активная персональная тренировка для клиента ID % с тренером ID % на % в % не найдена.', p_client_id, p_trainer_id, p_old_date, p_old_start_time;
    END IF;

    v_new_end_time := p_new_start_time + (v_duration_min * INTERVAL '1 minute');

    SELECT EXISTS (
        SELECT 1 FROM product
        WHERE staff_id = p_trainer_id
          AND product_id <> v_product_id
          AND product_date = p_new_date
          AND p_new_start_time < (start_time + (duration_min * INTERVAL '1 minute'))
          AND v_new_end_time > start_time
    ) INTO v_conflict_exists;

    IF v_conflict_exists THEN
        RAISE EXCEPTION 'Перенос отклонен: тренер ID % уже занят % в интервале % - %.', p_trainer_id, p_new_date, p_new_start_time, v_new_end_time;
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM product pr
        JOIN booking b ON pr.product_id = b.product_id
        JOIN purchase pu ON b.purchase_id = pu.purchase_id
        WHERE pu.client_id = p_client_id
          AND pr.product_id <> v_product_id
          AND b.status IN ('recorded', 'visited')
          AND pr.product_date = p_new_date
          AND p_new_start_time < (pr.start_time + (pr.duration_min * INTERVAL '1 minute'))
          AND v_new_end_time > pr.start_time
    ) INTO v_conflict_exists;

    IF v_conflict_exists THEN
        RAISE EXCEPTION 'Перенос отклонен: у клиента ID % уже запланировано другое занятие % в интервале % - %.', p_client_id, p_new_date, p_new_start_time, v_new_end_time;
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM product
        WHERE area_id = v_area_id
          AND product_id <> v_product_id
          AND product_date = p_new_date
          AND p_new_start_time < (start_time + (duration_min * INTERVAL '1 minute'))
          AND v_new_end_time > start_time
    ) INTO v_conflict_exists;

    IF v_conflict_exists THEN
        RAISE EXCEPTION 'Перенос отклонен: зона проведения (ID %) занята % в интервале % - %.', v_area_id, p_new_date, p_new_start_time, v_new_end_time;
    END IF;

    UPDATE product
    SET product_date = p_new_date, start_time = p_new_start_time
    WHERE product_id = v_product_id;
END;
$$;

/*
Примеры запросов для второй процедуры (sp_reschedule_personal_workout):
1) Подготовка: создание персональной тренировки для клиента ID 4 у тренера ID 3 на 2026-12-27 в 10:00
WITH new_prod AS (
    INSERT INTO product (staff_id, area_id, product_date, start_time, duration_min, price, product_type)
    VALUES (3, 1, '2026-12-27', '10:00:00', 60, 2500.00, 'workout')
    RETURNING product_id
),
new_work AS (
    INSERT INTO workout (product_id, workout_type, capacity)
    SELECT product_id, 'individual', 1 FROM new_prod
    RETURNING product_id
),
new_purch AS (
    INSERT INTO purchase (client_id, staff_id, purchase_type, purchase_date, all_price)
    VALUES (4, 1, 'booking', NOW(), 2500.00)
    RETURNING purchase_id
)
INSERT INTO booking (purchase_id, product_id, date_booking, status)
SELECT new_purch.purchase_id, new_work.product_id, NOW(), 'recorded'
FROM new_purch, new_work;

2) Успех, перенос персональной тренировки на 2026-12-28 в 16:00
CALL sp_reschedule_personal_workout(
    p_trainer_id => 3,
    p_client_id => 4,
    p_old_date => '2026-12-27',
    p_old_start_time => '10:00:00',
    p_new_date => '2026-12-28',
    p_new_start_time => '16:00:00'
);

3) Ошибка, тренировка по старому времени больше не существует (уже перенесена)
CALL sp_reschedule_personal_workout(
    p_trainer_id => 3,
    p_client_id => 4,
    p_old_date => '2026-12-27',
    p_old_start_time => '10:00:00',
    p_new_date => '2026-12-29',
    p_new_start_time => '16:00:00'
);

4) Ошибка, у клиента ID 4 уже есть другое занятие в это время (в другой зоне ID 2, поэтому зона ID 1 и тренер ID 3 свободны)
-- Сначала создаем для клиента ID 4 занятие в зоне ID 2 на 2026-12-29 в 11:00
CALL sp_create_group_workout(
    p_instructor_id => 2,
    p_area_id => 2,
    p_date => '2026-12-29',
    p_start_time => '11:00:00',
    p_duration_min => 60,
    p_capacity => 5::smallint,
    p_client_ids => ARRAY[4],
    p_admin_id => 2
);

-- Теперь пытаемся перенести персональную тренировку клиента ID 4 (зона ID 1, тренер ID 3) на 2026-12-29 в 11:00
CALL sp_reschedule_personal_workout(
    p_trainer_id => 3,
    p_client_id => 4,
    p_old_date => '2026-12-28',
    p_old_start_time => '16:00:00',
    p_new_date => '2026-12-29',
    p_new_start_time => '11:00:00'
);
*/