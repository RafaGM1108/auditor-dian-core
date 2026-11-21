-- Esquema de la base DuckDB de un cliente (SPEC §6). Versión 2: agrega los totales de
-- LegalMonetaryTotal que faltaban (cargos, descuentos, anticipos, redondeo).
-- Montos, precios, cantidades y TRM en DECIMAL(21,6) y tarifas en DECIMAL(9,3): la DIAN admite
-- hasta 15 dígitos con 6 decimales y tarifas con 3 decimales (Anexo FE 1.9: FAU14, FAS05,
-- FBB02, FAS14). Decisión 0004.

CREATE TABLE schema_version (
    version INTEGER NOT NULL,
    aplicada TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE cliente (
    id VARCHAR PRIMARY KEY,  -- NIT sin DV o cédula, solo dígitos
    nombre VARCHAR NOT NULL,
    creado TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE archivos_ingeridos (
    sha256 VARCHAR PRIMARY KEY,  -- del archivo tal como llegó: llave de idempotencia
    ruta VARCHAR NOT NULL,
    fecha_ingesta TIMESTAMP NOT NULL DEFAULT current_timestamp,
    documentos INTEGER NOT NULL,
    errores INTEGER NOT NULL
);

CREATE TABLE documentos (
    cufe VARCHAR PRIMARY KEY,  -- CUFE, CUDE o CUDS
    esquema_cufe VARCHAR,
    tipo VARCHAR,
    prefijo VARCHAR,
    numero VARCHAR,
    fecha_emision DATE,
    hora_emision TIMETZ,
    fecha_vencimiento DATE,
    forma_pago VARCHAR,  -- 1 contado, 2 crédito
    medios_pago VARCHAR[],  -- PaymentMeansCode de cada medio, en orden del XML
    moneda VARCHAR,
    trm DECIMAL(21, 6),
    emisor_tipo_identificacion VARCHAR,
    emisor_identificacion VARCHAR,
    emisor_dv VARCHAR,
    emisor_nombre VARCHAR,
    adquirente_tipo_identificacion VARCHAR,
    adquirente_identificacion VARCHAR,
    adquirente_dv VARCHAR,
    adquirente_nombre VARCHAR,
    subtotal DECIMAL(21, 6),
    base_gravable DECIMAL(21, 6),
    total_impuestos_incluidos DECIMAL(21, 6),
    descuentos DECIMAL(21, 6),
    cargos DECIMAL(21, 6),
    anticipos DECIMAL(21, 6),
    redondeo DECIMAL(21, 6),  -- puede ser negativo (Anexo FE 1.9, numeral 5.2.3.1)
    total_pagar DECIMAL(21, 6),
    validado_dian BOOLEAN,  -- NULL = desconocido
    sha256 VARCHAR NOT NULL REFERENCES archivos_ingeridos (sha256),
    miembro VARCHAR  -- nombre del XML dentro del ZIP
);

CREATE TABLE referencias (
    cufe VARCHAR NOT NULL REFERENCES documentos (cufe),
    orden INTEGER NOT NULL,
    numero VARCHAR,
    cufe_referenciado VARCHAR,
    fecha DATE,
    PRIMARY KEY (cufe, orden)
);

CREATE TABLE impuestos (
    cufe VARCHAR NOT NULL REFERENCES documentos (cufe),
    orden INTEGER NOT NULL,
    codigo VARCHAR,
    tarifa DECIMAL(9, 3),
    base DECIMAL(21, 6),
    valor DECIMAL(21, 6),
    PRIMARY KEY (cufe, orden)
);

-- En facturas y documento soporte son autorretenciones del emisor (FE 1.9 FAT01, DS 1.1 DSAT01).
CREATE TABLE retenciones (
    cufe VARCHAR NOT NULL REFERENCES documentos (cufe),
    orden INTEGER NOT NULL,
    codigo VARCHAR,
    tarifa DECIMAL(9, 3),
    base DECIMAL(21, 6),
    valor DECIMAL(21, 6),
    PRIMARY KEY (cufe, orden)
);

CREATE TABLE lineas (
    cufe VARCHAR NOT NULL REFERENCES documentos (cufe),
    orden INTEGER NOT NULL,
    numero VARCHAR,
    descripcion VARCHAR,
    cantidad DECIMAL(21, 6),
    unidad VARCHAR,
    valor_unitario DECIMAL(21, 6),
    valor_total DECIMAL(21, 6),
    PRIMARY KEY (cufe, orden)
);

CREATE TABLE impuestos_linea (
    cufe VARCHAR NOT NULL,
    linea INTEGER NOT NULL,  -- orden de la línea en lineas
    orden INTEGER NOT NULL,
    codigo VARCHAR,
    tarifa DECIMAL(9, 3),
    base DECIMAL(21, 6),
    valor DECIMAL(21, 6),
    PRIMARY KEY (cufe, linea, orden),
    FOREIGN KEY (cufe, linea) REFERENCES lineas (cufe, orden)
);

-- Advertencias de documentos y errores de lectura (cufe NULL cuando no hubo documento).
CREATE TABLE advertencias (
    sha256 VARCHAR NOT NULL REFERENCES archivos_ingeridos (sha256),
    miembro VARCHAR,
    cufe VARCHAR,
    codigo VARCHAR NOT NULL,
    detalle VARCHAR
);
