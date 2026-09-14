import uuid

from psycopg.types.json import Json


def unique_email():
    return f"test-{uuid.uuid4().hex}@example.com"


def unique_code():
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
                "Test Project",
            ),
        )
        return cursor.fetchone()[0]


def create_model_item(
    connection,
    item_type="VARIABLE",
):
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
                item_type,
                "Test Variable",
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
            VALUES (%s, %s, %s, %s)
            RETURNING model_item_version_id
            """,
            (
                model_item_id,
                version_number,
                Json({"description": f"Version {version_number}"}),
                user_id,
            ),
        )
        return cursor.fetchone()[0]


def create_profession(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO auth.professions (
                code,
                name,
                professional_group
            )
            VALUES (%s, %s, %s)
            RETURNING profession_id
            """,
            (
                unique_code(),
                "Test Profession",
                "Test Professional Group",
            ),
        )
        return cursor.fetchone()[0]


def create_specialty(connection, profession_id):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO auth.specialties (
                profession_id,
                code,
                name
            )
            VALUES (%s, %s, %s)
            RETURNING specialty_id
            """,
            (
                profession_id,
                unique_code(),
                "Test Specialty",
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
            VALUES (%s, %s)
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
    profession_id=None,
    specialty_id=None,
    clinical_domain_id=None,
    authority_level="L1",
    can_review=True,
    can_validate=False,
    review_scope="Test review scope",
    requires_interdisciplinary_validation=False,
    rule_version=1,
):
    if profession_id is None:
        profession_id = create_profession(connection)

    if clinical_domain_id is None:
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
                requires_interdisciplinary_validation,
                rule_version
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING authority_rule_id
            """,
            (
                profession_id,
                specialty_id,
                clinical_domain_id,
                authority_level,
                can_review,
                can_validate,
                review_scope,
                requires_interdisciplinary_validation,
                rule_version,
            ),
        )
        return cursor.fetchone()[0]


def nonexistent_id(connection, table, column):
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT COALESCE(MAX({column}), 0) + 1
            FROM {table}
            """
        )
        return cursor.fetchone()[0]


def create_review_assignment(
    connection,
    model_item_id=None,
    reviewer_user_id=None,
    assigned_by=None,
    authority_rule_id=None,
):
    if model_item_id is None:
        model_item_id = create_model_item(connection)

    if reviewer_user_id is None:
        reviewer_user_id = create_user(connection)

    if assigned_by is None:
        assigned_by = create_user(connection)

    if authority_rule_id is None:
        authority_rule_id = create_authority_rule(connection)

    return connection.execute(
        """
        INSERT INTO research.review_assignments (
            model_item_id,
            reviewer_user_id,
            authority_rule_id,
            assigned_by
        )
        VALUES (%s, %s, %s, %s)
        RETURNING review_assignment_id
        """,
        (
            model_item_id,
            reviewer_user_id,
            authority_rule_id,
            assigned_by,
        ),
    ).fetchone()[0]


def create_review(
    connection,
    review_assignment_id,
    model_item_version_id,
    reviewer_user_id,
):
    return connection.execute(
        """
        INSERT INTO research.reviews (
            review_assignment_id,
            model_item_version_id,
            reviewer_user_id
        )
        VALUES (%s, %s, %s)
        RETURNING review_id
        """,
        (
            review_assignment_id,
            model_item_version_id,
            reviewer_user_id,
        ),
    ).fetchone()[0]


def create_reviewer_profile(connection):
    user_id = create_user(connection)
    profession_id = create_profession(connection)

    reviewer_profile_id = connection.execute(
        """
        INSERT INTO auth.reviewer_profiles (
            user_id,
            profession_id
        )
        VALUES (%s, %s)
        RETURNING reviewer_profile_id
        """,
        (
            user_id,
            profession_id,
        ),
    ).fetchone()[0]

    return reviewer_profile_id, user_id


def create_verified_reviewer(connection):
    user_id = create_user(connection)
    profession_id = create_profession(connection)

    profile_id = connection.execute(
        """
        INSERT INTO auth.reviewer_profiles (
            user_id,
            profession_id,
            verification_status,
            verified_at,
            verified_by
        )
        VALUES (%s, %s, 'VERIFIED', NOW(), %s)
        RETURNING reviewer_profile_id
        """,
        (
            user_id,
            profession_id,
            user_id,
        ),
    ).fetchone()[0]

    return profile_id, user_id, profession_id
