import psycopg
import pytest
from psycopg.errors import (
    CheckViolation,
    ForeignKeyViolation,
    NotNullViolation,
    RaiseException,
    UniqueViolation,
)
from psycopg.types.json import Json

from tests.database.helpers import (
    create_authority_rule,
    create_clinical_domain,
    create_model_item,
    create_model_item_version,
    create_profession,
    create_specialty,
    create_user,
    create_verified_reviewer,
    nonexistent_id,
)


def test_review_assignment_requires_existing_model_item(
    database_connection,
):
    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    assigned_by = create_user(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    nonexistent_model_item_id = nonexistent_id(
        database_connection,
        "research.model_items",
        "model_item_id",
    )

    with pytest.raises(ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO research.review_assignments (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                nonexistent_model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by,
            ),
        )


def test_review_assignment_requires_reviewer_profile(
    database_connection,
):
    model_item_id, _ = create_model_item(database_connection)

    assigned_by = create_user(database_connection)
    profession_id = create_profession(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    nonexistent_user_id = nonexistent_id(
        database_connection,
        "auth.users",
        "user_id",
    )

    with pytest.raises(
        Exception,
        match="does not have a reviewer profile",
    ):
        database_connection.execute(
            """
            INSERT INTO research.review_assignments (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                model_item_id,
                nonexistent_user_id,
                authority_rule_id,
                assigned_by,
            ),
        )


def test_review_assignment_requires_existing_assigned_by(database_connection):
    model_item_id, _ = create_model_item(database_connection)

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)
    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    nonexistent_assigned_by = nonexistent_id(
        database_connection,
        "auth.users",
        "user_id",
    )

    with pytest.raises(ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO research.review_assignments (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                nonexistent_assigned_by,
            ),
        )


def test_review_assignment_status_must_be_valid(database_connection):
    model_item_id, _ = create_model_item(database_connection)

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)
    assigned_by = create_user(database_connection)
    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    with pytest.raises(CheckViolation):
        database_connection.execute(
            """
            INSERT INTO research.review_assignments (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by,
                status
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by,
                "INVALID",
            ),
        )


def test_review_requires_existing_assignment(database_connection):
    user_id = create_user(database_connection)
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    nonexistent_assignment_id = nonexistent_id(
        database_connection,
        "research.review_assignments",
        "review_assignment_id",
    )

    with pytest.raises(RaiseException, match="Review assignment"):
        database_connection.execute(
            """
            INSERT INTO research.reviews (
                review_assignment_id,
                model_item_version_id,
                reviewer_user_id
            )
            VALUES (%s, %s, %s)
            """,
            (
                nonexistent_assignment_id,
                version_id,
                user_id,
            ),
        )


def test_review_requires_existing_model_item_version(
    database_connection,
):
    model_item_id, _ = create_model_item(database_connection)

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    assigned_by = create_user(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assignment_id = database_connection.execute(
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

    nonexistent_version_id = nonexistent_id(
        database_connection,
        "research.model_item_versions",
        "model_item_version_id",
    )

    with pytest.raises(
        psycopg.errors.RaiseException,
        match="Model item version",
    ):
        database_connection.execute(
            """
            INSERT INTO research.reviews (
                review_assignment_id,
                model_item_version_id,
                reviewer_user_id
            )
            VALUES (%s, %s, %s)
            """,
            (
                assignment_id,
                nonexistent_version_id,
                reviewer_user_id,
            ),
        )


def test_review_assignment_requires_verified_reviewer(database_connection):
    model_item_id, _ = create_model_item(database_connection)

    reviewer_user_id = create_user(database_connection)
    profession_id = create_profession(database_connection)

    database_connection.execute(
        """
        INSERT INTO auth.reviewer_profiles (
            user_id,
            profession_id,
            verification_status
        )
        VALUES (%s, %s, 'PENDING')
        """,
        (reviewer_user_id, profession_id),
    )

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    with pytest.raises(
        psycopg.errors.RaiseException,
        match="not verified",
    ):
        database_connection.execute(
            """
            INSERT INTO research.review_assignments (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by,
            ),
        )


def test_review_assignment_requires_active_authority_rule(
    database_connection,
):
    model_item_id, _ = create_model_item(database_connection)

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    database_connection.execute(
        """
        UPDATE clinical.authority_rules
        SET is_active = FALSE
        WHERE authority_rule_id = %s
        """,
        (authority_rule_id,),
    )

    assigned_by = create_user(database_connection)

    with pytest.raises(
        psycopg.errors.RaiseException,
        match="does not exist or is inactive",
    ):
        database_connection.execute(
            """
            INSERT INTO research.review_assignments (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by,
            ),
        )


def test_review_assignment_requires_matching_profession(
    database_connection,
):
    model_item_id, _ = create_model_item(database_connection)

    _, reviewer_user_id, reviewer_profession_id = create_verified_reviewer(
        database_connection
    )

    authority_profession_id = create_profession(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=authority_profession_id,
    )

    assigned_by = create_user(database_connection)

    assert reviewer_profession_id != authority_profession_id

    with pytest.raises(
        psycopg.errors.RaiseException,
        match="does not match authority rule profession",
    ):
        database_connection.execute(
            """
            INSERT INTO research.review_assignments (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by,
            ),
        )


def test_review_assignment_requires_verified_specialty(
    database_connection,
):
    model_item_id, _ = create_model_item(database_connection)

    profile_id, reviewer_user_id, profession_id = create_verified_reviewer(
        database_connection
    )

    specialty_id = create_specialty(
        database_connection,
        profession_id,
    )

    database_connection.execute(
        """
        INSERT INTO auth.reviewer_specialties (
            reviewer_profile_id,
            specialty_id,
            verification_status
        )
        VALUES (%s, %s, 'PENDING')
        """,
        (
            profile_id,
            specialty_id,
        ),
    )

    clinical_domain_id = create_clinical_domain(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
        specialty_id=specialty_id,
        clinical_domain_id=clinical_domain_id,
    )

    assigned_by = create_user(database_connection)

    with pytest.raises(
        psycopg.errors.RaiseException,
        match="does not have the verified specialty",
    ):
        database_connection.execute(
            """
            INSERT INTO research.review_assignments (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                model_item_id,
                reviewer_user_id,
                authority_rule_id,
                assigned_by,
            ),
        )


def test_review_reviewer_must_match_assignment(database_connection):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, assigned_reviewer_id, profession_id = create_verified_reviewer(
        database_connection
    )

    _, different_reviewer_id, _ = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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
            assigned_reviewer_id,
            authority_rule_id,
            assigned_by,
        ),
    ).fetchone()[0]

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO research.reviews (
                review_assignment_id,
                model_item_version_id,
                reviewer_user_id
            )
            VALUES (%s, %s, %s)
            """,
            (
                assignment_id,
                version_id,
                different_reviewer_id,
            ),
        )


def test_review_assignment_allows_only_one_review(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    database_connection.execute(
        """
        INSERT INTO research.reviews (
            review_assignment_id,
            model_item_version_id,
            reviewer_user_id
        )
        VALUES (%s, %s, %s)
        """,
        (
            assignment_id,
            version_id,
            reviewer_user_id,
        ),
    )

    with pytest.raises(psycopg.errors.UniqueViolation):
        database_connection.execute(
            """
            INSERT INTO research.reviews (
                review_assignment_id,
                model_item_version_id,
                reviewer_user_id
            )
            VALUES (%s, %s, %s)
            """,
            (
                assignment_id,
                version_id,
                reviewer_user_id,
            ),
        )


def test_review_status_must_be_valid(database_connection):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    with pytest.raises(psycopg.errors.CheckViolation):
        database_connection.execute(
            """
            INSERT INTO research.reviews (
                review_assignment_id,
                model_item_version_id,
                reviewer_user_id,
                status
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                assignment_id,
                version_id,
                reviewer_user_id,
                "INVALID_STATUS",
            ),
        )


def test_review_submitted_status_requires_submitted_at(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    with pytest.raises(psycopg.errors.CheckViolation):
        database_connection.execute(
            """
            INSERT INTO research.reviews (
                review_assignment_id,
                model_item_version_id,
                reviewer_user_id,
                status
            )
            VALUES (%s, %s, %s, 'VALIDATED')
            """,
            (
                assignment_id,
                version_id,
                reviewer_user_id,
            ),
        )


def test_review_allows_valid_review(database_connection):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    review_id = database_connection.execute(
        """
        INSERT INTO research.reviews (
            review_assignment_id,
            model_item_version_id,
            reviewer_user_id,
            status
        )
        VALUES (%s, %s, %s, 'PENDING')
        RETURNING review_id
        """,
        (
            assignment_id,
            version_id,
            reviewer_user_id,
        ),
    ).fetchone()[0]

    assert review_id is not None


def test_review_comment_requires_existing_review(database_connection):
    nonexistent_review_id = nonexistent_id(
        database_connection,
        "research.reviews",
        "review_id",
    )

    author_user_id = create_user(database_connection)

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO research.review_comments (
                review_id,
                author_user_id,
                comment_text
            )
            VALUES (%s, %s, %s)
            """,
            (
                nonexistent_review_id,
                author_user_id,
                "Test clinical comment",
            ),
        )


def test_review_comment_requires_existing_author(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    review_id = database_connection.execute(
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
            assignment_id,
            version_id,
            reviewer_user_id,
        ),
    ).fetchone()[0]

    nonexistent_author_id = nonexistent_id(
        database_connection,
        "auth.users",
        "user_id",
    )

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO research.review_comments (
                review_id,
                author_user_id,
                comment_text
            )
            VALUES (%s, %s, %s)
            """,
            (
                review_id,
                nonexistent_author_id,
                "Test clinical comment",
            ),
        )


def test_review_comment_cannot_be_blank(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    review_id = database_connection.execute(
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
            assignment_id,
            version_id,
            reviewer_user_id,
        ),
    ).fetchone()[0]

    with pytest.raises(psycopg.errors.CheckViolation):
        database_connection.execute(
            """
            INSERT INTO research.review_comments (
                review_id,
                author_user_id,
                comment_text
            )
            VALUES (%s, %s, %s)
            """,
            (
                review_id,
                reviewer_user_id,
                "   ",
            ),
        )


def test_review_comment_allows_valid_comment(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    review_id = database_connection.execute(
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
            assignment_id,
            version_id,
            reviewer_user_id,
        ),
    ).fetchone()[0]

    comment_id = database_connection.execute(
        """
        INSERT INTO research.review_comments (
            review_id,
            author_user_id,
            comment_text
        )
        VALUES (%s, %s, %s)
        RETURNING comment_id
        """,
        (
            review_id,
            reviewer_user_id,
            "The clinical rule requires clarification.",
        ),
    ).fetchone()[0]

    assert comment_id is not None


def test_clinical_observation_requires_existing_review(
    database_connection,
):
    author_user_id = create_user(database_connection)

    nonexistent_review_id = nonexistent_id(
        database_connection,
        "research.reviews",
        "review_id",
    )

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO research.clinical_observations (
                review_id,
                author_user_id,
                category,
                description
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                nonexistent_review_id,
                author_user_id,
                "CLINICAL_RULE",
                "Test clinical observation.",
            ),
        )


