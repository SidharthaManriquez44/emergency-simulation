import uuid

import psycopg
import pytest
from psycopg.types.json import Json


def unique_email() -> str:
    return f"test_{uuid.uuid4().hex}@example.com"


def unique_code() -> str:
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
            """INSERT INTO research.projects (
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


def test_user_email_is_unique(database_connection):
    email = unique_email()

    with database_connection.cursor() as cursor:
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
                'John',
                'Doe'
            )
            """,
            (email,),
        )

        with pytest.raises(psycopg.errors.UniqueViolation):
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
                    'Jane',
                    'Doe'
                )
                """,
                (email,),
            )


def test_user_email_cannot_be_null(database_connection):
    with database_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.NotNullViolation):
            cursor.execute(
                """
                INSERT INTO auth.users (
                    email,
                    first_name,
                    last_name
                )
                VALUES (
                    NULL,
                    'Test',
                    'User'
                )
                """
            )


def test_project_name_cannot_be_null(database_connection):
    with database_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.NotNullViolation):
            cursor.execute(
                """
                INSERT INTO research.projects (
                    name,
                    description
                )
                VALUES (
                    NULL,
                    'Test project'
                )
                """
            )


def test_model_item_requires_existing_project(database_connection):
    user_id = create_user(database_connection)
    fake_project_id = nonexistent_project_id(database_connection)

    with database_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
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
                """,
                (
                    fake_project_id,
                    unique_code(),
                    user_id,
                ),
            )


def test_model_item_requires_existing_creator(database_connection):
    project_id = create_project(database_connection)
    fake_user_id = nonexistent_user_id(database_connection)

    with database_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
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
                """,
                (
                    project_id,
                    unique_code(),
                    fake_user_id,
                ),
            )


def nonexistent_project_id(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(MAX(project_id), 0) + 1
            FROM research.projects
            """
        )

        return cursor.fetchone()[0]


def nonexistent_user_id(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COALESCE(MAX(user_id), 0) + 1
            FROM auth.users
            """
        )

        return cursor.fetchone()[0]


def test_clinical_domain_cannot_reference_itself(database_connection):
    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO clinical.clinical_domains (
                code,
                name
            )
            VALUES (
                %s,
                %s
            )
            RETURNING clinical_domain_id
            """,
            (
                unique_code(),
                "Test Domain",
            ),
        )

        domain_id = cursor.fetchone()[0]

        with pytest.raises(psycopg.errors.CheckViolation):
            cursor.execute(
                """
                UPDATE clinical.clinical_domains
                SET parent_domain_id = clinical_domain_id
                WHERE clinical_domain_id = %s
                """,
                (domain_id,),
            )


def test_model_item_version_number_must_be_positive(
    database_connection,
):
    user_id = create_user(database_connection)
    project_id = create_project(database_connection)

    with database_connection.cursor() as cursor:
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

        model_item_id = cursor.fetchone()[0]

        with pytest.raises(psycopg.errors.CheckViolation):
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
                    0,
                    %s,
                    %s
                )
                """,
                (
                    model_item_id,
                    Json({"description": "Test content"}),
                    user_id,
                ),
            )


def create_variable(connection):
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
                'VARIABLE',
                'Test Variable',
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

        model_item_id = cursor.fetchone()[0]

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
                1,
                %s,
                %s
            )
            RETURNING model_item_version_id
            """,
            (
                model_item_id,
                Json({"description": "Test variable version"}),
                user_id,
            ),
        )

        version_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO clinical.variables (
                model_item_version_id,
                name,
                data_type,
                description
            )
            VALUES (
                %s,
                'Test Variable',
                'NUMERIC',
                'Test variable'
            )
            """,
            (version_id,),
        )

        return version_id


def test_parameter_minimum_cannot_exceed_maximum(
    database_connection,
):
    variable_id = create_variable(database_connection)

    with database_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.CheckViolation):
            cursor.execute(
                """
                INSERT INTO clinical.parameters (
                    variable_id,
                    distribution,
                    minimum_value,
                    maximum_value
                )
                VALUES (
                    %s,
                    'uniform',
                    100,
                    50
                )
                """,
                (variable_id,),
            )


def test_parameter_mode_must_be_within_bounds(
    database_connection,
):
    variable_id = create_variable(database_connection)

    with database_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.CheckViolation):
            cursor.execute(
                """
                INSERT INTO clinical.parameters (
                    variable_id,
                    distribution,
                    minimum_value,
                    mode_value,
                    maximum_value
                )
                VALUES (
                    %s,
                    'uniform',
                    10,
                    20,
                    15
                )
                """,
                (variable_id,),
            )


def test_triangular_distribution_requires_all_parameters(
    database_connection,
):
    variable_id = create_variable(database_connection)

    with database_connection.cursor() as cursor:
        with pytest.raises(psycopg.errors.CheckViolation):
            cursor.execute(
                """
                INSERT INTO clinical.parameters (
                    variable_id,
                    distribution,
                    minimum_value,
                    maximum_value
                )
                VALUES (
                    %s,
                    'triangular',
                    10,
                    20
                )
                """,
                (variable_id,),
            )


def create_profession(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO auth.professions (
                code,
                name,
                professional_group
            )
            VALUES (
                %s,
                %s,
                %s
            )
            RETURNING profession_id
            """,
            (
                unique_code(),
                "Test Profession",
                "Test Group",
            ),
        )

        return cursor.fetchone()[0]


def create_clinical_domain(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO clinical.clinical_domains (
                code,
                name
            )
            VALUES (
                %s,
                %s
            )
            RETURNING clinical_domain_id
            """,
            (
                unique_code(),
                "Test Clinical Domain",
            ),
        )

        return cursor.fetchone()[0]


def create_authority_rule(
    connection,
    *,
    authority_level="L1",
    can_review=True,
    can_validate=False,
    review_scope="Test review scope",
    rule_version=1,
):
    profession_id = create_profession(connection)
    clinical_domain_id = create_clinical_domain(connection)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO clinical.authority_rules (
                profession_id,
                specialty_id,
                clinical_domain_id,
                authority_level,
                can_review,
                can_validate,
                review_scope,
                rule_version
            )
            VALUES (
                %s,
                NULL,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING authority_rule_id
            """,
            (
                profession_id,
                clinical_domain_id,
                authority_level,
                can_review,
                can_validate,
                review_scope,
                rule_version,
            ),
        )

        return cursor.fetchone()[0]


def test_authority_level_must_be_valid(database_connection):
    with pytest.raises(psycopg.errors.CheckViolation):
        create_authority_rule(
            database_connection,
            authority_level="L6",
        )


def test_authority_review_scope_cannot_be_blank(
    database_connection,
):
    with pytest.raises(psycopg.errors.CheckViolation):
        create_authority_rule(
            database_connection,
            review_scope="   ",
        )


def test_authority_rule_version_must_be_positive(
    database_connection,
):
    with pytest.raises(psycopg.errors.CheckViolation):
        create_authority_rule(
            database_connection,
            rule_version=0,
        )


def test_authority_validation_requires_review(
    database_connection,
):
    with pytest.raises(psycopg.errors.CheckViolation):
        create_authority_rule(
            database_connection,
            can_review=False,
            can_validate=True,
        )
