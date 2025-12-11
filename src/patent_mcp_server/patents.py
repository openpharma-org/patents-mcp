"""
USPTO Patent Search MCP Server

This file provides a Model Context Protocol (MCP) server that exposes tools for interacting with multiple USPTO APIs:

1. ppubs.uspto.gov - Provides full text patent documents, PDF downloads, and advanced search
2. api.uspto.gov - Provides metadata, continuity information, transactions, and assignments

The server uses stdio transport for command-line tools, following the MCP standard.
"""
import os
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Union

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("uspto_patent_tools")

# Set up logging
logging.basicConfig(
    level=logging.INFO, # for production
    #level=logging.DEBUG, # for debugging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger('uspto_patent_mcp')

# Import USPTO client implementations
from patent_mcp_server.uspto.ppubs_uspto_gov import PpubsClient
from patent_mcp_server.uspto.api_uspto_gov import ApiUsptoClient
from patent_mcp_server.google.bigquery_client import GoogleBigQueryClient
from patent_mcp_server.constants import Defaults, GooglePatentsCountries
from patent_mcp_server.util.errors import ApiError

# Constants
USPTO_API_BASE = "https://api.uspto.gov"

# Create client instances for each USPTO API
ppubs_client = PpubsClient()  # ppubs.uspto.gov module
api_client = ApiUsptoClient() # api.uspto.gov module
google_bq_client = GoogleBigQueryClient()  # Google Patents BigQuery module

# =====================================================================
# Unified USPTO Patents Tool
# =====================================================================

@mcp.tool()
async def uspto_patents(
    method: str,
    # Search parameters (for ppubs_search_patents and ppubs_search_applications)
    query: Optional[str] = None,
    start: Optional[int] = 0,
    limit: Optional[int] = 100,
    sort: Optional[str] = "date_publ desc",
    default_operator: Optional[str] = "OR",
    expand_plurals: Optional[bool] = True,
    british_equivalents: Optional[bool] = True,
    # Document retrieval parameters (for ppubs_get_full_document)
    guid: Optional[str] = None,
    source_type: Optional[str] = None,
    # Patent number parameters (for ppubs_get_patent_by_number and ppubs_download_patent_pdf)
    patent_number: Optional[Union[str, int]] = None,
    # Application number parameter (for all get_app_* methods)
    app_num: Optional[str] = None,
    # Search applications parameters (for search_applications and download_applications)
    q: Optional[str] = None,
    offset: Optional[int] = 0,
    facets: Optional[str] = None,
    fields: Optional[str] = None,
    filters: Optional[str] = None,
    range_filters: Optional[str] = None,
    format: Optional[str] = "json",
    # POST search parameters (for search_applications_post and download_applications_post)
    filters_list: Optional[List[Dict[str, Any]]] = None,
    range_filters_list: Optional[List[Dict[str, Any]]] = None,
    sort_list: Optional[List[Dict[str, Any]]] = None,
    fields_list: Optional[List[str]] = None,
    facets_list: Optional[List[str]] = None,
    # Dataset search parameters (for search_datasets)
    product_title: Optional[str] = None,
    product_description: Optional[str] = None,
    product_short_name: Optional[str] = None,
    include_files: Optional[bool] = True,
    latest: Optional[bool] = False,
    labels: Optional[str] = None,
    categories: Optional[str] = None,
    datasets: Optional[str] = None,
    file_types: Optional[str] = None,
    # Dataset product parameters (for get_dataset_product)
    product_id: Optional[str] = None,
    file_data_from_date: Optional[str] = None,
    file_data_to_date: Optional[str] = None
) -> Dict[str, Any]:
    """Unified tool for USPTO patent operations: search patents and applications, retrieve full documents,
    download PDFs, and access metadata from USPTO databases.

    Use the method parameter to specify the operation type.

    Available methods:
    - ppubs_search_patents: Search granted patents in USPTO Public Search
    - ppubs_search_applications: Search published patent applications
    - ppubs_get_full_document: Get full patent document by GUID
    - ppubs_get_patent_by_number: Get granted patent's full text by number
    - ppubs_download_patent_pdf: Download granted patent as PDF
    - get_app: Get patent application data by number
    - search_applications: Search patent applications with query parameters
    - search_applications_post: Search patent applications with JSON payload
    - download_applications: Download patent applications with query parameters
    - download_applications_post: Download patent applications with JSON payload
    - get_app_metadata: Get application metadata
    - get_app_adjustment: Get patent term adjustment data
    - get_app_assignment: Get assignment data
    - get_app_attorney: Get attorney/agent information
    - get_app_continuity: Get continuity data
    - get_app_foreign_priority: Get foreign priority claims
    - get_app_transactions: Get transaction history
    - get_app_documents: Get document details
    - get_app_associated_documents: Get associated documents
    - get_status_codes: Search for status codes
    - get_status_codes_post: Search status codes with JSON payload
    - search_datasets: Search bulk dataset products
    - get_dataset_product: Get specific dataset product

    Args:
        method: The operation to perform (required)
        query: For ppubs_search_*: Search query string using USPTO syntax
        start: For ppubs_search_*: Starting position for results (default: 0)
        limit: For ppubs_search_*/search_*: Maximum results to return (default: 100/25)
        sort: For ppubs_search_*/search_*: Sort order
        default_operator: For ppubs_search_*: Default operator AND/OR (default: OR)
        expand_plurals: For ppubs_search_*: Include plural forms (default: True)
        british_equivalents: For ppubs_search_*: Include British spellings (default: True)
        guid: For ppubs_get_full_document: Document unique identifier
        source_type: For ppubs_get_full_document: Document type (USPAT or US-PGPUB)
        patent_number: For ppubs_get_patent_by_number/ppubs_download_patent_pdf: Patent number
        app_num: For get_app_*: U.S. Patent Application Number (e.g., 14412875)
        q: For search_*/download_*: Search query string
        offset: For search_*/download_*: Starting position (default: 0)
        facets: For search_*/download_*: Fields to facet upon
        fields: For search_*/download_*: Fields to include in response
        filters: For search_*/download_*: Filter conditions
        range_filters: For search_*/download_*: Range filter conditions
        format: For download_*: Download format (json or csv, default: json)
        filters_list: For *_post: List of filter objects
        range_filters_list: For *_post: List of range filter objects
        sort_list: For *_post: List of sort objects
        fields_list: For *_post: List of field names
        facets_list: For *_post: List of facet field names
        product_title: For search_datasets: Specific product title
        product_description: For search_datasets: Specific product description
        product_short_name: For search_datasets: Product identifier
        include_files: For search_datasets/get_dataset_product: Include files (default: true)
        latest: For search_datasets/get_dataset_product: Return latest only (default: false)
        labels: For search_datasets: Filter by labels
        categories: For search_datasets: Filter by categories
        datasets: For search_datasets: Filter by datasets
        file_types: For search_datasets: Filter by file types
        product_id: For get_dataset_product: Product identifier
        file_data_from_date: For get_dataset_product: Filter files from date (YYYY-MM-DD)
        file_data_to_date: For get_dataset_product: Filter files to date (YYYY-MM-DD)
    """

    # Route to the appropriate method
    if method == "ppubs_search_patents":
        if not query:
            return {"error": True, "message": "query parameter is required for ppubs_search_patents"}
        return await ppubs_client.run_query(
            query=query,
            start=start,
            limit=limit,
            sort=sort,
            default_operator=default_operator,
            sources=["USPAT"],
            expand_plurals=expand_plurals,
            british_equivalents=british_equivalents
        )

    elif method == "ppubs_search_applications":
        if not query:
            return {"error": True, "message": "query parameter is required for ppubs_search_applications"}
        return await ppubs_client.run_query(
            query=query,
            start=start,
            limit=limit,
            sort=sort,
            default_operator=default_operator,
            sources=["US-PGPUB"],
            expand_plurals=expand_plurals,
            british_equivalents=british_equivalents
        )

    elif method == "ppubs_get_full_document":
        if not guid or not source_type:
            return {"error": True, "message": "guid and source_type parameters are required for ppubs_get_full_document"}
        return await ppubs_client.get_document(guid, source_type)

    elif method == "ppubs_get_patent_by_number":
        if not patent_number:
            return {"error": True, "message": "patent_number parameter is required for ppubs_get_patent_by_number"}

        # Convert to string if integer
        patent_number = str(patent_number)

        # First search for the patent using specific field
        search_query = f'patentNumber:"{patent_number}"'
        logger.info(f"Searching for patent with query: {search_query}")

        result = await ppubs_client.run_query(
            query=search_query,
            sources=["USPAT"],
            limit=1
        )

        if result.get("error", False):
            return result

        # Handle different response structures
        if result.get("patents") and len(result["patents"]) > 0:
            patent = result["patents"][0]
            logger.info(f"Found patent: {patent.get('guid')}")
        elif result.get("docs") and len(result["docs"]) > 0:
            patent = result["docs"][0]
            logger.info(f"Found patent: {patent.get('guid')}")
        else:
            # Try alternative query format
            alternative_query = f'"{patent_number}".pn.'
            logger.info(f"No results found, trying alternative query: {alternative_query}")

            result = await ppubs_client.run_query(
                query=alternative_query,
                sources=["USPAT"],
                limit=1
            )

            if result.get("error", False):
                return result

            if not result.get("patents") and not result.get("docs"):
                return {
                    "error": True,
                    "message": f"Patent {patent_number} not found"
                }

            if result.get("patents") and len(result["patents"]) > 0:
                patent = result["patents"][0]
            elif result.get("docs") and len(result["docs"]) > 0:
                patent = result["docs"][0]
            else:
                return {
                    "error": True,
                    "message": f"Patent {patent_number} not found"
                }

        # Now get the full document
        return await ppubs_client.get_document(patent["guid"], patent["type"])

    elif method == "ppubs_download_patent_pdf":
        if not patent_number:
            return {"error": True, "message": "patent_number parameter is required for ppubs_download_patent_pdf"}

        # Convert to string if integer
        patent_number = str(patent_number)

        # First search for the patent using specific field
        search_query = f'patentNumber:"{patent_number}"'
        logger.info(f"Searching for patent with query: {search_query}")

        result = await ppubs_client.run_query(
            query=search_query,
            sources=["USPAT"],
            limit=1
        )

        if result.get("error", False):
            return result

        # Handle different response structures
        if result.get("patents") and len(result["patents"]) > 0:
            patent = result["patents"][0]
        elif result.get("docs") and len(result["docs"]) > 0:
            patent = result["docs"][0]
        else:
            # Try alternative query format
            alternative_query = f'"{patent_number}".pn.'
            logger.info(f"No results found, trying alternative query: {alternative_query}")

            result = await ppubs_client.run_query(
                query=alternative_query,
                sources=["USPAT"],
                limit=1
            )

            if result.get("error", False):
                return result

            if not result.get("patents") and not result.get("docs"):
                return {
                    "error": True,
                    "message": f"Patent {patent_number} not found"
                }

            if result.get("patents") and len(result["patents"]) > 0:
                patent = result["patents"][0]
            elif result.get("docs") and len(result["docs"]) > 0:
                patent = result["docs"][0]
            else:
                return {
                    "error": True,
                    "message": f"Patent {patent_number} not found"
                }

        # Handle different field naming in the response
        image_location = patent.get("imageLocation", patent.get("document_structure", {}).get("image_location"))
        page_count = patent.get("pageCount", patent.get("document_structure", {}).get("page_count"))

        if not image_location or not page_count:
            return {
                "error": True,
                "message": "Missing image location or page count information"
            }

        # Download the PDF
        return await ppubs_client.download_image(
            patent["guid"],
            image_location,
            page_count,
            patent["type"]
        )

    # API.USPTO.GOV methods
    elif method == "get_app":
        if not app_num:
            return {"error": True, "message": "app_num parameter is required for get_app"}
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/{app_num}"
        return await api_client.make_request(url)

    elif method == "search_applications":
        params = {
            "q": q,
            "sort": sort,
            "offset": offset,
            "limit": limit,
            "facets": facets,
            "fields": fields,
            "filters": filters,
            "rangeFilters": range_filters
        }

        query_string = api_client.build_query_string(params)
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/search"
        if query_string:
            url = f"{url}?{query_string}"

        return await api_client.make_request(url)

    elif method == "search_applications_post":
        data = {
            "q": q,
            "filters": filters_list,
            "rangeFilters": range_filters_list,
            "sort": sort_list,
            "fields": fields_list,
            "pagination": {"offset": offset, "limit": limit},
            "facets": facets_list
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        url = f"{USPTO_API_BASE}/api/v1/patent/applications/search"
        return await api_client.make_request(url, method="POST", data=data)

    elif method == "download_applications":
        params = {
            "q": q,
            "sort": sort,
            "offset": offset,
            "limit": limit,
            "fields": fields,
            "filters": filters,
            "rangeFilters": range_filters,
            "format": format
        }

        query_string = api_client.build_query_string(params)
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/search/download"
        if query_string:
            url = f"{url}?{query_string}"

        return await api_client.make_request(url)

    elif method == "download_applications_post":
        data = {
            "q": q,
            "filters": filters_list,
            "rangeFilters": range_filters_list,
            "sort": sort_list,
            "fields": fields_list,
            "pagination": {"offset": offset, "limit": limit},
            "format": format
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        url = f"{USPTO_API_BASE}/api/v1/patent/applications/search/download"
        return await api_client.make_request(url, method="POST", data=data)

    elif method == "get_app_metadata":
        if not app_num:
            return {"error": True, "message": "app_num parameter is required for get_app_metadata"}
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/{app_num}/meta-data"
        return await api_client.make_request(url)

    elif method == "get_app_adjustment":
        if not app_num:
            return {"error": True, "message": "app_num parameter is required for get_app_adjustment"}
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/{app_num}/adjustment"
        return await api_client.make_request(url)

    elif method == "get_app_assignment":
        if not app_num:
            return {"error": True, "message": "app_num parameter is required for get_app_assignment"}
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/{app_num}/assignment"
        return await api_client.make_request(url)

    elif method == "get_app_attorney":
        if not app_num:
            return {"error": True, "message": "app_num parameter is required for get_app_attorney"}
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/{app_num}/attorney"
        return await api_client.make_request(url)

    elif method == "get_app_continuity":
        if not app_num:
            return {"error": True, "message": "app_num parameter is required for get_app_continuity"}
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/{app_num}/continuity"
        return await api_client.make_request(url)

    elif method == "get_app_foreign_priority":
        if not app_num:
            return {"error": True, "message": "app_num parameter is required for get_app_foreign_priority"}
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/{app_num}/foreign-priority"
        return await api_client.make_request(url)

    elif method == "get_app_transactions":
        if not app_num:
            return {"error": True, "message": "app_num parameter is required for get_app_transactions"}
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/{app_num}/transactions"
        return await api_client.make_request(url)

    elif method == "get_app_documents":
        if not app_num:
            return {"error": True, "message": "app_num parameter is required for get_app_documents"}
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/{app_num}/documents"
        return await api_client.make_request(url)

    elif method == "get_app_associated_documents":
        if not app_num:
            return {"error": True, "message": "app_num parameter is required for get_app_associated_documents"}
        url = f"{USPTO_API_BASE}/api/v1/patent/applications/{app_num}/associated-documents"
        return await api_client.make_request(url)

    elif method == "get_status_codes":
        params = {
            "q": q,
            "offset": offset,
            "limit": limit,
        }

        query_string = api_client.build_query_string(params)
        url = f"{USPTO_API_BASE}/api/v1/patent/status-codes"
        if query_string:
            url = f"{url}?{query_string}"

        return await api_client.make_request(url)

    elif method == "get_status_codes_post":
        data = {
            "q": q,
            "pagination": {"offset": offset, "limit": limit}
        }

        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}

        url = f"{USPTO_API_BASE}/api/v1/patent/status-codes"
        return await api_client.make_request(url, method="POST", data=data)

    elif method == "search_datasets":
        params = {
            "q": q,
            "productTitle": product_title,
            "productDescription": product_description,
            "productShortName": product_short_name,
            "offset": offset,
            "limit": limit,
            "facets": facets,
            "includeFiles": include_files,
            "latest": latest,
            "labels": labels,
            "categories": categories,
            "datasets": datasets,
            "fileTypes": file_types
        }

        query_string = api_client.build_query_string(params)
        url = f"{USPTO_API_BASE}/api/v1/datasets/products/search"
        if query_string:
            url = f"{url}?{query_string}"

        return await api_client.make_request(url)

    elif method == "get_dataset_product":
        if not product_id:
            return {"error": True, "message": "product_id parameter is required for get_dataset_product"}

        params = {
            "fileDataFromDate": file_data_from_date,
            "fileDataToDate": file_data_to_date,
            "offset": offset,
            "limit": limit,
            "includeFiles": include_files,
            "latest": latest
        }

        query_string = api_client.build_query_string(params)
        url = f"{USPTO_API_BASE}/api/v1/datasets/products/{product_id}"
        if query_string:
            url = f"{url}?{query_string}"

        return await api_client.make_request(url)

    else:
        return {"error": True, "message": f"Unknown method: {method}"}


# =====================================================================
# Google Patents Tools
# =====================================================================

@mcp.tool()
async def google_search_patents(
    query: str,
    country: str = GooglePatentsCountries.US,
    limit: int = Defaults.SEARCH_LIMIT,
    offset: int = 0,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
) -> Dict[str, Any]:
    """Search Google Patents Public Datasets using BigQuery

    Searches patent titles and abstracts for the specified query string.
    Returns patent publication number, title, abstract, dates, inventors,
    assignees, and classification codes.

    Args:
        query: Search query string (searches titles and abstracts)
        country: Country code (US, EP, WO, JP, CN, KR, GB, DE, FR, CA, AU)
        limit: Maximum number of results to return (default: 100, max: 500)
        offset: Number of results to skip for pagination (default: 0)
        start_date: Optional start date for publication_date filter (YYYYMMDD format, e.g., 20220101)
        end_date: Optional end date for publication_date filter (YYYYMMDD format, e.g., 20251231)

    Returns:
        Dictionary containing search results with patent metadata
    """
    if limit > Defaults.SEARCH_LIMIT_MAX:
        return ApiError.validation_error(
            f"Limit cannot exceed {Defaults.SEARCH_LIMIT_MAX}", "limit"
        )

    if country not in GooglePatentsCountries.ALL:
        return ApiError.validation_error(
            f"Invalid country code. Must be one of: "
            f"{', '.join(GooglePatentsCountries.ALL)}",
            "country",
        )

    try:
        result = await google_bq_client.search_patents(
            query, country, limit, offset, start_date, end_date
        )
        return result
    except Exception as e:
        logger.error(f"Error searching Google Patents: {str(e)}")
        return ApiError.create(
            message=f"Failed to search Google Patents: {str(e)}",
            status_code=500
        )


@mcp.tool()
async def google_get_patent(publication_number: str) -> Dict[str, Any]:
    """Get full patent details from Google Patents by publication number

    Retrieves complete patent information including title, abstract, dates,
    inventors, assignees, classifications, and more.

    Args:
        publication_number: Patent publication number (e.g., US-9876543-B2)

    Returns:
        Dictionary containing complete patent details
    """
    try:
        result = await google_bq_client.get_patent_by_number(publication_number)
        return result
    except Exception as e:
        logger.error(f"Error fetching patent {publication_number}: {str(e)}")
        return ApiError.create(
            message=f"Failed to fetch patent: {str(e)}", status_code=500
        )


@mcp.tool()
async def google_get_patent_claims(publication_number: str) -> Dict[str, Any]:
    """Get patent claims from Google Patents by publication number

    Retrieves all claims for the specified patent, including claim numbers
    and full claim text.

    Args:
        publication_number: Patent publication number (e.g., US-9876543-B2)

    Returns:
        Dictionary containing claim number and text for each claim
    """
    try:
        result = await google_bq_client.get_patent_claims(publication_number)
        return result
    except Exception as e:
        logger.error(f"Error fetching claims for {publication_number}: {str(e)}")
        return ApiError.create(
            message=f"Failed to fetch claims: {str(e)}", status_code=500
        )


@mcp.tool()
async def google_get_patent_description(publication_number: str) -> Dict[str, Any]:
    """Get patent description from Google Patents by publication number

    Retrieves the detailed description section of the patent document.

    Args:
        publication_number: Patent publication number (e.g., US-9876543-B2)

    Returns:
        Dictionary containing patent description text
    """
    try:
        result = await google_bq_client.get_patent_description(publication_number)
        return result
    except Exception as e:
        logger.error(
            f"Error fetching description for {publication_number}: {str(e)}"
        )
        return ApiError.create(
            message=f"Failed to fetch description: {str(e)}", status_code=500
        )


@mcp.tool()
async def google_search_by_inventor(
    inventor_name: str,
    country: str = GooglePatentsCountries.US,
    limit: int = Defaults.SEARCH_LIMIT,
    offset: int = 0,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
) -> Dict[str, Any]:
    """Search Google Patents by inventor name

    Finds patents where the specified inventor is listed. Useful for tracking
    an inventor's patent portfolio.

    Args:
        inventor_name: Inventor name to search for
        country: Country code (US, EP, WO, JP, CN, KR, GB, DE, FR, CA, AU)
        limit: Maximum number of results to return (default: 100, max: 500)
        offset: Number of results to skip for pagination (default: 0)
        start_date: Optional start date for publication_date filter (YYYYMMDD format, e.g., 20220101)
        end_date: Optional end date for publication_date filter (YYYYMMDD format, e.g., 20251231)

    Returns:
        Dictionary containing search results
    """
    if limit > Defaults.SEARCH_LIMIT_MAX:
        return ApiError.validation_error(
            f"Limit cannot exceed {Defaults.SEARCH_LIMIT_MAX}", "limit"
        )

    if country not in GooglePatentsCountries.ALL:
        return ApiError.validation_error(
            f"Invalid country code. Must be one of: "
            f"{', '.join(GooglePatentsCountries.ALL)}",
            "country",
        )

    try:
        result = await google_bq_client.search_by_inventor(
            inventor_name, country, limit, offset, start_date, end_date
        )
        return result
    except Exception as e:
        logger.error(f"Error searching by inventor: {str(e)}")
        return ApiError.create(
            message=f"Failed to search by inventor: {str(e)}", status_code=500
        )


@mcp.tool()
async def google_search_by_assignee(
    assignee_name: str,
    country: str = GooglePatentsCountries.US,
    limit: int = Defaults.SEARCH_LIMIT,
    offset: int = 0,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
) -> Dict[str, Any]:
    """Search Google Patents by assignee/company name

    Finds patents assigned to a specific company or organization. Useful for
    analyzing a company's patent portfolio.

    Args:
        assignee_name: Assignee/company name to search for
        country: Country code (US, EP, WO, JP, CN, KR, GB, DE, FR, CA, AU)
        limit: Maximum number of results to return (default: 100, max: 500)
        offset: Number of results to skip for pagination (default: 0)
        start_date: Optional start date for publication_date filter (YYYYMMDD format, e.g., 20220101)
        end_date: Optional end date for publication_date filter (YYYYMMDD format, e.g., 20251231)

    Returns:
        Dictionary containing search results
    """
    if limit > Defaults.SEARCH_LIMIT_MAX:
        return ApiError.validation_error(
            f"Limit cannot exceed {Defaults.SEARCH_LIMIT_MAX}", "limit"
        )

    if country not in GooglePatentsCountries.ALL:
        return ApiError.validation_error(
            f"Invalid country code. Must be one of: "
            f"{', '.join(GooglePatentsCountries.ALL)}",
            "country",
        )

    try:
        result = await google_bq_client.search_by_assignee(
            assignee_name, country, limit, offset, start_date, end_date
        )
        return result
    except Exception as e:
        logger.error(f"Error searching by assignee: {str(e)}")
        return ApiError.create(
            message=f"Failed to search by assignee: {str(e)}", status_code=500
        )


@mcp.tool()
async def google_search_by_cpc(
    cpc_code: str,
    country: str = GooglePatentsCountries.US,
    limit: int = Defaults.SEARCH_LIMIT,
    offset: int = 0,
    start_date: Optional[int] = None,
    end_date: Optional[int] = None,
) -> Dict[str, Any]:
    """Search Google Patents by CPC classification code

    Finds patents with the specified Cooperative Patent Classification (CPC) code.
    Useful for finding patents in specific technology areas.

    Args:
        cpc_code: CPC code to search for (e.g., G06N3/08 for neural networks)
        country: Country code (US, EP, WO, JP, CN, KR, GB, DE, FR, CA, AU)
        limit: Maximum number of results to return (default: 100, max: 500)
        offset: Number of results to skip for pagination (default: 0)
        start_date: Optional start date for publication_date filter (YYYYMMDD format, e.g., 20220101)
        end_date: Optional end date for publication_date filter (YYYYMMDD format, e.g., 20251231)

    Returns:
        Dictionary containing search results
    """
    if limit > Defaults.SEARCH_LIMIT_MAX:
        return ApiError.validation_error(
            f"Limit cannot exceed {Defaults.SEARCH_LIMIT_MAX}", "limit"
        )

    if country not in GooglePatentsCountries.ALL:
        return ApiError.validation_error(
            f"Invalid country code. Must be one of: "
            f"{', '.join(GooglePatentsCountries.ALL)}",
            "country",
        )

    try:
        result = await google_bq_client.search_by_cpc(
            cpc_code, country, limit, offset, start_date, end_date
        )
        return result
    except Exception as e:
        logger.error(f"Error searching by CPC code: {str(e)}")
        return ApiError.create(
            message=f"Failed to search by CPC code: {str(e)}", status_code=500
        )


# =====================================================================
# Cleanup Handler
# =====================================================================

async def cleanup():
    """Clean up resources on shutdown."""
    logger.info("Shutting down USPTO Patent MCP server, cleaning up resources...")
    try:
        await ppubs_client.close()
        await api_client.close()
        await google_bq_client.close()
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")


def main():
    # Initialize and run the server with stdio transport
    logger.info("Starting USPTO Patent MCP server with stdio transport")
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