def test_clinical_observation_requires_existing_author(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    review_id = database_connection.execute(
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
            assignment_id,
            version_id,
            reviewer_user_id,
        ),
    ).fetchone()[0]

    nonexistent_author_id = nonexistent_id(
        database_connection,
        "auth.users",
        "user_id",
    )

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO research.clinical_observations (
                review_id,
                author_user_id,
                category,
                description
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                review_id,
                nonexistent_author_id,
                "CLINICAL_RULE",
                "Test clinical observation.",
            ),
        )


def test_clinical_observation_category_must_be_valid(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    review_id = database_connection.execute(
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
            assignment_id,
            version_id,
            reviewer_user_id,
        ),
    ).fetchone()[0]

    with pytest.raises(psycopg.errors.CheckViolation):
        database_connection.execute(
            """
            INSERT INTO research.clinical_observations (
                review_id,
                author_user_id,
                category,
                description
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                review_id,
                reviewer_user_id,
                "INVALID_CATEGORY",
                "Test clinical observation.",
            ),
        )


def test_clinical_observation_status_must_be_valid(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    review_id = database_connection.execute(
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
            assignment_id,
            version_id,
            reviewer_user_id,
        ),
    ).fetchone()[0]

    with pytest.raises(psycopg.errors.CheckViolation):
        database_connection.execute(
            """
            INSERT INTO research.clinical_observations (
                review_id,
                author_user_id,
                category,
                description,
                status
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                review_id,
                reviewer_user_id,
                "CLINICAL_RULE",
                "Test clinical observation.",
                "INVALID_STATUS",
            ),
        )


