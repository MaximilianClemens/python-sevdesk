"""
sevDesk API Code Generator

Generiert Python Models und Controllers aus der OpenAPI-Spezifikation.
Unterstuetzt Patches fuer Korrekturen an der offiziellen Spec.
"""

import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

OPENAPI_FILE = Path("openapi.yaml")
PATCHES_FILE = Path("generator/patches.yaml")
MODELS_DIR = Path("sevdesk/models")
CONVERTERS_DIR = Path("sevdesk/converters")
CONTROLLERS_DIR = Path("sevdesk/controllers")

# Python reservierte Woerter
PYTHON_KEYWORDS = {
    'from', 'to', 'import', 'class', 'def', 'return', 'if', 'else', 'elif',
    'for', 'while', 'break', 'continue', 'pass', 'try', 'except', 'finally',
    'raise', 'with', 'as', 'lambda', 'yield', 'assert', 'global', 'nonlocal',
    'del', 'and', 'or', 'not', 'in', 'is', 'None', 'True', 'False', 'type',
    'object', 'id', 'list', 'dict', 'set', 'tuple', 'str', 'int', 'float',
    'bool', 'bytes', 'bytearray'
}

# Typ-Mapping OpenAPI -> Python
TYPE_MAPPING = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "object": "dict",
}


def load_patches() -> dict:
    """Laedt Patches aus patches.yaml"""
    if not PATCHES_FILE.exists():
        return {}
    return yaml.safe_load(PATCHES_FILE.read_text()) or {}


def apply_patches(schemas: dict, patches: dict) -> dict:
    """Wendet Patches auf die Schemas an"""
    patched_count = 0
    for schema_name, prop_patches in patches.items():
        # Suche Schema (mit und ohne Model_ Prefix)
        target_schema = None
        for key in [schema_name, f"Model_{schema_name}"]:
            if key in schemas:
                target_schema = schemas[key]
                break

        if not target_schema:
            print(f"  Warnung: Schema '{schema_name}' nicht gefunden fuer Patch")
            continue

        properties = target_schema.get("properties", {})
        for prop_name, patch in prop_patches.items():
            if prop_name in properties:
                # Patch anwenden
                if "type" in patch:
                    old_type = properties[prop_name].get("type", "?")
                    properties[prop_name]["type"] = patch["type"]
                    print(f"  Patch: {schema_name}.{prop_name}: {old_type} -> {patch['type']}")
                    patched_count += 1
                if "description" in patch:
                    properties[prop_name]["description"] = patch["description"]
            else:
                print(f"  Warnung: Property '{prop_name}' nicht in {schema_name}")

    return schemas


def sanitize_field_name(name: str) -> str:
    """Macht aus Python Keywords sichere Feldnamen"""
    if name in PYTHON_KEYWORDS:
        return f"{name}_"
    return name


def sanitize_description(desc: str) -> str:
    """Bereinigt Description fuer Python-Strings"""
    if not desc:
        return ""
    # Newlines und problematische Zeichen entfernen/ersetzen
    desc = desc.replace('\n', ' ').replace('\r', ' ')
    desc = desc.replace('"', "'")
    desc = desc.replace('\\', '\\\\')
    # Mehrfache Leerzeichen zusammenfassen
    import re
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc


def sanitize_param_name(name: str) -> str:
    """Macht aus 'customFieldSetting[id]' -> 'customFieldSetting_id'"""
    sanitized = name.replace("[", "_").replace("]", "")
    return sanitize_field_name(sanitized)


def to_pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def first_up(name: str) -> str:
    return name[0].upper() + name[1:]


def load_openapi() -> dict:
    """Laedt die komplette OpenAPI Spec"""
    return yaml.safe_load(OPENAPI_FILE.read_text())


def resolve_ref(ref: str) -> str:
    """z. B. '#/components/schemas/Model_Contact' -> 'Contact'"""
    if not ref:
        return None
    name = ref.split("/")[-1]
    name = name.replace("Model_", "")
    return first_up(name)


