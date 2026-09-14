import pytest
from psycopg.types.json import Json


def unique_email():
    import uuid

    return f"test-{uuid.uuid4().hex}@example.com"


def unique_code():
    import uuid

    return f"TEST-{uuid.uuid4().hex}"


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
            VALUES (%s, %s, %s, %s)
            RETURNING user_id
            """,
            (
                unique_email(),
                "test-password-hash",
                "Test",
                "User",
            ),
        )
        return cursor.fetchone()[0]


def create_project(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO research.projects (
                project_code,
                name
            )
            VALUES (%s, %s)
            RETURNING project_id
            """,
            (
                unique_code(),
                "Version Immutability Test Project",
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
            VALUES (%s, %s, %s, %s, %s)
            RETURNING model_item_id
            """,
            (
                project_id,
                unique_code(),
                "VARIABLE",
                "Test Variable",
                user_id,
            ),
        )
        return cursor.fetchone()[0], user_id


def create_model_item_version(connection):
    model_item_id, user_id = create_model_item(connection)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO research.model_item_versions (
                model_item_id,
                version_number,
                content,
                created_by
            )
            VALUES (%s, %s, %s, %s)
            RETURNING model_item_version_id
            """,
            (
                model_item_id,
                1,
                Json({"description": "Original scientific version"}),
                user_id,
            ),
        )
        return cursor.fetchone()[0]


def test_model_item_version_cannot_be_updated(database_connection):
    version_id = create_model_item_version(database_connection)

    with pytest.raises(Exception, match="immutable scientific records"):
        with database_connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE research.model_item_versions
                SET version_number = 2
                WHERE model_item_version_id = %s
                """,
                (version_id,),
            )


def test_model_item_version_cannot_be_deleted(database_connection):
    version_id = create_model_item_version(database_connection)

    with pytest.raises(Exception, match="immutable scientific records"):
        with database_connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM research.model_item_versions
                WHERE model_item_version_id = %s
                """,
                (version_id,),
            )
