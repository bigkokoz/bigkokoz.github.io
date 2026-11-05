"""
claude_lampara.py — avisa en la lámpara lo que está haciendo Claude Code.

Uso manual:
    python claude_lampara.py aviso        # Claude necesita tu respuesta (ámbar que respira)
    python claude_lampara.py trabajando   # Claude está trabajando (punto azul que sube y baja)
    python claude_lampara.py listo        # terminó (la torre se llena de verde)
    python claude_lampara.py quitar       # quita el aviso
    python claude_lampara.py modo 3       # cualquier modo del firmware (0..7)

Requisito:  pip install pyserial
Importante: el puerto serie lo puede usar UN programa a la vez. Si la página web está
conectada a la lámpara, desconéctala antes de usar los avisos de Claude.

Para conectarlo a Claude Code, agrega esto a  %USERPROFILE%\\.claude\\settings.json
(cambia la ruta a donde guardaste este archivo):

{
  "hooks": {
    "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "python C:/Users/PC/lampara/claude_lampara.py trabajando" }] }],
    "Notification":     [{ "hooks": [{ "type": "command", "command": "python C:/Users/PC/lampara/claude_lampara.py aviso" }] }],
    "Stop":             [{ "hooks": [{ "type": "command", "command": "python C:/Users/PC/lampara/claude_lampara.py listo" }] }]
  }
}
"""
import sys, time

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    sys.exit("Falta pyserial: ejecuta  pip install pyserial")

COMANDOS = {"aviso": "A", "trabajando": "W", "listo": "K", "quitar": "X"}
PISTAS = ("arduino", "ch340", "usb-serial", "usb serial", "wch", "cp210")


def buscar_puerto():
    puertos = list(list_ports.comports())
    for p in puertos:
        texto = f"{p.description} {p.manufacturer or ''}".lower()
        if any(k in texto for k in PISTAS):
            return p.device
    return puertos[0].device if puertos else None


def enviar(linea):
    puerto = buscar_puerto()
    if not puerto:
        sys.exit("No encontré la lámpara. ¿Está conectada por USB?")
    s = serial.Serial()
    s.port, s.baudrate, s.timeout = puerto, 115200, 1
    s.dtr = False            # intenta no reiniciar el Arduino al abrir el puerto
    try:
        s.open()
    except serial.SerialException:
        sys.exit(f"{puerto} está ocupado. Desconecta la página web de la lámpara.")
    time.sleep(1.8)          # por si el Arduino se reinició igual
    s.write((linea + "\n").encode())
    s.flush()
    time.sleep(0.1)
    s.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    accion = sys.argv[1].lower()
    if accion == "modo" and len(sys.argv) > 2:
        enviar("M" + sys.argv[2])
    elif accion in COMANDOS:
        enviar(COMANDOS[accion])
    else:
        sys.exit(__doc__)