def extract_return_type(responses: dict) -> tuple:
    """Extrahiert den Return-Type aus den Responses"""
    if not responses:
        return None, False

    # Pruefe 200/201 Response
    success_response = responses.get("200") or responses.get("201")
    if not success_response:
        return None, False

    content = success_response.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})

    # Direkte Referenz
    if "$ref" in schema:
        return resolve_ref(schema["$ref"]), False

    # Pruefe auf properties (z.B. mit "objects" field)
    properties = schema.get("properties", {})
    if properties:
        # Suche nach array-fields in properties (z.B. "objects")
        for prop_name, prop_schema in properties.items():
            if prop_schema.get("type") == "array":
                items = prop_schema.get("items", {})
                if "$ref" in items:
                    return resolve_ref(items["$ref"]), True

        # Fallback: erste Referenz in properties
        for prop_name, prop_schema in properties.items():
            if "$ref" in prop_schema:
                return resolve_ref(prop_schema["$ref"]), False

    # Array von Objekten (direkt)
    if schema.get("type") == "array":
        items = schema.get("items", {})
        if "$ref" in items:
            return resolve_ref(items["$ref"]), True

    return None, False


def transform_schema(name: str, schema: dict):
    """Transformiert ein OpenAPI Schema in ein Model-Dict"""
    required = schema.get("required", [])
    properties = []
    converters = []
    needs_optional = False
    needs_any = False

    for prop_name, prop in schema.get("properties", {}).items():
        safe_prop_name = sanitize_field_name(prop_name)
        t = TYPE_MAPPING.get(prop.get("type", "string"), "Any")
        description = sanitize_description(prop.get("description", ""))

        # Pruefe ob Any verwendet wird
        if t == "Any":
            needs_any = True

        nullable = prop.get("nullable", False)
        is_required = prop_name in required
        submodel = None

        if prop.get("type") == "object" and "properties" in prop:
            submodel = first_up(safe_prop_name)
            t = submodel
            sub_required = prop.get("required", [])
            sub_properties = []
            sub_needs_any = False

            for n, p in prop.get("properties", {}).items():
                safe_sub_name = sanitize_field_name(n)
                sub_type = TYPE_MAPPING.get(p.get("type", "string"), "Any")
                if sub_type == "Any":
                    sub_needs_any = True
                sub_properties.append({
                    "name": safe_sub_name,
                    "original_name": n,
                    "type": f"Optional[{sub_type}]" if n not in sub_required else sub_type,
                    "default": None if n in sub_required else "None",
                    "description": sanitize_description(p.get("description", "")),
                })

            converters.append({
                "class_name": submodel,
                "properties": sub_properties,
                "needs_optional": len(sub_required) < len(prop.get("properties", {})),
                "needs_any": sub_needs_any
            })

        # Wenn nicht required oder nullable, dann Optional
        if not is_required or nullable:
            t = f"Optional[{t}]"
            needs_optional = True

        default = None if is_required else "None"

        properties.append({
            "name": safe_prop_name,
            "original_name": prop_name,
            "type": t,
            "default": default,
            "submodel": submodel,
            "description": description,
        })

    class_name = name.lstrip('Model_')
    class_name = first_up(class_name)

    # Schema-Level Description
    schema_description = sanitize_description(schema.get("description", ""))

    return {
        "class_name": class_name,
        "properties": properties,
        "converters": converters,
        "needs_optional": needs_optional,
        "needs_any": needs_any,
        "description": schema_description,
    }


def transform_paths(paths: dict):
    """Transformiert OpenAPI Paths in Controller-Dicts"""
    controllers = {}
    for path, methods in paths.items():
        for method, details in methods.items():
            tag = details.get("tags", ["Default"])[0]
            operation_id = details.get("operationId", f"{method}_{path.replace('/', '_')}")
            parameters = details.get("parameters", [])
            request_body = details.get("requestBody", {})
            summary = details.get("summary", "")
            description = details.get("description", "")
            responses = details.get("responses", {})

            if tag not in controllers:
                controllers[tag] = []

            controllers[tag].append({
                "method": method.upper(),
                "path": path,
                "function": operation_id,
                "parameters": parameters,
                "requestBody": request_body,
                "summary": summary,
                "description": description,
                "responses": responses
            })
    return controllers


