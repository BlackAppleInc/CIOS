# Módulo: Procesamiento Automatizado de Correo

## 1. Contexto Arquitectónico
- **Objetivo:** Ingesta, parseo y extracción de datos estructurados de correos electrónicos.
- **Integración:** API de Gmail (preferido en ecosistema Google) o IMAP.
- **Orquestación:** Antigravity / [Especificar entorno, ej. Node.js/Python].

## 2. Decisiones de Diseño (Aciertos)
- **Autenticación:** [Especificar el método que funcionó, ej. OAuth2 con Refresh Tokens o Service Accounts con Domain-wide Delegation].
- **Optimización de Payload:** Extracción exclusiva del `text/plain` para minimizar el consumo de tokens cuando el texto deba ser procesado por un LLM.
- **Manejo de Eventos:** [Especificar si se usó Webhooks/PubSub vs Polling].

## 3. Errores Conocidos y Mitigaciones (Gotchas)
- **Fallo:** El parser colapsa al procesar correos tipo `multipart/alternative` o con hilos anidados complejos.
- **Solución:** Recorrido recursivo del árbol MIME (payload parts) buscando iterativamente el mimeType `text/plain` y descartando adjuntos no solicitados.
- **Fallo:** Ruido en los datos por historial de correos ("On [Date], [Name] wrote...").
- **Solución:** Implementación de regex o lógica de limpieza para truncar el cuerpo del mensaje original y descartar el historial.
- **Fallo:** Expiración silenciosa de credenciales.
- **Solución:** Middleware de validación de tokens previo a la ejecución del *fetch*.

## 4. Código Base Validado (Implementación Histórica)
*Nota para el usuario: Reemplaza este bloque con el script funcional generado previamente por Claude.*

`processing/cleaner.py`
```python
from bs4 import BeautifulSoup

from exceptions.core import ProcessingError


def extract_text_from_html(html_content: str) -> str:
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        raise ProcessingError(f"html extraction failed: {e}") from e
```

`processing/parser.py`
```python
import base64

from exceptions.core import ProcessingError
from processing.cleaner import extract_text_from_html


class EmailParser:
    __slots__ = ()

    def parse_payload(self, payload: dict) -> dict:
        result = {"plain_text": "", "html": "", "attachments": []}
        try:
            self._walk(payload, result)
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(f"payload parse failed: {e}") from e
        return self.finalize_body(result)

    def _walk(self, part: dict, result: dict) -> None:
        mime_type = part.get("mimeType", "")
        filename = part.get("filename", "")
        body = part.get("body", {})

        if filename:
            result["attachments"].append({
                "filename": filename,
                "mimeType": mime_type,
                "attachmentId": body.get("attachmentId", ""),
                "size": body.get("size", 0),
            })
        elif mime_type == "text/plain":
            data = body.get("data")
            if data:
                result["plain_text"] += self._decode(data)
        elif mime_type == "text/html":
            data = body.get("data")
            if data:
                result["html"] += self._decode(data)

        for sub_part in part.get("parts", []) or []:
            self._walk(sub_part, result)

    def _decode(self, data: str) -> str:
        try:
            return base64.urlsafe_b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")
        except Exception as e:
            raise ProcessingError(f"base64 decode failed: {e}") from e

    def finalize_body(self, parsed_data: dict) -> dict:
        if not parsed_data["plain_text"] and parsed_data["html"]:
            parsed_data["plain_text"] = extract_text_from_html(parsed_data["html"])
        return parsed_data
```