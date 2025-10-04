import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

OPENAPI_FILE = Path("openapi.yaml")
MODELS_DIR = Path("models")
CONVERTERS_DIR = Path("converters")

# Typ-Mapping OpenAPI -> Python
TYPE_MAPPING = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "object": "dict",  # wird ggf. ersetzt durch Submodell
}

def to_pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))

def first_up(name: str) -> str:
    return name[0].upper() + name[1:]

def load_schemas() -> dict:
    data = yaml.safe_load(OPENAPI_FILE.read_text())
    return data.get("components", {}).get("schemas", {})

def transform_schema(name: str, schema: dict):
    required = schema.get("required", [])
    properties = []
    converters = []

    for prop_name, prop in schema.get("properties", {}).items():
        t = TYPE_MAPPING.get(prop.get("type", "string"), "Any")
        nullable = prop.get("nullable", False)
        submodel = None

        # verschachteltes Objekt → eigenes Submodell + Converter
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

def main():
    MODELS_DIR.mkdir(exist_ok=True)
    CONVERTERS_DIR.mkdir(exist_ok=True)

    env = Environment(loader=FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True)
    model_template = env.get_template("model_template.jinja")
    converter_template = env.get_template("converter_template.jinja")

    schemas = load_schemas()
    for schema_name, schema in schemas.items():
        model = transform_schema(schema_name, schema)

        # Schreibe Hauptmodell
        content = model_template.render(model=model)
        file_path = MODELS_DIR / f"{model['class_name'].lower()}.py"
        file_path.write_text(content)
        print(f"✅ Model geschrieben: {file_path}")

        # Schreibe Converter-Submodelle
        for conv in model["converters"]:
            conv_content = converter_template.render(model=conv)
            conv_path = CONVERTERS_DIR / f"{conv['class_name'].lower()}.py"
            conv_path.write_text(conv_content)
            print(f"   ↳ Converter geschrieben: {conv_path}")

if __name__ == "__main__":
    main()