def test_clinical_observation_description_cannot_be_blank(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    review_id = database_connection.execute(
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
            assignment_id,
            version_id,
            reviewer_user_id,
        ),
    ).fetchone()[0]

    with pytest.raises(psycopg.errors.CheckViolation):
        database_connection.execute(
            """
            INSERT INTO research.clinical_observations (
                review_id,
                author_user_id,
                category,
                description
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                review_id,
                reviewer_user_id,
                "CLINICAL_RULE",
                "   ",
            ),
        )


def test_clinical_observation_allows_valid_observation(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(database_connection)

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    _, reviewer_user_id, profession_id = create_verified_reviewer(database_connection)

    authority_rule_id = create_authority_rule(
        database_connection,
        profession_id=profession_id,
    )

    assigned_by = create_user(database_connection)

    assignment_id = database_connection.execute(
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

    review_id = database_connection.execute(
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
            assignment_id,
            version_id,
            reviewer_user_id,
        ),
    ).fetchone()[0]

    observation_id = database_connection.execute(
        """
        INSERT INTO research.clinical_observations (
            review_id,
            author_user_id,
            category,
            description,
            evidence,
            proposed_action,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING observation_id
        """,
        (
            review_id,
            reviewer_user_id,
            "PARAMETER",
            "The waiting-time parameter requires clinical review.",
            "Clinical evidence should be reviewed.",
            "Review and update the parameterization.",
            "OPEN",
        ),
    ).fetchone()[0]

    assert observation_id is not None


def test_clinical_rule_requires_existing_model_item_version(
    database_connection,
):
    nonexistent_version_id = nonexistent_id(
        database_connection,
        "research.model_item_versions",
        "model_item_version_id",
    )

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.clinical_rules (
                model_item_version_id,
                rule_expression
            )
            VALUES (%s, %s)
            """,
            (
                nonexistent_version_id,
                Json({"condition": "test"}),
            ),
        )


def test_clinical_rule_model_item_version_is_unique(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(
        database_connection,
        item_type="CLINICAL_RULE",
    )

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.clinical_rules (
            model_item_version_id,
            rule_expression
        )
        VALUES (%s, %s)
        """,
        (
            version_id,
            Json({"condition": "first"}),
        ),
    )

    with pytest.raises(psycopg.errors.UniqueViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.clinical_rules (
                model_item_version_id,
                rule_expression
            )
            VALUES (%s, %s)
            """,
            (
                version_id,
                Json({"condition": "second"}),
            ),
        )


def test_clinical_rule_requires_rule_expression(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(
        database_connection,
        item_type="CLINICAL_RULE",
    )

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    with pytest.raises(psycopg.errors.NotNullViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.clinical_rules (
                model_item_version_id
            )
            VALUES (%s)
            """,
            (version_id,),
        )


def test_clinical_rule_allows_valid_rule(
    database_connection,
):
    model_item_id, creator_user_id = create_model_item(
        database_connection,
        item_type="CLINICAL_RULE",
    )

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        creator_user_id,
        1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.clinical_rules (
            model_item_version_id,
            rule_expression,
            description
        )
        VALUES (%s, %s, %s)
        """,
        (
            version_id,
            Json(
                {
                    "condition": "patient_stable",
                    "action": "eligible_for_observation",
                }
            ),
            "Test clinical rule.",
        ),
    )

    row = database_connection.execute(
        """
        SELECT model_item_version_id, rule_expression, description
        FROM clinical.clinical_rules
        WHERE model_item_version_id = %s
        """,
        (version_id,),
    ).fetchone()

    assert row is not None
    assert row[0] == version_id
    assert row[1] == {
        "condition": "patient_stable",
        "action": "eligible_for_observation",
    }
    assert row[2] == "Test clinical rule."


def test_diagnosis_requires_existing_model_item_version(database_connection):

    nonexistent_version_id = nonexistent_id(
        database_connection,
        "research.model_item_versions",
        "model_item_version_id",
    )

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.diagnoses (
                model_item_version_id,
                diagnosis_code,
                name
            )
            VALUES (%s, %s, %s)
            """,
            (
                nonexistent_version_id,
                "TEST-001",
                "Test diagnosis",
            ),
        )


def test_diagnosis_model_item_version_requires_diagnosis_type(database_connection):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="VARIABLE",
    )

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        version_number=1,
    )

    with pytest.raises(
        psycopg.errors.RaiseException,
        match="requires type DIAGNOSIS",
    ):
        database_connection.execute(
            """
            INSERT INTO clinical.diagnoses (
                model_item_version_id,
                diagnosis_code,
                name
            )
            VALUES (%s, %s, %s)
            """,
            (
                version_id,
                "TEST-001",
                "Test diagnosis",
            ),
        )


def test_diagnosis_model_item_version_is_unique(database_connection):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        version_number=1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (
            version_id,
            "TEST-001",
            "Test diagnosis",
        ),
    )

    with pytest.raises(psycopg.errors.UniqueViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.diagnoses (
                model_item_version_id,
                diagnosis_code,
                name
            )
            VALUES (%s, %s, %s)
            """,
            (
                version_id,
                "TEST-002",
                "Another diagnosis",
            ),
        )


def test_diagnosis_requires_diagnosis_code(database_connection):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        version_number=1,
    )

    with pytest.raises(psycopg.errors.NotNullViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.diagnoses (
                model_item_version_id,
                diagnosis_code,
                name
            )
            VALUES (%s, NULL, %s)
            """,
            (
                version_id,
                "Test diagnosis",
            ),
        )


def test_diagnosis_requires_name(database_connection):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        version_number=1,
    )

    with pytest.raises(psycopg.errors.NotNullViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.diagnoses (
                model_item_version_id,
                diagnosis_code,
                name
            )
            VALUES (%s, %s, NULL)
            """,
            (
                version_id,
                "TEST-001",
            ),
        )


