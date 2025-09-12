import asyncio
import csv
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Any, Optional

from notion_client import Client, AsyncClient
from notion_client.helpers import collect_paginated_api, iterate_paginated_api
from notion_client.errors import APIResponseError
from pprint import pprint

# =============================================================================
# CONFIGURATION
# =============================================================================

# Set your token as environment variable: export NOTION_TOKEN="your_token_here"

# Initialize clients
load_dotenv()
api_key = os.getenv("NOTION_TOKEN")

notion = Client(auth=api_key)
async_notion = AsyncClient(auth=api_key)


def __init__client () -> Client: 
    """Initialize and return a Notion client."""
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise ValueError("Missing NOTION_TOKEN environment variable")
    return Client(auth=token)

def extract_id_from_url(url: str) -> str:
    """Extract the ID from a Notion URL: 
    1. Searches for characters "v=" and takes the next 32 characters. 
    2. The URL ends in a page ID. It should be a 32 character long string. 
    3. Format this value by inserting hyphens (-) in the following pattern:
                8-4-4-4-12 (each number is the length of characters between the hyphens).
                Example: 1429989fe8ac4effbc8f57f56486db54 becomes 1429989f-e8ac-4eff-bc8f-57f56486db54.
    """
    url = url.strip().replace("-", "").replace("{", "").replace("}", "")
    if "v=" in url:
        id_start = url.split("v=")[-1]
        #print(f"ID start: {id_start}")
        id_part = url.split("v=")[-1][:32]
        #print(f"ID part: {id_part}")
        return f"{id_part[:8]}-{id_part[8:12]}-{id_part[12:16]}-{id_part[16:20]}-{id_part[20:]}"
    else:
        return "url does not contain 'v='"
    
def get_notion_databases():
    """
    Discover all databases accessible to the Notion integration
    
    Args:
        notion_client: Authenticated Notion client
        
    Returns:
        dict: {database_name: database_id}
    """
    try:
        # Search for all content
        results = notion.search()
        
        # Filter for databases only
        databases = [item for item in results["results"] if item["object"] == "database"] # type: ignore
        
        database_mapping = {}
        for database in databases:
            # Extract database name safely
            title = "Untitled"
            if database.get("title") and len(database["title"]) > 0:
                title = database["title"][0]["plain_text"]
            
            database_mapping[title] = database["id"]
        
        print(f"🔍 Found {len(database_mapping)} databases:")
        for name in database_mapping.keys():
            print(f"  - {name}")
            
        return database_mapping
        
    except Exception as e:
        print(f"❌ Error discovering databases: {e}")
        return {}


def get_database_schema(database_ids):
    """
    Get the schema/structure of databases
    
    Args:
        database_ids: dict of {name: id}
        
    Returns:
        dict: {database_name: {properties}}
    """
    schemas = {}
    
    for name, db_id in database_ids.items():
        try:
            db_info = notion.databases.retrieve(database_id=db_id)
            schemas[name] = {
                prop_name: prop_info['type'] 
                for prop_name, prop_info in db_info["properties"].items() # type: ignore
            }
            
            print(f"\n📋 {name} Schema:")
            for prop_name, prop_type in schemas[name].items():
                print(f"  - {prop_name}: {prop_type}")
                
        except Exception as e:
            print(f"❌ Error getting schema for {name}: {e}")
            schemas[name] = {}
    
    return schemas


def extract_property_value(prop_value):
    """Helper function to extract values from different property types"""
    prop_type = prop_value["type"]
    
    extractors = {
        "title": lambda x: x["title"][0]["plain_text"] if x["title"] else "",
        "rich_text": lambda x: " ".join([text["plain_text"] for text in x["rich_text"]]),
        "number": lambda x: x["number"],
        "select": lambda x: x["select"]["name"] if x["select"] else None,
        "multi_select": lambda x: [option["name"] for option in x["multi_select"]],
        "date": lambda x: x["date"]["start"] if x["date"] else None,
        "checkbox": lambda x: x["checkbox"],
        "url": lambda x: x["url"],
        "email": lambda x: x["email"],
        "phone_number": lambda x: x["phone_number"],
        "people": lambda x: [person["name"] for person in x["people"]],
        "files": lambda x: [file["name"] for file in x["files"]],
        "formula": lambda x: x["formula"].get("string") or x["formula"].get("number"),
        "relation": lambda x: len(x["relation"]),  # Just count of relations
        "rollup": lambda x: x["rollup"].get("number") or x["rollup"].get("array", [])
    }
    
    return extractors.get(prop_type, lambda x: str(x.get(prop_type, "")))(prop_value)

