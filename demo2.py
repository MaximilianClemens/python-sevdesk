from sevdesk import Client
from sevdesk.models.contact import Contact
from sevdesk.converters.category import Category

sevdesk = Client('4521c2ea5ad4ecec3d33de07ac668859')

# Beispiel 1: Organisation erstellen
company = Contact(
    name="Acme Corp",
    category=Category(id_=3, objectName="Category")
)
result = sevdesk.contact.createContact(body=company)

# Beispiel 2: Person erstellen
person = Contact(
    surename="John",
    familyname="Doe",
    gender="m",
    category=Category(id_=3, objectName="Category")
)
result = sevdesk.contact.createContact(body=person)
print(result)

print(f"Neuer Kontakt ID: {result.id_}")