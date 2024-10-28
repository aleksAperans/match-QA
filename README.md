# Sayari Match Resolution Labelling App

This application is a Flask-based web interface for processing and labeling entity resolution results using the Sayari API. It allows users to upload CSV files containing entity information, process them through Sayari's resolution service, and manually label the results.

## Features

- Upload CSV files with entity information
- Process entities through Sayari's resolution API
- Display resolution results with input and output information
- Allow manual labeling of name, address, and overall match quality
- Translate entity information to English
- Export labeled results as a CSV file
- Visualize match statistics with a pie chart

## Prerequisites

- Python 3.7+
- Flask
- Sayari API credentials (for both production and development environments)
- Google Translate API access (for translation feature)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/sayari-match-resolution-app.git
   cd sayari-match-resolution-app
   ```


2. Create a `.env` file in the project root and add your Sayari API credentials:
   ```
   # Prod Credentials
   client_id=your_production_client_id
   client_secret=your_production_client_secret

   # Dev Credentials
   dev_client_id=your_development_client_id
   dev_client_secret=your_development_client_secret
   ```

## Usage

1. Start the Flask application:
   ```
   python app.py or python3 app.py
   ```

2. Open a web browser and navigate to `http://localhost:5000`

3. Use the web interface to:
   - Upload a CSV file with entity information
   - Configure resolution parameters
   - Process the file through Sayari's resolution API
   - View and label the results
   - Export labeled results

## Project Structure

- `app.py`: Main Flask application file
- `templates/`: HTML templates for the web interface
- `label_storage/`: Directory for storing label data
- `.env`: Configuration file for API credentials

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Sayari for providing the resolution API
- Flask and its extensions for the web framework
- Chart.js for data visualization
