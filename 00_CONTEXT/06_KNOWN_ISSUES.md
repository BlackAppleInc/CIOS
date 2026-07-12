# Known Issues

<!-- Placeholder for future known issues -->

- The `GeminiProvider` schema translator currently handles flat OBJECT and ARRAY structures but lacks support for Pydantic's complex types including `anyOf` (nullable/Optional fields), `enum`, and `$defs` (nested models). This will cause failures if complex structured generation is requested in the future.
