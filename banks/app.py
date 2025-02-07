import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from data_analysis.bank_stats import BankSavingsAnalyzer
from data_analysis.model_visualization import SavingsModelVisualizer
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')

# Create static directory if it doesn't exist
static_dir = Path(__file__).parent / 'static'
static_dir.mkdir(exist_ok=True)

# Initialize the analyzers
data_dir = Path(__file__).parent / 'data'
analyzer = BankSavingsAnalyzer(data_dir)
visualizer = SavingsModelVisualizer(data_dir)

# Generate visualizations on startup
visualizer.generate_all_visualizations()

@app.route('/')
def index():
    """Render the main page"""
    try:
        # Get initial statistics
        stats = analyzer.get_all_stats()
        return render_template('index.html', stats=stats)
    except Exception as e:
        logger.exception('Error in index route')
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    """Handle prediction requests"""
    try:
        data = request.json
        logger.debug(f'Received prediction request with data: {data}')
        
        # Extract parameters
        num_clients = int(data['num_clients'])
        company_types = data['company_types']  # List of selected types
        engagement_level = data['engagement_level']
        
        logger.debug(f'Parsed parameters: num_clients={num_clients}, company_types={company_types}, engagement_level={engagement_level}')
        
        # Get predictions
        annual_savings = analyzer.predict_annual_savings(
            num_clients=num_clients,
            company_types=company_types,
            engagement_level=engagement_level
        )
        logger.debug(f'Generated annual savings prediction: {annual_savings}')
        
        # Get top offers based on selected parameters
        top_offers = analyzer.get_top_offers(
            num_clients=num_clients,
            company_types=company_types,
            engagement_level=engagement_level
        )
        logger.debug(f'Generated top offers: {top_offers.to_dict("records")}')
        
        response_data = {
            'annual_savings': annual_savings,
            'top_offers': top_offers.to_dict('records')
        }
        logger.debug(f'Sending response: {response_data}')
        
        return jsonify(response_data)
    except Exception as e:
        logger.exception('Error in predict route')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
