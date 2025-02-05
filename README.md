# Job Set & Match!

A Streamlit application that helps prioritize your job search by automatically analyzing job offers and generating application materials using Claude AI.

## Features

- Automated job offer analysis using Claude AI
- Structured evaluation of career fit and profile match
- Strategic recommendations for job applications
- Automatic cover letter generation
- PDF file management and organization
- Efficient data storage with JSON and Parquet support

## Project Structure

```
app/
├── config/               # Configuration management
│   ├── paths.py         # Path configurations
│   └── settings.py      # Global settings
├── core/                # Core functionality
│   ├── analyzer/        # Job analysis components
│   │   ├── prompts/     # Claude AI prompts
│   │   └── offer_analyzer.py
│   └── storage/         # Data storage components
│       ├── base.py      # Abstract storage interface
│       ├── json_handler.py
│       └── parquet_handler.py
├── data/                # Application data
│   ├── analyses/        # Analysis results
│   │   ├── json/       # JSON storage
│   │   └── parquet/    # Parquet storage
│   └── context/        # Personal context documents
├── migrations/          # Data migration utilities
├── offers/             # Job offer PDFs
│   ├── 0_new/         # New offers to analyze
│   ├── 1_in_progress/ # Offers being processed
│   └── 2_archived/    # Processed offers
└── app.py              # Main Streamlit application
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a .env file with your API key:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

## Usage

1. Place job offer PDFs in `app/offers/0_new/`
2. Run the application:
   ```bash
   cd app
   streamlit run app.py
   ```
3. Click "Analyze New Offers" to process job offers
4. View analyses, generate cover letters, and manage offers through the interface

## Configuration

- `MAX_FILE_SIZE_MB`: Maximum PDF file size (default: 10MB)
- `CLEANUP_DAYS`: Days to keep archived files (default: 30)

## Data Storage

The application uses both JSON and Parquet storage:
- JSON: Human-readable, backwards compatible
- Parquet: Efficient columnar storage for better performance

To migrate from JSON to Parquet:
```bash
python migrate_storage.py --verify
```

## Personal Context

Place your personal context documents in `app/data/context/`:
- `profile.txt`: Professional profile
- `resume.txt`: CV/Resume
- `preferences.txt`: Job preferences

## Development

### Requirements
- Python 3.8+
- Dependencies listed in requirements.txt

### Code Style
The project uses:
- black for code formatting
- flake8 for linting
- isort for import sorting
- mypy for type checking

### Testing
Run tests with:
```bash
pytest
```

## License

See LICENSE file.
