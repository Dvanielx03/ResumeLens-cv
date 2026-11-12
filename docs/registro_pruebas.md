# Verificación de ResumeLens

Fecha: **11 de noviembre de 2026, America/Bogota**. Pruebas con datos ficticios. Aplicación servida por Docker en `http://localhost:8503`.

## Python

```text
Windows / Python 3.12.15:
python -m pytest -q
25 passed in 5.55s

Linux / imagen python:3.12-slim:
docker build --target test -t resumelens-tests .
docker run --rm resumelens-tests
25 passed in 0.73s

ruff check app tests scripts
All checks passed!
```

Cobertura funcional: pesos y renormalización; límites del contrato; PDF/TXT inválidos; PDF sin texto; tamaño máximo; extracción del PDF de ejemplo; cadena LangChain con modelo falso; cita inventada; reparación única; 0/1/2 errores transitorios; agotamiento de intentos; autenticación y cuota diaria no reintentables; entrada inválida sin invocar modelo; informe descargable.

## Navegador

Requiere [Playwright CLI](https://github.com/microsoft/playwright-cli), Chromium/Chrome instalado y el contenedor iniciado. Crear `docs/evidencias` y `output` si se ejecuta desde una copia sin esas carpetas.

```bash
playwright-cli -s=resumelens open http://localhost:8503 --browser=chrome
playwright-cli -s=resumelens run-code --filename=scripts/auditar_interfaz.js
```

Resultado final: **PASS, 9 comprobaciones, erroresJavaScript: []**.

1. Entradas vacías: mensaje de error, sin puntuación.
2. Ejemplo ficticio: 89%, desglose y cita literal visibles.
3. Descarga del informe Markdown y nombre correctos. Se comprobó también su contenido guardado en `output/`.
4. Cambiar el puesto oculta el resultado obsoleto.
5. PDF real de ejemplo extraído; consentimiento obligatorio para la ruta del proveedor.
6. Sin API key: mensaje claro, sin resultado alternativo.
7. TXT insuficiente rechazado antes de llamar a IA.
8. Viewport 390×844: sin desbordamiento horizontal ni recorte del porcentaje, tras terminar el cierre automático de la barra lateral.
9. Limpiar reinicia documento, puesto y resultado; sin excepciones JavaScript de página.

Escritorio: 1440×1080. La emulación de 390 px **no sustituye** una prueba en celular físico. Se revisaron visualmente las capturas, no solo los selectores.

Durante la creación de la auditoría se ajustaron esperas tras el rerun de Limpiar y se pulsó la etiqueta visible del checkbox nativo de Streamlit, cuyo input está cubierto por su label. La primera captura móvil se descartó porque se tomó durante la transición de la barra lateral. El script final espera a su cierre y comprueba los límites del porcentaje.

## Docker y proveedores

`resumelens-app`: estado `healthy`; usuario `resumelens`, no root. La imagen no contiene `.env`, Secrets ni datos personales. Se adaptó el Dockerfile de Garaje a una única aplicación; no se reutilizaron contenedores ni puertos del sitio existente.

Se construyeron los adaptadores `ChatGoogleGenerativeAI` y `ChatOpenAI` con credenciales ficticias, sin invocar sus APIs.

**Pendiente:** evaluación generativa con una API key y cuota reales. No había claves configuradas. El 89% de las capturas es una salida predefinida del ejemplo, validada contra el CV ficticio; no es una medición de calidad del modelo ni una respuesta de un proveedor real.

## Evidencias

- [Inicio](evidencias/01-inicio.png)
- [Resultado de ejemplo](evidencias/02-resultado.png)
- [PDF y validación de clave](evidencias/03-pdf-y-validacion.png)
- [Viewport móvil](evidencias/04-movil.png)
