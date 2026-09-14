import pytest
from helpers import (
    create_authority_rule,
    create_clinical_domain,
    create_profession,
    nonexistent_id,
)
from psycopg.errors import ForeignKeyViolation, RaiseException


def test_authority_rule_requires_existing_profession(database_connection):
    clinical_domain_id = create_clinical_domain(database_connection)

    nonexistent_profession_id = nonexistent_id(
        database_connection,
        "auth.professions",
        "profession_id",
    )

    with pytest.raises(ForeignKeyViolation):
        create_authority_rule(
            database_connection,
            profession_id=nonexistent_profession_id,
            clinical_domain_id=clinical_domain_id,
        )


def test_authority_rule_requires_existing_clinical_domain(database_connection):
    profession_id = create_profession(database_connection)

    nonexistent_clinical_domain_id = nonexistent_id(
        database_connection,
        "clinical.clinical_domains",
        "clinical_domain_id",
    )

    with pytest.raises(ForeignKeyViolation):
        create_authority_rule(
            database_connection,
            profession_id=profession_id,
            clinical_domain_id=nonexistent_clinical_domain_id,
        )


def test_authority_rule_requires_existing_specialty(database_connection):
    profession_id = create_profession(database_connection)
    clinical_domain_id = create_clinical_domain(database_connection)

    nonexistent_specialty_id = nonexistent_id(
        database_connection,
        "auth.specialties",
        "specialty_id",
    )

    with pytest.raises(
        RaiseException,
        match=r"Specialty .* does not exist",
    ):
        create_authority_rule(
            database_connection,
            profession_id=profession_id,
            specialty_id=nonexistent_specialty_id,
            clinical_domain_id=clinical_domain_id,
        )
