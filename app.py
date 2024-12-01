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

def initialize_app():
    """Initialize the application state and configuration."""
    st.set_page_config(
        page_title="Job Set & Match!",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Check environment variables
    check_environment()

    # Initialize core components
    if 'file_manager' not in st.session_state:
        st.session_state.file_manager = FileManager(
            NEW_OFFERS_PATH,
            IN_PROGRESS_PATH,
            ARCHIVED_PATH,
            max_file_size_mb=MAX_FILE_SIZE_MB,
            cleanup_days=CLEANUP_DAYS
        )

    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = OfferAnalyzer()

    if 'data_handler' not in st.session_state:
        st.session_state.data_handler = DataHandler(ANALYSES_FILE)

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
        with st.spinner(f"Analyzing {new_path.name} with Claude AI..."):
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
    st.progress(rating/10)
    st.markdown(f"Score: {rating}/10")

def display_section_with_bullets(title, items, format: str = "streamlit"):
    if format == "markdown" and items:
        section = f"**{title}**\n"
        for item in items:
            section += f"- {item}\n" if not item == items[-1] else f"- {item}"
        return section
    elif items:
        st.markdown(f"#### {title}")
        for item in items:
            st.markdown(f"- {item}")

def display_job_summary(job_summary):
    st.markdown("### Résumé de l'offre")
    st.markdown(f"**Entreprise:** {job_summary['jobCompany']}")
    st.markdown(f"**Poste:** {job_summary['jobTitle']}")
    st.markdown(f"**Localisation:** {job_summary['jobLocation']}")
    st.markdown(f"**Aperçu:** {job_summary['jobOverview']}")

def display_strategic_recommendations(recommendations):
    st.markdown(f"### Recommandations Stratégiques")
    decision_icon = "✅" if recommendations['shouldApply']['decision'] else "❌"
    st.markdown(f"{decision_icon} **Décision:** {recommendations['shouldApply']['chanceRating']}/10\n\n{recommendations['shouldApply']['explanation']}")

    display_section_with_bullets("Points clés à mettre en avant", recommendations['keyPointsToEmphasize'])
    display_section_with_bullets("Mots-clés à utiliser", recommendations['keyWordsToUse'])

    st.markdown("#### Étapes de préparation")
    st.markdown(recommendations['preparationSteps'])

    st.markdown("#### Points d'attention pour l'entretien")
    st.markdown(recommendations['interviewFocusAreas'])

def markdown_strategic_recommendations(analysis: dict) -> str:
    """Format analysis for copying to clipboard."""
    analysis_markdown = f"""
### Résumé de l'offre
**Poste**: {analysis['jobSummary']['jobTitle']}
**Entreprise**: {analysis['jobSummary']['jobCompany']}
**Localisation**: {analysis['jobSummary']['jobLocation']}
**Aperçu**: {analysis['jobSummary']['jobOverview']}

### Intérêt pour votre carrière
**Analyse**: {analysis['careerFitAnalysis']['careerAnalysis']}
**Note**: {analysis['careerFitAnalysis']['careerDevelopmentRating']}

### Adéquation du profil
**Analyse**: {analysis['profileMatchAssessment']['profileMatchAnalysis']}
**Note**: {analysis['profileMatchAssessment']['matchCompatibilityRating']}

### Probabilité de succès
**Analyse*: {analysis['competitiveProfile']['competitiveAnalysis']}
**Note**: {analysis['competitiveProfile']['successProbabilityRating']}

### Recommandations stratégiques:
**Dois-je candidater à cette offre?**
{"✅ oui" if analysis['strategicRecommendations']['shouldApply']['decision'] else "❌ non"} - {analysis['strategicRecommendations']['shouldApply']['chanceRating']}/10
{analysis['strategicRecommendations']['shouldApply']['explanation']}
{display_section_with_bullets("Points clés à mettre en avant", analysis['strategicRecommendations']['keyPointsToEmphasize'], format="markdown")}
{display_section_with_bullets("Mots-clés à utiliser", analysis['strategicRecommendations']['keyWordsToUse'], format="markdown")}
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

# def forget_offer(file_name: str):
#     """Archive an offer and remove its analysis."""
#     file_path = IN_PROGRESS_PATH / file_name
#     if file_path.exists():
#         if st.session_state.file_manager.move_to_archived(file_path):
#             st.success(f"Archived {file_name}")
#         else:
#             st.error(f"Failed to archive {file_name}")

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

def display_dashboard():
    """Display the main dashboard with offer analyses and API usage."""
    analyses = st.session_state.data_handler.get_all_analyses()
    api_usage = st.session_state.data_handler.get_api_usage()

    # Filter out forgotten analyses
    active_analyses = [a for a in analyses if not a.get("forget", False)]

    # Sort remaining analyses
    analyses_ordered = sorted(active_analyses, key=lambda x: x["note_total"], reverse=True)

    # Analyses Table
    st.subheader("Job Offers")
    if not analyses_ordered:
        st.info("No analyzed offers to display.")
        return

    for analysis in analyses_ordered:
        decision_icon = "✅" if analysis['strategicRecommendations']['shouldApply']['decision'] else "❌"
        with st.expander(f"{analysis['jobSummary']['jobCompany']} - {analysis['jobSummary']['jobTitle']}" , icon=decision_icon):
            col1, col2 = st.columns([0.7, 0.3], gap="medium")

            with col1:
                # Display job summary
                display_job_summary(analysis['jobSummary'])

                # Display scores with gauges
                display_rating_with_gauge("Développement de carrière",
                                        analysis['careerFitAnalysis']['careerDevelopmentRating'])
                st.markdown(analysis['careerFitAnalysis']['careerAnalysis'])

                display_rating_with_gauge("Compatibilité du profil",
                                        analysis['profileMatchAssessment']['matchCompatibilityRating'])
                st.markdown(analysis['profileMatchAssessment']['profileMatchAnalysis'])

                display_rating_with_gauge("Probabilité de succès",
                                        analysis['competitiveProfile']['successProbabilityRating'])
                st.markdown(analysis['competitiveProfile']['competitiveAnalysis'])

                # Display strategic recommendations
                display_strategic_recommendations(analysis['strategicRecommendations'])

            with col2:
                # Generate Cover Letter
                if analysis.get("cover_letter"):
                    st.info("Une lettre de motivation existe déjà pour cette offre.")
                    st.code(analysis["cover_letter"]["content"], language=None)

                    st.download_button(
                        "Download Cover Letter",
                        analysis["cover_letter"]["content"],
                        file_name=f"{analysis['file_name']}_cover_letter_{datetime.now().strftime('%Y%m%d')}.txt"
                    )
                else:
                    if st.button("Generate Cover Letter", key=f"gen_{analysis['file_name']}"):
                        generate_cover_letter(analysis)

                # Tools
                st.divider()
                st.code(markdown_strategic_recommendations(analysis), language=None)
                st.code(analysis.get('offerContent', ''), language=None)

                # Forget button
                with st.container():
                    st.divider()
                    if st.button("Forget", key=f"del_{analysis['file_name']}"):
                        forget_offer(analysis['file_name'])


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
    st.write("A Streamlit application that leverages Claude AI to analyze job offers \
            and generate application materials.")

    # Primary Action
    with st.container():
        # Clear Analyses Button
        col1, col2 = st.columns([0.85, 0.15])

        with col1:
            if st.button("Analyze New Offers", type="primary"):
                analyze_new_offers()

        with col2:
            if st.button("Clear Analyses", type="secondary"):
                if st.session_state.data_handler.clear_analyses():
                    st.success("Analyses cleared successfully")
                    st.rerun()
                else:
                    st.error("Failed to clear analyses")

    # Main Dashboard
    display_dashboard()

if __name__ == "__main__":
    main()
