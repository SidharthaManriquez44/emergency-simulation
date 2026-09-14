import pytest

from tests.database.helpers import (
    create_model_item,
    create_model_item_version,
)


def test_model_item_version_cannot_be_updated(database_connection):
    model_item_id, user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        1,
    )

    with pytest.raises(
        Exception,
        match="immutable scientific records",
    ):
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
    model_item_id, user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        1,
    )

    with pytest.raises(
        Exception,
        match="immutable scientific records",
    ):
        with database_connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM research.model_item_versions
                WHERE model_item_version_id = %s
                """,
                (version_id,),
            )
