# Unofficial Patents MCP Server

A MCP Server for accessing patent data from multiple sources including the United States Patent and Trademark Office (USPTO) and Google Patents. This server provides access to:

- **USPTO Patent Public Search** - Full-text search and document retrieval through the [Patent Public Search](https://www.uspto.gov/patents/search/patent-public-search) API
- **USPTO Open Data Portal (ODP)** - Metadata, continuity, and assignment data through the [ODP API](https://data.uspto.gov/home)
- **Google Patents** - Access to 90M+ patent publications from 17+ countries via Google BigQuery

## Features

This server provides tools for:

1. **Patent Search** - Search for patents and patent applications
2. **Full Text Documents** - Get complete text of patents including claims, description, etc.
3. **PDF Downloads** - Download patents as PDF files. (But Claude Desktop doesn't support this as a client currently.)
4. **Metadata** - Access patent bibliographic information, assignments, and litigation data

## API Sources

This server interacts with three patent data sources:

- **ppubs.uspto.gov** - For full text document access, PDF downloads, and advanced search
- **api.uspto.gov** - For metadata, continuity information, transactions, and assignments
- **Google Patents (BigQuery)** - For searching 90M+ patent publications across US, EP, WO, JP, CN, KR, GB, DE, FR, CA, AU and more

## API Key Setup

### USPTO Open Data Portal API Key

To use the api.uspto.gov tools, you need to obtain an Open Data Portal (ODP) API key:

1. Visit [USPTO's Getting Started page](https://data.uspto.gov/apis/getting-started) and follow the instructions to request an API key if you don't already have one.

2. Add your API key to the `.env` file in the patent_mcp_server directory:
   ```
   USPTO_API_KEY=<your_key_here>
   ```
You don't need quotes or the < > brackets around your key. The ppubs tools will run without this API key, but the API key is required for the api tools.

### Google Cloud Setup

To use the Google Patents tools, you need to set up a Google Cloud project with BigQuery access:

1. **Create a Google Cloud Project** (if you don't have one):
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Note your project ID

2. **Enable BigQuery API**:
   - In your Google Cloud project, navigate to "APIs & Services" > "Library"
   - Search for "BigQuery API" and enable it

3. **Create a Service Account and Download Credentials**:
   - Navigate to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Give it a name (e.g., "patent-mcp-server")
   - Grant it the "BigQuery User" role
   - Click "Done"
   - Click on the created service account
   - Go to the "Keys" tab
   - Click "Add Key" > "Create New Key" > "JSON"
   - Save the downloaded JSON file to a secure location

4. **Configure Environment Variables**:
   Add the following to your `.env` file:
   ```
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
   ```

   Replace `your-project-id` with your actual Google Cloud project ID and `/path/to/your/service-account-key.json` with the full path to your downloaded credentials file.

**Note:** Google Patents data in BigQuery is publicly available, but you still need a Google Cloud project to run queries. BigQuery offers a [free tier](https://cloud.google.com/bigquery/pricing#free-tier) with 1 TB of query data processed per month at no charge.

## Claude Desktop Configuration

To integrate this MCP server with Claude Desktop:

1. Update your Claude Desktop configuration file (`claude_desktop_config.json`):
   ```json
    {
      "mcpServers": {
        "patents": {
          "command": "uv",
          "args": [
            "--directory",
            "/Users/username/patent_mcp_server",
            "run",
            "patent-mcp-server"
          ]
        }
      }
    }
   ```
   You can find `claude_desktop_config.json` on a mac by opening the Claude Desktop app, opening Settings (from the Claude menu or by Command + ' on the keyboard), clicking "Developer" in in the sidebar, and "Edit Config."

2. Replace `/Users/username/patent_mcp_server` with the actual path to your patent_mcp_server directory if that's not where it was cloned. (If you're on a mac, this may mean simply replacing `username` with your username.)

When integrated with Claude Desktop, the server will be automatically started when needed and doesn't need to be run separately. The server uses stdio transport for communication with Claude Desktop or other MCP clients running on the same host.

## Available Functions

The server provides the following functions to interact with patent data from multiple sources. Note that the Claude Desktop client does not fully support all of these tools. For example, Claude Desktop does not at present allow for download of PDFs.

### Public Patent Search (ppubs.uspto.gov)
- `ppubs_search_patents` - Search for granted patents in USPTO Public Search
- `ppubs_search_applications` - Search for published patent applications in USPTO Public Search
- `ppubs_get_full_document` - Get full patent document details by GUID from ppubs.uspto.gov
- `ppubs_get_patent_by_number` - Get a granted patent's full text by number from ppubs.uspto.gov
- `ppubs_download_patent_pdf` - Download a granted patent as PDF from ppubs.uspto.gov (not currently supported by Claude Desktop)

### Open Data Portal API (api.uspto.gov)
Requires USPTO API Key (see API Key Setup above).

- `get_app(app_num)` - Get basic patent application data
- `search_applications(...)` - Search for patent applications using query parameters
- `download_applications(...)` - Download patent applications using query parameters
- `get_app_metadata(app_num)` - Get application metadata
- `get_app_adjustment(app_num)` - Get patent term adjustment data
- `get_app_assignment(app_num)` - Get assignment data
- `get_app_attorney(app_num)` - Get attorney/agent information
- `get_app_continuity(app_num)` - Get continuity data
- `get_app_foreign_priority(app_num)` - Get foreign priority claims
- `get_app_transactions(app_num)` - Get transaction history
- `get_app_documents(app_num)` - Get document details
- `get_app_associated_documents(app_num)` - Get associated documents
- `get_status_codes(...)` - Search for status codes
- `search_datasets(...)` - Search bulk dataset products
- `get_dataset_product(...)` - Get a specific product by its identifier

### Google Patents (BigQuery)
Requires Google Cloud setup (see Google Cloud Setup above). Provides access to 90M+ patent publications from 17+ countries.

**Supported Countries:** US, EP (European Patent Office), WO (WIPO/PCT), JP (Japan), CN (China), KR (South Korea), GB (United Kingdom), DE (Germany), FR (France), CA (Canada), AU (Australia), and more.

- `google_search_patents(query, country, limit, offset, start_date, end_date)` - Full-text search across patent titles and abstracts
- `google_get_patent(publication_number)` - Get complete patent details by publication number
- `google_get_patent_claims(publication_number)` - Get patent claims text
- `google_get_patent_description(publication_number)` - Get patent description text
- `google_search_by_inventor(inventor_name, country, limit, offset)` - Search patents by inventor name
- `google_search_by_assignee(assignee_name, country, limit, offset)` - Search patents by company/assignee
- `google_search_by_cpc(cpc_code, country, limit, offset)` - Search patents by CPC classification code

Refer to the function docstrings in the code for detailed parameter information.