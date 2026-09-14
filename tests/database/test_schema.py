def test_required_schemas_exist(database_connection):
    expected_schemas = {
        "auth",
        "research",
        "clinical",
        "simulation",
        "audit",
    }

    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = ANY(%s);
            """,
            (list(expected_schemas),),
        )

        actual_schemas = {row[0] for row in cursor.fetchall()}

    assert actual_schemas == expected_schemas


def test_expected_table_count(database_connection):
    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM pg_tables
            WHERE schemaname IN (
                'auth',
                'research',
                'clinical',
                'simulation',
                'audit'
            );
            """
        )

        table_count = cursor.fetchone()[0]

    assert table_count == 37


def test_expected_views_exist(database_connection):
    expected_views = {
        "v_current_model_items",
        "v_review_status_summary",
    }

    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.views
            WHERE table_schema = 'research';
            """
        )

        actual_views = {row[0] for row in cursor.fetchall()}

    assert actual_views == expected_views
