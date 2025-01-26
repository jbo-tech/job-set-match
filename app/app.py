"""
Job Set & Match! - A Streamlit application that helps prioritize your job search by
automatically analyzing job offers and generating application materials using Claude AI.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import os
import json
import base64

# Import helpers
from helpers import (
    FileManager,
    OfferAnalyzer,
    DataHandler,
    OFFERS_PATH,
    NEW_OFFERS_PATH,
    IN_PROGRESS_PATH,
    ARCHIVED_PATH,
    DATA_PATH,
    ANALYSES_FILE,
    MAX_FILE_SIZE_MB,
    CLEANUP_DAYS
)

def check_environment():
    """Check if all required environment variables are set."""
    if not os.getenv('ANTHROPIC_API_KEY'):
        st.error("ANTHROPIC_API_KEY not found in environment variables. Please set it in your .env file.")
        st.stop()

@st.cache_resource
def init_file_manager():
    return FileManager(
        NEW_OFFERS_PATH,
        IN_PROGRESS_PATH,
        ARCHIVED_PATH,
        max_file_size_mb=MAX_FILE_SIZE_MB,
        cleanup_days=CLEANUP_DAYS
    )

@st.cache_resource
def init_analyzer():
    return OfferAnalyzer()

@st.cache_resource
def init_data_handler():
    return DataHandler(ANALYSES_FILE)

def initialize_app():
    """Initialize the application state and configuration."""
    st.set_page_config(
        page_title="Job Set & Match!",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.session_state.update({
        'allow_output_mutation': True,
        'suppress_st_warning': True
    })

    # Check environment variables
    check_environment()

    # Initialize core components
    if 'file_manager' not in st.session_state:
        st.session_state.file_manager = init_file_manager()

    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = init_analyzer()

    if 'data_handler' not in st.session_state:
        st.session_state.data_handler = init_data_handler()

def analyze_new_offers():
    """Analyze new job offers using Claude API."""
    new_offers = st.session_state.file_manager.get_new_offers()

    if not new_offers:
        st.warning("No new offers found in the input directory.")
        return

    for offer_path in new_offers:
        # Check file size
        if (offer_path.stat().st_size / (1024 * 1024)) > MAX_FILE_SIZE_MB:
            st.error(f"File too large: {offer_path.name} (max {MAX_FILE_SIZE_MB}MB)")
            continue

        # Move to in_progress first
        new_path = st.session_state.file_manager.move_to_in_progress(offer_path)
        if not new_path:
            st.error(f"Failed to process {offer_path.name}")
            continue

        # Analyze offer with Claude
        with st.spinner(f"Analyzing {new_path.name} with AI..."):
            analysis = st.session_state.analyzer.analyze_pdf(new_path)
            if not analysis:
                st.error(f"Failed to analyze {new_path.name}")
                continue

        # Standardize filename using analysis results
        standardized_path = st.session_state.file_manager.rename_after_analysis(
            new_path,
            analysis["jobSummary"]["jobCompany"],
            analysis["jobSummary"]["jobTitle"]
        )

        if not standardized_path:
            st.error(f"Failed to standardize filename for {new_path.name}")
            continue

        # Update analysis with new filename
        analysis["file_name"] = standardized_path.name

        # Save analysis
        if st.session_state.data_handler.add_analysis(analysis):
            st.success(f"Successfully analyzed {standardized_path.name}")
        else:
            st.error(f"Failed to save analysis for {standardized_path.name}")

def display_rating_with_gauge(title, rating):
    st.markdown(f"### {title}")
    # st.progress(rating/10)
    st.markdown(f"Score: {rating}/10")

def display_section_with_bullets(title, items, format: str = "streamlit"):
    if not items:  # Handle empty/nonexistent data
        items = ["No data available"]

    if format == "markdown" and items:
        section = f"**{title}**\n"
        if type(items) == list:
            for item in items:
                section += f"- {item}\n" if not item == items[-1] else f"- {item}"
        else:
            section += f"{items}"
        return section
    elif items:
        st.markdown(f"#### {title}")
        if type(items) == list:
            for item in items:
                st.markdown(f"- {item}")
        else:
            st.markdown(f"{items}")

def display_job_summary(job_summary):
    st.markdown("### Résumé de l'offre")
    st.markdown(f"**Entreprise:** {job_summary['jobCompany']}")
    st.markdown(f"**Poste:** {job_summary['jobTitle']}")
    st.markdown(f"**Localisation:** {job_summary['jobLocation']}")
    st.markdown(f"**Aperçu:** {job_summary['jobOverview']}")
    display_section_with_bullets("Facteurs de risque pour le recrutement:", job_summary['jobFailureFactors'], format="streamlit")
    if job_summary.get('jobPainPointsAnalysis'):
        display_section_with_bullets("Analyses des pain points:", job_summary['jobPainPointsAnalysis'], format="streamlit")

def display_strategic_recommendations(recommendations):
    """Display strategic recommendations with error handling."""
    st.markdown(f"### Recommandations Stratégiques")

    # Safely get decision data
    decision_data = recommendations.get('shouldApply', {})
    decision_icon = "✅" if decision_data.get('decision', False) else "❌"
    chance_rating = decision_data.get('chanceRating', "N/A")
    explanation = decision_data.get('explanation', "No explanation available")

    st.markdown(f"{decision_icon} **Décision:** {chance_rating}/10\n\n{explanation}")

    # Safely display key points with fallbacks
    display_section_with_bullets(
        "Points clés de l'offre",
        recommendations.get('keyPointsInJobOffer', ["Aucun point clé disponible"])
    )

    display_section_with_bullets(
        "Points clés de mon profil",
        recommendations.get('matchingPointsWithProfile', ["Aucune correspondance identifiée"])
    )

    display_section_with_bullets(
        "Mots-clés à utiliser",
        recommendations.get('keyWordsToUse', ["Aucun mot-clé suggéré"])
    )

    # Handle optional fields
    st.markdown("#### Étapes de préparation")
    st.markdown(recommendations.get('preparationSteps', "Aucune étape fournie"))

    st.markdown("#### Points d'attention pour l'entretien")
    st.markdown(recommendations.get('interviewFocusAreas', "Aucun point d'attention spécifié"))

@st.cache_data(ttl=600, show_spinner="Generating markdown...")
def generate_markdown_content(analysis: dict) -> str:
    """Generate markdown content for the analysis file.

    Args:
        analysis (dict): The analysis data containing job summary, recommendations, and cover letter

    Returns:
        str: Formatted markdown content with frontmatter
    """
    today = datetime.now().strftime('%Y-%m-%d')

    # Create frontmatter
    frontmatter = f"""---
