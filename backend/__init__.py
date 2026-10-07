"""Backend FastAPI local del reto CIMAT.

Envuelve `nucleo.analizar()` sin reescribirlo: recibe las resonancias, las analiza en
segundo plano (una a la vez, porque la CPU no da para mas) e informa el avance. Pensado
para correr en 127.0.0.1 y abrirse en el navegador; las imagenes nunca salen del equipo.

    from backend import crear_app
    app = crear_app()
"""

from .app import crear_app  # noqa: F401
