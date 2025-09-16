import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("BEARER_TOKEN")


## Nested JSON are accesesed with brackets []


def who_am_i(): 
    url = "https://api.affinity.co/v2/auth/whoami"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    print(data)

    return data["user"]


#----------------------------------------------------------- COMPANY ENDPOINTS -----------------------------------------------------------#



# Pagination Example:
# The "cursor" parameter (e.g., "ICAgICAgYmVmb3JlOjo6Nw") is used for pagination.
# To fetch companies from subsequent pages, take the "next_url" value from the API response
# and extract the cursor parameter to add it to your next query.

def get_companies(): 
    """Get a list of companies."""
    url = "https://api.affinity.co/v2/companies"
    query = {
    "limit": "10",
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers, params=query)
    data = response.json()
    data = data["data"]
    for company in data: 
        name = company["name"]
        id = company["id"]
        print(f"Company: {name} (ID: {id})")
    return data


def get_company_by_id(company_id): 
    """Get a specific company by ID."""
    url = f"https://api.affinity.co/v2/companies/{company_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    name = data["name"]
    id = data["id"]
    print(f"Company: {name} (ID: {id})")
    return  name


def get_company_fields():
    """Get custom fields for companies."""
    url = "https://api.affinity.co/v2/companies/fields"
    query = {
    "limit": "5"
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers, params=query)

    data = response.json()
    data = data["data"]
    for field in data:
        id = field["id"]
        name = field["name"]
        enrichment_source = field["enrichmentSource"]
        print(f"Field: {name} (ID: {id}) - Enrichment Source: {enrichment_source}")
    return None

def get_company_lists(company_id): 
    """Get lists associated with a specific company."""
    url = f"https://api.affinity.co/v2/companies/{company_id}/lists"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    data = data["data"]
    name_company = get_company_by_id(company_id)
    i = 0
    print(f"Lists in which the company {name_company} is included:")
    for lst in data:
        i += 1  
        id = lst["id"]
        name = lst["name"]
        print(f"{i}: {name} (ID: {id})")
    return None


def get_company_list_entries(companyid):
    """Paginate through the List Entries (AKA rows) for the given Company across all Lists. Each List Entry includes field data for the Company,
    including list-specific field data. Each List Entry also includes metadata about its creation, i.e., when it was added to the List and by whom."""

    url = f"https://api.affinity.co/v2/companies/{companyid}/list-entries"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    data = data["data"]
    name_company = get_company_by_id(companyid)
    i = 0
    print(f"List Entries for the company {name_company}:")
    for entry in data:
        i += 1  
        id = entry["id"]
        fields = entry["fields"]
        print(f"{i}: Entry ID: {id} - Fields: {fields}")

    return None 

#----------------------------------------------------------- EMAILS -----------------------------------------------------------# -_> Está en beta luego no acaba de funcionar del todo.
def get_emails(): 
    """Get a list of emails."""
    url = "https://api.affinity.co/v2/emails"
    query = {
    "limit": "10",
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers, params=query)
    data = response.json()
    
    print(data)



#----------------------------------------------------------- LISTS -----------------------------------------------------------#


def get_lists():  
    """Get a list of lists."""
    url = "https://api.affinity.co/v2/lists"
    query = {
    "limit": "10",
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers, params=query)
    data = response.json()
    data = data["data"]
    #print(data)
    for list in data:
        name = list["name"]
        id = list["id"]
        print(f"List: {name} (ID: {id})")   

    return None


def get_list_by_id(list_id): 
    """Get a specific list by ID."""
    url = f"https://api.affinity.co/v2/lists/{list_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    name = data["name"]
    content = data["type"]
    print(f"List Name: {name} (Content: {content})")
    return None

def get_list_entries_by_list_id(list_id):
    """Get entries in a specific list by ID."""
    url = f"https://api.affinity.co/v2/lists/{list_id}/list-entries"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    data = data["data"]
    "Data structure example: [{'id': 14355554, 'listId': 51750, 'creatorId': 41826372, 'type': 'company', 'createdAt': '2020-03-28T07:00:00Z', 'entity': {'id': 148821928, 'name': 'LightBee', 'domain': 'lightbeecorp.com', 'domains': ['lightbeecorp.com'], 'isGlobal': True}}, {'id': 14355555, 'listId': 51750, 'creatorId': 41826372, 'type': 'company', 'createdAt': '2020-02-12T08:00:00Z', 'entity': {'id': 224617431, 'name': 'Sateliot', 'domain': 'sateliot.space', 'domains': ['sateliot.space'], 'isGlobal': True}}, {'id': 14355556, 'listId': 51750, 'creatorId': 41826372, 'type': 'company', 'createdAt': '2020-02-12T08:00:00Z'"
    for item in data[:1]:
        main_id = item["id"]
        name = item["entity"]["name"]   # nombre de la empresa asociada
        print(f"ID {main_id}: {name}")

    return None

def get_single_entry_by_entry_id_on_specific_list_by_listid(entry_id, list_id):
    """Get a specific entry by ID within a specific list."""
    url = f"https://api.affinity.co/v2/lists/{list_id}/list-entries/{entry_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    print(data)
    return None

import requests
from typing import Any, Dict, Optional, List

# Se asume que api_key está definido en tu entorno
# api_key = "..."

