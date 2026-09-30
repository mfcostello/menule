# MenULE 🍽️

<p align="center">
  <img src="assets/favicon.ico" alt="Logo MenULE" width="120"/>
</p>

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Reflex](https://img.shields.io/badge/Framework-Reflex-2B2D42?logo=react)
![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy_2.0-red?logo=sqlite)
![MySQL](https://img.shields.io/badge/Database-MySQL-blue?logo=mysql)
![License](https://img.shields.io/badge/Licencia-MIT-green)

**MenULE** es una aplicación web full-stack desarrollada con **Reflex** y **Python** para la gestión integral de un comedor universitario. Permite administrar usuarios por roles, gestionar menús, procesar reservas, reportar incidencias y controlar los pagos de forma fluida y reactiva.

> **Nota de versión:** Este proyecto es una evolución y ampliación web completa a partir de una primera versión de escritorio. La arquitectura ha sido migrada íntegramente a una stack web reactiva en Python.

---

## 📋 Índice
- [Características y Roles](#-características-y-roles)
- [Arquitectura y Tecnologías](#-arquitectura-y-tecnologías)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Ejecución](#-ejecución)
- [Autoría](#-autoría)

---

## 👥 Características y Roles

El sistema gestiona de forma diferenciada el acceso según el rol detectado o registrado:

| Rol | Funcionalidades Principales | Dominio de Correo |
| :--- | :--- | :--- |
| **Estudiante** | Reserva de menús, recarga de saldo, consulta de historial e incidencias | `@estudiantes.unileon.es` |
| **Profesor** | Reserva de menús con tarifas reducidas, gestión de cuenta | `@unileon.es` |
| **Visitante** | Pago puntual y reservas rápidas sin cuenta de saldo | General (`@gmail.com`, etc.) |
| **Personal Comedor** | Procesamiento de pedidos diarios, actualización de stock y menús | `@comedor.unileon.es` |
| **Administrador** | Panel global de gestión de usuarios, auditoría y métricas | `@menule.com` |

---

## 🛠️ Arquitectura y Tecnologías

La aplicación adopta una arquitectura web reactiva basada en estados (*State Management*) y aislamiento de persistencia mediante ORM:

* **Frontend & Backend (Full-stack):** [Reflex](https://reflex.dev) — Componentes de UI reactivos y backend Python unificado mediante WebSocket.
* **ORM & Base de Datos:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) sobre **MySQL** / MariaDB.
* **Seguridad & Autenticación:** [Bcrypt](https://pypi.org/project/bcrypt/) para hashing seguro de contraseñas y [Pydantic](https://docs.pydantic.dev/) para validación de schemas.
* **Gestión de Entorno:** [python-dotenv](https://pypi.org/project/python-dotenv/) para carga de variables de entorno.

---

## 📂 Estructura del Proyecto

```text
menule/
├── app/                        # Aplicación principal Reflex
│   ├── components/             # Componentes de UI reutilizables (módulos, modales, navbars)
│   ├── pages/                  # Vistas/Rutas de la aplicación (Login, Dashboard, Menús, etc.)
│   ├── states/                 # Lógica de estado reactivo y eventos (Auth, Reservas, Admin)
│   ├── database.py             # Configuración de conexión con SQLAlchemy
│   ├── models.py               # Modelos/Entidades de la base de datos
│   └── app.py                  # Punto de entrada y enrutado de Reflex
├── assets/                     # Recursos estáticos (imágenes, favicons, CSS)
├── rxconfig.py                 # Archivo de configuración de Reflex
├── .env.example                # Plantilla de variables de entorno
├── requirements.txt            # Dependencias del proyecto
└── README.md                   # Documentación principal