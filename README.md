# Tres-Bashers para Android (Ported by Juanmote)

Parche para convertir **tu copia de la APK oficial de Android de Tres-Bashers** (de [ondydev](https://ondydev.itch.io/tres-bashers)) en una versión pensada para consolas Android (Odin 3 Max, Retroid Pocket Classic, Rotate…) y móviles.

**Este repositorio no contiene el juego.** Ni gráficos, ni sonidos, ni su código. Solo contiene las diferencias y las herramientas para aplicarlas sobre el archivo que tú ya tienes. Necesitas tener el juego (APK oficial) para poder usarlo.

## Qué añade

- Traducción completa al **castellano** (con acentos, ¿? y ¡!), con selector CASTELLANO / ENGLISH en opciones. Menús de pausa y controles en ambos idiomas.
- **Exportar / importar partida** a un archivo `TresBashers_N.sav` (carpeta Download). Requiere dar a la app "Acceso a todos los archivos".
- **Controles táctiles propios**, en horizontal y a los lados de la pantalla (cruceta a la izquierda; saltar, golpe, luz y arma a la derecha; pausa arriba). Modo AUTO / FORZAR SÍ / FORZAR NO; se ocultan solos al usar un mando.
- Pantalla forzada en **horizontal**.
- Pantalla cuadrada con marcos laterales (se recuerdan las opciones).
- Mandos: salir de la pantalla de controles, manejar con mando todos los botones, disposición Nintendo por defecto (B golpear, A saltar, Y linterna, X arma).
- Modo Jerry desbloqueado y menú de cheats (invencible, colores, armas, mapa y radar).
- "Ported by Juanmote" junto a la versión, ajustes de menús y logros pulidos, icono nuevo.

## Qué necesitas

1. **La APK oficial de Tres-Bashers para Android** (descárgala de la página del juego). Los parches están hechos para esa versión concreta; si la tuya es distinta, el programa te avisará y se negará a continuar.
2. **Python 3.8 o superior** (python.org). En Windows, marca "Add Python to PATH" al instalar.
3. **Java** (para firmar la APK). Cualquier JRE/JDK 11 o superior vale (por ejemplo Temurin).
4. Dos librerías de Python. En una terminal: `python -m pip install pillow numpy`
5. Internet la primera vez: se descargan solas las herramientas [UndertaleModTool CLI](https://github.com/UnderminersTeam/UndertaleModTool) y [uber-apk-signer](https://github.com/patrickfav/uber-apk-signer).

## Cómo usarlo

1. Descarga este repositorio (botón verde **Code → Download ZIP**) y descomprímelo.
2. Copia tu APK oficial dentro de esa carpeta (por ejemplo como `Tres-Bashers.apk`).
3. Abre una terminal en la carpeta y ejecuta:

   ```
   python build.py Tres-Bashers.apk
   ```

4. Tarda unos minutos. Al terminar tendrás **`Tres-Bashers_1.2.4_ES.apk`**, ya firmada. Cópiala al móvil o consola e instálala.

Notas:
- La primera vez se crea una clave de firma propia en `mi_clave/`. **Guárdala**: si la pierdes, para actualizar tendrás que desinstalar la app (y perderás la partida; usa antes *exportar partida*).
- Si ya tenías instalada otra versión del juego firmada con otra clave (por ejemplo la APK oficial), Android no la deja actualizar: desinstálala primero.
- Para importar/exportar partida: Ajustes de Android → Aplicaciones → Tres-Bashers → Permisos → *Acceso a todos los archivos* → permitir.

## Cómo funciona (para curiosos)

`build.py` extrae el `game.droid` de tu APK, vuelca su código con UndertaleModCli y le aplica las diferencias de `patch/code.json` (guardadas como "conservar N líneas / insertar estas líneas", sin copiar código original). Después dibuja los sprites en castellano a partir de tus propios gráficos, añade los glifos acentuados a las fuentes (`patch/fonts.json`, `patch/pixels.json`), reconstruye `game.droid`, modifica el manifiesto de Android (permiso de archivos, orientación, versión), cambia los iconos y firma.

```
build.py            programa principal
patch/              diferencias de código, glifos y píxeles de fuentes
tools/              scripts auxiliares (UndertaleModCli, sprites, manifiesto)
assets/res/         iconos de la app
```

## Créditos y aviso

- **Tres-Bashers** es obra de **ondydev**. Apoya al autor: https://ondydev.itch.io/tres-bashers
- Herramientas: [UndertaleModTool](https://github.com/UnderminersTeam/UndertaleModTool) y [uber-apk-signer](https://github.com/patrickfav/uber-apk-signer).
- Port y parches: Juanmote. Proyecto de aficionado sin ánimo de lucro, sin relación con el autor del juego.
- Si ondydev pide que se retire este repositorio, se retirará.

Licencia del código de este repositorio: MIT (ver `LICENSE`).