def _coerce_number(x):
    if x is None:
        return None
    try:
        i = int(x)
        if float(x) == float(i):
            return i
        return float(x)
    except Exception:
        return x

def _normalize_field(field: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    v = field.get("value", {})
    data = v.get("data")
    if data is None:
        return None  # ignorar nulos

    vtype = v.get("type")

    if vtype == "number":
        data = _coerce_number(data)
    elif vtype == "location":
        raw = {
            "streetAddress": data.get("streetAddress"),
            "city": data.get("city"),
            "state": data.get("state"),
            "country": data.get("country"),
            "continent": data.get("continent"),
        }
        location_str = ", ".join([p for p in [raw["city"], raw["state"], raw["country"]] if p])
        data = {"raw": raw, "location_str": location_str}

    return {
        "id": field.get("id"),
        "name": field.get("name"),
        "source": field.get("enrichmentSource"),
        "type": vtype,
        "data": data,
    }

def _parse_company_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    fields = payload.get("data", [])
    normalized: Dict[str, Dict[str, Any]] = {}

    for f in fields:
        item = _normalize_field(f)
        if item:
            normalized[item["id"]] = item

    def get_data(fid, default=None):
        return normalized.get(fid, {}).get("data", default)

    summary = {
        "company_urls": {
            "dealroom": get_data("dealroom-url"),
            "linkedin": get_data("affinity-data-linkedin-url"),
        },
        "description": get_data("dealroom-description"),
        "industries": get_data("dealroom-industry") or [],
        "technologies": get_data("dealroom-technologies") or [],
        "business_models": get_data("dealroom-business-models") or [],
        "client_focus": get_data("dealroom-client-focus") or [],
        "ownership_types": get_data("dealroom-ownership-types") or [],
        "employees_range": get_data("dealroom-number-of-employees"),
        "year_founded": get_data("dealroom-year-founded"),
        "funding": {
            "last_eur": get_data("dealroom-last-funding-amount"),
            "total_eur": get_data("dealroom-total-funding-amount"),
        },
        "location": (get_data("dealroom-location") or {}).get("raw"),
        "location_str": (get_data("dealroom-location") or {}).get("location_str"),
    }

    return {
        "normalized_fields": normalized,  # por id
        "summary": summary,               # lo importante
    }

def get_fields_on_single_entry(entry_id: str, list_id: str) -> Dict[str, Any]:
    """
    Obtiene los fields de una list-entry de Affinity, sigue la paginación si existe
    y devuelve:
      {
        "normalized_fields": { <id>: {id, name, source, type, data}, ... },
        "summary": { ... }  # resumen de negocio
      }
    """
    base_url = f"https://api.affinity.co/v2/lists/{list_id}/list-entries/{entry_id}/fields"
    headers = {"Authorization": f"Bearer {api_key}"}

    all_fields: List[Dict[str, Any]] = []
    next_url: Optional[str] = base_url

    while next_url:
        resp = requests.get(next_url, headers=headers, timeout=20)
        resp.raise_for_status()
        chunk = resp.json()

        # acumula fields
        all_fields.extend(chunk.get("data", []))

        # paginación
        pagination = chunk.get("pagination", {})
        next_url = pagination.get("nextUrl")

    payload = {"data": all_fields}
    return _parse_company_payload(payload)


def get_single_field_on_single_entry(entry_id: str, list_id: str, field_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene un field específico de una list-entry de Affinity.
    Devuelve {id, name, source, type, data} o None si no existe.

    El field_id es el ID que se encuentra en la primera linea debajo de cada field dentro de la field list que devuelve la función get_fields_on_single_entry.
    """
    url = "https://api.affinity.co/v2/lists/" + list_id + "/list-entries/" + entry_id + "/fields/" + field_id
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data
    return None

def update_single_field_on_single_entry(entry_id: str, list_id: str, field_id: str, value: Any): ############ PENDIENTE DE PROBAR en función de si hace falta manipular rows
    """
    Actualiza un field específico de una list-entry de Affinity.
    Devuelve True si se actualizó correctamente, False en caso contrario.

    El field_id es el ID que se encuentra en la primera linea debajo de cada field dentro de la field list que devuelve la función get_fields_on_single_entry.
    El value es el nuevo valor que se quiere asignar al field.
    """
    url = f"https://api.affinity.co/v2/lists/{list_id}/list-entries/{entry_id}/fields/{field_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "value": {
            "type": field_id,
            "data": {
                "str": value
            }
        }
    }
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code == 204:
        print("Field updated successfully.")
    else: 
        print(f"Failed to update field. Status code: {response.status_code}, Response: {response.text}")
    return None

if __name__ == "__main__":
    #get_list_entries_by_list_id(51750)c
    #get_single_entry_by_entry_id_on_specific_list_by_listid(14355554, 51750)
    result = get_single_field_on_single_entry(entry_id="14355566", list_id="51750", field_id="last-event")
    #result = get_fields_on_single_entry(entry_id="14355566", list_id="51750")
    print(result)
    from rich import print as rprint
    from rich.pretty import Pretty
    update_single_field_on_single_entry(entry_id="14355566", list_id="51750", field_id="dealroom-location", value="Australia") # type: ignore


    #rprint(Pretty(result["summary"], indent_guides=True))