def extract_all_database_data(database_ids):
    """
    Extract all data from specified databases
    
    Args:
        notion_client: Authenticated Notion client
        database_ids: dict of {database_name: database_id}
        
    Returns:
        dict: {database_name: [list of entries]}
    """
    all_data = {}
    
    for name, db_id in database_ids.items():
        print(f"\n🔍 Extracting from {name}...")
        
        try:
            # Handle pagination for large databases
            all_pages = []
            has_more = True
            start_cursor = None
            
            while has_more:
                query_params = {"database_id": db_id}
                if start_cursor:
                    query_params["start_cursor"] = start_cursor
                
                query_result = notion.databases.query(**query_params)
                all_pages.extend(query_result["results"]) # type: ignore
                
                has_more = query_result["has_more"] # type: ignore
                start_cursor = query_result.get("next_cursor") # type: ignore
            
            # Process all pages
            database_data = []
            for page in all_pages:
                page_data = {
                    "notion_id": page["id"],
                    "created_time": page["created_time"],
                    "last_edited_time": page["last_edited_time"],
                    "notion_url": page["url"]
                }
                
                # Extract all properties
                for prop_name, prop_value in page["properties"].items():
                    page_data[prop_name] = extract_property_value(prop_value)
                
                database_data.append(page_data)
            
            all_data[name] = database_data
            print(f"✅ Extracted {len(database_data)} entries from {name}")
            
        except Exception as e:
            print(f"❌ Error extracting from {name}: {e}")
            all_data[name] = []
    
    return all_data

def filter_database_data(notion_client, database_id, filters=None, sorts=None, limit=None):
    """
    Filter and search specific database data
    
    Args:
        notion_client: Authenticated Notion client
        database_id: Single database ID
        filters: Notion API filter object
        sorts: Notion API sorts array
        limit: Max number of results
        
    Returns:
        list: Filtered entries
    """
    query_params = {"database_id": database_id}
    
    if filters:
        query_params["filter"] = filters
    if sorts:
        query_params["sorts"] = sorts
    if limit:
        query_params["page_size"] = min(limit, 100)  # API limit is 100
    
    try:
        result = notion_client.databases.query(**query_params)
        
        processed_data = []
        for page in result["results"]:
            page_data = {"notion_id": page["id"]}
            for prop_name, prop_value in page["properties"].items():
                page_data[prop_name] = extract_property_value(prop_value)
            processed_data.append(page_data)
        
        return processed_data
    except Exception as e:
        print(f"❌ Filter error: {e}")
        return []

def export_data_to_csv(database_data, output_dir="./exports"):
    """Export database data to CSV files"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    for db_name, data in database_data.items():
        if not data:
            continue
            
        safe_name = db_name.replace(" ", "_").replace("/", "_").lower()
        filepath = os.path.join(output_dir, f"{safe_name}.csv")
        
        # Get all unique keys
        all_keys = set()
        for entry in data:
            all_keys.update(entry.keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(all_keys))
            writer.writeheader()
            writer.writerows(data)
        
        print(f"📁 Exported {db_name} to {filepath}")

def export_data_to_json(database_data, filename="notion_export.json"):
    """Export all database data to JSON"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(database_data, f, indent=2, default=str)
    print(f"📁 Exported all data to {filename}")

def analyze_database_data(database_data):
    """Analyze and summarize the extracted data"""
    print(f"\n📈 DATA ANALYSIS")
    print(f"{'='*50}")
    
    for db_name, data in database_data.items():
        print(f"\n🗃️  {db_name}:")
        print(f"   Entries: {len(data)}")
        
        if data:
            sample = data[0]
            properties = [k for k in sample.keys() if k not in ['notion_id', 'created_time', 'last_edited_time', 'notion_url']]
            print(f"   Properties: {', '.join(properties)}")
            
            dates = [entry['created_time'] for entry in data if entry.get('created_time')]
            if dates:
                print(f"   Date range: {min(dates)[:10]} to {max(dates)[:10]}")


