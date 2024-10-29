# Sayari Match Resolution Labelling App

This application is a Flask-based web interface for processing and labeling match resolution results using the Sayari API. It allows users to upload CSV files containing entity information, process them through Sayari's resolution service, and manually label the results.

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

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your .env file with your Sayari API credentials as described in the Configuration section.

4. Run the application:
   ```
   python app.py
   ```

5. Open a web browser and navigate to `http://localhost:5000`
```

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
