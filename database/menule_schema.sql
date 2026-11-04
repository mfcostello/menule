-- -----------------------------------------------------
-- MENULE: Estructura de base de datos
-- Compatible con MySQL 8.0+
-- -----------------------------------------------------
-- Instrucciones:
-- 1. Ejecuta este script en tu gestor MySQL para crear el esquema completo.
-- 2. Incluye tablas, claves foráneas, índices, vistas y datos iniciales.
-- -----------------------------------------------------

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

-- Crear la base de datos y seleccionarla
CREATE DATABASE IF NOT EXISTS menule;
USE menule;

-- Tabla principal de usuarios
CREATE TABLE IF NOT EXISTS Usuarios (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    dni VARCHAR(20) UNIQUE,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    fecha_alta DATE,
    credencial_activa BOOLEAN DEFAULT TRUE,
    tipo ENUM('estudiante', 'profesor', 'administrador', 'personal_comedor', 'visitante') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de estudiantes (cada estudiante es también un usuario con monedero y TUI)
CREATE TABLE IF NOT EXISTS Estudiantes (
    id_usuario INT PRIMARY KEY,
    grado_academico VARCHAR(100),
    tui_numero VARCHAR(30) UNIQUE,
    saldo DECIMAL(10,2) DEFAULT 0.00,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de profesores (cada profesor es también un usuario con monedero y TUI)
CREATE TABLE IF NOT EXISTS Profesores (
    id_usuario INT PRIMARY KEY,
    grado_academico VARCHAR(100),
    tui_numero VARCHAR(30) UNIQUE,
    saldo DECIMAL(10,2) DEFAULT 0.00,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de personal de comedor (cada miembro es también un usuario)
CREATE TABLE IF NOT EXISTS PersonalComedor (
    id_usuario INT PRIMARY KEY,
    fecha_contratacion DATE,
    especialidad VARCHAR(100),
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla de platos disponibles en el catálogo
CREATE TABLE IF NOT EXISTS Platos (
    id_plato INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    tipo VARCHAR(50),
    alergenos VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Menús ofrecidos por fecha y servicio
CREATE TABLE IF NOT EXISTS Menus (
    id_menu INT PRIMARY KEY AUTO_INCREMENT,
    fecha DATE NOT NULL,
    tipo ENUM('desayuno', 'almuerzo', 'cena') NOT NULL,
    max_reservas INT DEFAULT 150,
    disponible BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Relación muchos a muchos entre Menús y Platos ofrecidos
CREATE TABLE IF NOT EXISTS MenuPlatos (
    id_menu INT NOT NULL,
    id_plato INT NOT NULL,
    PRIMARY KEY (id_menu, id_plato),
    FOREIGN KEY (id_menu) REFERENCES Menus(id_menu) ON DELETE CASCADE,
    FOREIGN KEY (id_plato) REFERENCES Platos(id_plato) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Reservas realizadas por usuarios para un menú
CREATE TABLE IF NOT EXISTS Reservas (
    id_reserva INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    id_menu INT NOT NULL,
    fecha_reserva DATETIME NOT NULL,
    estado ENUM('pendiente', 'confirmada', 'cancelada', 'recogida') DEFAULT 'pendiente',
    estado_bit TINYINT(1) DEFAULT 0,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_menu) REFERENCES Menus(id_menu) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Platos específicos seleccionados en una reserva (1º, 2º, postre)
CREATE TABLE IF NOT EXISTS ReservaPlatos (
    id_reserva INT NOT NULL,
    id_plato INT NOT NULL,
    PRIMARY KEY (id_reserva, id_plato),
    FOREIGN KEY (id_reserva) REFERENCES Reservas(id_reserva) ON DELETE CASCADE,
    FOREIGN KEY (id_plato) REFERENCES Platos(id_plato) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Pagos y transacciones realizadas
CREATE TABLE IF NOT EXISTS Pagos (
    id_pago INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    id_reserva INT NULL,
    monto DECIMAL(10,2) NOT NULL,
    metodo ENUM('tui', 'bono', 'tarjeta', 'efectivo') NOT NULL,
    fecha_pago DATETIME NOT NULL,
    descuento DECIMAL(10,2) DEFAULT 0.00,
    estado ENUM('pendiente', 'completado', 'fallido', 'reembolsado') DEFAULT 'pendiente',
    correo VARCHAR(150),
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_reserva) REFERENCES Reservas(id_reserva) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Registro de incidencias (con campo destino para enrutado cocina/administración)
CREATE TABLE IF NOT EXISTS Incidencias (
    id_incidencia INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NULL,
    id_responsable INT NULL,
    titulo VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    numero_seguimiento VARCHAR(50), 
    fecha_reporte DATETIME NOT NULL,
    estado ENUM('abierta', 'en_proceso', 'resuelta', 'cerrada') DEFAULT 'abierta',
    prioridad ENUM('baja', 'media', 'alta', 'critica') DEFAULT 'media',
    destino ENUM('cocina', 'administracion') NOT NULL DEFAULT 'cocina',
    fecha_resolucion DATETIME NULL,
    solucion TEXT NULL,
    FOREIGN KEY (id_usuario) REFERENCES Usuarios(id_usuario) ON DELETE SET NULL,
    FOREIGN KEY (id_responsable) REFERENCES Usuarios(id_usuario) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Ingredientes para el control de inventario de cocina
CREATE TABLE IF NOT EXISTS Ingredientes (
    id_ingrediente INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    unidad_medida VARCHAR(20) DEFAULT 'Kg',
    stock_actual DECIMAL(10,2) DEFAULT 0.00,
    stock_minimo DECIMAL(10,2) DEFAULT 0.00,
    alergeno BOOLEAN DEFAULT FALSE,
    tipo_alergeno VARCHAR(50) DEFAULT 'Ninguno'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Índices para optimizar rendimiento de consultas frecuentes
CREATE INDEX idx_usuario_email ON Usuarios(email);
CREATE INDEX idx_usuario_tipo ON Usuarios(tipo);
CREATE INDEX idx_menu_fecha ON Menus(fecha);
CREATE INDEX idx_reserva_usuario ON Reservas(id_usuario);
CREATE INDEX idx_reserva_menu ON Reservas(id_menu);
CREATE INDEX idx_reserva_estado ON Reservas(estado);
CREATE INDEX idx_pago_reserva ON Pagos(id_reserva);
CREATE INDEX idx_pago_usuario ON Pagos(id_usuario);
CREATE INDEX idx_incidencia_estado ON Incidencias(estado);
CREATE INDEX idx_incidencia_destino ON Incidencias(destino);
CREATE INDEX idx_ingrediente_stock ON Ingredientes(stock_actual, stock_minimo);

-- -----------------------------------------------------
-- Vistas analíticas y de soporte
-- -----------------------------------------------------

-- Menús disponibles y número de reservas confirmadas
CREATE OR REPLACE VIEW VistaMenusDisponibles AS
SELECT m.*, COUNT(r.id_reserva) AS reservas_actuales
FROM Menus m
LEFT JOIN Reservas r ON m.id_menu = r.id_menu AND r.estado = 'confirmada'
WHERE m.disponible = TRUE
GROUP BY m.id_menu;

-- Ingredientes con stock crítico (por debajo o igual al mínimo)
CREATE OR REPLACE VIEW VistaStockCritico AS
SELECT i.*, (i.stock_actual <= i.stock_minimo) AS bajo_stock
FROM Ingredientes i
WHERE i.stock_actual <= i.stock_minimo;

-- Estadísticas diarias de reservas, ingresos y platos vendidos
CREATE OR REPLACE VIEW VistaEstadisticasDiarias AS
-- Ventas y platos se agregan por separado y luego se unen por fecha: unir
-- directamente Pagos con ReservaPlatos repetiría cada pago una vez por plato
-- (x3 en un menú completo). Compatible con ONLY_FULL_GROUP_BY.
SELECT
    v.fecha,
    v.total_reservas,
    v.ingresos,
    pv.platos_vendidos
FROM (
    SELECT
        DATE(r.fecha_reserva) AS fecha,
        COUNT(DISTINCT r.id_reserva) AS total_reservas,
        SUM(p.monto) AS ingresos
    FROM Reservas r
    JOIN Pagos p ON r.id_reserva = p.id_reserva AND p.estado = 'completado'
    WHERE r.estado <> 'cancelada'
    GROUP BY DATE(r.fecha_reserva)
) v
LEFT JOIN (
    SELECT
        DATE(r.fecha_reserva) AS fecha,
        GROUP_CONCAT(DISTINCT rp.id_plato) AS platos_vendidos
    FROM Reservas r
    JOIN ReservaPlatos rp ON r.id_reserva = rp.id_reserva
    WHERE r.estado <> 'cancelada'
    GROUP BY DATE(r.fecha_reserva)
) pv ON pv.fecha = v.fecha;

-- -----------------------------------------------------
-- Datos Semilla (Usuarios preconfigurados)
-- -----------------------------------------------------

-- Usuario administrador por defecto (contraseña: admin1234)
INSERT INTO Usuarios (
    id_usuario, dni, nombre, apellido, email, contrasena_hash, telefono, fecha_alta, credencial_activa, tipo
) VALUES (
    1, '00000000A', 'Admin', 'Principal', 'admin@menule.com',
    '$2b$12$eU7/AaNLbEWybmHMM5pI1OsEPg95Bm/V2e0KZZ3fTR7FGqZUo1SpK',
    '600000000', CURDATE(), TRUE, 'administrador'
) ON DUPLICATE KEY UPDATE nombre='Admin';

-- Usuario genérico reservado para visitantes anónimos (id_usuario = 0)
INSERT INTO Usuarios (
    id_usuario, dni, nombre, apellido, email, contrasena_hash, telefono, fecha_alta, credencial_activa, tipo 
) VALUES (
    0, '00000000B', 'Visitante', 'Principal', 'visitante@menule.com',
    '$2b$12$eU7/AaNLbEWybmHMM5pI1OsEPg95Bm/V2e0KZZ3fTR7FGqZUo1SpK',
    '600000000', CURDATE(), TRUE, 'visitante'
) ON DUPLICATE KEY UPDATE nombre='Visitante';