link: -
sourcing: -
status: applied
applied: {today}
updated: {today}
---

"""

    # Add offer content
    offer_content = analysis.get('offerContent', '')

    # Get strategic recommendations
    strategic_content = markdown_strategic_recommendations(analysis)

    # Get cover letter if it exists
    cover_letter = ''
    if analysis and isinstance(analysis, dict):
        cover_letter_dict = analysis.get('cover_letter')
        if cover_letter_dict and isinstance(cover_letter_dict, dict):
            cover_letter = cover_letter_dict.get('content', '')

    return f"{frontmatter}\n{offer_content}\n\n# Analyse\n{strategic_content}\n\n# Lettre de motivation\n{cover_letter}"

@st.cache_data(ttl=600, show_spinner=False)
def markdown_strategic_recommendations(analysis: dict) -> str:
    """Format analysis for copying to clipboard."""
    analysis_markdown = f"""
### Résumé de l'offre
**Poste**: {analysis['jobSummary']['jobTitle']}
**Entreprise**: {analysis['jobSummary']['jobCompany']}
**Localisation**: {analysis['jobSummary']['jobLocation']}
**Aperçu**: {analysis['jobSummary']['jobOverview']}
{display_section_with_bullets("Facteurs de risque pour le recrutement", analysis['jobSummary']['jobFailureFactors'], format="markdown")}
{display_section_with_bullets("Analyses des pain points", analysis['jobSummary'].get('jobPainPointsAnalysis','//'), format="markdown")}