def test_diagnosis_allows_valid_diagnosis(database_connection):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        version_number=1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name,
            description
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            version_id,
            "TEST-001",
            "Test diagnosis",
            "Test diagnosis description",
        ),
    )

    row = database_connection.execute(
        """
        SELECT
            model_item_version_id,
            diagnosis_code,
            name,
            description
        FROM clinical.diagnoses
        WHERE model_item_version_id = %s
        """,
        (version_id,),
    ).fetchone()

    assert row == (
        version_id,
        "TEST-001",
        "Test diagnosis",
        "Test diagnosis description",
    )


def test_observation_protocol_requires_existing_model_item_version(
    database_connection,
):
    nonexistent_version_id = nonexistent_id(
        database_connection,
        "research.model_item_versions",
        "model_item_version_id",
    )

    diagnosis_model_item_id, diagnosis_user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    diagnosis_version_id = create_model_item_version(
        database_connection,
        diagnosis_model_item_id,
        diagnosis_user_id,
        version_number=1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (
            diagnosis_version_id,
            "TEST-001",
            "Test diagnosis",
        ),
    )

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.observation_protocols (
                model_item_version_id,
                diagnosis_version_id,
                protocol_definition
            )
            VALUES (%s, %s, %s)
            """,
            (
                nonexistent_version_id,
                diagnosis_version_id,
                Json({"steps": []}),
            ),
        )


def test_observation_protocol_model_item_version_requires_observation_protocol_type(
    database_connection,
):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="VARIABLE",
    )

    version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        version_number=1,
    )

    diagnosis_model_item_id, diagnosis_user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    diagnosis_version_id = create_model_item_version(
        database_connection,
        diagnosis_model_item_id,
        diagnosis_user_id,
        version_number=1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (
            diagnosis_version_id,
            "TEST-001",
            "Test diagnosis",
        ),
    )

    with pytest.raises(
        psycopg.errors.RaiseException,
        match="requires type OBSERVATION_PROTOCOL",
    ):
        database_connection.execute(
            """
            INSERT INTO clinical.observation_protocols (
                model_item_version_id,
                diagnosis_version_id,
                protocol_definition
            )
            VALUES (%s, %s, %s)
            """,
            (
                version_id,
                diagnosis_version_id,
                Json({"steps": []}),
            ),
        )


def test_observation_protocol_requires_existing_diagnosis(
    database_connection,
):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="OBSERVATION_PROTOCOL",
    )

    protocol_version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        version_number=1,
    )

    nonexistent_diagnosis_version_id = nonexistent_id(
        database_connection,
        "research.model_item_versions",
        "model_item_version_id",
    )

    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.observation_protocols (
                model_item_version_id,
                diagnosis_version_id,
                protocol_definition
            )
            VALUES (%s, %s, %s)
            """,
            (
                protocol_version_id,
                nonexistent_diagnosis_version_id,
                Json({"steps": []}),
            ),
        )


