SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;
SET search_path = public, pg_catalog;
SET default_tablespace = '';
SET default_with_oids = false;

-- Drop everything first, in case we're modifying an existing db.

drop table if exists adapter_population_queue cascade;
drop table if exists adapter_population_queue_package_scope cascade;
drop table if exists adapter_process_status cascade;
drop table if exists adapter_process_status_return_body cascade;
drop table if exists adapter_process_status_status cascade;

-- adapter_population_queue

CREATE TABLE adapter_population_queue (
    id integer NOT NULL,
    package_scope_id integer NOT NULL,
    package_identifier bigint NOT NULL,
    package_revision bigint NOT NULL,
    "timestamp" timestamp with time zone NOT NULL
);

-- ALTER TABLE public.adapter_population_queue OWNER TO pasta_gmn_adapter;

CREATE SEQUENCE adapter_population_queue_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

-- ALTER TABLE public.adapter_population_queue_id_seq OWNER TO pasta_gmn_adapter;

ALTER SEQUENCE adapter_population_queue_id_seq OWNED BY adapter_population_queue.id;

SELECT pg_catalog.setval('adapter_population_queue_id_seq', 1, true);


-- adapter_population_queue_package_scope

CREATE TABLE adapter_population_queue_package_scope (
    id integer NOT NULL,
    package_scope character varying(1024) NOT NULL
);

-- ALTER TABLE public.adapter_population_queue_package_scope OWNER TO pasta_gmn_adapter;

CREATE SEQUENCE adapter_population_queue_package_scope_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

-- ALTER TABLE public.adapter_population_queue_package_scope_id_seq OWNER TO pasta_gmn_adapter;

ALTER SEQUENCE adapter_population_queue_package_scope_id_seq OWNED BY adapter_population_queue_package_scope.id;

SELECT pg_catalog.setval('adapter_population_queue_package_scope_id_seq', 1, true);

-- adapter_process_status

CREATE TABLE adapter_process_status (
    id integer NOT NULL,
    population_queue_item_id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    status_id integer NOT NULL,
    return_code integer NOT NULL,
    return_body_id integer NOT NULL
);

-- ALTER TABLE public.adapter_process_status OWNER TO pasta_gmn_adapter;

CREATE SEQUENCE adapter_process_status_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

-- ALTER TABLE public.adapter_process_status_id_seq OWNER TO pasta_gmn_adapter;

ALTER SEQUENCE adapter_process_status_id_seq OWNED BY adapter_process_status.id;

SELECT pg_catalog.setval('adapter_process_status_id_seq', 1, true);


-- adapter_process_status_return_body

CREATE TABLE adapter_process_status_return_body (
    id integer NOT NULL,
    return_body character varying(2048) NOT NULL
);

-- ALTER TABLE public.adapter_process_status_return_body OWNER TO pasta_gmn_adapter;

CREATE SEQUENCE adapter_process_status_return_body_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

-- ALTER TABLE public.adapter_process_status_return_body_id_seq OWNER TO pasta_gmn_adapter;

ALTER SEQUENCE adapter_process_status_return_body_id_seq OWNED BY adapter_process_status_return_body.id;

SELECT pg_catalog.setval('adapter_process_status_return_body_id_seq', 1, true);


-- adapter_process_status_status

CREATE TABLE adapter_process_status_status (
    id integer NOT NULL,
    status character varying(1024) NOT NULL
);

-- ALTER TABLE public.adapter_process_status_status OWNER TO pasta_gmn_adapter;

CREATE SEQUENCE adapter_process_status_status_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;

-- ALTER TABLE public.adapter_process_status_status_id_seq OWNER TO pasta_gmn_adapter;

ALTER SEQUENCE adapter_process_status_status_id_seq OWNED BY adapter_process_status_status.id;

SELECT pg_catalog.setval('adapter_process_status_status_id_seq', 1, true);

-- Defaults.

