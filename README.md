# Job Set & Match!

A Streamlit application that leverages Claude AI to analyze job offers and generate application materials.

## Features

- 📄 AI-powered job offer analysis using Claude
- 📝 Smart cover letter generation
- 📊 Interactive dashboard
- 📁 Automatic file management
- 💰 API cost tracking

## Project Structure

```
job_set_and_match/
├── helpers/
│   ├── __init__.py
│   ├── analyzer.py      # Claude API integration for analysis and generation
│   └── config.py        # Constants and environment configs
│   ├── data_handler.py  # API response and cost tracking
│   └── file_manager.py  # File operations handling
├── offers/
│   ├── new/            # New PDFs to analyze
│   ├── in_progress/    # Being worked on
│   └── archived/       # Rejected offers
├── data/
│   └── analyses.json   # Analysis results and API usage data
├── .env.example        # Example environment variables
├── .gitignore         # Git ignore rules
├── app.py             # Main Streamlit application
└── requirements.txt   # Project dependencies
```

## Setup

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env with your settings
   # Required:
   ANTHROPIC_API_KEY=your-api-key-here

   # Optional:
   MAX_FILE_SIZE_MB=10
   CLEANUP_DAYS=30
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Usage

1. Place job offer PDFs in the `offers/new` directory
   - Files can have any name initially
   - After analysis, files are automatically renamed using the format:
     `company_position_date.pdf`

2. Add personal context files to `./data` directory
   - Add any text files (*.txt) that describe your profile:
     * CV/Resume
     * Professional summary
     * Key achievements
     * Skills and expertise
     * Notable projects
   - Files are automatically processed and used to enhance analysis accuracy
   - Each file should be a plain text file (.txt format)
   - Content should be clear and well-structured
   - Files are used to provide context for both analysis and cover letter generation

3. Click "Analyze New Offers" to process job offers
   - Claude AI analyzes each offer for:
     * Company and position details
     * Required and preferred skills
     * Experience requirements
     * Benefits and culture indicators
     * Potential red flags
   - Match scores are calculated based on the analysis

4. Use the dashboard to:
   - View detailed analysis results
   - Generate tailored cover letters
   - Track API usage costs
   - Archive processed offers

## Environment Variables

The application uses the following environment variables:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| ANTHROPIC_API_KEY | Yes | Your Claude API key | None |
| MAX_FILE_SIZE_MB | No | Maximum PDF file size | 10 |
| CLEANUP_DAYS | No | Days before archived files are deleted | 30 |

## File Management

The application manages files through three stages:

1. **New** (`offers/new/`)
   - Initial upload location
   - Accepts any PDF filename
   - Pending analysis

2. **In Progress** (`offers/in_progress/`)
   - Currently being analyzed
   - Files renamed after analysis
   - Cover letter generation available

3. **Archived** (`offers/archived/`)
   - Processed or rejected offers
   - Auto-cleaned after specified days (CLEANUP_DAYS)

## Data Storage

Analysis results and API usage are stored in `data/analyses.json`:

```json
{
  "timestamp": "2024-02-19T10:00:00",
  "analyses": [
    {
      "timestamp": "2024-02-19T10:00:00",
      "offers": [
        {
          "jobSummary": {
            "jobTitle": "",
            "jobCompany": "",
            "jobLocation": "",
            "jobOverview": ""
          },
          "careerFitAnalysis": {
            "careerAnalysis": "",
            "careerDevelopmentRating": 0
          },
          "profileMatchAssessment": {
            "profileMatchAnalysis": "",
            "matchCompatibilityRating": 0
          },
          "competitiveProfile": {
            "competitiveAnalysis": "",
            "successProbabilityRating": 0
          },
          "strategicRecommendations": {
            "shouldApply": {
              "decision": false,
              "explanation": "",
              "chanceRating": 0
            },
            "keyPointsToEmphasize": [],
            "keyWordsToUse": [],
            "preparationSteps": "",
            "interviewFocusAreas": ""
          },
          "offerContent": "",
          "file_name": "",
          "analysis_cost": 0.0,
          "cover_letter": {
            "content": "",
            "generated_at": "2024-02-19T10:00:00",
            "generation_cost": 0.0
          }
        }
      ]
    }
  ],
  "api_usage": {
    "total_cost": 0.0,
    "analysis_costs": 0.0,
    "cover_letter_costs": 0.0,
    "requests_count": 0
  }
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
