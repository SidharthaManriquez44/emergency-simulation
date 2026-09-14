import psycopg
import pytest
from psycopg.types.json import Json


def unique_email() -> str:
    import uuid

    return f"test_{uuid.uuid4().hex}@example.com"


def unique_code() -> str:
    import uuid

    return f"TEST_{uuid.uuid4().hex[:12]}"


def create_user(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO auth.users (
                email,
                password_hash,
                first_name,
                last_name
            )
            VALUES (
                %s,
                'test-password-hash',
                'Test',
                'User'
            )
            RETURNING user_id
            """,
            (unique_email(),),
        )

        return cursor.fetchone()[0]


def create_project(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO research.projects (
                project_code,
                name,
                description
            )
            VALUES (
                %s,
                %s,
                'Test project'
            )
            RETURNING project_id
            """,
            (
                unique_code(),
                "Test Project",
            ),
        )

        return cursor.fetchone()[0]


def create_model_item(connection):
    user_id = create_user(connection)
    project_id = create_project(connection)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO research.model_items (
                project_id,
                item_code,
                item_type,
                name,
                created_by
            )
            VALUES (
                %s,
                %s,
                'CLINICAL_RULE',
                'Test Rule',
                %s
            )
            RETURNING model_item_id
            """,
            (
                project_id,
                unique_code(),
                user_id,
            ),
        )

        return cursor.fetchone()[0], user_id


def create_model_item_version(
    connection,
    model_item_id,
    user_id,
    version_number,
):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO research.model_item_versions (
                model_item_id,
                version_number,
                content,
                created_by
            )
            VALUES (
                %s,
                %s,
                %s,
                %s
            )
            RETURNING model_item_version_id
            """,
            (
                model_item_id,
                version_number,
                Json({"description": (f"Test version {version_number}")}),
                user_id,
            ),
        )

        return cursor.fetchone()[0]


def test_model_item_version_requires_existing_model_item(
    database_connection,
):
    user_id = create_user(database_connection)

    with database_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            cursor.execute(
                """
                INSERT INTO research.model_item_versions (
                    model_item_id,
                    version_number,
                    content,
                    created_by
                )
                VALUES (
                    999999999,
                    1,
                    %s,
                    %s
                )
                """,
                (
                    Json({"description": "Test"}),
                    user_id,
                ),
            )


def test_model_item_version_number_is_unique_per_model_item(
    database_connection,
):
    model_item_id, user_id = create_model_item(database_connection)

    create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        1,
    )

    with pytest.raises(psycopg.errors.UniqueViolation):
        create_model_item_version(
            database_connection,
            model_item_id,
            user_id,
            1,
        )


def test_different_model_items_can_have_same_version_number(
    database_connection,
):
    model_item_a, user_id_a = create_model_item(database_connection)

    model_item_b, user_id_b = create_model_item(database_connection)

    version_a = create_model_item_version(
        database_connection,
        model_item_a,
        user_id_a,
        1,
    )

    version_b = create_model_item_version(
        database_connection,
        model_item_b,
        user_id_b,
        1,
    )

    assert version_a != version_b


def test_model_item_supports_multiple_versions(
    database_connection,
):
    model_item_id, user_id = create_model_item(database_connection)

    version_1 = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        1,
    )

    version_2 = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        2,
    )

    version_3 = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        3,
    )

    assert version_1 != version_2
    assert version_2 != version_3
    assert version_1 != version_3