def test_observation_protocol_model_item_version_is_unique(
    database_connection,
):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="OBSERVATION_PROTOCOL",
    )

    protocol_version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        version_number=1,
    )

    diagnosis_model_item_id, diagnosis_user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    diagnosis_version_id = create_model_item_version(
        database_connection,
        diagnosis_model_item_id,
        diagnosis_user_id,
        version_number=1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (
            diagnosis_version_id,
            "TEST-001",
            "Test diagnosis",
        ),
    )

    database_connection.execute(
        """
        INSERT INTO clinical.observation_protocols (
            model_item_version_id,
            diagnosis_version_id,
            protocol_definition
        )
        VALUES (%s, %s, %s)
        """,
        (
            protocol_version_id,
            diagnosis_version_id,
            Json({"steps": ["assessment"]}),
        ),
    )

    with pytest.raises(psycopg.errors.UniqueViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.observation_protocols (
                model_item_version_id,
                diagnosis_version_id,
                protocol_definition
            )
            VALUES (%s, %s, %s)
            """,
            (
                protocol_version_id,
                diagnosis_version_id,
                Json({"steps": ["treatment"]}),
            ),
        )


def test_observation_protocol_requires_protocol_definition(
    database_connection,
):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="OBSERVATION_PROTOCOL",
    )

    protocol_version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        version_number=1,
    )

    diagnosis_model_item_id, diagnosis_user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    diagnosis_version_id = create_model_item_version(
        database_connection,
        diagnosis_model_item_id,
        diagnosis_user_id,
        version_number=1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (
            diagnosis_version_id,
            "TEST-001",
            "Test diagnosis",
        ),
    )

    with pytest.raises(psycopg.errors.NotNullViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.observation_protocols (
                model_item_version_id,
                diagnosis_version_id,
                protocol_definition
            )
            VALUES (%s, %s, NULL)
            """,
            (
                protocol_version_id,
                diagnosis_version_id,
            ),
        )


