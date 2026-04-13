CREATE TABLE IF NOT EXISTS calls_live (
    unique_id                 TEXT PRIMARY KEY,
    from_number               TEXT,
    agent_id                  TEXT,
    timestamp                 TIMESTAMPTZ,
    duration_seconds          INTEGER,
    callee_name               TEXT,
    apellido                  TEXT,
    edad                      TEXT,
    direccion                 TEXT,
    ciudad                    TEXT,
    codigo_postal             TEXT,
    adress_origine            TEXT,
    code_postal               TEXT,
    tipo_vivienda             TEXT,
    superfici_vivienda        TEXT,
    superfici_desvan          TEXT,
    estado_desvan             TEXT,
    accesso_desvan            TEXT,
    tiene_desvan              TEXT,
    calefaccion               TEXT,
    suelo                     TEXT,
    altura                    TEXT,
    piso_casa                 TEXT,
    proprietad                TEXT,
    disponibilidad_visita     TEXT,
    disponibilidad_llamada    TEXT,
    debe_ser_llamado_de_nuevo TEXT,
    resumen_conversacion      TEXT,
    other_extract             TEXT,
    messagerie                TEXT,
    classification            TEXT DEFAULT '',
    resultat                  TEXT DEFAULT '',
    list_name                 TEXT,
    url                       TEXT,
    inserted_at               TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pipeline_audit (
    id             SERIAL PRIMARY KEY,
    run_id         TEXT,
    script         TEXT,
    period_from    TIMESTAMPTZ,
    period_to      TIMESTAMPTZ,
    api_declared   INTEGER DEFAULT 0,
    api_fetched    INTEGER DEFAULT 0,
    after_filter   INTEGER DEFAULT 0,
    inserted_in_db INTEGER DEFAULT 0,
    ignored_in_db  INTEGER DEFAULT 0,
    error_message  TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_calls_timestamp ON calls_live (timestamp);
CREATE INDEX IF NOT EXISTS idx_calls_agent     ON calls_live (agent_id);
CREATE INDEX IF NOT EXISTS idx_calls_from      ON calls_live (from_number);