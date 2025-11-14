"""AI agent that queries MongoDB, runs analysis via LLM, and stores results."""
import os
from pymongo import MongoClient
from flask import Flask, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongo:27017')
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

app = Flask(__name__)

def run_analysis():
    """Fetch recent logs, generate AI analysis, store result."""
    try:
        logger.info("Starting analysis...")
        logger.info(f"Connecting to MongoDB at {MONGO_URI}")
        
        client = MongoClient(MONGO_URI)
        db = client.dalias
        processed_logs = db.processed_logs
        
        # Get recent logs
        logger.info("Fetching logs...")
        logs = list(processed_logs.find().sort([('_id', -1)]).limit(100))
        logger.info(f"Found {len(logs)} logs")
        
        if not logs:
            return "No logs found for analysis."
        
        # Calculate statistics
        total = len(logs)
        errors = sum(1 for l in logs if l.get('level') == 'error')
        warnings = sum(1 for l in logs if l.get('level') == 'warning')
        anomalies = sum(1 for l in logs if l.get('anomaly'))
        services = set(l.get('service', 'unknown') for l in logs)
        
        # Get only critical/anomalous logs for analysis
        critical_logs = [l for l in logs if l.get('anomaly') or l.get('level') in ['error', 'warning']][:15]
        
        log_summary = "\n".join([
            f"[{l.get('timestamp', 'N/A')}] [{l.get('service', 'unknown')}] "
            f"[{l.get('level', 'info')}] {l.get('message', '')}"
            for l in critical_logs
        ])
        
        # Check if API key is set
        if not GOOGLE_API_KEY:
            logger.warning("Google API key not set, returning mock analysis")
            return f"""QUICK ANALYSIS (Mock - No API Key)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STATS
- Total: {total} logs | Errors: {errors} | Warnings: {warnings} | Anomalies: {anomalies} ({round(anomalies/total*100, 1)}%)
- Services: {', '.join(sorted(services))}

TOP ISSUES
- Database connection timeouts detected
- Background job failures occurring
- High anomaly rate indicates instability

RECOMMENDATIONS
- Check database health and connection pools
- Review error logs for root cause
- Monitor system resources

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Set GOOGLE_API_KEY for AI-powered analysis
"""
        
        # Call LLM with focused prompt for concise output
        logger.info("Calling Gemini API...")
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        
        prompt = f"""You are a system monitoring AI. Analyze these logs and provide a CONCISE summary.

STATS:
- Total: {total} logs
- Errors: {errors}
- Warnings: {warnings}
- Anomalies: {anomalies} ({round(anomalies/total*100, 1)}%)
- Services: {', '.join(sorted(services))}

CRITICAL ISSUES (last 15):
{log_summary}

Provide a SHORT analysis (max 150 words) with:
1. ONE sentence describing the main issue
2. List 2-3 specific problems (use bullet points)
3. List 2-3 actionable recommendations (use bullet points)

Format:
MAIN ISSUE: [one sentence]

KEY PROBLEMS:
- [problem 1]
- [problem 2]
- [problem 3]

RECOMMENDATIONS:
- [action 1]
- [action 2]
- [action 3]

Be SPECIFIC and ACTIONABLE. No fluff or lengthy explanations."""
        
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        response = model.generate_content(prompt)
        analysis_text = response.text
        
        # Format the final output
        formatted_output = f"""SYSTEM HEALTH ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUICK STATS
- Total: {total} logs | Errors: {errors} | Warnings: {warnings} | Anomalies: {anomalies} ({round(anomalies/total*100, 1)}%)
- Services: {', '.join(sorted(services))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{analysis_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Last updated: {logs[0].get('timestamp')}
Analyzed {total} log entries
"""
        
        logger.info("Analysis completed, storing results...")
        # Store analysis result
        db.agent_analysis.insert_one({
            'timestamp': logs[0].get('timestamp'),
            'analysis': formatted_output,
            'log_count': total,
            'stats': {
                'total': total,
                'errors': errors,
                'warnings': warnings,
                'anomalies': anomalies,
                'anomaly_rate': round(anomalies/total*100, 1),
                'services': list(services)
            }
        })
        
        return formatted_output
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        return f"Analysis failed: {str(e)}"

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/analyze')
def analyze():
    """Endpoint to trigger analysis."""
    logger.info("Analysis endpoint called")
    result = run_analysis()
    return result

if __name__ == '__main__':
    logger.info("Starting agent service on port 5000")
    logger.info(f"MongoDB URI: {MONGO_URI}")
    logger.info(f"Google API Key set: {bool(GOOGLE_API_KEY)}")
    app.run(host='0.0.0.0', port=5000, debug=True)