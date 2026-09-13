-- ============================================================================
-- Sidhartha Research
-- Emergency Department Clinical Model & Simulation Platform
-- PostgreSQL Schema
-- Version: 1.0
--
-- Methodological principle:
--   El dominio clínico valida la representación del sistema y sus reglas
--   clínicas; la ingeniería valida la implementación y el comportamiento
--   computacional del modelo.
--
-- This database is intentionally scoped to the Emergency Department project.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- 2. SCHEMAS
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS research;
CREATE SCHEMA IF NOT EXISTS clinical;
CREATE SCHEMA IF NOT EXISTS simulation;
CREATE SCHEMA IF NOT EXISTS audit;

-- ============================================================================
-- 3. CLINICAL DOMAINS
-- Created first because auth.reviewer_experience depends on it.
-- ============================================================================

CREATE TABLE clinical.clinical_domains (
    clinical_domain_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parent_domain_id BIGINT NULL,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_clinical_domains_parent
    FOREIGN KEY (parent_domain_id)
    REFERENCES clinical.clinical_domains (clinical_domain_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_clinical_domains_not_self_parent
    CHECK (parent_domain_id IS NULL OR parent_domain_id <> clinical_domain_id),

    CONSTRAINT ck_clinical_domains_code_not_blank
    CHECK (BTRIM(code) <> ''),

    CONSTRAINT ck_clinical_domains_name_not_blank
    CHECK (BTRIM(name) <> '')
);

-- ============================================================================
-- 4. AUTH
-- ============================================================================

CREATE TABLE auth.users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_users_email_not_blank
    CHECK (BTRIM(email) <> ''),

    CONSTRAINT ck_users_password_hash_not_blank
    CHECK (BTRIM(password_hash) <> ''),

    CONSTRAINT ck_users_first_name_not_blank
    CHECK (BTRIM(first_name) <> ''),

    CONSTRAINT ck_users_last_name_not_blank
    CHECK (BTRIM(last_name) <> '')
);

CREATE TABLE auth.roles (
    role_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT ck_roles_code_not_blank
    CHECK (BTRIM(code) <> ''),

    CONSTRAINT ck_roles_name_not_blank
    CHECK (BTRIM(name) <> '')
);

CREATE TABLE auth.permissions (
    permission_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,

    CONSTRAINT ck_permissions_code_not_blank
    CHECK (BTRIM(code) <> ''),

    CONSTRAINT ck_permissions_name_not_blank
    CHECK (BTRIM(name) <> '')
);

CREATE TABLE auth.user_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,

    PRIMARY KEY (user_id, role_id),

    CONSTRAINT fk_user_roles_user
    FOREIGN KEY (user_id)
    REFERENCES auth.users (user_id)
    ON DELETE CASCADE
    ON UPDATE RESTRICT,

    CONSTRAINT fk_user_roles_role
    FOREIGN KEY (role_id)
    REFERENCES auth.roles (role_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT
);

