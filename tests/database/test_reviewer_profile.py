import pytest
from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation

from tests.database.helpers import (
    create_clinical_domain,
    create_profession,
    create_specialty,
    create_user,
    nonexistent_id,
)


def test_reviewer_profile_requires_existing_user(database_connection):
    profession_id = create_profession(database_connection)
    nonexistent_user_id = nonexistent_id(
        database_connection,
        "auth.users",
        "user_id",
    )

    with pytest.raises(ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO auth.reviewer_profiles (
                user_id,
                profession_id
            )
            VALUES (%s, %s)
            """,
            (nonexistent_user_id, profession_id),
        )


def test_reviewer_profile_requires_existing_profession(database_connection):
    user_id = create_user(database_connection)
    nonexistent_profession_id = nonexistent_id(
        database_connection,
        "auth.professions",
        "profession_id",
    )

    with pytest.raises(ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO auth.reviewer_profiles (
                user_id,
                profession_id
            )
            VALUES (%s, %s)
            """,
            (user_id, nonexistent_profession_id),
        )


def test_reviewer_profile_user_is_unique(database_connection):
    user_id = create_user(database_connection)
    profession_id = create_profession(database_connection)

    database_connection.execute(
        """
        INSERT INTO auth.reviewer_profiles (
            user_id,
            profession_id
        )
        VALUES (%s, %s)
        """,
        (user_id, profession_id),
    )

    with pytest.raises(UniqueViolation):
        database_connection.execute(
            """
            INSERT INTO auth.reviewer_profiles (
                user_id,
                profession_id
            )
            VALUES (%s, %s)
            """,
            (user_id, profession_id),
        )


def test_reviewer_profile_verification_status_must_be_valid(database_connection):
    user_id = create_user(database_connection)
    profession_id = create_profession(database_connection)

    with pytest.raises(CheckViolation):
        database_connection.execute(
            """
            INSERT INTO auth.reviewer_profiles (
                user_id,
                profession_id,
                verification_status
            )
            VALUES (%s, %s, %s)
            """,
            (user_id, profession_id, "INVALID"),
        )


def test_verified_reviewer_profile_requires_verified_at(database_connection):
    user_id = create_user(database_connection)
    profession_id = create_profession(database_connection)
    verified_by = create_user(database_connection)

    with pytest.raises(CheckViolation):
        database_connection.execute(
            """
            INSERT INTO auth.reviewer_profiles (
                user_id,
                profession_id,
                verification_status,
                verified_by
            )
            VALUES (%s, %s, 'VERIFIED', %s)
            """,
            (user_id, profession_id, verified_by),
        )


def test_verified_reviewer_profile_requires_verified_by(database_connection):
    user_id = create_user(database_connection)
    profession_id = create_profession(database_connection)

    with pytest.raises(CheckViolation):
        database_connection.execute(
            """
            INSERT INTO auth.reviewer_profiles (
                user_id,
                profession_id,
                verification_status,
                verified_at
            )
            VALUES (%s, %s, 'VERIFIED', NOW())
            """,
            (user_id, profession_id),
        )


def test_reviewer_specialty_requires_existing_profile(database_connection):
    specialty_profession_id = create_profession(database_connection)
    specialty_id = create_specialty(
        database_connection,
        specialty_profession_id,
    )

    nonexistent_profile_id = nonexistent_id(
        database_connection,
        "auth.reviewer_profiles",
        "reviewer_profile_id",
    )

    with pytest.raises(ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO auth.reviewer_specialties (
                reviewer_profile_id,
                specialty_id
            )
            VALUES (%s, %s)
            """,
            (nonexistent_profile_id, specialty_id),
        )


def test_reviewer_specialty_requires_existing_specialty(database_connection):
    user_id = create_user(database_connection)
    profession_id = create_profession(database_connection)

    database_connection.execute(
        """
        INSERT INTO auth.reviewer_profiles (
            user_id,
            profession_id
        )
        VALUES (%s, %s)
        RETURNING reviewer_profile_id
        """,
        (user_id, profession_id),
    )

    profile = database_connection.execute(
        """
        SELECT reviewer_profile_id
        FROM auth.reviewer_profiles
        WHERE user_id = %s
        """,
        (user_id,),
    ).fetchone()

    nonexistent_specialty_id = nonexistent_id(
        database_connection,
        "auth.specialties",
        "specialty_id",
    )

    with pytest.raises(ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO auth.reviewer_specialties (
                reviewer_profile_id,
                specialty_id
            )
            VALUES (%s, %s)
            """,
            (profile[0], nonexistent_specialty_id),
        )


def test_verified_reviewer_specialty_requires_verified_at(database_connection):
    user_id = create_user(database_connection)
    profession_id = create_profession(database_connection)
    specialty_id = create_specialty(
        database_connection,
        profession_id,
    )

    profile_id = database_connection.execute(
        """
        INSERT INTO auth.reviewer_profiles (
            user_id,
            profession_id
        )
        VALUES (%s, %s)
        RETURNING reviewer_profile_id
        """,
        (user_id, profession_id),
    ).fetchone()[0]

    with pytest.raises(CheckViolation):
        database_connection.execute(
            """
            INSERT INTO auth.reviewer_specialties (
                reviewer_profile_id,
                specialty_id,
                verification_status
            )
            VALUES (%s, %s, 'VERIFIED')
            """,
            (profile_id, specialty_id),
        )


def test_reviewer_experience_requires_existing_profile(database_connection):
    clinical_domain_id = create_clinical_domain(database_connection)
    nonexistent_profile_id = nonexistent_id(
        database_connection,
        "auth.reviewer_profiles",
        "reviewer_profile_id",
    )

    with pytest.raises(ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO auth.reviewer_experience (
                reviewer_profile_id,
                clinical_domain_id,
                experience_type
            )
            VALUES (%s, %s, %s)
            """,
            (
                nonexistent_profile_id,
                clinical_domain_id,
                "EMERGENCY_MEDICINE",
            ),
        )


def test_reviewer_specialty_must_match_reviewer_profession(
    database_connection,
):
    reviewer_user_id = create_user(database_connection)

    reviewer_profession_id = create_profession(database_connection)

    other_profession_id = create_profession(database_connection)

    specialty_id = create_specialty(
        database_connection,
        other_profession_id,
    )

    profile = database_connection.execute(
        """
        INSERT INTO auth.reviewer_profiles (
            user_id,
            profession_id
        )
        VALUES (%s, %s)
        RETURNING reviewer_profile_id
        """,
        (
            reviewer_user_id,
            reviewer_profession_id,
        ),
    ).fetchone()

    with pytest.raises(Exception, match="does not belong to reviewer profession"):
        database_connection.execute(
            """
            INSERT INTO auth.reviewer_specialties (
                reviewer_profile_id,
                specialty_id
            )
            VALUES (%s, %s)
            """,
            (
                profile[0],
                specialty_id,
            ),
        )