def test_observation_protocol_allows_valid_protocol(
    database_connection,
):
    protocol_model_item_id, protocol_user_id = create_model_item(
        database_connection,
        item_type="OBSERVATION_PROTOCOL",
    )

    protocol_version_id = create_model_item_version(
        database_connection,
        protocol_model_item_id,
        protocol_user_id,
        version_number=1,
    )

    diagnosis_model_item_id, diagnosis_user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    diagnosis_version_id = create_model_item_version(
        database_connection,
        diagnosis_model_item_id,
        diagnosis_user_id,
        version_number=1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (
            diagnosis_version_id,
            "TEST-001",
            "Test diagnosis",
        ),
    )

    protocol_definition = {
        "steps": [
            {
                "sequence": 1,
                "action": "initial_assessment",
            },
            {
                "sequence": 2,
                "action": "reassessment",
            },
        ],
        "eligibility": {
            "stable": True,
        },
    }

    database_connection.execute(
        """
        INSERT INTO clinical.observation_protocols (
            model_item_version_id,
            diagnosis_version_id,
            protocol_definition
        )
        VALUES (%s, %s, %s)
        """,
        (
            protocol_version_id,
            diagnosis_version_id,
            Json(protocol_definition),
        ),
    )

    row = database_connection.execute(
        """
        SELECT
            model_item_version_id,
            diagnosis_version_id,
            protocol_definition
        FROM clinical.observation_protocols
        WHERE model_item_version_id = %s
        """,
        (protocol_version_id,),
    ).fetchone()

    assert row[0] == protocol_version_id
    assert row[1] == diagnosis_version_id
    assert row[2] == protocol_definition


