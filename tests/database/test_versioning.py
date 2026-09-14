import psycopg
import pytest
from helpers import (
    create_model_item,
    create_model_item_version,
    create_user,
)
from psycopg.types.json import Json


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
