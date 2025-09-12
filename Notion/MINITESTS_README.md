# Minitests.py - Complete Notion API Integration Tool

## 📋 Table of Contents
- [Overview](#overview)
- [Setup & Configuration](#setup--configuration)
- [Core Functions](#core-functions)
- [Interactive Components](#interactive-components)
- [Input Validation System](#input-validation-system)
- [Data Processing & Export](#data-processing--export)
- [Usage Examples](#usage-examples)
- [Building Upon This Code](#building-upon-this-code)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

`minitests.py` is a comprehensive Notion API integration tool that provides:
- **Database Discovery**: Automatically find all databases in your workspace
- **Schema Analysis**: Understand database structure and property types
- **Data Extraction**: Pull all data with automatic pagination handling
- **Interactive Management**: Create and edit pages through guided prompts
- **Input Validation**: Robust validation for all Notion property types
- **Export Capabilities**: JSON and CSV export functionality

### Key Features
- ✅ Zero configuration database discovery
- ✅ Intelligent property type handling
- ✅ Interactive CLI for non-technical users
- ✅ Comprehensive input validation
- ✅ Automatic pagination for large datasets
- ✅ Export to multiple formats

---

## 🛠️ Setup & Configuration

### Prerequisites
```bash
pip install notion-client python-dotenv
```

### Environment Setup
Create a `.env` file in your project directory:
```env
NOTION_TOKEN=your_integration_token_here
```

### Integration Setup
1. Go to [Notion Developers](https://www.notion.so/my-integrations)
2. Create a new integration
3. Copy the "Internal Integration Token"
4. Add the integration to your databases (Database → ... → Add connections)

---

## 🔧 Core Functions

### 1. Client Initialization

#### `__init__client() -> Client`
```python
def __init__client() -> Client:
    """Initialize and return a Notion client."""
```

**Purpose**: Create authenticated Notion client instance
**Returns**: Configured Notion client
**Considerations**:
- Validates token exists in environment
- Raises `ValueError` if token missing
- Should be called before any API operations

**Example**:
```python
client = __init__client()
```

---

### 2. URL Processing

#### `extract_id_from_url(url: str) -> str`
```python
def extract_id_from_url(url: str) -> str:
    """Extract the ID from a Notion URL"""
```

**Purpose**: Convert Notion URLs to properly formatted database/page IDs
**Parameters**:
- `url`: Any Notion URL (database or page)

**Returns**: Formatted ID (8-4-4-4-12 pattern)
**Considerations**:
- Handles URLs with `v=` parameter
- Removes hyphens and brackets from input
- Returns error message if URL format invalid

**Usage**:
```python
url = "https://notion.so/myworkspace/Tasks-1429989fe8ac4effbc8f57f56486db54?v=..."
db_id = extract_id_from_url(url)
# Returns: "1429989f-e8ac-4eff-bc8f-57f56486db54"
```

**Building Upon**: Extend to handle different URL formats or validate IDs before processing.

---

### 3. Database Discovery

#### `get_notion_databases() -> Dict[str, str]`
```python
def get_notion_databases():
    """Discover all databases accessible to the Notion integration"""
```

**Purpose**: Automatically find all accessible databases
**Returns**: `{database_name: database_id}` mapping
**Considerations**:
- Uses Notion search API to find all content
- Filters results to databases only
- Handles databases with missing titles
- Returns empty dict on API errors

**Example Output**:
```python
{
    "Tasks Database": "abc123...",
    "Project Tracker": "def456...",
    "Meeting Notes": "ghi789..."
}
```

**Building Upon**:
- Add filtering by workspace
- Cache results to avoid repeated API calls
- Add database type categorization

---

### 4. Schema Analysis

#### `get_database_schema(database_ids: Dict) -> Dict`
```python
def get_database_schema(database_ids):
    """Get the schema/structure of databases"""
```

**Purpose**: Analyze database structure and property types
**Parameters**:
- `database_ids`: Dictionary from `get_notion_databases()`

**Returns**: `{database_name: {property_name: property_type}}`
**Considerations**:
- Retrieves detailed schema for each database
- Maps property names to their types
- Prints formatted schema information
- Handles API errors gracefully

**Example Output**:
```python
{
    "Tasks Database": {
        "Name": "title",
        "Status": "select",
        "Priority": "number",
        "Due Date": "date",
        "Completed": "checkbox"
    }
}
```

**Building Upon**:
- Add property constraint analysis (select options, number ranges)
- Generate schema documentation automatically
- Compare schemas across databases

---

### 5. Data Extraction

#### `extract_property_value(prop_value: Dict) -> Any`
```python
def extract_property_value(prop_value):
    """Helper function to extract values from different property types"""
```

**Purpose**: Convert Notion property objects to Python values
**Parameters**:
- `prop_value`: Raw property object from Notion API

**Returns**: Extracted value in appropriate Python type
**Considerations**:
- Handles 15+ different Notion property types
- Returns appropriate Python types (str, int, bool, list)
- Graceful handling of null/empty values
- Special handling for complex types (relations, rollups)

**Supported Property Types**:
- `title`, `rich_text` → `str`
- `number` → `int`/`float`
- `select` → `str`
- `multi_select` → `List[str]`
- `date` → `str` (ISO format)
- `checkbox` → `bool`
- `url`, `email`, `phone_number` → `str`
- `people` → `List[str]` (names)
- `files` → `List[str]` (filenames)
- `relation` → `int` (count)
- `rollup`, `formula` → Various types

**Building Upon**:
- Add timezone handling for dates
- Support for block content extraction
- Custom formatting for specific property types

---

#### `extract_all_database_data(database_ids: Dict) -> Dict`
```python
def extract_all_database_data(database_ids):
    """Extract all data from specified databases"""
```

**Purpose**: Pull complete data from all databases with pagination
**Parameters**:
- `database_ids`: Dictionary from `get_notion_databases()`

**Returns**: `{database_name: [list_of_page_objects]}`
**Considerations**:
- Handles automatic pagination for large datasets
- Includes metadata (ID, creation time, URL)
- Processes all properties using `extract_property_value()`
- Provides progress feedback during extraction

**Each page object includes**:
```python
{
    "notion_id": "page_id",
    "created_time": "2024-01-01T10:00:00.000Z",
    "last_edited_time": "2024-01-01T12:00:00.000Z", 
    "notion_url": "https://notion.so/...",
    "Property1": "extracted_value1",
    "Property2": "extracted_value2",
    # ... all database properties
}
```

**Building Upon**:
- Add incremental sync (only new/modified pages)
- Implement data caching with timestamps
- Add filtering during extraction

---

#### `filter_database_data(notion_client, database_id, filters=None, sorts=None, limit=None)`
```python
def filter_database_data(notion_client, database_id, filters=None, sorts=None, limit=None):
    """Filter and search specific database data"""
```

**Purpose**: Query databases with specific conditions
**Parameters**:
- `notion_client`: Authenticated client
- `database_id`: Single database ID
- `filters`: Notion API filter object
- `sorts`: Sorting configuration
- `limit`: Maximum results

**Returns**: List of filtered page objects
**Example Usage**:
```python
# Get incomplete tasks
recent_tasks = filter_database_data(
    notion_client=notion,
    database_id="abc123...",
    filters={
        "property": "Status",
        "select": {"equals": "In Progress"}
    },
    sorts=[{
        "property": "Due Date",
        "direction": "ascending"
    }],
    limit=50
)
```

**Building Upon**:
- Create predefined filter templates
- Add complex multi-condition filtering
- Implement saved search functionality

---

### 6. Export Functions

#### `export_data_to_csv(database_data, output_dir="./exports")`
```python
def export_data_to_csv(database_data, output_dir="./exports"):
    """Export database data to CSV files"""
```

**Purpose**: Export data to CSV format for external analysis
**Parameters**:
- `database_data`: Output from `extract_all_database_data()`
- `output_dir`: Directory for CSV files

**Considerations**:
- Creates one CSV per database
- Handles Unicode content properly
- Sanitizes filenames for filesystem compatibility
- Includes all columns found in any page

**Building Upon**:
- Add column ordering/filtering options
- Support for Excel format
- Batch export configuration

#### `export_data_to_json(database_data, filename="notion_export.json")`
```python
def export_data_to_json(database_data, filename="notion_export.json"):
    """Export all database data to JSON"""
```

**Purpose**: Create structured JSON backup/export
**Parameters**:
- `database_data`: All extracted data
- `filename`: Output file path

**Features**:
- Pretty-printed JSON with 2-space indentation
- Handles date/datetime objects automatically
- Preserves all data types and structure

**Building Upon**:
- Add JSON schema generation
- Support for nested/hierarchical exports
- Compression for large datasets

---

### 7. Data Analysis

#### `analyze_database_data(database_data)`
```python
def analyze_database_data(database_data):
    """Analyze and summarize the extracted data"""
```

**Purpose**: Provide insights into database content
**Features**:
- Entry counts per database
- Property lists
- Date range analysis
- Summary statistics

**Building Upon**:
- Add data quality analysis
- Generate visualizations
- Identify data patterns and anomalies

---

## 🎮 Interactive Components

### Database Selection

#### `interactive_database_selector(database_ids, all_data)`
```python
def interactive_database_selector(database_ids, all_data):
    """Interactive function to select which database to work with"""
```

**Purpose**: User-friendly database selection interface
**Returns**: `(selected_name, selected_id, selected_data)`
**Features**:
- Shows databases with entry counts
- Handles invalid input gracefully
- Supports keyboard interrupt (Ctrl+C)

**Building Upon**:
- Add search/filter functionality
- Show database previews
- Remember last selected database

### Action Selection

#### `interactive_action_selector()`
```python
def interactive_action_selector():
    """Select what action to perform"""
```

**Purpose**: Present available actions to users
**Available Actions**:
1. Create new page
2. Edit existing page
3. View page details
4. Go back to database selection

**Building Upon**:
- Add bulk operations
- Implement custom action plugins
- Add action history/undo

---

## 🛡️ Input Validation System

### Property Options Discovery

#### `get_database_property_options(notion_client, database_id)`
```python
def get_database_property_options(notion_client, database_id):
    """Get available options for select, multi_select, and other constrained fields"""
```

**Purpose**: Discover constraints for database properties
**Returns**: `{property_name: {"type": type, "options": [available_options]}}`
**Supports**:
- Select field options
- Multi-select field options
- Property type information

### Input Validation

#### `validate_and_convert_input(value, prop_type, prop_options=None)`
```python
def validate_and_convert_input(value, prop_type, prop_options=None):
    """Validate user input against Notion property type"""
```

**Purpose**: Ensure user input matches Notion property requirements
**Parameters**:
- `value`: User input string
- `prop_type`: Notion property type
- `prop_options`: Available options (for constrained fields)

**Returns**: `(is_valid, converted_value, error_message)`

**Validation Rules**:

| Property Type | Validation Rules | Example Input | Converted Output |
|---------------|-----------------|---------------|------------------|
| `title`/`rich_text` | Any text | "My Task" | "My Task" |
| `number` | Integer or float | "42.5" | 42.5 |
| `checkbox` | Boolean variations | "yes", "1", "true" | `True` |
| `select` | Must match available options | "In Progress" | "In Progress" |
| `multi_select` | Comma-separated valid options | "Tag1, Tag2" | ["Tag1", "Tag2"] |
| `date` | YYYY-MM-DD format | "2024-03-20" | "2024-03-20" |
| `url` | Must start with http/https | "https://example.com" | "https://example.com" |
| `email` | Must contain @ and . | "user@domain.com" | "user@domain.com" |
| `phone_number` | Any format accepted | "(555) 123-4567" | "(555) 123-4567" |

**Error Handling**:
- Clear error messages for invalid input
- Suggestions for correct format
- Graceful handling of read-only properties

**Building Upon**:
- Add regex patterns for custom validation
- Support for complex date formats
- Integration with external validation services

### Property Input Collection

#### `collect_property_input(prop_name, prop_type, prop_options=None, current_value=None)`
```python
def collect_property_input(prop_name, prop_type, prop_options=None, current_value=None):
    """Collect and validate input for a single property"""
```

**Purpose**: User-friendly property input collection
**Features**:
- Context-aware prompts
- Shows current values when editing
- Provides helpful hints for each property type
- Allows skipping with Enter
- Handles keyboard interrupts gracefully

**Example Prompts**:
```
📝 Status (select) [current: To Do]
   Options: To Do, In Progress, Done
   Enter value (or press Enter to skip): In Progress

📝 Due Date (date)
   Format: YYYY-MM-DD (e.g., 2024-03-20)
   Enter value (or press Enter to skip): 2024-03-25
```

---

## 📄 Page Management Functions

### Property Formatting

#### `create_notion_property_value(prop_type, value)`
```python
def create_notion_property_value(prop_type, value):
    """Convert validated value to Notion API property format"""
```

**Purpose**: Transform user input into Notion API format
**Handles All Property Types**:
- Converts Python values to Notion property objects
- Handles null/empty values appropriately
- Provides fallback formatting for unknown types

**Example Transformations**:
```python
# Input: value="My Task", prop_type="title"
# Output: {"title": [{"text": {"content": "My Task"}}]}

# Input: value=["Tag1", "Tag2"], prop_type="multi_select"  
# Output: {"multi_select": [{"name": "Tag1"}, {"name": "Tag2"}]}
```

### Page Creation

#### `interactive_create_page(notion_client, database_id, database_name)`
```python
def interactive_create_page(notion_client, database_id, database_name):
    """Interactive page creation"""
```

**Purpose**: Guide users through page creation process
**Workflow**:
1. Discover database schema and constraints
2. Collect input for each property
3. Validate all inputs
4. Show summary for confirmation
5. Create page via API
6. Display success/error results

**Features**:
- Skip read-only properties automatically
- Show helpful hints for each field
- Confirmation before creation
- Error handling with clear messages

**Building Upon**:
- Template system for common page types
- Bulk page creation
- Import from external sources

### Page Editing

#### `interactive_edit_page(notion_client, database_id, database_name, database_data)`
```python
def interactive_edit_page(notion_client, database_id, database_name, database_data):
    """Interactive page editing"""
```

**Purpose**: Update existing pages through guided interface
**Workflow**:
1. Display existing pages for selection
2. Show current property values
3. Collect updates for desired properties
4. Validate changes
5. Apply updates via API

**Features**:
- Shows current values as defaults
- Only updates specified properties
- Preserves unchanged data
- Confirmation before applying changes

**Considerations**:
- Limits display to first 10 pages for performance
- Handles large datasets gracefully
- Updates database data cache after changes

**Building Upon**:
- Add search functionality for page selection
- Support for bulk editing operations
- Change history/audit trail

---

## 🔄 Main Workflow Functions

### Complete Workflow

#### `main_notion_workflow()`
```python
def main_notion_workflow():
    """Complete workflow for Notion data extraction"""
```

**Purpose**: Automated end-to-end data processing
**Steps**:
1. Initialize client
2. Discover all databases
3. Analyze database schemas
4. Extract all data
5. Perform data analysis
6. Export to CSV and JSON

**Building Upon**:
- Add scheduling for regular exports
- Configuration file support
- Custom processing steps

### Interactive Management

#### `interactive_notion_manager(notion_client, database_ids, all_data)`
```python
def interactive_notion_manager(notion_client, database_ids, all_data):
    """Main interactive function for managing Notion databases"""
```

**Purpose**: Complete interactive database management system
**Features**:
- Database selection loop
- Action selection menu
- Page creation and editing
- Data viewing and analysis
- Automatic data refresh after modifications

### Complete Interactive Workflow

#### `complete_interactive_workflow()`
```python
def complete_interactive_workflow():
    """Complete workflow with interactive database management"""
```

**Purpose**: Entry point for interactive mode
**Workflow**:
1. Load all databases and data
2. Launch interactive manager
3. Handle all user interactions

---

## 📚 Usage Examples

### Basic Data Extraction
```python
# Quick data extraction
database_ids = get_notion_databases()
all_data = extract_all_database_data(database_ids)
export_data_to_json(all_data)
```

### Filtered Queries
```python
# Get recent completed tasks
recent_complete = filter_database_data(
    notion_client=notion,
    database_id=database_ids["Tasks"],
    filters={
        "and": [
            {
                "property": "Status", 
                "select": {"equals": "Done"}
            },
            {
                "property": "Completed Date",
                "date": {"past_week": {}}
            }
        ]
    },
    sorts=[{
        "property": "Completed Date",
        "direction": "descending"
    }]
)
```

### Custom Analysis
```python
# Analyze task completion rates
def analyze_task_completion(task_data):
    total_tasks = len(task_data)
    completed_tasks = len([t for t in task_data if t.get('Status') == 'Done'])
    
    completion_rate = completed_tasks / total_tasks * 100
    print(f"Completion Rate: {completion_rate:.1f}%")
    
    # Analyze by priority
    high_priority = [t for t in task_data if t.get('Priority', 0) >= 3]
    print(f"High Priority Tasks: {len(high_priority)}")

# Use with extracted data
task_data = all_data['Tasks Database']
analyze_task_completion(task_data)
```

---

## 🏗️ Building Upon This Code

### 1. **Extend Database Operations**

```python
def sync_with_external_system(database_data):
    """Sync Notion data with external system"""
    for db_name, pages in database_data.items():
        for page in pages:
            # Push to external API
            external_api.update(page['notion_id'], page)

def incremental_sync(database_id, last_sync_time):
    """Only sync pages modified since last sync"""
    filters = {
        "property": "Last edited time",
        "last_edited_time": {
            "after": last_sync_time
        }
    }
    return filter_database_data(notion, database_id, filters)
```

### 2. **Add Custom Validations**

```python
def add_custom_validator(prop_type, validator_func):
    """Add custom validation for specific property types"""
    # Extend validate_and_convert_input with custom rules
    pass

def validate_project_code(value):
    """Custom validator for project code format: PROJ-YYYY-NNN"""
    import re
    pattern = r'^PROJ-\d{4}-\d{3}$'
    return re.match(pattern, value) is not None
```

### 3. **Implement Batch Operations**

```python
def bulk_update_pages(database_id, page_ids, updates):
    """Update multiple pages with same properties"""
    for page_id in page_ids:
        notion.pages.update(page_id=page_id, properties=updates)

def create_pages_from_csv(database_id, csv_file):
    """Create multiple pages from CSV file"""
    import csv
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert CSV row to Notion properties
            properties = convert_csv_row_to_properties(row)
            notion.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
```

### 4. **Add Reporting Features**

```python
def generate_database_report(database_data):
    """Generate comprehensive database report"""
    report = {
        'total_databases': len(database_data),
        'total_pages': sum(len(pages) for pages in database_data.values()),
        'database_details': {}
    }
    
    for db_name, pages in database_data.items():
        report['database_details'][db_name] = {
            'page_count': len(pages),
            'property_types': get_property_type_distribution(pages),
            'last_modified': max(p.get('last_edited_time', '') for p in pages)
        }
    
    return report

def export_to_html_report(report_data):
    """Export report as HTML dashboard"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head><title>Notion Database Report</title></head>
    <body>
        <h1>Database Summary</h1>
        <!-- Report content here -->
    </body>
    </html>
    """
    # Generate HTML report
```

### 5. **Add Configuration Management**

```python
import yaml

def load_config(config_file='notion_config.yaml'):
    """Load configuration from YAML file"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

def save_workspace_config(database_ids, filename='workspace.yaml'):
    """Save current workspace configuration"""
    config = {
        'databases': database_ids,
        'last_sync': datetime.now().isoformat(),
        'settings': {
            'export_format': 'json',
            'include_metadata': True
        }
    }
    
    with open(filename, 'w') as f:
        yaml.dump(config, f, indent=2)
```

### 6. **Implement Caching System**

```python
import pickle
from datetime import datetime, timedelta

class NotionCache:
    def __init__(self, cache_file='notion_cache.pkl'):
        self.cache_file = cache_file
        self.cache = self.load_cache()
    
    def get_cached_data(self, key, max_age_hours=1):
        """Get cached data if not expired"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(hours=max_age_hours):
                return data
        return None
    
    def set_cached_data(self, key, data):
        """Store data in cache with timestamp"""
        self.cache[key] = (data, datetime.now())
        self.save_cache()
    
    def load_cache(self):
        try:
            with open(self.cache_file, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return {}
    
    def save_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)
```

### 7. **Add API Rate Limiting**

```python
import time
from functools import wraps

class RateLimiter:
    def __init__(self, calls_per_second=3):
        self.calls_per_second = calls_per_second
        self.last_call = 0
    
    def wait_if_needed(self):
        now = time.time()
        time_since_last = now - self.last_call
        min_interval = 1.0 / self.calls_per_second
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_call = time.time()

rate_limiter = RateLimiter()

def rate_limited_api_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        rate_limiter.wait_if_needed()
        return func(*args, **kwargs)
    return wrapper
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. **Authentication Errors**
```
❌ Error: Unauthorized (401)
```
**Solutions**:
- Verify `NOTION_TOKEN` in `.env` file
- Check integration permissions
- Ensure integration is added to databases

#### 2. **Missing Databases**
```
🔍 Found 0 databases
```
**Solutions**:
- Add integration to databases: Database → ... → Add connections
- Check integration capabilities in Notion settings
- Verify workspace permissions

#### 3. **Property Validation Errors**
```
❌ Must be one of: Option1, Option2
```
**Solutions**:
- Check spelling and case sensitivity
- Use `get_database_property_options()` to verify available options
- Update database schema if needed

#### 4. **Rate Limiting**
```
❌ API Error: rate_limited
```
**Solutions**:
- Implement delays between requests
- Use batch operations when possible
- Consider caching frequently accessed data

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints to functions
def debug_extract_data(database_ids):
    print(f"DEBUG: Processing {len(database_ids)} databases")
    for name, db_id in database_ids.items():
        print(f"DEBUG: Extracting from {name} ({db_id})")
        # ... extraction code
```

### Performance Optimization

```python
# For large datasets
def optimized_extraction(database_ids, max_workers=3):
    """Use threading for concurrent database extraction"""
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(extract_single_database, db_id): name 
            for name, db_id in database_ids.items()
        }
        
        results = {}
        for future in concurrent.futures.as_completed(futures):
            db_name = futures[future]
            try:
                results[db_name] = future.result()
            except Exception as e:
                print(f"Error extracting {db_name}: {e}")
                results[db_name] = []
        
        return results
```

---

## 📝 Best Practices

1. **Always validate environment setup first**
2. **Handle API errors gracefully**
3. **Use pagination for large datasets**
4. **Cache frequently accessed data**
5. **Implement proper rate limiting**
6. **Provide clear user feedback**
7. **Log operations for debugging**
8. **Backup data before bulk operations**

This comprehensive tool provides a solid foundation for any Notion integration project. The modular design makes it easy to extend with additional functionality while maintaining reliability and user-friendliness.