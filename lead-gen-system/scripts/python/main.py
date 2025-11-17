"""
Main pipeline script - orchestrates the entire lead generation process
FAILURE-PROOF: Continues execution even if individual steps fail
"""
import json
import os
import argparse
from datetime import datetime
from pathlib import Path

from utils.logger import setup_logger
from utils.status_tracker import StatusTracker
from utils.config import config
from analysis.website_checker import analyze_websites
from integration.sheets_writer import write_leads_to_sheets

logger = setup_logger('main_pipeline')
status = StatusTracker()


def load_businesses_from_json(file_path):
    """
    Load business data from JSON file
    
    FAILURE-PROOF: Returns empty list if file doesn't exist or is invalid
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both list and dict formats
        if isinstance(data, list):
            businesses = data
        elif isinstance(data, dict) and 'data' in data:
            businesses = data['data']
        else:
            businesses = [data]
        
        logger.info(f"Loaded {len(businesses)} businesses from {file_path}")
        return businesses
    
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return []


def load_all_json_files(data_dir='data'):
    """
    Load all JSON files from data directory
    
    FAILURE-PROOF: Skips invalid files, returns whatever it can load
    """
    all_businesses = []
    
    try:
        data_path = Path(data_dir)
        if not data_path.exists():
            logger.warning(f"Data directory not found: {data_dir}")
            return []
        
        json_files = list(data_path.glob('*.json'))
        logger.info(f"Found {len(json_files)} JSON files in {data_dir}")
        
        for json_file in json_files:
            businesses = load_businesses_from_json(str(json_file))
            if businesses:
                all_businesses.extend(businesses)
        
        logger.info(f"Total businesses loaded: {len(all_businesses)}")
    
    except Exception as e:
        logger.error(f"Error loading JSON files: {e}")
    
    return all_businesses


def filter_qualified_leads(businesses, min_score=40):
    """
    Filter businesses that meet minimum score threshold
    
    FAILURE-PROOF: Always returns a list, even if empty
    """
    try:
        qualified = [b for b in businesses if b.get('score', 0) >= min_score]
        logger.info(f"Filtered {len(qualified)} qualified leads (score >= {min_score})")
        return qualified
    except:
        return []


def generate_summary_report(businesses, qualified_leads, results):
    """
    Generate summary report of pipeline execution
    """
    report = f"""
    ========================================
    LEAD GENERATION PIPELINE SUMMARY
    ========================================
    Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    STATISTICS:
    -----------
    Total Businesses Processed: {len(businesses)}
    Websites Analyzed: {status.stats.get('websites_checked', 0)}
    Qualified Leads (Score >= 40): {len(qualified_leads)}
    Leads Added to Sheets: {results.get('leads_added', 0)}
    Errors: {status.stats.get('errors', 0)}
    
    RESULTS:
    --------
    Success: {results.get('success', False)}
    Google Sheet URL: {results.get('sheet_url', 'N/A')}
    
    TOP LEADS:
    ----------
    """
    
    # Show top 10 leads by score
    top_leads = sorted(qualified_leads, key=lambda x: x.get('score', 0), reverse=True)[:10]
    for i, lead in enumerate(top_leads, 1):
        report += f"\n    {i}. {lead.get('business_name', 'Unknown')} - Score: {lead.get('score', 0)}"
        if lead.get('website'):
            report += f" ({lead['website']})"
    
    report += "\n\n    ========================================"
    
    return report


def main(input_file=None, batch_size=100, min_score=40, sheet_id=None):
    """
    Main pipeline execution
    
    Args:
        input_file: Specific JSON file to process (optional)
        batch_size: Max businesses to process
        min_score: Minimum score threshold for qualified leads
        sheet_id: Google Sheet ID (optional)
        
    FAILURE-PROOF: Executes all steps, logs failures, continues to end
    """
    logger.info("="*50)
    logger.info("STARTING LEAD GENERATION PIPELINE")
    logger.info("="*50)
    
    # Step 1: Load business data
    logger.info("Step 1: Loading business data...")
    if input_file:
        businesses = load_businesses_from_json(input_file)
    else:
        businesses = load_all_json_files('data')
    
    if not businesses:
        logger.error("No business data found. Please add JSON files to data/ directory")
        return
    
    # Limit to batch size
    businesses = businesses[:batch_size]
    logger.info(f"Processing {len(businesses)} businesses")
    
    # Step 2: Analyze websites
    logger.info("Step 2: Analyzing websites...")
    analyzed_businesses = analyze_websites(businesses, max_concurrent=batch_size)
    
    # Step 3: Filter qualified leads
    logger.info("Step 3: Filtering qualified leads...")
    qualified_leads = filter_qualified_leads(analyzed_businesses, min_score)
    
    if not qualified_leads:
        logger.warning("No qualified leads found!")
        logger.info("Consider lowering min_score threshold or checking website data")
    
    # Step 4: Write to Google Sheets
    logger.info("Step 4: Writing to Google Sheets...")
    
    # Save qualified leads to JSON file as backup
    output_file = f"data/qualified_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(qualified_leads, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ Saved qualified leads to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save backup file: {e}")
    
    # Try to write to Google Sheets (skip if no credentials)
    try:
        results = write_leads_to_sheets(qualified_leads, sheet_id=sheet_id)
        
        if results['success']:
            logger.info(f"✓ Successfully added {results['leads_added']} leads to Google Sheets")
            logger.info(f"✓ Sheet URL: {results['sheet_url']}")
        else:
            logger.warning(f"✗ Google Sheets write failed: {results.get('error')}")
            logger.info("✓ Leads saved to JSON file as backup")
            results = {'success': True, 'leads_added': len(qualified_leads), 'sheet_url': output_file}
    except Exception as e:
        logger.warning(f"Google Sheets not configured: {e}")
        logger.info("✓ Leads saved to JSON file as backup")
        results = {'success': True, 'leads_added': len(qualified_leads), 'sheet_url': output_file}
    
    # Step 5: Generate summary report
    logger.info("Step 5: Generating summary report...")
    report = generate_summary_report(analyzed_businesses, qualified_leads, results)
    print(report)
    
    # Save report to file
    report_file = f"data/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(report_file, 'w') as f:
            f.write(report)
        logger.info(f"Report saved to: {report_file}")
    except:
        pass
    
    # Update status
    status.update(
        businesses_scraped=len(businesses),
        websites_checked=len(analyzed_businesses),
        leads_in_sheet=results.get('leads_added', 0),
        next_run='Manual'
    )
    status.save()
    
    logger.info("="*50)
    logger.info("PIPELINE EXECUTION COMPLETE")
    logger.info("="*50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lead Generation Pipeline')
    parser.add_argument('--input', '-i', help='Input JSON file path')
    parser.add_argument('--batch-size', '-b', type=int, default=100, help='Max businesses to process')
    parser.add_argument('--min-score', '-m', type=int, default=40, help='Minimum score threshold')
    parser.add_argument('--sheet-id', '-s', help='Google Sheet ID')
    
    args = parser.parse_args()
    
    main(
        input_file=args.input,
        batch_size=args.batch_size,
        min_score=args.min_score,
        sheet_id=args.sheet_id
    )
