-- Bootstrap roles for Translator. Idempotent.
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'temporal') THEN
        CREATE ROLE temporal LOGIN PASSWORD 'temporal';
    END IF;
END $$;

GRANT CONNECT ON DATABASE translator TO temporal;
GRANT USAGE, CREATE ON SCHEMA public TO temporal;