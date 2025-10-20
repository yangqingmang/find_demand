# Find Demand - Market Demand Analysis Toolkit

## Project Overview

This project is a Python-based toolkit for market demand analysis. It automates the process of discovering, validating, and executing on market demand. The toolkit collects data from various sources, including Google, Reddit, and Product Hunt, and then uses a combination of scoring, intent analysis, and trend monitoring to identify high-opportunity keywords. It can also generate landing pages based on the analysis.

The project is structured into several components:

*   **`src/collectors`**: Contains the code for collecting data from different sources.
*   **`src/demand_mining`**: Contains the core logic for demand mining, including managers, analyzers, and tools.
*   **`src/pipeline`**: Contains the code for cleaning, transforming, and orchestrating the data.
*   **`src/website_builder`**: Contains the code for generating websites based on the analysis.
*   **`config`**: Contains the configuration files for the project.
*   **`data`**: Contains sample data and cached artifacts.
*   **`docs`**: Contains documentation for the project.
*   **`output`**: Contains the generated reports and other outputs.
*   **`tests`**: Contains the tests for the project.

## Building and Running

### Installation

1.  Create a virtual environment:
    ```bash
    python -m venv .venv
    ```
2.  Activate the virtual environment:
    *   On Windows:
        ```bash
        .venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
3.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Install Playwright browsers:
    ```bash
    playwright install chromium
    ```

### Running the Application

The application is run from the command line using `main.py`. Here are some examples:

*   Analyze a prepared keyword list:
    ```bash
    python main.py --input data/keywords.csv
    ```
*   Seed discovery and analysis pipeline:
    ```bash
    python main.py --discover "AI tool" "AI generator"
    ```
*   Get a full CLI reference:
    ```bash
    python main.py --help
    ```

### Testing

The project uses `pytest` for testing. To run the tests, use the following command:

```bash
pytest
```

## Development Conventions

*   **Coding Style**: The project follows the PEP 8 style guide for Python code.
*   **Testing**: The project uses `pytest` for testing. New features should be accompanied by tests.
*   **Configuration**: The project is configured using JSON files in the `config/` directory.
*   **Dependencies**: New dependencies should be added to the `requirements.txt` file.