def generate_models(openapi_spec: dict, env: Environment, patches: dict):
    """Generiert alle Models und Converters"""
    schemas = openapi_spec.get("components", {}).get("schemas", {})

    # Patches anwenden
    if patches:
        print("\nWende Patches an...")
        schemas = apply_patches(schemas, patches)

    model_template = env.get_template("model_template.jinja")
    converter_template = env.get_template("converter_template.jinja")

    print("\nGeneriere Models...")
    for schema_name, schema in schemas.items():
        model = transform_schema(schema_name, schema)

        content = model_template.render(model=model)
        file_path = MODELS_DIR / f"{model['class_name'].lower()}.py"
        file_path.write_text(content)
        print(f"  Model: {file_path}")

        for conv in model["converters"]:
            conv_content = converter_template.render(model=conv)
            conv_path = CONVERTERS_DIR / f"{conv['class_name'].lower()}.py"
            conv_path.write_text(conv_content)
            print(f"    Converter: {conv_path}")


def generate_controllers(openapi_spec: dict, env: Environment):
    """Generiert alle Controllers"""
    paths = openapi_spec.get("paths", {})
    controllers = transform_paths(paths)
    controller_template = env.get_template("controller_template.jinja")

    print("\nGeneriere Controllers...")
    for tag, operations in controllers.items():
        imports = set()
        needs_optional = False
        needs_any = False
        funcs = []

        for op in operations:
            # Pruefe RequestBody auf Referenzen
            model_ref = None
            if "$ref" in str(op.get("requestBody", {})):
                ref = op["requestBody"]["content"]["application/json"]["schema"]["$ref"]
                model_ref = resolve_ref(ref)
                imports.add(model_ref)

            # Parameter pruefen
            params = []
            for p in op.get("parameters", []):
                param_required = p.get("required", False)
                param_name = sanitize_param_name(p["name"])
                param_original_name = p["name"]
                param_description = sanitize_description(p.get("description", ""))

                if "$ref" in p.get("schema", {}):
                    ref = p["schema"]["$ref"]
                    model_name = resolve_ref(ref)
                    imports.add(model_name)
                    param_type = model_name if param_required else f"Optional[{model_name}]"
                    if not param_required:
                        needs_optional = True
                    params.append({
                        "name": param_name,
                        "original_name": param_original_name,
                        "type": param_type,
                        "required": param_required,
                        "description": param_description,
                    })
                else:
                    t = TYPE_MAPPING.get(p.get("schema", {}).get("type", "string"), "Any")
                    if t == "Any":
                        needs_any = True
                    param_type = t if param_required else f"Optional[{t}]"
                    if not param_required:
                        needs_optional = True
                    params.append({
                        "name": param_name,
                        "original_name": param_original_name,
                        "type": param_type,
                        "required": param_required,
                        "description": param_description,
                    })

            # Sortiere Parameter: required zuerst, dann optional
            params.sort(key=lambda p: (not p["required"], p["name"]))

            # Return Type extrahieren
            return_model, is_list = extract_return_type(op.get("responses", {}))
            if return_model:
                imports.add(return_model)
                if is_list:
                    return_type = f"list[{return_model}]"
                else:
                    return_type = return_model
            else:
                return_type = None

            funcs.append({
                "name": op["function"],
                "method": op["method"],
                "path": op["path"],
                "summary": op["summary"],
                "description": op.get("description", ""),
                "params": params,
                "body_model": model_ref,
                "return_type": return_type,
            })

        ctrl_code = controller_template.render(
            controller_name=tag,
            functions=funcs,
            imports=sorted(imports),
            needs_optional=needs_optional,
            needs_any=needs_any,
        )
        ctrl_path = CONTROLLERS_DIR / f"{tag.lower()}_controller.py"
        ctrl_path.write_text(ctrl_code)
        print(f"  Controller: {ctrl_path}")


def main():
    print("sevDesk API Code Generator")
    print("=" * 40)

    # Verzeichnisse erstellen
    MODELS_DIR.mkdir(exist_ok=True)
    CONVERTERS_DIR.mkdir(exist_ok=True)
    CONTROLLERS_DIR.mkdir(exist_ok=True)

    # Jinja Environment
    env = Environment(loader=FileSystemLoader("./generator"), trim_blocks=True, lstrip_blocks=True)

    # Patches laden
    patches = load_patches()
    if patches:
        print(f"Patches geladen: {len(patches)} Schema(s)")

    # OpenAPI Spec laden
    openapi_spec = load_openapi()

    # Generierung
    generate_models(openapi_spec, env, patches)
    generate_controllers(openapi_spec, env)

    print("\nFertig!")


if __name__ == "__main__":
    main()
