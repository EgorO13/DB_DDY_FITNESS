from config import get_connection


def run_report():
    print("\nДоступные отчеты:")
    print("1. Отчет по продажам абонементов")
    print("2. Анализ загруженности тренеров")
    print("3. Статистика посещений клиентов")
    print("4. Анализ финансовых потоков по направлениям")
    print("5. Рейтинг активности клиентов")
    print("6. Все сразу")

    try:
        n = int(input("\nВведите номер отчета [1; 6]: "))
        if not (1 <= n <= 6): raise ValueError
    except ValueError:
        print("Неверный номер отчета.")
        return

    subsSelect = """
SELECT 
    s.sub_name AS "Тип абонемента",
    ROUND(EXTRACT(EPOCH FROM (AGE(c.date_end, c.date_start))) / (60*60*24*30)) AS "Срок (мес)",
    COUNT(DISTINCT c.purchase_id) AS "Договоров всего",
    SUM(DISTINCT p.all_price) AS "Сумма продаж",
    COALESCE(SUM(pd.price), 0) AS "Оплачено средств",
    COUNT(DISTINCT CASE WHEN c.payment_type = 'installment' THEN c.purchase_id END) AS "Из них в рассрочку",
    ROUND(COALESCE(AVG(pd.price), 0), 2) AS "Средний платеж"
FROM contract c
JOIN sub s ON c.sub_id = s.sub_id
JOIN purchase p ON c.purchase_id = p.purchase_id
LEFT JOIN pay_dock pd ON p.purchase_id = pd.purchase_id
GROUP BY s.sub_name, "Срок (мес)";
    """

    staffSelect = """
SELECT 
    st.last_name || ' ' || st.first_name AS "ФИО тренера",
    sr.grade AS "Грейд",
    COALESCE(STRING_AGG(DISTINCT g.address, '; '), 'Не привязан к залу') AS "Спортцентры",
    COUNT(DISTINCT CASE WHEN w.workout_type = 'individual' THEN prod.product_id END) AS "Перс. тренировки",
    COUNT(DISTINCT CASE WHEN w.workout_type = 'group' THEN prod.product_id END) AS "Групп. занятия",
    COALESCE(SUM(CASE WHEN prod.product_type = 'workout' THEN prod.duration_min ELSE 0 END), 0) AS "Время занятий (мин)",
    ROUND(COUNT(DISTINCT CASE WHEN prod.product_type = 'workout' THEN prod.product_id END) / 12.0, 2) AS "Средняя загрузка/мес"
FROM staff st
JOIN staff_role sr ON st.staff_role_id = sr.staff_role_id
LEFT JOIN work_in_gym wig ON st.staff_id = wig.staff_id
LEFT JOIN gym g ON wig.gym_id = g.gym_id
LEFT JOIN product prod ON st.staff_id = prod.staff_id AND EXTRACT(YEAR FROM prod.product_date) = 2026
LEFT JOIN workout w ON prod.product_id = w.product_id
GROUP BY st.staff_id, sr.grade;
    """

    visitSelect = """
SELECT 
    cl.last_name || ' ' || cl.first_name AS "ФИО клиента",
    COUNT(DISTINCT v.visit_id) AS "Посещений центра",
    COUNT(DISTINCT CASE WHEN w.workout_type = 'individual' THEN b.purchase_id END) AS "Индивидуальных",
    COUNT(DISTINCT CASE WHEN w.workout_type = 'group' THEN b.purchase_id END) AS "Групповых",
    COUNT(DISTINCT s.product_id) AS "Доп. услуг",
    COALESCE(SUM(EXTRACT(EPOCH FROM (v.exit_time - v.entry_time)) / 60), 0) AS "Всего минут в клубе"
FROM client cl
LEFT JOIN visit v ON cl.client_id = v.client_id
LEFT JOIN purchase p ON cl.client_id = p.client_id
LEFT JOIN booking b ON p.purchase_id = b.purchase_id AND b.status = 'visited'
LEFT JOIN product prod ON b.product_id = prod.product_id
LEFT JOIN workout w ON prod.product_id = w.product_id
LEFT JOIN service s ON prod.product_id = s.product_id
GROUP BY cl.client_id, cl.last_name, cl.first_name;
    """

    moneySelect = """
WITH financial_summary AS (
    SELECT 
        SUM(CASE WHEN p.purchase_type = 'contract' THEN pd.price ELSE 0 END) AS subs_income,
        SUM(CASE WHEN p.purchase_type = 'booking' AND w.workout_type = 'individual' THEN pd.price ELSE 0 END) AS personal_income,
        SUM(CASE WHEN p.purchase_type = 'booking' AND w.workout_type = 'group' THEN pd.price ELSE 0 END) AS group_income,
        SUM(CASE WHEN p.purchase_type = 'booking' AND s.product_id IS NOT NULL THEN pd.price ELSE 0 END) AS service_income,
        SUM(pd.price) AS total_income
    FROM pay_dock pd
    JOIN purchase p ON pd.purchase_id = p.purchase_id
    LEFT JOIN booking b ON p.purchase_id = b.purchase_id
    LEFT JOIN product prod ON b.product_id = prod.product_id
    LEFT JOIN workout w ON prod.product_id = w.product_id
    LEFT JOIN service s ON prod.product_id = s.product_id
)
SELECT 'Абонементы' AS "Направление", subs_income AS "Сумма оплат", ROUND((subs_income / total_income) * 100, 2) AS "Доля (%)" FROM financial_summary UNION ALL
SELECT 'Персональные тренировки', personal_income, ROUND((personal_income / total_income) * 100, 2) FROM financial_summary UNION ALL
SELECT 'Групповые занятия', group_income, ROUND((group_income / total_income) * 100, 2) FROM financial_summary UNION ALL
SELECT 'Дополнительные услуги', service_income, ROUND((service_income / total_income) * 100, 2) FROM financial_summary;
    """

    clientSelect = """
SELECT 
    cl.last_name || ' ' || cl.first_name AS "ФИО клиента",
    COUNT(DISTINCT v.visit_id) AS "Визиты",
    COALESCE(SUM(pd.price), 0) AS "Оплачено (руб)",
    COUNT(DISTINCT b.purchase_id) AS "Посещенные тренировки",
    COUNT(DISTINCT s.product_id) AS "Взято доп. услуг"
FROM client cl
LEFT JOIN visit v ON cl.client_id = v.client_id AND v.visit_date BETWEEN '2026-01-01' AND '2026-12-31'
LEFT JOIN purchase p ON cl.client_id = p.client_id
LEFT JOIN pay_dock pd ON p.purchase_id = pd.purchase_id AND pd.payment_date BETWEEN '2026-01-01' AND '2026-12-31'
LEFT JOIN booking b ON p.purchase_id = b.purchase_id AND b.status = 'visited'
LEFT JOIN product prod ON b.product_id = prod.product_id
LEFT JOIN service s ON prod.product_id = s.product_id
GROUP BY cl.client_id, cl.last_name, cl.first_name
ORDER BY "Визиты" DESC, "Оплачено (руб)" DESC;
    """

    report_list = []
    if n == 6:
        report_list = [
            (1, "ОТЧЕТ ПО ПРОДАЖАМ АБОНЕМЕНТОВ", subsSelect),
            (2, "АНАЛИЗ ЗАГРУЖЕННОСТИ ТРЕНЕРОВ", staffSelect),
            (3, "СТАТИСТИКА ПОСЕЩЕНИЙ КЛИЕНТОВ", visitSelect),
            (4, "АНАЛИЗ ФИНАНСОВЫХ ПОТОКОВ ПО НАПРАВЛЕНИЯМ", moneySelect),
            (5, "РЕЙТИНГ АКТИВНОСТИ КЛИЕНТОВ", clientSelect)
        ]
    else:
        titles = {
            1: "ОТЧЕТ ПО ПРОДАЖАМ АБОНЕМЕНТОВ",
            2: "АНАЛИЗ ЗАГРУЖЕННОСТИ ТРЕНЕРОВ",
            3: "СТАТИСТИКА ПОСЕЩЕНИЙ КЛИЕНТОВ",
            4: "АНАЛИЗ ФИНАНСОВЫХ ПОТОКОВ ПО НАПРАВЛЕНИЯМ",
            5: "РЕЙТИНГ АКТИВНОСТИ КЛИЕНТОВ"
        }
        report_list = [(n, titles[n],
                        queries := {1: subsSelect, 2: staffSelect, 3: visitSelect, 4: moneySelect, 5: clientSelect}[n])]

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for num, title, sql in report_list:
                print(f"\n=== {num}. {title} ===")
                cursor.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                print(" | ".join(columns))
                print("-" * 120)
                for row in cursor.fetchall():
                    print(" | ".join(str(val) for val in row))
                print("=" * 120)
    except Exception as error:
        print("Error:", error)
    finally:
        conn.close()


if __name__ == "__main__":
    run_report()