def main_notion_workflow():
    """Complete workflow for Notion data extraction"""
    # Initialize client    
    __init__client()

    # Step 1: Discover databases
    database_ids = get_notion_databases() # type: ignore
    if not database_ids:
        print("No databases found!")
        return
    
    # Step 2: Get database schemas
    schemas = get_database_schema(database_ids) # type: ignore
    
    # Step 3: Extract all data
    all_data = extract_all_database_data(database_ids)
    
    # Step 4: Analyze data
    analyze_database_data(all_data)
    
    # Step 5: Export data
    export_data_to_csv(all_data)
    export_data_to_json(all_data)
    
    return database_ids, all_data, schemas

# Example usage with specific filtering
def example_filtered_extraction():
    notion = Client(auth="your_integration_token")
    
    # Get database IDs
    database_ids = get_notion_databases(notion) # type: ignore
    
    # Example: Get only recent entries from API Test Form
    if "API Test Form" in database_ids:
        recent_entries = filter_database_data(
            notion,
            database_ids["API Test Form"],
            sorts=[{"timestamp": "created_time", "direction": "descending"}],
            limit=10
        )
        print(f"Found {len(recent_entries)} recent entries")


# =============================================================================
# INTERACTIVE SELECTORS

def interactive_database_selector(database_ids, all_data):
    """
    Interactive function to select which database to work with
    
    Args:
        database_ids: dict of {database_name: database_id}
        all_data: dict of {database_name: [entries]}
        
    Returns:
        tuple: (selected_db_name, selected_db_id, selected_db_data)
    """
    if not database_ids:
        print("❌ No databases available!")
        return None, None, None
    
    print(f"\n🗃️  Available Databases:")
    print("=" * 40)
    
    db_list = list(database_ids.items())
    for i, (name, db_id) in enumerate(db_list, 1):
        entry_count = len(all_data.get(name, []))
        print(f"{i}. {name} ({entry_count} entries)")
    
    while True:
        try:
            choice = input(f"\nSelect database (1-{len(db_list)}): ").strip()
            choice_idx = int(choice) - 1
            
            if 0 <= choice_idx < len(db_list):
                selected_name, selected_id = db_list[choice_idx]
                selected_data = all_data.get(selected_name, [])
                
                print(f"\n✅ Selected: {selected_name}")
                return selected_name, selected_id, selected_data
            else:
                print(f"❌ Please enter a number between 1 and {len(db_list)}")
                
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return None, None, None

