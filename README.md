# Auto Inventor

Auto Inventor is an AI-powered tool that leverages Large Language Models (LLMs) to generate new invention ideas based on user prompts and existing patents. It automates the process of patent research, idea generation, and initial patent drafting.

## Features

- Patent research using Google Patents Public Dataset
- AI-powered invention idea generation
- Detailed invention description creation
- Initial patent document drafting
- Comprehensive final report generation

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Python 3.7+
- An Anthropic API key
- Access to Google Cloud Platform and BigQuery
- Google Cloud credentials set up

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/auto-inventor.git
   cd auto-inventor
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   - Create a `.env` file in the project root
   - Add your Anthropic API key:
     ```
     ANTHROPIC_API_KEY=your_api_key_here
     ```
   - Set up your Google Cloud credentials as per Google Cloud documentation

## Usage

1. Run the main script:
   ```
   python main.py
   ```

2. Enter your invention prompt when prompted.

3. The script will generate a comprehensive report including:
   - Relevant patents
   - New invention ideas
   - Detailed invention description
   - Initial patent document

4. The final report will be saved as a Markdown file in the project directory.

## Project Structure

- `main.py`: The main script that orchestrates the entire process
- `requirements.txt`: List of Python package dependencies
- `README.md`: This file, containing project documentation

## Contributing

Contributions to Auto Inventor are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Anthropic for their powerful Claude AI model
- Google for providing access to the Patents Public Dataset

## Disclaimer

This tool is for educational and research purposes only. Always consult with a qualified patent attorney before filing a patent application.