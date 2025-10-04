import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

OPENAPI_FILE = Path("openapi.yaml")
MODELS_DIR = Path("models")

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
    for prop_name, prop in schema.get("properties", {}).items():
        t = TYPE_MAPPING.get(prop.get("type", "string"), "Any")
        nullable = prop.get("nullable", False)
        submodel = None

        # verschachteltes Objekt → eigenes Submodell
        if prop.get("type") == "object" and "properties" in prop:
            submodel = first_up(prop_name)

            t = submodel

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
    }

def main():
    MODELS_DIR.mkdir(exist_ok=True)
    env = Environment(loader=FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template("model_template.jinja")

    schemas = load_schemas()
    for schema_name, schema in schemas.items():
        model = transform_schema(schema_name, schema)
        content = template.render(model=model)

        file_path = MODELS_DIR / f"{model['class_name'].lower()}.py"
        file_path.write_text(content)
        print(f"✅ Model geschrieben: {file_path}")

if __name__ == "__main__":
    main()