### Intérêt pour votre carrière
{display_section_with_bullets("Analyse", analysis['careerFitAnalysis']['careerAnalysis'], format="markdown")}
**Note**: {analysis['careerFitAnalysis']['careerDevelopmentRating']}

### Adéquation du profil
{display_section_with_bullets("Analyse", analysis['profileMatchAssessment']['profileMatchAnalysis'], format="markdown")}
**Note**: {analysis['profileMatchAssessment']['matchCompatibilityRating']}

### Probabilité de succès
{display_section_with_bullets("Analyse", analysis['competitiveProfile']['competitiveAnalysis'], format="markdown")}
**Note**: {analysis['competitiveProfile']['successProbabilityRating']}

### Recommandations stratégiques:
**Dois-je candidater à cette offre?**
{"✅ oui" if analysis['strategicRecommendations']['shouldApply']['decision'] else "❌ non"} - {analysis['strategicRecommendations']['shouldApply']['chanceRating']}/10
{analysis['strategicRecommendations']['shouldApply']['explanation']}
{display_section_with_bullets("Points clés de l'offre", analysis['strategicRecommendations']['keyPointsInJobOffer'], format="markdown") if analysis['strategicRecommendations']['keyPointsInJobOffer'] else "Aucun point clé disponible"}
{display_section_with_bullets("Points clés de mon profil", analysis['strategicRecommendations']['matchingPointsWithProfile'], format="markdown") if analysis['strategicRecommendations']['matchingPointsWithProfile'] else "Aucune correspondance identifiée"}
{display_section_with_bullets("Mots-clés à utiliser", analysis['strategicRecommendations']['keyWordsToUse'], format="markdown") if analysis['strategicRecommendations']['keyWordsToUse'] else "Aucun mot-clé suggéré"}
**Étapes de préparation**
{analysis['strategicRecommendations']['preparationSteps']}
{analysis['strategicRecommendations']['interviewFocusAreas']}
    """
    return analysis_markdown

def generate_cover_letter(analysis: dict):
    """Generate cover letter using Claude API."""
    with st.spinner("Generating cover letter with Claude AI..."):
        result = st.session_state.analyzer.generate_cover_letter(analysis)
        print(result)
        if result:
            st.session_state.data_handler.add_cover_letter_cost(result["generation_cost"])
            st.code(result["content"], language=None)

            st.download_button(
                "Download Cover Letter",
                result["content"],
                file_name=f"{analysis['file_name']}_cover_letter_{datetime.now().strftime('%Y%m%d')}.txt"
            )

        else:
            st.error("Failed to generate cover letter")

def forget_offer(file_name: str):
    """Archive an offer and update its analysis status."""
    # Move file to archive
    file_path = IN_PROGRESS_PATH / file_name
    if file_path.exists():
        if st.session_state.file_manager.move_to_archived(file_path):
            # Update analysis forget status
            analyses = st.session_state.data_handler.get_all_analyses()
            for analysis in analyses:
                if analysis["file_name"] == file_name:
                    analysis["forget"] = True

            st.success(f"Archived {file_name}")
            st.rerun()  # Force Streamlit to refresh

        else:
            st.error(f"Failed to archive {file_name}")

@st.cache_data(ttl=300, show_spinner=False)
def get_pdf_path(file_name: str) -> Path:
    """Get the path to a PDF file, checking both in_progress and archived directories."""
    in_progress_path = IN_PROGRESS_PATH / file_name
    if in_progress_path.exists():
        return in_progress_path

    archived_path = ARCHIVED_PATH / file_name
    if archived_path.exists():
        return archived_path

    return None

def filter_analyses_by_period(analyses: list, period: str) -> list:
    """Filter analyses based on selected time period."""
    now = datetime.now()

    # Get all batches and their timestamps
    batch_timestamps = {}
    for batch in st.session_state.data_handler.data['analyses']:
        batch_timestamp = datetime.fromisoformat(batch['timestamp'])
        for offer in batch['offers']:
            batch_timestamps[offer['file_name']] = batch_timestamp

    # Filter based on period
    if period == "Today":
        return [a for a in analyses if batch_timestamps[a['file_name']].date() == now.date()]
    elif period == "Last Week":
        week_ago = now - pd.Timedelta(days=7)
        return [a for a in analyses if batch_timestamps[a['file_name']] >= week_ago]
    elif period == "Last Month":
        month_ago = now - pd.Timedelta(days=30)
        return [a for a in analyses if batch_timestamps[a['file_name']] >= month_ago]
    else:  # "All"
        return analyses

def group_analyses_by_day(analyses: list) -> dict:
    """Group analyses by day and sort within each group."""
    # Get all batches and their timestamps
    batch_timestamps = {}
    for batch in st.session_state.data_handler.data['analyses']:
        batch_timestamp = datetime.fromisoformat(batch['timestamp'])
        for offer in batch['offers']:
            batch_timestamps[offer['file_name']] = batch_timestamp

    grouped = {}
    for analysis in analyses:
        day = batch_timestamps[analysis['file_name']].date()
        if day not in grouped:
            grouped[day] = []
        grouped[day].append(analysis)

    # Sort each day's analyses
    for day in grouped:
        grouped[day] = sorted(
            grouped[day],
            key=lambda x: x.get(
                "note_total",
                # Fallback calculation with error handling
                (
                    x.get('careerFitAnalysis', {}).get('careerDevelopmentRating', 0) +
                    x.get('profileMatchAssessment', {}).get('matchCompatibilityRating', 0) +
                    x.get('competitiveProfile', {}).get('successProbabilityRating', 0)
                )  # Average if all components exist
            ),
            reverse=True
        )
    # Sort days
    return dict(sorted(grouped.items(), reverse=True))

def display_dashboard():
    """Display the main dashboard with offer analyses and API usage."""
    analyses = st.session_state.data_handler.get_all_analyses()
    api_usage = st.session_state.data_handler.get_api_usage()

    # Filter out forgotten analyses
    active_analyses = [a for a in analyses if not a.get("forget", False)]

    # Add period filter
    period = st.pills(
        "Selected Period",
        options=["Today", "Last Week", "Last Month", "All"],
        selection_mode="single",
        label_visibility="hidden",
        default="Today"
    )

    # Filter by period
    filtered_analyses = filter_analyses_by_period(active_analyses, period)

    # Group by day
    grouped_analyses = group_analyses_by_day(filtered_analyses)

    # Analyses Table
    # st.subheader("Job Offers")
    if not filtered_analyses:
        st.info("No analyzed offers to display.")
        return

    # Display analyses grouped by day
    for day, day_analyses in grouped_analyses.items():
        st.markdown(f"### {day.strftime('%A %d %B %Y')} - {len(day_analyses)} offers")
        for analysis in day_analyses:
            decision_icon = "✅" if analysis['strategicRecommendations']['shouldApply']['decision'] else "❌"
            with st.expander(f"{analysis['jobSummary']['jobCompany']} - {analysis['jobSummary']['jobTitle']} - {analysis['strategicRecommendations']['shouldApply']['chanceRating']}/10" , icon=decision_icon):
                col1, col2 = st.columns([0.7, 0.3], gap="medium")

                with col1:
                    # Display job summary
                    display_job_summary(analysis['jobSummary'])

                    # Display scores with gauges
                    display_rating_with_gauge("Développement de carrière", analysis['careerFitAnalysis']['careerDevelopmentRating'])
                    display_section_with_bullets("Analyse", analysis['careerFitAnalysis']['careerAnalysis'], format="streamlit")

                    display_rating_with_gauge("Compatibilité du profil", analysis['profileMatchAssessment']['matchCompatibilityRating'])
                    display_section_with_bullets("Analyse", analysis['profileMatchAssessment']['profileMatchAnalysis'], format="streamlit")

                    display_rating_with_gauge("Probabilité de succès", analysis['competitiveProfile']['successProbabilityRating'])
                    display_section_with_bullets("Analyset", analysis['competitiveProfile']['competitiveAnalysis'], format="streamlit")

                    # Display strategic recommendations
                    display_strategic_recommendations(analysis['strategicRecommendations'])

                    # PDF viewer
                    pdf_path = get_pdf_path(analysis['file_name'])
                    st.write("Debug - PDF Path:", str(pdf_path))  # Display the resolved path

                    if pdf_path and pdf_path.exists():
                        with open(pdf_path, "rb") as pdf_file:
                            st.download_button(
                                label="View PDF",
                                data=pdf_file,
                                file_name="document.pdf",
                                mime="application/pdf",
                                    key=f"pdf_{analysis['file_name']}"
                            )

                with col2:
                    # Forget button
                    with st.container():
                        if st.button("Forget", key=f"del_{analysis['file_name']}"):
                            forget_offer(analysis['file_name'])
                        st.divider()

                    st.code(analysis.get('offerContent', ''), language=None)

                    # Display content preview
                    st.code(markdown_strategic_recommendations(analysis), language=None)

                    st.divider()

                    # Generate Cover Letter
                    if analysis.get("cover_letter"):
                        st.info("Une lettre de motivation existe déjà pour cette offre.")
                        st.code(analysis["cover_letter"]["content"], language=None)

                        st.download_button(
                            "Download Cover Letter",
                            analysis["cover_letter"]["content"],
                            file_name=f"{analysis['file_name']}_cover_letter_{datetime.now().strftime('%Y%m%d')}.txt",
                            key=f"dl_{analysis['file_name']}-coverletter"
                        )
                    else:
                        if st.button("Generate Cover Letter", key=f"gen_{analysis['file_name']}"):
                            generate_cover_letter(analysis)

                    st.divider()

                    # Download markdown button
                    markdown_content = generate_markdown_content(analysis)
                    st.download_button(
                        "Download Analysis (.md)",
                        markdown_content,
                        file_name=f"{analysis['jobSummary']['jobCompany']} - {analysis['jobSummary']['jobTitle']} - {analysis['strategicRecommendations']['shouldApply']['chanceRating']}.md",
                        mime="text/markdown",
                        key=f"dl_{analysis['file_name']}-markdown"
                    )

    st.divider()

    # API Usage Stats
    st.subheader("API Usage")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Cost", f"${api_usage['total_cost']:.4f}")
    with col2:
        st.metric("Analysis Costs", f"${api_usage['analysis_costs']:.4f}")
    with col3:
        st.metric("Cover Letter Costs", f"${api_usage['cover_letter_costs']:.4f}")
    with col4:
        st.metric("Requests", f"{api_usage['requests_count']}")

    # Configuration Info
    st.sidebar.subheader("Configuration")
    st.sidebar.info(f"""
    - Max file size: {MAX_FILE_SIZE_MB}MB
    - Cleanup after: {CLEANUP_DAYS} days
    """)

def main():
    """Main application function."""
    initialize_app()

    # Header
    st.title("🎯 Job Set & Match!")
    st.write("A Streamlit application that leverages AI to analyze job offers \
            and generate application materials.")
    st.write(" ")

    # Primary Action
    with st.container():
        # Clear Analyses Button
        col1, col2 = st.columns([1, 3],vertical_alignment="center")

        with col1:
            if st.button(f"Analyze {len(st.session_state.file_manager.get_new_offers())} New Offers", type="primary"):
                analyze_new_offers()

        with col2:
            st.markdown(f"")

            # Note: This feature is disabled for now
            # if st.button("Clear Analyses", type="secondary"):
            #     if st.session_state.data_handler.clear_analyses():
            #         st.success("Analyses cleared successfully")
            #         st.rerun()
            #     else:
            #         st.error("Failed to clear analyses")

    # Main Dashboard
    display_dashboard()

if __name__ == "__main__":
    main()