ALTER TABLE ONLY adapter_population_queue ALTER COLUMN id SET DEFAULT nextval('adapter_population_queue_id_seq'::regclass);
ALTER TABLE ONLY adapter_population_queue_package_scope ALTER COLUMN id SET DEFAULT nextval('adapter_population_queue_package_scope_id_seq'::regclass);
ALTER TABLE ONLY adapter_process_status ALTER COLUMN id SET DEFAULT nextval('adapter_process_status_id_seq'::regclass);
ALTER TABLE ONLY adapter_process_status_return_body ALTER COLUMN id SET DEFAULT nextval('adapter_process_status_return_body_id_seq'::regclass);
ALTER TABLE ONLY adapter_process_status_status ALTER COLUMN id SET DEFAULT nextval('adapter_process_status_status_id_seq'::regclass);

-- Constraints.

ALTER TABLE ONLY adapter_population_queue
    ADD CONSTRAINT adapter_population_queue_pkey PRIMARY KEY (id);

ALTER TABLE ONLY ADAPTER_POPULATION_QUEUE_PACKAGE_SCOPE
    ADD CONSTRAINT adapter_population_queue_package_scope_package_scope_key UNIQUE (package_scope);

ALTER TABLE ONLY adapter_population_queue_package_scope
    ADD CONSTRAINT adapter_population_queue_package_scope_pkey PRIMARY KEY (id);

ALTER TABLE ONLY adapter_process_status
    ADD CONSTRAINT adapter_process_status_pkey PRIMARY KEY (id);

ALTER TABLE ONLY adapter_process_status_return_body
    ADD CONSTRAINT adapter_process_status_return_body_return_body_key UNIQUE (return_body);

ALTER TABLE ONLY adapter_process_status_return_body
    ADD CONSTRAINT adapter_process_status_return_body_pkey PRIMARY KEY (id);

ALTER TABLE ONLY adapter_process_status_status
    ADD CONSTRAINT adapter_process_status_status_pkey PRIMARY KEY (id);

ALTER TABLE ONLY adapter_process_status_status
    ADD CONSTRAINT adapter_process_status_status_status_key UNIQUE (status);

ALTER TABLE ONLY adapter_population_queue
    ADD CONSTRAINT adapter_population_queue_package_scope_id_fkey FOREIGN KEY (package_scope_id) REFERENCES adapter_population_queue_package_scope(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE ONLY adapter_process_status
    ADD CONSTRAINT adapter_process_status_return_body_id_fkey FOREIGN KEY (return_body_id) REFERENCES adapter_process_status_return_body(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE ONLY adapter_process_status
    ADD CONSTRAINT adapter_process_status_population_queue_item_id_fkey FOREIGN KEY (population_queue_item_id) REFERENCES adapter_population_queue(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE ONLY adapter_process_status
    ADD CONSTRAINT adapter_process_status_status_id_fkey FOREIGN KEY (status_id) REFERENCES adapter_process_status_status(id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;

-- Indexes

CREATE INDEX adapter_population_queue_package_identifier ON adapter_population_queue USING btree (package_identifier);
CREATE INDEX adapter_population_queue_package_revision ON adapter_population_queue USING btree (package_revision);
CREATE INDEX adapter_population_queue_package_scope_id ON adapter_population_queue USING btree (package_scope_id);
CREATE INDEX adapter_population_queue_timestamp ON adapter_population_queue USING btree ("timestamp");
CREATE INDEX adapter_process_status_return_code ON adapter_process_status USING btree (return_code);
CREATE INDEX adapter_process_status_return_body_id ON adapter_process_status USING btree (return_body_id);
CREATE INDEX adapter_process_status_population_queue_item_id ON adapter_process_status USING btree (population_queue_item_id);
CREATE INDEX adapter_process_status_status_id ON adapter_process_status USING btree (status_id);
CREATE INDEX adapter_process_status_timestamp ON adapter_process_status USING btree ("timestamp");

-- Permissions

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;