def interactive_action_selector():
    """Select what action to perform"""
    print(f"\n🔧 What would you like to do?")
    print("1. Create new page")
    print("2. Edit existing page")
    print("3. View page details")
    print("4. Go back to database selection")
    
    while True:
        try:
            choice = input("\nSelect action (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            else:
                print("❌ Please enter 1, 2, 3, or 4")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return 4
        

# =============================================================================
# INPUT VALIDATION FUNCTIONS
def get_database_property_options(notion_client, database_id):
    """Get available options for select, multi_select, and other constrained fields"""
    try:
        db_info = notion_client.databases.retrieve(database_id=database_id)
        property_options = {}
        
        for prop_name, prop_info in db_info["properties"].items():
            if prop_info["type"] == "select" and "select" in prop_info:
                options = [opt["name"] for opt in prop_info["select"].get("options", [])]
                property_options[prop_name] = {"type": "select", "options": options}
                
            elif prop_info["type"] == "multi_select" and "multi_select" in prop_info:
                options = [opt["name"] for opt in prop_info["multi_select"].get("options", [])]
                property_options[prop_name] = {"type": "multi_select", "options": options}
                
            else:
                property_options[prop_name] = {"type": prop_info["type"], "options": None}
        
        return property_options
    except Exception as e:
        print(f"❌ Error getting property options: {e}")
        return {}

def validate_and_convert_input(value, prop_type, prop_options=None):
    """
    Validate user input against Notion property type
    
    Args:
        value: User input string
        prop_type: Notion property type
        prop_options: Available options for select/multi_select
        
    Returns:
        tuple: (is_valid, converted_value, error_message)
    """
    if not value.strip() and prop_type not in ["checkbox"]:
        return True, None, None  # Empty is usually OK
    
    try:
        if prop_type == "title" or prop_type == "rich_text":
            return True, value.strip(), None
            
        elif prop_type == "number":
            if value.strip() == "":
                return True, None, None
            try:
                # Try int first, then float
                if '.' in value:
                    return True, float(value), None
                else:
                    return True, int(value), None
            except ValueError:
                return False, None, "Must be a number"
                
        elif prop_type == "checkbox":
            lower_val = value.lower().strip()
            if lower_val in ['true', 't', 'yes', 'y', '1', 'on']:
                return True, True, None
            elif lower_val in ['false', 'f', 'no', 'n', '0', 'off', '']:
                return True, False, None
            else:
                return False, None, "Enter yes/no, true/false, or 1/0"
                
        elif prop_type == "select":
            if not prop_options:
                return True, value.strip(), None
            
            if value.strip() in prop_options:
                return True, value.strip(), None
            else:
                return False, None, f"Must be one of: {', '.join(prop_options)}"
                
        elif prop_type == "multi_select":
            if not value.strip():
                return True, [], None
                
            # Split by comma and clean up
            selected = [item.strip() for item in value.split(',')]
            
            if prop_options:
                invalid = [item for item in selected if item not in prop_options]
                if invalid:
                    return False, None, f"Invalid options: {', '.join(invalid)}. Available: {', '.join(prop_options)}"
            
            return True, selected, None
            
        elif prop_type == "date":
            if value.strip() == "":
                return True, None, None
                
            # Try to parse common date formats
            import re
            from datetime import datetime
            
            # YYYY-MM-DD format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', value.strip()):
                try:
                    datetime.strptime(value.strip(), '%Y-%m-%d')
                    return True, value.strip(), None
                except ValueError:
                    return False, None, "Invalid date format"
            else:
                return False, None, "Use YYYY-MM-DD format (e.g., 2024-03-20)"
                
        elif prop_type == "url":
            if value.strip() == "":
                return True, None, None
            if value.startswith(('http://', 'https://')):
                return True, value.strip(), None
            else:
                return False, None, "Must start with http:// or https://"
                
        elif prop_type == "email":
            if value.strip() == "":
                return True, None, None
            if '@' in value and '.' in value:
                return True, value.strip(), None
            else:
                return False, None, "Must be a valid email address"
                
        elif prop_type == "phone_number":
            return True, value.strip(), None  # Notion is flexible with phone formats
            
        elif prop_type in ["formula", "rollup", "created_time", "created_by", "last_edited_time", "last_edited_by"]:
            return False, None, f"{prop_type} is read-only and cannot be edited"
            
        else:
            return True, value.strip(), None  # Default: accept as string
            
    except Exception as e:
        return False, None, f"Validation error: {str(e)}"

def collect_property_input(prop_name, prop_type, prop_options=None, current_value=None):
    """
    Collect and validate input for a single property
    
    Args:
        prop_name: Name of the property
        prop_type: Type of the property
        prop_options: Available options (for select/multi_select)
        current_value: Current value (for editing)
        
    Returns:
        Validated value or None if skipped
    """
    # Skip read-only properties
    if prop_type in ["formula", "rollup", "created_time", "created_by", "last_edited_time", "last_edited_by"]:
        print(f"⏭️  Skipping {prop_name} ({prop_type} is read-only)")
        return None
    
    # Build prompt
    prompt = f"\n📝 {prop_name} ({prop_type})"
    
    if current_value is not None:
        prompt += f" [current: {current_value}]"
    
    # Add helpful hints
    if prop_type == "select" and prop_options:
        prompt += f"\n   Options: {', '.join(prop_options)}"
    elif prop_type == "multi_select" and prop_options:
        prompt += f"\n   Options: {', '.join(prop_options)} (comma-separated)"
    elif prop_type == "checkbox":
        prompt += "\n   Enter: yes/no, true/false, or 1/0"
    elif prop_type == "date":
        prompt += "\n   Format: YYYY-MM-DD (e.g., 2024-03-20)"
    elif prop_type == "number":
        prompt += "\n   Enter any number (integer or decimal)"
    
    prompt += f"\n   Enter value (or press Enter to skip): "
    
    while True:
        try:
            user_input = input(prompt).strip()
            
            # Allow skipping
            if not user_input:
                return None
            
            # Validate input
            is_valid, converted_value, error_msg = validate_and_convert_input(
                user_input, prop_type, prop_options
            )
            
            if is_valid:
                return converted_value
            else:
                print(f"❌ {error_msg}")
                continue
                
        except KeyboardInterrupt:
            print(f"\n⏭️  Skipping {prop_name}")
            return None
        

# =============================================================================
# Page Creation and Editing Functions
def create_notion_property_value(prop_type, value):
    """Convert validated value to Notion API property format"""
    if value is None:
        return None
    
    property_formatters = {
        "title": lambda v: {"title": [{"text": {"content": str(v)}}]},
        "rich_text": lambda v: {"rich_text": [{"text": {"content": str(v)}}]},
        "number": lambda v: {"number": v},
        "select": lambda v: {"select": {"name": str(v)}},
        "multi_select": lambda v: {"multi_select": [{"name": item} for item in v]},
        "checkbox": lambda v: {"checkbox": v},
        "date": lambda v: {"date": {"start": str(v)}},
        "url": lambda v: {"url": str(v)},
        "email": lambda v: {"email": str(v)},
        "phone_number": lambda v: {"phone_number": str(v)},
    }
    
    formatter = property_formatters.get(prop_type)
    if formatter:
        return formatter(value)
    else:
        # Default to rich_text for unknown types
        return {"rich_text": [{"text": {"content": str(value)}}]}

def interactive_create_page(notion_client, database_id, database_name):
    """Interactive page creation"""
    print(f"\n📄 Creating new page in: {database_name}")
    print("=" * 50)
    
    # Get property options
    property_options = get_database_property_options(notion_client, database_id)
    
    # Collect input for each property
    page_properties = {}
    
    for prop_name, prop_info in property_options.items():
        prop_type = prop_info["type"]
        options = prop_info.get("options")
        
        value = collect_property_input(prop_name, prop_type, options)
        
        if value is not None:
            notion_property = create_notion_property_value(prop_type, value)
            if notion_property:
                page_properties[prop_name] = notion_property
    
    if not page_properties:
        print("❌ No properties provided. Page creation cancelled.")
        return None
    
    # Confirm creation
    print(f"\n📋 Page Summary:")
    for prop_name, prop_value in page_properties.items():
        print(f"  {prop_name}: {prop_value}")
    
    confirm = input(f"\n✅ Create this page? (y/n): ").lower().strip()
    
    if confirm in ['y', 'yes']:
        try:
            new_page = notion_client.pages.create(
                parent={"database_id": database_id},
                properties=page_properties
            )
            print(f"🎉 Successfully created page!")
            print(f"📄 Page ID: {new_page['id']}")
            print(f"🔗 URL: {new_page['url']}")
            return new_page
            
        except Exception as e:
            print(f"❌ Error creating page: {e}")
            return None
    else:
        print("❌ Page creation cancelled.")
        return None

def interactive_edit_page(notion_client, database_id, database_name, database_data):
    """Interactive page editing"""
    if not database_data:
        print("❌ No pages found in this database.")
        return None
    
    print(f"\n✏️  Edit page in: {database_name}")
    print("=" * 50)
    
    # Show existing pages
    for i, page in enumerate(database_data[:10], 1):  # Show first 10 pages
        title = "Untitled"
        # Try to find a title-like property
        for prop_name, value in page.items():
            if prop_name.lower() in ['name', 'title', 'task', 'item'] and value:
                title = str(value)[:50]
                break
        
        print(f"{i}. {title}")
    
    if len(database_data) > 10:
        print(f"... and {len(database_data) - 10} more pages")
    
    while True:
        try:
            choice = input(f"\nSelect page to edit (1-{min(10, len(database_data))}): ").strip()
            choice_idx = int(choice) - 1
            
            if 0 <= choice_idx < min(10, len(database_data)):
                selected_page = database_data[choice_idx]
                break
            else:
                print(f"❌ Please enter a number between 1 and {min(10, len(database_data))}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Edit cancelled.")
            return None
    
    # Get current page details and property options
    page_id = selected_page['notion_id']
    property_options = get_database_property_options(notion_client, database_id)
    
    print(f"\n📄 Editing page: {page_id}")
    print("Current values:")
    for prop_name, current_value in selected_page.items():
        if prop_name not in ['notion_id', 'created_time', 'last_edited_time', 'notion_url']:
            print(f"  {prop_name}: {current_value}")
    
    # Collect updates
    updates = {}
    
    for prop_name, prop_info in property_options.items():
        prop_type = prop_info["type"]
        options = prop_info.get("options")
        current_value = selected_page.get(prop_name)
        
        value = collect_property_input(prop_name, prop_type, options, current_value)
        
        if value is not None:
            notion_property = create_notion_property_value(prop_type, value)
            if notion_property:
                updates[prop_name] = notion_property
    
    if not updates:
        print("❌ No updates provided. Edit cancelled.")
        return None
    
    # Confirm updates
    print(f"\n📋 Updates Summary:")
    for prop_name, prop_value in updates.items():
        print(f"  {prop_name}: {prop_value}")
    
    confirm = input(f"\n✅ Apply these updates? (y/n): ").lower().strip()
    
    if confirm in ['y', 'yes']:
        try:
            updated_page = notion_client.pages.update(
                page_id=page_id,
                properties=updates
            )
            print(f"🎉 Successfully updated page!")
            return updated_page
            
        except Exception as e:
            print(f"❌ Error updating page: {e}")
            return None
    else:
        print("❌ Update cancelled.")
        return None
    

def interactive_notion_manager(notion_client, database_ids, all_data):
    """
    Main interactive function for managing Notion databases
    
    Args:
        notion_client: Authenticated Notion client
        database_ids: dict of {database_name: database_id}
        all_data: dict of {database_name: [entries]}
    """
    print(f"\n🚀 Welcome to Interactive Notion Manager!")
    print("=" * 50)
    
    while True:
        try:
            # Step 1: Select database
            db_name, db_id, db_data = interactive_database_selector(database_ids, all_data)
            
            if not db_name:  # User cancelled or error
                break
            
            while True:
                # Step 2: Select action
                action = interactive_action_selector()
                
                if action == 1:  # Create new page
                    new_page = interactive_create_page(notion_client, db_id, db_name)
                    if new_page:
                        # Refresh data to include new page
                        all_data[db_name] = extract_all_database_data( {db_name: db_id})[db_name] # type: ignore
                        
                elif action == 2:  # Edit existing page
                    updated_page = interactive_edit_page(notion_client, db_id, db_name, db_data)
                    if updated_page:
                        # Refresh data to show updates
                        all_data[db_name] = extract_all_database_data({db_name: db_id})[db_name] # type: ignore
                        
                elif action == 3:  # View page details
                    if db_data:
                        print(f"\n📊 {db_name} Details:")
                        analyze_database_data({db_name: db_data})
                    else:
                        print("❌ No data available for this database.")
                        
                elif action == 4:  # Go back
                    break
                
                input("\nPress Enter to continue...")
            
        except KeyboardInterrupt:
            print(f"\n👋 Goodbye!")
            break

# Complete workflow with interactive management
def complete_interactive_workflow():
    """Complete workflow with interactive database management"""
    # Initialize
    __init__client()
    notion = Client(auth=api_key)    
    # Load databases and data
    print("🔍 Loading Notion workspace...")
    database_ids = get_notion_databases() # type: ignore
    
    if not database_ids:
        print("❌ No databases found!")
        return
    
    all_data = extract_all_database_data(database_ids)
    
    # Start interactive manager
    interactive_notion_manager(notion, database_ids, all_data)

# Run it!
if __name__ == "__main__":
    complete_interactive_workflow()