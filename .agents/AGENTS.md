# Reglas del Proyecto

## Seguridad y Privacidad (Credenciales y Entornos)
Nunca leas, imprimas, ni cites el contenido de archivos .env, credenciales, API keys, o contraseñas en tus respuestas — ni siquiera parcialmente. Si necesitas verificar longitud o formato, hazlo con una expresión que confirme solo la propiedad (ej: longitud en caracteres) sin mostrar el valor:
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(len(os.getenv('IMAP_PASSWORD', '')))"
```
Esto imprime un número, no el secreto.
