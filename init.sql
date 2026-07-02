CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE observations (
    id SERIAL PRIMARY KEY,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Point, 4326),
    date DATE NOT NULL,
    temperature_eau DOUBLE PRECISION,
    salinite DOUBLE PRECISION,
    ph DOUBLE PRECISION,
    oxygene_dissous DOUBLE PRECISION,
    turbidite DOUBLE PRECISION,
    conductivite DOUBLE PRECISION,
    profondeur DOUBLE PRECISION,
    nitrates DOUBLE PRECISION,
    phosphates DOUBLE PRECISION,
    matiere_organique DOUBLE PRECISION,
    type_mangrove VARCHAR(100),
    nature_sol VARCHAR(100),
    niveau_degradation VARCHAR(50),
    especes_presentes TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_observations_geom ON observations USING GIST (geom);