def test_disposition_rule_requires_existing_model_item_version(database_connection):
    diagnosis_model_item_id, diagnosis_user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )
    diagnosis_version_id = create_model_item_version(
        database_connection,
        diagnosis_model_item_id,
        diagnosis_user_id,
        1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (diagnosis_version_id, "TEST-DX", "Test diagnosis"),
    )

    nonexistent_version_id = nonexistent_id(
        database_connection,
        "research.model_item_versions",
        "model_item_version_id",
    )

    with pytest.raises(ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.disposition_rules (
                model_item_version_id,
                diagnosis_version_id,
                destination,
                rule_definition
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                nonexistent_version_id,
                diagnosis_version_id,
                "DISCHARGE",
                Json({"condition": "stable"}),
            ),
        )


def test_disposition_rule_model_item_version_requires_disposition_rule_type(
    database_connection,
):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="VARIABLE",
    )

    model_item_version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        1,
    )

    diagnosis_model_item_id, diagnosis_user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    diagnosis_version_id = create_model_item_version(
        database_connection,
        diagnosis_model_item_id,
        diagnosis_user_id,
        1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (diagnosis_version_id, "TEST-DX", "Test diagnosis"),
    )

    with pytest.raises(
        RaiseException,
        match="requires type DISPOSITION_RULE",
    ):
        database_connection.execute(
            """
            INSERT INTO clinical.disposition_rules (
                model_item_version_id,
                diagnosis_version_id,
                destination,
                rule_definition
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                model_item_version_id,
                diagnosis_version_id,
                "DISCHARGE",
                Json({"condition": "stable"}),
            ),
        )


def test_disposition_rule_requires_existing_diagnosis(database_connection):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="DISPOSITION_RULE",
    )

    model_item_version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        1,
    )

    nonexistent_diagnosis_version_id = nonexistent_id(
        database_connection,
        "clinical.diagnoses",
        "model_item_version_id",
    )

    with pytest.raises(ForeignKeyViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.disposition_rules (
                model_item_version_id,
                diagnosis_version_id,
                destination,
                rule_definition
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                model_item_version_id,
                nonexistent_diagnosis_version_id,
                "DISCHARGE",
                Json({"condition": "stable"}),
            ),
        )


def test_disposition_rule_model_item_version_is_unique(database_connection):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="DISPOSITION_RULE",
    )

    model_item_version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        1,
    )

    diagnosis_model_item_id, diagnosis_user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    diagnosis_version_id = create_model_item_version(
        database_connection,
        diagnosis_model_item_id,
        diagnosis_user_id,
        1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (diagnosis_version_id, "TEST-DX", "Test diagnosis"),
    )

    database_connection.execute(
        """
        INSERT INTO clinical.disposition_rules (
            model_item_version_id,
            diagnosis_version_id,
            destination,
            rule_definition
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            model_item_version_id,
            diagnosis_version_id,
            "DISCHARGE",
            Json({"condition": "stable"}),
        ),
    )

    with pytest.raises(UniqueViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.disposition_rules (
                model_item_version_id,
                diagnosis_version_id,
                destination,
                rule_definition
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                model_item_version_id,
                diagnosis_version_id,
                "OBSERVATION",
                Json({"condition": "requires_observation"}),
            ),
        )


