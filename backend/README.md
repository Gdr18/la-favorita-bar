# 🍻 Back end de La Favorita Bar

API REST desarrollada con **Python + Flask + MongoDB** para gestionar productos y pedidos en línea del bar _La
Favorita_.
Esta aplicación permite a usuarios con distintos roles consultar y modificar la base de datos de forma segura,
facilitando tanto la realización de pedidos por parte de los clientes como su gestión por parte del personal del bar,
entre otras funcionalidades.

<p align="center">
  <a href="https://www.youtube.com/watch?v=UmdkoXxtj_sO">
    <img src="https://img.youtube.com/vi/UmdkoXxtj_s/0.jpg" alt="Demo del proyecto">
  </a>
  <br>
  <em>Vídeo demostrativo del proyecto en YouTube</em>
</p>

---

## 🚀 Tecnologías utilizadas

- **Python**
- **Flask**
- **MongoDB (PyMongo)**
- **Pydantic** – Validación de datos
- **JWT (Flask-JWT-Extended)** – Autenticación basada en tokens
- **OAuth** – Autenticación de terceros (Google)
- **SendGrid** – Envío de correos electrónicos
- **pytest** – Testing automatizado
- **python-dotenv** – Variables de entorno

---

## ✨ Funcionalidades principales

- Registro e inicio de sesión con JWT y Google OAuth
- Gestión de productos, usuarios, pedidos y platos (crear, listar, editar, eliminar)
- Sistema de roles para restringir el acceso a ciertas acciones para garantizar la seguridad
- Envío de correos electrónicos (bienvenida y confirmación de usuario)

___

## ⚙️ Instalación local

1. Clona este repositorio:

```
git clone https://github.com/Gdr18/la_favorita_backend.git
cd la_favorita_backend
```

2. Crea y activa un entorno virtual:

```
python -m venv venv
venv\Scripts\activate
```

3. Instala las dependencias:

```
pip install -r requirements.txt
```

4. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables de entorno:

```
MONGO_DB_URI = "mongodburi"
CONFIG = config.DevelopmentConfigv (modo depuración) o config.Config
JWT_SECRET_KEY = "jwtsecretkey"
CLIENT_ID = "googleclientid"
CLIENT_SECRET = "googleclientsecret"
SECRET_KEY = "secretkey"
SENDGRID_API_KEY = "sendgridapikey"
DEFAULT_SENDER_EMAIL = "senderemail@lafavorita.com"
EMAIL_CONFIRMATION_LINK = "http://localhost:5000/auth/confirm-email/"
```

- `MONGO_DB_URI`: URI de conexión a la base de datos MongoDB.
- `CONFIG`: Configuración de la aplicación (desarrollo/producción).
- `JWT_SECRET_KEY`: Clave secreta para la autenticación JWT.
- `CLIENT_ID` y `CLIENT_SECRET`: Credenciales de OAuth para autenticación con Google.
- `SECRET_KEY`: Clave secreta para la aplicación Flask.
- `SENDGRID_API_KEY`: Clave API de SendGrid para el envío de correos electrónicos.
- `DEFAULT_SENDER_EMAIL`: Correo electrónico del remitente por defecto.
- `EMAIL_CONFIRMATION_LINK`: URL base para la confirmación de correos electrónicos.

5. Ejecuta la aplicación:

```
python run.py
```

___

## 🧪 Tests

Este proyecto incluye pruebas automáticas con pytest, pytest-mock y pytest-cov.

Para ejecutarlas:

```
python -m pytest
```

En consola aparecerá el código que ha pasado y fallado las pruebas, junto con la cobertura de cada archivo.

---

## 📓 Documentación de la API

Puedes consultar la documentación y probar todos los endpoints desde las colecciones de Postman:

🔗 [Colección de Postman Producción](https://www.postman.com/maintenance-participant-28116252/workspace/gdor-comparte/collection/26739293-8ed71c06-f67a-40b3-8b21-6e642cabcce4?action=share&creator=26739293)
🔗 [Colección de Postman Local](https://www.postman.com/maintenance-participant-28116252/workspace/gdor-comparte/collection/26739293-51b9ab63-6047-487f-a538-17276126744f?action=share&creator=26739293)

> 💡 Asegúrate de iniciar sesión primero con una cuenta de prueba para obtener un `access_token` válido.

---

## 🧪 Cuentas de prueba

Puedes iniciar sesión con las siguientes credenciales para obtener tokens JWT válidos. Estos te permitirán acceder a los
endpoints según el rol asignado:

### 👩‍💻 Developer

- Email: `developer_user@outlook.com`
- Contraseña: `Developer_user123`

### 👑 Admin

- Email: `admin_user@outlook.com`
- Contraseña: `Admin_user123`

### 🧑‍🔧 Staff

- Email: `staff_user@outlook.com`
- Contraseña: `Staff_user123`

> Los tokens de acceso son temporales. Puedes obtener uno nuevo en cualquier momento repitiendo el login.

### 👤 Cliente

El rol `cliente` se asigna automáticamente a cualquier usuario que se registre a través del endpoint de
`/auth/register`. No necesitas permisos especiales para registrarte.

### 🧾 Equivalencia de roles (internos)

| Rol (nomenclatura) | Valor en base de datos |
|--------------------|------------------------|
| `customer`         | `3`                    |
| `staff`            | `2`                    |
| `admin`            | `1`                    |
| `developer`        | `0`                    |

---

## 🔐 Acceso a endpoints por rol

Cada endpoint protegido requiere un determinado nivel de rol (`developer`, `admin`, `staff`). Estos niveles
están definidos en la lógica del backend y limitan el acceso a funciones como:

La documentación en Postman especifica, donde corresponde, qué rol es necesario.

___

## 👩‍💻 Autor

Desarrollado por **Gádor García Martínez**  
[GitHub](https://github.com/Gdr18) · [LinkedIn](https://www.linkedin.com/in/g%C3%A1dor-garc%C3%ADa-mart%C3%ADnez-99a33717b/)  

