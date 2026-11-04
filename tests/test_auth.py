from app.models import Usuario
from app.services.auth_service import AuthService

from tests.conftest import PASSWORD


def test_login_correcto(datos):
    user = AuthService.login(datos, "user1@test.es", PASSWORD)
    assert user is not None and user.id_usuario == 1


def test_login_normaliza_email(datos):
    assert AuthService.login(datos, "  USER1@test.es ", PASSWORD) is not None


def test_login_password_incorrecta(datos):
    assert AuthService.login(datos, "user1@test.es", "otra") is None


def test_login_usuario_inexistente(datos):
    assert AuthService.login(datos, "nadie@test.es", PASSWORD) is None


def test_password_en_texto_plano_no_se_acepta(datos):
    user = datos.get(Usuario, 1)
    user.contrasena_hash = "plano"
    datos.commit()
    assert AuthService.login(datos, "user1@test.es", "plano") is None


def test_cuenta_desactivada_no_puede_entrar(datos):
    datos.get(Usuario, 1).credencial_activa = False
    datos.commit()
    assert AuthService.login(datos, "user1@test.es", PASSWORD) is None


def test_cuenta_generica_de_visitante_no_puede_entrar(datos):
    assert AuthService.login(datos, "visitante@menule.com", PASSWORD) is None