CREATE TABLE auth.role_permissions (
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,

    PRIMARY KEY (role_id, permission_id),

    CONSTRAINT fk_role_permissions_role
    FOREIGN KEY (role_id)
    REFERENCES auth.roles (role_id)
    ON DELETE CASCADE
    ON UPDATE RESTRICT,

    CONSTRAINT fk_role_permissions_permission
    FOREIGN KEY (permission_id)
    REFERENCES auth.permissions (permission_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT
);

CREATE TABLE auth.professions (
    profession_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    professional_group TEXT NOT NULL,
    is_clinical BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT ck_professions_code_not_blank
    CHECK (BTRIM(code) <> ''),

    CONSTRAINT ck_professions_name_not_blank
    CHECK (BTRIM(name) <> ''),

    CONSTRAINT ck_professions_group_not_blank
    CHECK (BTRIM(professional_group) <> '')
);

CREATE TABLE auth.specialties (
    specialty_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profession_id BIGINT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT fk_specialties_profession
    FOREIGN KEY (profession_id)
    REFERENCES auth.professions (profession_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_specialties_code_not_blank
    CHECK (BTRIM(code) <> ''),

    CONSTRAINT ck_specialties_name_not_blank
    CHECK (BTRIM(name) <> '')
);

CREATE TABLE auth.reviewer_profiles (
    reviewer_profile_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    profession_id BIGINT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'PENDING',
    verified_at TIMESTAMPTZ NULL,
    verified_by BIGINT NULL,
    verification_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_reviewer_profiles_user
    FOREIGN KEY (user_id)
    REFERENCES auth.users (user_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_reviewer_profiles_profession
    FOREIGN KEY (profession_id)
    REFERENCES auth.professions (profession_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_reviewer_profiles_verified_by
    FOREIGN KEY (verified_by)
    REFERENCES auth.users (user_id)
    ON DELETE SET NULL
    ON UPDATE RESTRICT,

    CONSTRAINT ck_reviewer_profiles_verification_status
    CHECK (
        verification_status IN ('PENDING', 'VERIFIED', 'REJECTED', 'SUSPENDED')
    ),

    CONSTRAINT ck_reviewer_profiles_verified_data
    CHECK (
        verification_status <> 'VERIFIED'
        OR (verified_at IS NOT NULL AND verified_by IS NOT NULL)
    )
);

CREATE TABLE auth.reviewer_specialties (
    reviewer_profile_id BIGINT NOT NULL,
    specialty_id BIGINT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'PENDING',
    verified_at TIMESTAMPTZ NULL,

    PRIMARY KEY (reviewer_profile_id, specialty_id),

    CONSTRAINT fk_reviewer_specialties_profile
    FOREIGN KEY (reviewer_profile_id)
    REFERENCES auth.reviewer_profiles (reviewer_profile_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_reviewer_specialties_specialty
    FOREIGN KEY (specialty_id)
    REFERENCES auth.specialties (specialty_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_reviewer_specialties_status
    CHECK (
        verification_status IN ('PENDING', 'VERIFIED', 'REJECTED', 'SUSPENDED')
    ),

    CONSTRAINT ck_reviewer_specialties_verified_at
    CHECK (
        verification_status <> 'VERIFIED'
        OR verified_at IS NOT NULL
    )
);

CREATE TABLE auth.reviewer_experience (
    reviewer_experience_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reviewer_profile_id BIGINT NOT NULL,
    clinical_domain_id BIGINT NULL,
    experience_type TEXT NOT NULL,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at TIMESTAMPTZ NULL,
    notes TEXT,

    CONSTRAINT fk_reviewer_experience_profile
    FOREIGN KEY (reviewer_profile_id)
    REFERENCES auth.reviewer_profiles (reviewer_profile_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_reviewer_experience_domain
    FOREIGN KEY (clinical_domain_id)
    REFERENCES clinical.clinical_domains (clinical_domain_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_reviewer_experience_type_not_blank
    CHECK (BTRIM(experience_type) <> ''),

    CONSTRAINT ck_reviewer_experience_verified_data
    CHECK (NOT verified OR verified_at IS NOT NULL)
);

-- ============================================================================
-- 5. RESEARCH
-- ============================================================================

CREATE TABLE research.projects (
    project_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_projects_code_not_blank
    CHECK (BTRIM(project_code) <> ''),

    CONSTRAINT ck_projects_name_not_blank
    CHECK (BTRIM(name) <> ''),

    CONSTRAINT ck_projects_status
    CHECK (status IN ('DRAFT', 'ACTIVE', 'CLOSED', 'ARCHIVED'))
);

CREATE TABLE research.project_members (
    project_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    membership_type TEXT NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    PRIMARY KEY (project_id, user_id),

    CONSTRAINT fk_project_members_project
    FOREIGN KEY (project_id)
    REFERENCES research.projects (project_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_project_members_user
    FOREIGN KEY (user_id)
    REFERENCES auth.users (user_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_project_membership_type
    CHECK (membership_type IN ('OWNER', 'RESEARCHER', 'REVIEWER'))
);

CREATE TABLE research.model_items (
    model_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL,
    item_code TEXT NOT NULL UNIQUE,
    item_type TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_model_items_project
    FOREIGN KEY (project_id)
    REFERENCES research.projects (project_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_model_items_created_by
    FOREIGN KEY (created_by)
    REFERENCES auth.users (user_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_model_items_type
    CHECK (
        item_type IN (
            'CLINICAL_RULE',
            'OBSERVATION_PROTOCOL',
            'DIAGNOSIS',
            'DISPOSITION_RULE',
            'VARIABLE'
        )
    ),

    CONSTRAINT ck_model_items_code_not_blank
    CHECK (BTRIM(item_code) <> ''),

    CONSTRAINT ck_model_items_name_not_blank
    CHECK (BTRIM(name) <> '')
);

CREATE TABLE research.model_item_versions (
    model_item_version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_item_id BIGINT NOT NULL,
    version_number INTEGER NOT NULL,
    content JSONB NOT NULL,
    created_by BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_model_item_versions_item_version
    UNIQUE (model_item_id, version_number),

    CONSTRAINT fk_model_item_versions_item
    FOREIGN KEY (model_item_id)
    REFERENCES research.model_items (model_item_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_model_item_versions_created_by
    FOREIGN KEY (created_by)
    REFERENCES auth.users (user_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_model_item_versions_number
    CHECK (version_number > 0)
);

CREATE TABLE research.model_item_version_domains (
    model_item_version_id BIGINT NOT NULL,
    clinical_domain_id BIGINT NOT NULL,

    PRIMARY KEY (model_item_version_id, clinical_domain_id),

    CONSTRAINT fk_version_domains_version
    FOREIGN KEY (model_item_version_id)
    REFERENCES research.model_item_versions (model_item_version_id)
    ON DELETE CASCADE
    ON UPDATE RESTRICT,

    CONSTRAINT fk_version_domains_domain
    FOREIGN KEY (clinical_domain_id)
    REFERENCES clinical.clinical_domains (clinical_domain_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT
);

CREATE TABLE research.bibliographic_references (
    reference_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    citation TEXT NOT NULL,
    title TEXT NOT NULL,
    authors TEXT,
    publication_year INTEGER,
    doi TEXT,
    url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_references_citation_not_blank
    CHECK (BTRIM(citation) <> ''),

    CONSTRAINT ck_references_title_not_blank
    CHECK (BTRIM(title) <> ''),

    CONSTRAINT ck_references_year
    CHECK (
        publication_year IS NULL
        OR publication_year BETWEEN 1000 AND 3000
    )
);

CREATE TABLE research.sources (
    source_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reference_id BIGINT NOT NULL,
    source_type TEXT NOT NULL,
    location TEXT,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_sources_reference
    FOREIGN KEY (reference_id)
    REFERENCES research.bibliographic_references (reference_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_sources_type_not_blank
    CHECK (BTRIM(source_type) <> '')
);

CREATE TABLE research.model_item_sources (
    model_item_version_id BIGINT NOT NULL,
    source_id BIGINT NOT NULL,

    PRIMARY KEY (model_item_version_id, source_id),

    CONSTRAINT fk_model_item_sources_version
    FOREIGN KEY (model_item_version_id)
    REFERENCES research.model_item_versions (model_item_version_id)
    ON DELETE CASCADE
    ON UPDATE RESTRICT,

    CONSTRAINT fk_model_item_sources_source
    FOREIGN KEY (source_id)
    REFERENCES research.sources (source_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT
);

CREATE TABLE research.review_assignments (
    review_assignment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    model_item_id BIGINT NOT NULL,
    reviewer_user_id BIGINT NOT NULL,
    authority_rule_id BIGINT NOT NULL,
    assigned_by BIGINT NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'ASSIGNED',

    CONSTRAINT uq_review_assignments_id_reviewer
    UNIQUE (review_assignment_id, reviewer_user_id),

    CONSTRAINT fk_review_assignments_item
    FOREIGN KEY (model_item_id)
    REFERENCES research.model_items (model_item_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_review_assignments_reviewer
    FOREIGN KEY (reviewer_user_id)
    REFERENCES auth.users (user_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_review_assignments_assigned_by
    FOREIGN KEY (assigned_by)
    REFERENCES auth.users (user_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_review_assignments_status
    CHECK (status IN ('ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'))
);

CREATE TABLE research.reviews (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_assignment_id BIGINT NOT NULL UNIQUE,
    model_item_version_id BIGINT NOT NULL,
    reviewer_user_id BIGINT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    started_at TIMESTAMPTZ NULL,
    submitted_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_reviews_assignment_reviewer
    FOREIGN KEY (review_assignment_id, reviewer_user_id)
    REFERENCES research.review_assignments
    (review_assignment_id, reviewer_user_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_reviews_version
    FOREIGN KEY (model_item_version_id)
    REFERENCES research.model_item_versions (model_item_version_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_reviews_reviewer
    FOREIGN KEY (reviewer_user_id)
    REFERENCES auth.users (user_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_reviews_status
    CHECK (
        status IN (
            'PENDING',
            'IN_REVIEW',
            'OBSERVED',
            'MODIFIED',
            'READY_FOR_REVALIDATION',
            'VALIDATED'
        )
    ),

    CONSTRAINT ck_reviews_submitted_at
    CHECK (
        status IN ('PENDING', 'IN_REVIEW')
        OR submitted_at IS NOT NULL
    )
);

CREATE TABLE research.review_comments (
    comment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL,
    author_user_id BIGINT NOT NULL,
    comment_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_review_comments_review
    FOREIGN KEY (review_id)
    REFERENCES research.reviews (review_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_review_comments_author
    FOREIGN KEY (author_user_id)
    REFERENCES auth.users (user_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_review_comments_text_not_blank
    CHECK (BTRIM(comment_text) <> '')
);

CREATE TABLE research.clinical_observations (
    observation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id BIGINT NOT NULL,
    author_user_id BIGINT NOT NULL,
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    evidence TEXT,
    proposed_action TEXT,
    status TEXT NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_clinical_observations_review
    FOREIGN KEY (review_id)
    REFERENCES research.reviews (review_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_clinical_observations_author
    FOREIGN KEY (author_user_id)
    REFERENCES auth.users (user_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_clinical_observations_category
    CHECK (
        category IN (
            'CLINICAL_RULE',
            'SOURCE',
            'PARAMETER',
            'VARIABLE',
            'MODEL_REPRESENTATION',
            'TERMINOLOGY',
            'MISSING_EVIDENCE',
            'OTHER'
        )
    ),

    CONSTRAINT ck_clinical_observations_status
    CHECK (status IN ('OPEN', 'RESOLVED', 'REJECTED')),

    CONSTRAINT ck_clinical_observations_description_not_blank
    CHECK (BTRIM(description) <> '')
);

-- ============================================================================
-- 6. CLINICAL
-- ============================================================================

CREATE TABLE clinical.authority_rules (
    authority_rule_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profession_id BIGINT NOT NULL,
    specialty_id BIGINT NULL,
    clinical_domain_id BIGINT NOT NULL,
    authority_level TEXT NOT NULL,
    can_review BOOLEAN NOT NULL DEFAULT TRUE,
    can_validate BOOLEAN NOT NULL DEFAULT FALSE,
    review_scope TEXT NOT NULL,
    requires_interdisciplinary_validation BOOLEAN NOT NULL DEFAULT FALSE,
    rule_version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_authority_rules_profession
    FOREIGN KEY (profession_id)
    REFERENCES auth.professions (profession_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_authority_rules_specialty
    FOREIGN KEY (specialty_id)
    REFERENCES auth.specialties (specialty_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_authority_rules_domain
    FOREIGN KEY (clinical_domain_id)
    REFERENCES clinical.clinical_domains (clinical_domain_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_authority_rules_level
    CHECK (authority_level IN ('L1', 'L2', 'L3', 'L4', 'L5')),

    CONSTRAINT ck_authority_rules_scope_not_blank
    CHECK (BTRIM(review_scope) <> ''),

    CONSTRAINT ck_authority_rules_version
    CHECK (rule_version > 0),

    CONSTRAINT ck_authority_rules_validation_requires_review
    CHECK (NOT can_validate OR can_review)
);

CREATE TABLE clinical.clinical_rules (
    model_item_version_id BIGINT PRIMARY KEY,
    rule_expression JSONB NOT NULL,
    description TEXT,

    CONSTRAINT fk_clinical_rules_version
    FOREIGN KEY (model_item_version_id)
    REFERENCES research.model_item_versions (model_item_version_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT
);

CREATE TABLE clinical.diagnoses (
    model_item_version_id BIGINT PRIMARY KEY,
    diagnosis_code TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,

    CONSTRAINT fk_diagnoses_version
    FOREIGN KEY (model_item_version_id)
    REFERENCES research.model_item_versions (model_item_version_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_diagnoses_code_not_blank
    CHECK (BTRIM(diagnosis_code) <> ''),

    CONSTRAINT ck_diagnoses_name_not_blank
    CHECK (BTRIM(name) <> '')
);

CREATE TABLE clinical.observation_protocols (
    model_item_version_id BIGINT PRIMARY KEY,
    diagnosis_version_id BIGINT NOT NULL,
    protocol_definition JSONB NOT NULL,

    CONSTRAINT fk_observation_protocols_version
    FOREIGN KEY (model_item_version_id)
    REFERENCES research.model_item_versions (model_item_version_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_observation_protocols_diagnosis
    FOREIGN KEY (diagnosis_version_id)
    REFERENCES clinical.diagnoses (model_item_version_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT
);

CREATE TABLE clinical.disposition_rules (
    model_item_version_id BIGINT PRIMARY KEY,
    diagnosis_version_id BIGINT NOT NULL,
    destination TEXT NOT NULL,
    rule_definition JSONB NOT NULL,

    CONSTRAINT fk_disposition_rules_version
    FOREIGN KEY (model_item_version_id)
    REFERENCES research.model_item_versions (model_item_version_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_disposition_rules_diagnosis
    FOREIGN KEY (diagnosis_version_id)
    REFERENCES clinical.diagnoses (model_item_version_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_disposition_rules_destination
    CHECK (
        destination IN (
            'DISCHARGE',
            'OBSERVATION',
            'HOSPITALIZATION',
            'ICU',
            'OR',
            'OTHER_CRITICAL_CARE'
        )
    )
);

CREATE TABLE clinical.variables (
    model_item_version_id BIGINT PRIMARY KEY,
    name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    description TEXT,

    CONSTRAINT fk_variables_version
    FOREIGN KEY (model_item_version_id)
    REFERENCES research.model_item_versions (model_item_version_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_variables_name_not_blank
    CHECK (BTRIM(name) <> ''),

    CONSTRAINT ck_variables_data_type_not_blank
    CHECK (BTRIM(data_type) <> '')
);

CREATE TABLE clinical.parameters (
    parameter_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    variable_id BIGINT NOT NULL,
    distribution TEXT NOT NULL,
    minimum_value NUMERIC,
    mode_value NUMERIC,
    maximum_value NUMERIC,

    CONSTRAINT fk_parameters_variable
    FOREIGN KEY (variable_id)
    REFERENCES clinical.variables (model_item_version_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_parameters_distribution_not_blank
    CHECK (BTRIM(distribution) <> ''),

    CONSTRAINT ck_parameters_bounds
    CHECK (
        minimum_value IS NULL
        OR maximum_value IS NULL
        OR minimum_value <= maximum_value
    ),

    CONSTRAINT ck_parameters_mode_bounds
    CHECK (
        mode_value IS NULL
        OR (
            (minimum_value IS NULL OR minimum_value <= mode_value)
            AND (maximum_value IS NULL OR mode_value <= maximum_value)
        )
    ),

    CONSTRAINT ck_parameters_triangular
    CHECK (
        LOWER(distribution) <> 'triangular'
        OR (
            minimum_value IS NOT NULL
            AND mode_value IS NOT NULL
            AND maximum_value IS NOT NULL
        )
    )
);

-- ============================================================================
-- 7. SIMULATION
-- ============================================================================

CREATE TABLE simulation.simulations (
    simulation_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_by BIGINT NOT NULL,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_simulations_project
    FOREIGN KEY (project_id)
    REFERENCES research.projects (project_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_simulations_created_by
    FOREIGN KEY (created_by)
    REFERENCES auth.users (user_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_simulations_name_not_blank
    CHECK (BTRIM(name) <> ''),

    CONSTRAINT ck_simulations_status
    CHECK (status IN ('DRAFT', 'READY', 'RUNNING', 'COMPLETED', 'ARCHIVED'))
);

CREATE TABLE simulation.simulation_model_items (
    simulation_id BIGINT NOT NULL,
    model_item_version_id BIGINT NOT NULL,

    PRIMARY KEY (simulation_id, model_item_version_id),

    CONSTRAINT fk_simulation_model_items_simulation
    FOREIGN KEY (simulation_id)
    REFERENCES simulation.simulations (simulation_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT fk_simulation_model_items_version
    FOREIGN KEY (model_item_version_id)
    REFERENCES research.model_item_versions (model_item_version_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT
);

CREATE TABLE simulation.scenarios (
    scenario_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    simulation_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    configuration JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_scenarios_simulation
    FOREIGN KEY (simulation_id)
    REFERENCES simulation.simulations (simulation_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_scenarios_name_not_blank
    CHECK (BTRIM(name) <> '')
);

CREATE TABLE simulation.experiments (
    experiment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    scenario_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    configuration JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_experiments_scenario
    FOREIGN KEY (scenario_id)
    REFERENCES simulation.scenarios (scenario_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_experiments_name_not_blank
    CHECK (BTRIM(name) <> '')
);

CREATE TABLE simulation.experiment_runs (
    experiment_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_id BIGINT NOT NULL,
    run_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'RUNNING',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ NULL,
    execution_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,

    CONSTRAINT uq_experiment_runs_number
    UNIQUE (experiment_id, run_number),

    CONSTRAINT fk_experiment_runs_experiment
    FOREIGN KEY (experiment_id)
    REFERENCES simulation.experiments (experiment_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_experiment_runs_number
    CHECK (run_number > 0),

    CONSTRAINT ck_experiment_runs_status
    CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED')),

    CONSTRAINT ck_experiment_runs_completed_at
    CHECK (
        (status = 'RUNNING' AND completed_at IS NULL)
        OR
        (status <> 'RUNNING' AND completed_at IS NOT NULL)
    )
);

CREATE TABLE simulation.results (
    result_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    experiment_run_id BIGINT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value NUMERIC,
    metric_unit TEXT,
    result_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_results_experiment_run
    FOREIGN KEY (experiment_run_id)
    REFERENCES simulation.experiment_runs (experiment_run_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_results_metric_name_not_blank
    CHECK (BTRIM(metric_name) <> '')
);

-- ============================================================================
-- 8. AUDIT
-- ============================================================================

CREATE TABLE audit.audit_events (
    audit_event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_user_id BIGINT NULL,
    event_type TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    model_version_id BIGINT NULL,
    previous_state JSONB,
    new_state JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_audit_events_actor
    FOREIGN KEY (actor_user_id)
    REFERENCES auth.users (user_id)
    ON DELETE SET NULL
    ON UPDATE RESTRICT,

    CONSTRAINT fk_audit_events_model_version
    FOREIGN KEY (model_version_id)
    REFERENCES research.model_item_versions (model_item_version_id)
    ON DELETE RESTRICT
    ON UPDATE RESTRICT,

    CONSTRAINT ck_audit_events_event_type_not_blank
    CHECK (BTRIM(event_type) <> ''),

    CONSTRAINT ck_audit_events_resource_type_not_blank
    CHECK (BTRIM(resource_type) <> '')
);

-- ============================================================================
-- 9. CROSS-SCHEMA / SEMANTIC FOREIGN KEYS
-- ============================================================================

ALTER TABLE research.review_assignments
ADD CONSTRAINT fk_review_assignments_authority_rule
FOREIGN KEY (authority_rule_id)
REFERENCES clinical.authority_rules (authority_rule_id)
ON DELETE RESTRICT
ON UPDATE RESTRICT;

-- ============================================================================
-- 10. INDEXES
-- ============================================================================

CREATE UNIQUE INDEX uq_references_doi
ON research.bibliographic_references (LOWER(doi))
WHERE doi IS NOT NULL AND BTRIM(doi) <> '';

CREATE UNIQUE INDEX uq_project_active_owner
ON research.project_members (project_id)
WHERE membership_type = 'OWNER' AND is_active = TRUE;

CREATE INDEX ix_specialties_profession
ON auth.specialties (profession_id);

CREATE INDEX ix_reviewer_profiles_profession
ON auth.reviewer_profiles (profession_id);

CREATE INDEX ix_reviewer_specialties_specialty
ON auth.reviewer_specialties (specialty_id);

CREATE INDEX ix_reviewer_experience_domain
ON auth.reviewer_experience (clinical_domain_id);

CREATE INDEX ix_project_members_user
ON research.project_members (user_id);

CREATE INDEX ix_model_items_project
ON research.model_items (project_id);

CREATE INDEX ix_model_item_versions_item
ON research.model_item_versions (model_item_id);

CREATE INDEX ix_version_domains_domain
ON research.model_item_version_domains (clinical_domain_id);

CREATE INDEX ix_sources_reference
ON research.sources (reference_id);

CREATE INDEX ix_model_item_sources_source
ON research.model_item_sources (source_id);

CREATE INDEX ix_review_assignments_item
ON research.review_assignments (model_item_id);

CREATE INDEX ix_review_assignments_reviewer
ON research.review_assignments (reviewer_user_id);

CREATE INDEX ix_review_assignments_authority_rule
ON research.review_assignments (authority_rule_id);

CREATE INDEX ix_reviews_version
ON research.reviews (model_item_version_id);

CREATE INDEX ix_reviews_reviewer
ON research.reviews (reviewer_user_id);

CREATE INDEX ix_review_comments_review
ON research.review_comments (review_id);

CREATE INDEX ix_clinical_observations_review
ON research.clinical_observations (review_id);

CREATE INDEX ix_authority_rules_profession_domain
ON clinical.authority_rules (profession_id, clinical_domain_id);

CREATE INDEX ix_authority_rules_specialty
ON clinical.authority_rules (specialty_id);

CREATE INDEX ix_authority_rules_domain
ON clinical.authority_rules (clinical_domain_id);

CREATE INDEX ix_observation_protocols_diagnosis
ON clinical.observation_protocols (diagnosis_version_id);

CREATE INDEX ix_disposition_rules_diagnosis
ON clinical.disposition_rules (diagnosis_version_id);

CREATE INDEX ix_parameters_variable
ON clinical.parameters (variable_id);

CREATE INDEX ix_simulation_model_items_version
ON simulation.simulation_model_items (model_item_version_id);

CREATE INDEX ix_scenarios_simulation
ON simulation.scenarios (simulation_id);

CREATE INDEX ix_experiments_scenario
ON simulation.experiments (scenario_id);

CREATE INDEX ix_experiment_runs_experiment
ON simulation.experiment_runs (experiment_id);

CREATE INDEX ix_results_experiment_run
ON simulation.results (experiment_run_id);

CREATE INDEX ix_audit_events_actor
ON audit.audit_events (actor_user_id);

CREATE INDEX ix_audit_events_model_version
ON audit.audit_events (model_version_id);

CREATE INDEX ix_audit_events_resource
ON audit.audit_events (resource_type, resource_id);

CREATE INDEX ix_audit_events_created_at
ON audit.audit_events (created_at);

-- ============================================================================
-- 11. FUNCTIONS
-- ============================================================================

CREATE OR REPLACE FUNCTION auth.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION clinical.validate_specialty_profession()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    specialty_profession_id BIGINT;
BEGIN
    IF NEW.specialty_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT profession_id
      INTO specialty_profession_id
      FROM auth.specialties
     WHERE specialty_id = NEW.specialty_id;

    IF specialty_profession_id IS NULL THEN
        RAISE EXCEPTION 'Specialty % does not exist', NEW.specialty_id;
    END IF;

    IF specialty_profession_id <> NEW.profession_id THEN
        RAISE EXCEPTION
            'Authority rule specialty % does not belong to profession %',
            NEW.specialty_id, NEW.profession_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION auth.validate_reviewer_specialty_profession()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    reviewer_profession_id BIGINT;
    specialty_profession_id BIGINT;
BEGIN
    SELECT profession_id
      INTO reviewer_profession_id
      FROM auth.reviewer_profiles
     WHERE reviewer_profile_id = NEW.reviewer_profile_id;

    SELECT profession_id
      INTO specialty_profession_id
      FROM auth.specialties
     WHERE specialty_id = NEW.specialty_id;

    IF reviewer_profession_id IS NULL THEN
        RAISE EXCEPTION
            'Reviewer profile % does not exist',
            NEW.reviewer_profile_id;
    END IF;

    IF specialty_profession_id IS NULL THEN
        RAISE EXCEPTION
            'Specialty % does not exist',
            NEW.specialty_id;
    END IF;

    IF reviewer_profession_id <> specialty_profession_id THEN
        RAISE EXCEPTION
            'Specialty % does not belong to reviewer profession %',
            NEW.specialty_id, reviewer_profession_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION research.validate_review_version()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    assignment_item_id BIGINT;
    version_item_id BIGINT;
BEGIN
    SELECT model_item_id
      INTO assignment_item_id
      FROM research.review_assignments
     WHERE review_assignment_id = NEW.review_assignment_id;

    SELECT model_item_id
      INTO version_item_id
      FROM research.model_item_versions
     WHERE model_item_version_id = NEW.model_item_version_id;

    IF assignment_item_id IS NULL THEN
        RAISE EXCEPTION
            'Review assignment % does not exist',
            NEW.review_assignment_id;
    END IF;

    IF version_item_id IS NULL THEN
        RAISE EXCEPTION
            'Model item version % does not exist',
            NEW.model_item_version_id;
    END IF;

    IF assignment_item_id <> version_item_id THEN
        RAISE EXCEPTION
            'Review assignment % belongs to model item %, but version % belongs to model item %',
            NEW.review_assignment_id,
            assignment_item_id,
            NEW.model_item_version_id,
            version_item_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION research.validate_review_assignment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    profile_status TEXT;
    profile_profession_id BIGINT;
    rule_profession_id BIGINT;
    rule_specialty_id BIGINT;
BEGIN
    SELECT verification_status, profession_id
      INTO profile_status, profile_profession_id
      FROM auth.reviewer_profiles
     WHERE user_id = NEW.reviewer_user_id;

    IF profile_status IS NULL THEN
        RAISE EXCEPTION
            'Reviewer user % does not have a reviewer profile',
            NEW.reviewer_user_id;
    END IF;

    IF profile_status <> 'VERIFIED' THEN
        RAISE EXCEPTION
            'Reviewer user % is not verified',
            NEW.reviewer_user_id;
    END IF;

    SELECT profession_id, specialty_id
      INTO rule_profession_id, rule_specialty_id
      FROM clinical.authority_rules
     WHERE authority_rule_id = NEW.authority_rule_id
       AND is_active = TRUE;

    IF rule_profession_id IS NULL THEN
        RAISE EXCEPTION
            'Authority rule % does not exist or is inactive',
            NEW.authority_rule_id;
    END IF;

    IF profile_profession_id <> rule_profession_id THEN
        RAISE EXCEPTION
            'Reviewer profession % does not match authority rule profession %',
            profile_profession_id,
            rule_profession_id;
    END IF;

    IF rule_specialty_id IS NOT NULL
       AND NOT EXISTS (
            SELECT 1
              FROM auth.reviewer_specialties rs
             WHERE rs.reviewer_profile_id = (
                    SELECT reviewer_profile_id
                      FROM auth.reviewer_profiles
                     WHERE user_id = NEW.reviewer_user_id
                   )
               AND rs.specialty_id = rule_specialty_id
               AND rs.verification_status = 'VERIFIED'
       )
    THEN
        RAISE EXCEPTION
            'Reviewer % does not have the verified specialty required by authority rule %',
            NEW.reviewer_user_id,
            NEW.authority_rule_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION research.validate_model_item_entity_type()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    expected_item_type TEXT;
    actual_item_type   TEXT;
BEGIN
    SELECT mi.item_type
      INTO actual_item_type
      FROM research.model_item_versions v
      JOIN research.model_items mi
        ON mi.model_item_id = v.model_item_id
     WHERE v.model_item_version_id = NEW.model_item_version_id;

    expected_item_type :=
        CASE TG_TABLE_NAME
            WHEN 'clinical_rules' THEN 'CLINICAL_RULE'
            WHEN 'diagnoses' THEN 'DIAGNOSIS'
            WHEN 'observation_protocols' THEN 'OBSERVATION_PROTOCOL'
            WHEN 'disposition_rules' THEN 'DISPOSITION_RULE'
            WHEN 'variables' THEN 'VARIABLE'
            ELSE NULL
        END;

    IF expected_item_type IS NULL THEN
        RETURN NEW;
    END IF;

    IF actual_item_type <> expected_item_type THEN
        RAISE EXCEPTION
            'Model item version % has type %, but table %.% requires type %',
            NEW.model_item_version_id,
            actual_item_type,
            TG_TABLE_SCHEMA,
            TG_TABLE_NAME,
            expected_item_type;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION research.prevent_model_version_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'Model item versions are immutable scientific records; create a new version instead';
END;
$$;

CREATE OR REPLACE FUNCTION simulation.prevent_historical_run_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION
            'Experiment runs are historical scientific records and cannot be deleted';
    END IF;

    IF OLD.status <> 'RUNNING' THEN
        RAISE EXCEPTION
            'Experiment run % is already historical (%); it cannot be modified',
            OLD.experiment_run_id,
            OLD.status;
    END IF;

    IF NEW.experiment_run_id <> OLD.experiment_run_id
       OR NEW.experiment_id <> OLD.experiment_id
       OR NEW.run_number <> OLD.run_number
       OR NEW.started_at <> OLD.started_at
    THEN
        RAISE EXCEPTION
            'Experiment run identity and start metadata are immutable';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION audit.prevent_audit_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'Audit events are append-only and cannot be updated or deleted';
END;
$$;

CREATE OR REPLACE FUNCTION research.audit_review_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    event_name TEXT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        event_name := 'REVIEW_CREATED';
    ELSIF TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status THEN
        event_name := 'STATUS_CHANGED';
    ELSE
        RETURN NEW;
    END IF;

    INSERT INTO audit.audit_events (
        actor_user_id,
        event_type,
        resource_type,
        resource_id,
        model_version_id,
        previous_state,
        new_state
    )
    VALUES (
        NEW.reviewer_user_id,
        event_name,
        'REVIEW',
        NEW.review_id::TEXT,
        NEW.model_item_version_id,
        CASE
            WHEN TG_OP = 'UPDATE' THEN
                jsonb_build_object('status', OLD.status)
            ELSE NULL
        END,
        jsonb_build_object('status', NEW.status)
    );

    RETURN NEW;
END;
$$;

-- ============================================================================
-- 12. TRIGGERS
-- ============================================================================

CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON auth.users
FOR EACH ROW
EXECUTE FUNCTION auth.set_updated_at();

CREATE TRIGGER trg_reviewer_profiles_updated_at
BEFORE UPDATE ON auth.reviewer_profiles
FOR EACH ROW
EXECUTE FUNCTION auth.set_updated_at();

CREATE TRIGGER trg_projects_updated_at
BEFORE UPDATE ON research.projects
FOR EACH ROW
EXECUTE FUNCTION auth.set_updated_at();

CREATE TRIGGER trg_authority_rules_specialty_profession
BEFORE INSERT OR UPDATE ON clinical.authority_rules
FOR EACH ROW
EXECUTE FUNCTION clinical.validate_specialty_profession();

CREATE TRIGGER trg_reviewer_specialty_profession
BEFORE INSERT OR UPDATE ON auth.reviewer_specialties
FOR EACH ROW
EXECUTE FUNCTION auth.validate_reviewer_specialty_profession();

CREATE TRIGGER trg_review_assignments_validate
BEFORE INSERT OR UPDATE ON research.review_assignments
FOR EACH ROW
EXECUTE FUNCTION research.validate_review_assignment();

CREATE TRIGGER trg_reviews_validate_version
BEFORE INSERT OR UPDATE ON research.reviews
FOR EACH ROW
EXECUTE FUNCTION research.validate_review_version();

CREATE TRIGGER trg_clinical_rules_item_type
BEFORE INSERT OR UPDATE ON clinical.clinical_rules
FOR EACH ROW
EXECUTE FUNCTION research.validate_model_item_entity_type();

CREATE TRIGGER trg_diagnoses_item_type
BEFORE INSERT OR UPDATE ON clinical.diagnoses
FOR EACH ROW
EXECUTE FUNCTION research.validate_model_item_entity_type();

CREATE TRIGGER trg_observation_protocols_item_type
BEFORE INSERT OR UPDATE ON clinical.observation_protocols
FOR EACH ROW
EXECUTE FUNCTION research.validate_model_item_entity_type();

CREATE TRIGGER trg_disposition_rules_item_type
BEFORE INSERT OR UPDATE ON clinical.disposition_rules
FOR EACH ROW
EXECUTE FUNCTION research.validate_model_item_entity_type();

CREATE TRIGGER trg_variables_item_type
BEFORE INSERT OR UPDATE ON clinical.variables
FOR EACH ROW
EXECUTE FUNCTION research.validate_model_item_entity_type();

CREATE TRIGGER trg_model_item_versions_immutable
BEFORE UPDATE OR DELETE ON research.model_item_versions
FOR EACH ROW
EXECUTE FUNCTION research.prevent_model_version_mutation();

CREATE TRIGGER trg_experiment_runs_historical
BEFORE UPDATE OR DELETE ON simulation.experiment_runs
FOR EACH ROW
EXECUTE FUNCTION simulation.prevent_historical_run_mutation();

CREATE TRIGGER trg_audit_events_append_only
BEFORE UPDATE OR DELETE ON audit.audit_events
FOR EACH ROW
EXECUTE FUNCTION audit.prevent_audit_mutation();

CREATE TRIGGER trg_reviews_audit
AFTER INSERT OR UPDATE ON research.reviews
FOR EACH ROW
EXECUTE FUNCTION research.audit_review_event();

-- ============================================================================
-- 13. DERIVED VIEWS
-- ============================================================================

CREATE OR REPLACE VIEW research.v_current_model_items AS
SELECT
    mi.model_item_id,
    mi.project_id,
    mi.item_code,
    mi.item_type,
    mi.name,
    mi.description,
    v.model_item_version_id,
    v.version_number,
    v.content,
    v.created_by AS version_created_by,
    v.created_at AS version_created_at
FROM research.model_items AS mi
INNER JOIN LATERAL (
    SELECT
        miv.model_item_version_id,
        miv.version_number,
        miv.content,
        miv.created_by,
        miv.created_at
    FROM research.model_item_versions AS miv
    WHERE miv.model_item_id = mi.model_item_id
    ORDER BY miv.version_number DESC
    LIMIT 1
) AS v ON TRUE;

CREATE OR REPLACE VIEW research.v_review_status_summary AS
SELECT
    mi.model_item_id,
    mi.item_code,
    mi.name,
    miv.model_item_version_id,
    miv.version_number,
    COUNT(r.review_id) AS review_count,
    COUNT(r.review_id) FILTER (WHERE r.status = 'VALIDATED')
        AS validated_review_count,
    COUNT(r.review_id) FILTER (
        WHERE r.status IN ('OBSERVED', 'MODIFIED', 'READY_FOR_REVALIDATION')
    ) AS open_or_revalidation_review_count,
    CASE
        WHEN COUNT(r.review_id) = 0
            THEN 'PENDING_REVIEW'
        WHEN
            COUNT(r.review_id) FILTER (WHERE r.status IN (
                'OBSERVED', 'MODIFIED', 'READY_FOR_REVALIDATION'
            )) > 0
            THEN 'REQUIRES_REVIEW'
        WHEN
            COUNT(r.review_id) > 0
            AND COUNT(r.review_id) = COUNT(r.review_id) FILTER (
                WHERE r.status = 'VALIDATED'
            )
            THEN 'VALIDATED'
        ELSE 'IN_REVIEW'
    END AS derived_status
FROM research.model_items AS mi
INNER JOIN research.model_item_versions AS miv
    ON mi.model_item_id = miv.model_item_id
LEFT JOIN research.reviews AS r
    ON miv.model_item_version_id = r.model_item_version_id
GROUP BY
    mi.model_item_id,
    mi.item_code,
    mi.name,
    miv.model_item_version_id,
    miv.version_number;

-- ============================================================================
-- 14. INITIAL ROLE CATALOG
-- ============================================================================

INSERT INTO auth.roles (code, name, description)
VALUES
(
    'REVIEWER', 'Clinical Reviewer',
    'Verified clinical professional authorized to review within assigned scope.'
),
(
    'RESEARCH_TEAM', 'Research Team',
    'Member of the research team responsible for model '
    || 'construction and governance.'
),
(
    'SYSTEM', 'System',
    'Technical/system role for controlled platform operations.'
)
ON CONFLICT (code) DO NOTHING;

COMMIT;

-- ============================================================================
-- END OF SCHEMA v1.0
-- ============================================================================
