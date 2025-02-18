import logging
from flask import Flask, render_template, request, jsonify
from data_analysis.bank_stats import BankSavingsAnalyzer
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')

# Initialize the analyzer
data_dir = Path(__file__).parent / 'data'
analyzer = BankSavingsAnalyzer(data_dir)

def format_number(num):
    """Format numbers with appropriate units (K, M, B) and minimal decimal places."""
    if abs(num) >= 1e9:
        return f"${num/1e9:.1f}B"
    elif abs(num) >= 1e6:
        return f"${num/1e6:.1f}M"
    elif abs(num) >= 1e3:
        return f"${num/1e3:.1f}K"
    else:
        return f"${num:.0f}"

@app.route('/')
def index():
    """Render the main page"""
    return render_template('new_index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle prediction requests"""
    try:
        data = request.get_json()
        
        # Extract values from request
        num_startup_clients = int(data.get('num_startup_clients', 0))
        num_sme_clients = int(data.get('num_sme_clients', 0))
        engagement_level = data.get('engagement_level', 'rarely')
        
        # Calculate predictions
        predictions = {}
        total_savings = 0
        
        if num_startup_clients > 0:
            startup_pred = analyzer.predict_annual_savings(
                num_startup_clients,
                ['startup'],
                engagement_level
            )
            predictions['startup'] = {
                'clients': num_startup_clients,
                'savings': startup_pred,
                'formatted_savings': format_number(startup_pred)
            }
            total_savings += startup_pred
            
        if num_sme_clients > 0:
            sme_pred = analyzer.predict_annual_savings(
                num_sme_clients,
                ['sme'],
                engagement_level
            )
            predictions['sme'] = {
                'clients': num_sme_clients,
                'savings': sme_pred,
                'formatted_savings': format_number(sme_pred)
            }
            total_savings += sme_pred
            
        predictions['total'] = {
            'savings': total_savings,
            'formatted_savings': format_number(total_savings)
        }
        
        # Get top offers if there are any clients
        if total_savings > 0:
            total_clients = num_startup_clients + num_sme_clients
            company_types = []
            if num_startup_clients > 0:
                company_types.append('startup')
            if num_sme_clients > 0:
                company_types.append('sme')
                
            top_offers = analyzer.get_top_offers(
                total_clients,
                company_types,
                engagement_level
            )
            
            # Format top offers for display
            predictions['top_offers'] = [{
                'name': offer['Name of offer'],
                'savings': format_number(offer['avg_savings']),
                'companies': int(offer['unique_companies']),
                'usage_count': int(offer['usage_count'])
            } for offer in top_offers]
        
        return jsonify({
            'success': True,
            'predictions': predictions
        })
        
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
