import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

OPENAPI_FILE = Path("openapi.yaml")
PATHS_FILE = Path("openapi.yaml")
MODELS_DIR = Path("sevdesk/models")
CONVERTERS_DIR = Path("sevdesk/converters")
CONTROLLERS_DIR = Path("sevdesk/controllers")

# Typ-Mapping OpenAPI -> Python
TYPE_MAPPING = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "object": "dict",
}

def sanitize_param_name(name: str) -> str:
    """Macht aus 'customFieldSetting[id]' -> 'customFieldSetting_id'"""
    return name.replace("[", "_").replace("]", "")

def to_pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))

def first_up(name: str) -> str:
    return name[0].upper() + name[1:]

def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())

def load_schemas() -> dict:
    data = load_yaml(OPENAPI_FILE)
    return data.get("components", {}).get("schemas", {})

def transform_schema(name: str, schema: dict):
    required = schema.get("required", [])
    properties = []
    converters = []

    for prop_name, prop in schema.get("properties", {}).items():
        t = TYPE_MAPPING.get(prop.get("type", "string"), "Any")
        nullable = prop.get("nullable", False)
        submodel = None

        if prop.get("type") == "object" and "properties" in prop:
            submodel = first_up(prop_name)
            t = submodel
            converters.append({
                "class_name": submodel,
                "properties": [
                    {
                        "name": n,
                        "type": TYPE_MAPPING.get(p.get("type", "string"), "Any"),
                        "default": None if n in prop.get("required", []) else "None"
                    }
                    for n, p in prop.get("properties", {}).items()
                ]
            })

        if nullable:
            t = f"Optional[{t}]"

        default = None if prop_name in required else "None"

        properties.append(
            {
                "name": prop_name,
                "type": t,
                "default": default,
                "submodel": submodel,
            }
        )

    class_name = name.lstrip('Model_')
    class_name = first_up(class_name)

    return {
        "class_name": class_name,
        "properties": properties,
        "converters": converters,
    }

def transform_paths(paths: dict):
    controllers = {}
    for path, methods in paths.items():
        for method, details in methods.items():
            tag = details.get("tags", ["Default"])[0]
            operation_id = details.get("operationId", f"{method}_{path.replace('/', '_')}")
            parameters = details.get("parameters", [])
            request_body = details.get("requestBody", {})
            summary = details.get("summary", "")
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
                "responses": responses
            })
    return controllers

def resolve_ref(ref: str) -> str:
    """z. B. '#/components/schemas/Model_Contact' → 'Contact'"""
    if not ref:
        return None
    name = ref.split("/")[-1]
    name = name.replace("Model_", "")
    return first_up(name)

def extract_return_type(responses: dict) -> tuple:
    """Extrahiert den Return-Type aus den Responses"""
    if not responses:
        return None, False
    
    # Prüfe 200/201 Response
    success_response = responses.get("200") or responses.get("201")
    if not success_response:
        return None, False
    
    content = success_response.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})
    
    # Direkte Referenz
    if "$ref" in schema:
        return resolve_ref(schema["$ref"]), False
    
    # Prüfe auf properties (z.B. mit "objects" field)
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

def main():
    MODELS_DIR.mkdir(exist_ok=True)
    CONVERTERS_DIR.mkdir(exist_ok=True)
    CONTROLLERS_DIR.mkdir(exist_ok=True)

    env = Environment(loader=FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True)
    model_template = env.get_template("model_template.jinja")
    converter_template = env.get_template("converter_template.jinja")
    controller_template = env.get_template("controller_template.jinja")

    # --- Modelle generieren ---
    schemas = load_schemas()
    for schema_name, schema in schemas.items():
        model = transform_schema(schema_name, schema)

        content = model_template.render(model=model)
        file_path = MODELS_DIR / f"{model['class_name'].lower()}.py"
        file_path.write_text(content)
        print(f"✅ Model geschrieben: {file_path}")

        for conv in model["converters"]:
            conv_content = converter_template.render(model=conv)
            conv_path = CONVERTERS_DIR / f"{conv['class_name'].lower()}.py"
            conv_path.write_text(conv_content)
            print(f"   ↳ Converter geschrieben: {conv_path}")

    # --- Controller generieren ---
    paths_data = load_yaml(PATHS_FILE).get("paths", {})
    controllers = transform_paths(paths_data)

    for tag, operations in controllers.items():
        imports = set()
        funcs = []

        for op in operations:
            # Prüfe RequestBody auf Referenzen
            model_ref = None
            if "$ref" in str(op.get("requestBody", {})):
                ref = op["requestBody"]["content"]["application/json"]["schema"]["$ref"]
                model_ref = resolve_ref(ref)
                imports.add(model_ref)

            # Parameter prüfen
            params = []
            for p in op.get("parameters", []):
                param_required = p.get("required", False)
                param_name = sanitize_param_name(p["name"])
                param_original_name = p["name"]
                
                if "$ref" in p.get("schema", {}):
                    ref = p["schema"]["$ref"]
                    model_name = resolve_ref(ref)
                    imports.add(model_name)
                    param_type = model_name if param_required else f"Optional[{model_name}]"
                    params.append({
                        "name": param_name,
                        "original_name": param_original_name,
                        "type": param_type,
                        "required": param_required
                    })
                else:
                    t = TYPE_MAPPING.get(p.get("schema", {}).get("type", "string"), "Any")
                    param_type = t if param_required else f"Optional[{t}]"
                    params.append({
                        "name": param_name,
                        "original_name": param_original_name,
                        "type": param_type,
                        "required": param_required
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
                "params": params,
                "body_model": model_ref,
                "return_type": return_type,
            })

        ctrl_code = controller_template.render(
            controller_name=tag,
            functions=funcs,
            imports=sorted(imports),
        )
        ctrl_path = CONTROLLERS_DIR / f"{tag.lower()}_controller.py"
        ctrl_path.write_text(ctrl_code)
        print(f"🧩 Controller geschrieben: {ctrl_path}")

if __name__ == "__main__":
    main()