"""
Google Sheets integration - simplified and failure-proof
Writes lead data to Google Sheets
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
from utils.logger import setup_logger
from utils.config import config
import pandas as pd

logger = setup_logger('sheets_writer')

# Google Sheets API scope
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def authenticate_sheets(credentials_file=None):
    """
    Authenticate with Google Sheets API
    
    Args:
        credentials_file: Path to service account JSON file
        
    Returns:
        Authenticated gspread client
        
    FAILURE-PROOF: Returns None if authentication fails
    """
    try:
        if not credentials_file:
            credentials_file = config.GOOGLE_SERVICE_ACCOUNT_JSON
        
        if not credentials_file or not os.path.exists(credentials_file):
            logger.error(f"Credentials file not found: {credentials_file}")
            return None
        
        creds = Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        logger.info("Successfully authenticated with Google Sheets")
        return client
    
    except Exception as e:
        logger.error(f"Failed to authenticate with Google Sheets: {e}")
        return None


def get_or_create_sheet(client, sheet_id=None, sheet_name="Lead Gen Data"):
    """
    Get existing sheet or create new one
    
    Args:
        client: Authenticated gspread client
        sheet_id: Google Sheet ID (optional)
        sheet_name: Name of worksheet tab
        
    Returns:
        Worksheet object or None
        
    FAILURE-PROOF: Returns None if operation fails
    """
    try:
        if not client:
            return None
        
        if sheet_id:
            # Open existing spreadsheet
            spreadsheet = client.open_by_key(sheet_id)
        else:
            # Create new spreadsheet
            spreadsheet = client.create(f"Lead Gen Data {datetime.now().strftime('%Y-%m-%d')}")
            logger.info(f"Created new spreadsheet: {spreadsheet.url}")
        
        # Get or create worksheet
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)
        
        return worksheet
    
    except Exception as e:
        logger.error(f"Failed to get/create sheet: {e}")
        return None


def initialize_sheet_headers(worksheet):
    """
    Set up column headers in the sheet
    
    FAILURE-PROOF: Returns False if operation fails
    """
    try:
        headers = [
            'Business Name',
            'Website',
            'Phone',
            'Address',
            'Score',
            'Has Website',
            'Has SSL',
            'Fast Load',
            'Category',
            'Location',
            'Source',
            'Added Date'
        ]
        
        # Check if headers already exist
        existing = worksheet.row_values(1)
        if not existing or existing[0] != headers[0]:
            worksheet.update('A1:L1', [headers])
            logger.info("Sheet headers initialized")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to initialize headers: {e}")
        return False


def append_leads(worksheet, leads):
    """
    Append leads to the Google Sheet
    
    Args:
        worksheet: Google Sheets worksheet object
        leads: List of lead dicts
        
    Returns:
        Number of leads successfully added
        
    FAILURE-PROOF: Continues processing even if individual rows fail
    """
    if not worksheet:
        logger.error("No worksheet provided")
        return 0
    
    added_count = 0
    rows_to_add = []
    
    for lead in leads:
        try:
            analysis = lead.get('website_analysis', {})
            
            row = [
                lead.get('business_name', ''),
                lead.get('website', ''),
                lead.get('phone', ''),
                lead.get('address', ''),
                lead.get('score', 0),
                'Yes' if analysis.get('exists') else 'No',
                'Yes' if analysis.get('has_ssl') else 'No',
                'Yes' if analysis.get('fast_load') else 'No',
                lead.get('category', ''),
                lead.get('location', ''),
                lead.get('source', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            rows_to_add.append(row)
        
        except Exception as e:
            logger.error(f"Failed to format lead: {e}")
            continue
    
    # Batch append for efficiency
    if rows_to_add:
        try:
            worksheet.append_rows(rows_to_add)
            added_count = len(rows_to_add)
            logger.info(f"Successfully added {added_count} leads to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to append rows: {e}")
            # Try one by one as fallback
            for row in rows_to_add:
                try:
                    worksheet.append_row(row)
                    added_count += 1
                except:
                    continue
    
    return added_count


def write_leads_to_sheets(leads, sheet_id=None, credentials_file=None):
    """
    Main function to write leads to Google Sheets
    
    Args:
        leads: List of lead dicts with website analysis
        sheet_id: Google Sheet ID (optional)
        credentials_file: Path to service account JSON
        
    Returns:
        dict with success status and count
        
    FAILURE-PROOF: Always returns a valid result dict
    """
    result = {
        'success': False,
        'leads_added': 0,
        'sheet_url': None,
        'error': None
    }
    
    try:
        # Authenticate
        client = authenticate_sheets(credentials_file)
        if not client:
            result['error'] = 'Authentication failed'
            return result
        
        # Get/create worksheet
        worksheet = get_or_create_sheet(client, sheet_id)
        if not worksheet:
            result['error'] = 'Failed to get/create worksheet'
            return result
        
        # Initialize headers
        initialize_sheet_headers(worksheet)
        
        # Append leads
        count = append_leads(worksheet, leads)
        
        result['success'] = count > 0
        result['leads_added'] = count
        result['sheet_url'] = worksheet.spreadsheet.url
        
        logger.info(f"Write to Sheets complete: {count} leads added")
    
    except Exception as e:
        logger.error(f"Failed to write to Google Sheets: {e}")
        result['error'] = str(e)
    
    return result


def write_dataframe_to_sheets(df: pd.DataFrame, sheet_id: str | None = None, credentials_file: str | None = None, split_by_venture: bool = True) -> dict:
    """Write a pandas DataFrame to Google Sheets.

    - Creates/opens a spreadsheet
    - Writes an 'All_Leads' worksheet
    - Optionally writes one worksheet per venture_type

    Returns dict with success, sheet_url, worksheets list
    """
    result = {
        'success': False,
        'sheet_url': None,
        'worksheets': [],
        'error': None
    }

    try:
        client = authenticate_sheets(credentials_file)
        if not client:
            result['error'] = 'Authentication failed'
            return result

        # Open or create spreadsheet
        if sheet_id:
            spreadsheet = client.open_by_key(sheet_id)
        else:
            spreadsheet = client.create(f"Leads {datetime.now().strftime('%Y-%m-%d')}")
            logger.info(f"Created spreadsheet: {spreadsheet.url}")

        def upsert_worksheet(title: str, rows: int, cols: int):
            try:
                ws = spreadsheet.worksheet(title)
                ws.clear()
            except Exception:
                ws = spreadsheet.add_worksheet(title=title, rows=max(rows, 1000), cols=max(cols, 20))
            return ws

        # All_Leads
        all_ws = upsert_worksheet('All_Leads', rows=len(df) + 2, cols=len(df.columns) + 2)
        # Prepare values
        header = [list(df.columns)]
        values = df.fillna('').astype(str).values.tolist()
        all_ws.update('A1', header + values)
        result['worksheets'].append('All_Leads')

        if split_by_venture and 'venture_type' in df.columns:
            for vt, sub in df.groupby('venture_type'):
                if not vt:
                    continue
                safe = ''.join(ch if ch.isalnum() or ch in ('_',) else '_' for ch in str(vt))[:28]
                ws = upsert_worksheet(safe, rows=len(sub) + 2, cols=len(sub.columns) + 2)
                ws.update('A1', [list(sub.columns)] + sub.fillna('').astype(str).values.tolist())
                result['worksheets'].append(safe)

        result['success'] = True
        result['sheet_url'] = spreadsheet.url
        logger.info(f"Finished writing DataFrame to Google Sheets: {spreadsheet.url}")
        return result

    except Exception as e:
        logger.error(f"Failed to write DataFrame to Google Sheets: {e}")
        result['error'] = str(e)
        return result


def write_df_to_specific_worksheet(df: pd.DataFrame, worksheet_title: str = 'Instagram_Influencer_Leads', sheet_id: str | None = None, credentials_file: str | None = None) -> dict:
    """Write a DataFrame to a specific worksheet in the target spreadsheet.

    - Authenticates via service account
    - Opens existing spreadsheet by `sheet_id` or creates a new one
    - Upserts the worksheet named `worksheet_title`
    - Clears and writes headers + values starting at A1

    Returns dict with success, sheet_url, worksheet_title
    """
    result = {
        'success': False,
        'sheet_url': None,
        'worksheet_title': worksheet_title,
        'error': None
    }

    try:
        client = authenticate_sheets(credentials_file)
        if not client:
            result['error'] = 'Authentication failed'
            return result

        # Open or create spreadsheet
        if sheet_id:
            spreadsheet = client.open_by_key(sheet_id)
        else:
            spreadsheet = client.create(f"Leads {datetime.now().strftime('%Y-%m-%d')}")
            logger.info(f"Created spreadsheet: {spreadsheet.url}")

        # Upsert worksheet
        try:
            ws = spreadsheet.worksheet(worksheet_title)
            ws.clear()
        except Exception:
            ws = spreadsheet.add_worksheet(title=worksheet_title, rows=max(len(df) + 2, 1000), cols=max(len(df.columns) + 2, 20))

        # Prepare and update
        header = [list(df.columns)]
        values = df.fillna('').astype(str).values.tolist()
        ws.update('A1', header + values)

        result['success'] = True
        result['sheet_url'] = spreadsheet.url
        logger.info(f"Wrote {len(values)} rows to worksheet '{worksheet_title}' -> {spreadsheet.url}")
        return result

    except Exception as e:
        logger.error(f"Failed to write DataFrame to worksheet '{worksheet_title}': {e}")
        result['error'] = str(e)
        return result


if __name__ == '__main__':
    # Optional CLI: push data/leads.csv to Sheets
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'leads.csv')
        if os.path.exists(data_path):
            df = pd.read_csv(data_path)
            print('Uploading data/leads.csv to Google Sheets...')
            res = write_dataframe_to_sheets(df, sheet_id=config.GOOGLE_SHEET_ID or None, credentials_file=config.GOOGLE_SERVICE_ACCOUNT_JSON or None)
            print(res)
        else:
            print('data/leads.csv not found. Run utils/merge_datasets.py first.')
    except Exception as e:
        print('Error:', e)


if __name__ == "__main__":
    # Test with sample data
    test_leads = [
        {
            'business_name': 'Test Restaurant',
            'website': 'https://example.com',
            'phone': '9876543210',
            'address': 'Mumbai',
            'score': 80,
            'category': 'Restaurants',
            'location': 'Mumbai',
            'source': 'test',
            'website_analysis': {
                'exists': True,
                'has_ssl': True,
                'fast_load': True
            }
        }
    ]
    
    print("NOTE: To test, you need to:")
    print("1. Create a service account in Google Cloud Console")
    print("2. Download the JSON credentials file")
    print("3. Set GOOGLE_SERVICE_ACCOUNT_JSON in .env")
    print("4. Share your Google Sheet with the service account email")