def test_disposition_rule_destination_must_be_valid(database_connection):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="DISPOSITION_RULE",
    )

    model_item_version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        1,
    )

    diagnosis_model_item_id, diagnosis_user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    diagnosis_version_id = create_model_item_version(
        database_connection,
        diagnosis_model_item_id,
        diagnosis_user_id,
        1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (diagnosis_version_id, "TEST-DX", "Test diagnosis"),
    )

    with pytest.raises(CheckViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.disposition_rules (
                model_item_version_id,
                diagnosis_version_id,
                destination,
                rule_definition
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                model_item_version_id,
                diagnosis_version_id,
                "INVALID_DESTINATION",
                Json({"condition": "stable"}),
            ),
        )


def test_disposition_rule_requires_rule_definition(database_connection):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="DISPOSITION_RULE",
    )

    model_item_version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        1,
    )

    diagnosis_model_item_id, diagnosis_user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    diagnosis_version_id = create_model_item_version(
        database_connection,
        diagnosis_model_item_id,
        diagnosis_user_id,
        1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (diagnosis_version_id, "TEST-DX", "Test diagnosis"),
    )

    with pytest.raises(NotNullViolation):
        database_connection.execute(
            """
            INSERT INTO clinical.disposition_rules (
                model_item_version_id,
                diagnosis_version_id,
                destination,
                rule_definition
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                model_item_version_id,
                diagnosis_version_id,
                "DISCHARGE",
                None,
            ),
        )


def test_disposition_rule_allows_valid_disposition_rule(database_connection):
    model_item_id, user_id = create_model_item(
        database_connection,
        item_type="DISPOSITION_RULE",
    )

    model_item_version_id = create_model_item_version(
        database_connection,
        model_item_id,
        user_id,
        1,
    )

    diagnosis_model_item_id, diagnosis_user_id = create_model_item(
        database_connection,
        item_type="DIAGNOSIS",
    )

    diagnosis_version_id = create_model_item_version(
        database_connection,
        diagnosis_model_item_id,
        diagnosis_user_id,
        1,
    )

    database_connection.execute(
        """
        INSERT INTO clinical.diagnoses (
            model_item_version_id,
            diagnosis_code,
            name
        )
        VALUES (%s, %s, %s)
        """,
        (diagnosis_version_id, "TEST-DX", "Test diagnosis"),
    )

    database_connection.execute(
        """
        INSERT INTO clinical.disposition_rules (
            model_item_version_id,
            diagnosis_version_id,
            destination,
            rule_definition
        )
        VALUES (%s, %s, %s, %s)
        """,
        (
            model_item_version_id,
            diagnosis_version_id,
            "DISCHARGE",
            Json(
                {
                    "condition": "stable",
                    "criteria": ["vital_signs_stable"],
                }
            ),
        ),
    )

    row = database_connection.execute(
        """
        SELECT
            model_item_version_id,
            diagnosis_version_id,
            destination,
            rule_definition
        FROM clinical.disposition_rules
        WHERE model_item_version_id = %s
        """,
        (model_item_version_id,),
    ).fetchone()

    assert row == (
        model_item_version_id,
        diagnosis_version_id,
        "DISCHARGE",
        {
            "condition": "stable",
            "criteria": ["vital_signs_stable"],
        },
    )
