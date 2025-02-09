"""
Job Set & Match! - A Streamlit application that helps prioritize your job search by
automatically analyzing job offers and generating application materials using Claude AI.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import asyncio

# Import helpers
from app.core.file_manager import FileManager
from app.core.data_handler import DataHandler
from app.core.analyzer import OfferAnalyzer
from app.config import (
    init_config,
    IN_PROGRESS_PATH,
    ARCHIVED_PATH,
    MAX_FILE_SIZE_MB,
    CLEANUP_DAYS,
    BATCH_POLLING_INTERVAL,
    BATCH_MAX_SIZE
)

def check_environment():
    """Check if all required environment variables are set."""
    try:
        config = init_config()
        return True
    except ValueError as e:
        st.error(str(e))
        st.stop()
        return False

def init_file_manager():
    return FileManager()

def init_analyzer():
    return OfferAnalyzer()

def init_data_handler():
    return DataHandler()

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

    if 'analyze_json' not in st.session_state:
        st.session_state.analyze_json = None

    st.markdown("""
        <style>
            .st-key-main_dashboard > div > .stColumn:first-child .stButton button {
                text-align: left;
                padding-left: 2em;
                flex: auto;
                flex-direction: row;
                align-items: center;
                justify-content: start;
            }
            .st-key-main_dashboard > div > .stColumn:first-child .stButton button div {
                max-width: calc(100% - 2em);
            }
            .st-key-main_dashboard > div > .stColumn:first-child .stButton button div > p {
                text-overflow: ellipsis;
                white-space: nowrap;
                overflow: hidden;
            }
            .st-key-main_dashboard > div > .stColumn + .stColumn > div {
                position: sticky;
                top: 10vh;
            }
            .st-key-main_dashboard > div > .stColumn + .stColumn .st-key-analysis_content_container {
                overflow-y: auto;
                overflow-x: hidden;
                max-height: 80vh;
            }
            .st-key-main_dashboard > div > .stColumn + .stColumn .st-key-analysis_content_container > * {
                max-width: 100%;
            }
            .st-key-main_dashboard > div > .stColumn + .stColumn .st-key-analysis_content_container code {
                white-space: normal;
            }
        </style>
    """, unsafe_allow_html=True)

def analyze_new_offers():
    """Analyze new job offers using Claude API."""
    new_offers = st.session_state.file_manager.get_new_offers()

    if not new_offers:
        st.warning("No new offers found in the input directory.")
        return

    first_offer = True # Flag to identify the first offer only

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
        if st.session_state.data_handler.add_analysis(analysis, new_batch=first_offer):
            st.success(f"Successfully analyzed {standardized_path.name}")
            first_offer = False
        else:
            st.error(f"Failed to save analysis for {standardized_path.name}")
    st.rerun()

async def analyze_new_offers_sync():
    """Analyze new job offers using Claude API in parallel."""
    new_offers = st.session_state.file_manager.get_new_offers()

    if not new_offers:
        st.warning("No new offers found in the input directory.")
        return

    valid_offers = []
    for offer_path in new_offers:
        if (offer_path.stat().st_size / (1024 * 1024)) > MAX_FILE_SIZE_MB:
            st.error(f"File too large: {offer_path.name}")
            continue

        new_path = st.session_state.file_manager.move_to_in_progress(offer_path)
        if new_path:
            valid_offers.append(new_path)
        else:
            st.error(f"Failed to process {offer_path.name}")

    if valid_offers:
        with st.spinner(f"Analyzing {len(valid_offers)} files in parallel..."):
            analyses = await st.session_state.analyzer.analyze_pdfs_parallel(valid_offers)

            for analysis in analyses:
                file_path = IN_PROGRESS_PATH / analysis["file_name"]
                standardized_path = st.session_state.file_manager.rename_after_analysis(
                    file_path,
                    analysis["jobSummary"]["jobCompany"],
                    analysis["jobSummary"]["jobTitle"]
                )

                if standardized_path:
                    analysis["file_name"] = standardized_path.name
                    if st.session_state.data_handler.add_analysis(analysis):
                        st.success(f"Successfully analyzed {standardized_path.name}")
                    else:
                        st.error(f"Failed to save analysis for {standardized_path.name}")
                else:
                    st.error(f"Failed to standardize filename for {analysis['file_name']}")

    st.rerun()

def generate_full_content(analysis: dict) -> str:
    """Generate markdown content for the analysis file.

    Args:
        analysis (dict): The analysis data containing job summary, recommendations, and cover letter

    Returns:
        str: Formatted markdown content with frontmatter
    """
    today = datetime.now().strftime('%Y-%m-%d')

    # Create frontmatter
    frontmatter = f"""---
link:
sourcing:
status: applied
applied: {today}
updated: {today}
---

"""

    # Add offer content
    offer_content = analysis.get('offerContent', '')

    # Get strategic recommendations
    strategic_content = generate_analysis_markdown(analysis)

    # Get cover letter if it exists
    cover_letter = ''
    if analysis and isinstance(analysis, dict):
        cover_letter_dict = analysis.get('cover_letter')
        if cover_letter_dict and isinstance(cover_letter_dict, dict):
            cover_letter = cover_letter_dict.get('content', '')

    return f"{frontmatter}\n{offer_content}\n\n## Analyse\n{strategic_content}\n\n## Lettre de motivation\n{cover_letter}"

def generate_analysis_markdown(analysis: dict):
    """Generate markdown analysis for display."""
    try:
        if not hasattr(st.session_state, 'analyzer'):
            st.error("Analyzer not initialized properly")
            return ""

        if 'analysis_markdown' in analysis:
            return analysis['analysis_markdown']

        if not hasattr(st.session_state.analyzer, 'generate_analysis_markdown'):
            st.error("Method not found in analyzer")
            return ""

        return st.session_state.analyzer.generate_analysis_markdown(analysis)
    except Exception as e:
        st.error(f"Error generating markdown: {str(e)}")
        return ""

def generate_cover_letter(analysis: dict):
    """Generate cover letter using Claude API."""
    with st.spinner("Generating cover letter with Claude AI..."):
        result = st.session_state.analyzer.generate_cover_letter(analysis)
        print(result)
        if result:
            st.session_state.data_handler.add_cover_letter_cost(result["generation_cost"])
            st.code(result["content"], language=None, height=200)

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

def analyze_footer(debug_info: bool = False):
    """Display footer with API usage stats and configuration info."""
    api_usage = st.session_state.data_handler.get_api_usage()

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

    if debug_info:

        # Add file manager info
        st.sidebar.subheader("File System:")
        st.sidebar.write(f"New Offers Path: {st.session_state.file_manager.new_dir}")
        st.sidebar.write(f"Path exists: {st.session_state.file_manager.new_dir.exists()}")
        st.sidebar.write(f"Files in directory: {list(st.session_state.file_manager.new_dir.glob('*.pdf'))}")
        st.sidebar.divider()

        # Verify API usage data
        st.sidebar.subheader("API Usage:")
        st.sidebar.write(api_usage)
        st.sidebar.divider()

def set_var_analyze_json(value: dict = ""):
    st.session_state["analyze_json"] = value

def analyze_list(debug_info: bool = False, period: str = "Today"):
    """Display a list of analyzed job offers."""
    analyses = st.session_state.data_handler.get_all_analyses()

    # Filter out forgotten analyses
    active_analyses = [a for a in analyses if not a.get("forget", False)]

    # Filter by period
    filtered_analyses = filter_analyses_by_period(active_analyses, period)

    # Group by day
    grouped_analyses = group_analyses_by_day(filtered_analyses)

    # Analyses Table
    if not filtered_analyses:
        st.info("No analyzed offers to display.")

    # Display analyses grouped by day
    for day, day_analyses in grouped_analyses.items():
        st.markdown(f"### {day.strftime('%A %d %B %Y')} - {len(day_analyses)} offers")
        for analysis in day_analyses:
            decision_icon = "✅" if analysis['strategicRecommendations']['shouldApply']['decision'] else "❌"

            st.button(f"{analysis['jobSummary']['jobCompany']} - {analysis['jobSummary']['jobTitle']} - {analysis['strategicRecommendations']['shouldApply'].get('chanceRating', 0)}/10" , \
                        icon=decision_icon, \
                        key=f"btn_{analysis['file_name']}", \
                        help=f"Show info about the offer", \
                        type="secondary", \
                        use_container_width=True,
                        args=(analysis,),
                        on_click=set_var_analyze_json)

    if debug_info:

        # Add internal state info
        st.sidebar.write("Selected period:", period)
        st.sidebar.write("Number of analyses loaded:", len(analyses))

        # Add grouped analyses info
        st.sidebar.subheader(f"Grouped analyses: {len(grouped_analyses)}")
        if grouped_analyses:
            st.sidebar.write("First group:", list(grouped_analyses.items())[0])
            st.sidebar.divider()

        # Add Streamlit context info
        st.context.cookies
        st.context.headers

        # Add storage info
        # st.sidebar.subheader("Storage Information:")
        # st.sidebar.write("Storage Base Path:", st.session_state.data_handler.data_path)
        # st.sidebar.write("Storage Files:")
        # st.sidebar.write(f"- analyses.parquet exists: {(base_path / 'analyses.parquet').exists()}")
        # st.sidebar.write(f"- api_usage.parquet exists: {(base_path / 'api_usage.parquet').exists()}")
        # st.sidebar.divider()

        # # Add analyses data
        # st.sidebar.subheader("Analyses DataFrame Info:")
        # st.sidebar.write(f"Number of records: {analyses_df.shape[0]}")
        # st.sidebar.write(f"Shape: {analyses_df.shape}")
        # if not analyses_df.empty:
        #     st.sidebar.write("Data Types:", analyses_df.dtypes)
        #     st.sidebar.write("First row:", analyses_df.iloc[0].to_dict())
        #     st.sidebar.write(f"Columns: {analyses_df.columns.tolist()}")
        # else:
        #     st.sidebar.warning("DataFrame is empty!")
        # st.sidebar.divider()

        # # Add companies data
        # st.sidebar.subheader("Companies DataFrame Info:")
        # st.sidebar.write(f"Number of records: {companies_df.shape[0]}")
        # st.sidebar.write(f"Shape: {companies_df.shape}")
        # if not companies_df.empty:
        #     st.sidebar.write("Data Types:", companies_df.dtypes)
        #     st.sidebar.write("First row:", companies_df.iloc[0].to_dict())
        #     st.sidebar.write(f"Columns: {companies_df.columns.tolist()}")
        # else:
        #     st.sidebar.warning("DataFrame is empty!")
        # st.sidebar.divider()

@st.fragment()
def analyze_content(analysis: dict = None):
    """Display detailed analysis content for a selected job offer."""
    test = st.empty()
    if analysis:
        analysis_content = generate_analysis_markdown(analysis)
        with test.container(border=True, key="analysis_content_container"):

            st.markdown(analysis_content)

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
            st.divider()

            # Forget button
            if st.button("Forget", key=f"del_{analysis['file_name']}"):
                forget_offer(analysis['file_name'])
            st.divider()

            st.code(analysis.get('offerContent', ''), language=None)

            # Display content preview
            st.code(analysis_content, language=None, height=400)

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
            markdown_content = generate_full_content(analysis)
            st.download_button(
                "Download Analysis (.md)",
                markdown_content,
                file_name=f"{analysis['jobSummary']['jobCompany']} - {analysis['jobSummary']['jobTitle']} - {analysis['strategicRecommendations']['shouldApply'].get('chanceRating', 0)}.md",
                mime="text/markdown",
                key=f"dl_{analysis['file_name']}-markdown",
                type="primary"
            )

def main():
    """Main application function."""
    initialize_app()

    # Header
    st.title("🎯 Job Set & Match!")
    st.write("A Streamlit application that leverages AI to analyze job offers \
            and generate application materials.")
    st.write(" ")

    # Primary Action
    with st.container(key="primary_action"):
        # Clear Analyses Button
        col1, col2 = st.columns([1, 3],vertical_alignment="center")

        with col1:
            if st.button(f"Analyze {len(st.session_state.file_manager.get_new_offers())} New Offers", type="primary"):
                # import asyncio
                # asyncio.run(analyze_new_offers())
                # analyze_new_offers()
                asyncio.run(analyze_new_offers_sync())

        with col2:
            st.markdown(f"")

            # Note: This feature is disabled for now
            # if st.button("Clear Analyses", type="secondary"):
            #     if st.session_state.data_handler.clear_analyses():
            #         st.success("Analyses cleared successfully")
            #         st.rerun()
            #     else:
            #         st.error("Failed to clear analyses")

    # Configuration Info
    st.sidebar.subheader("Configuration")
    st.sidebar.info(f"""
    - Max file size: {MAX_FILE_SIZE_MB}MB
    - Cleanup after: {CLEANUP_DAYS} days
    """)

    # Add debug information
    debug_info = st.sidebar.checkbox("Show Debug Info",key="debug_info")

    # Add period filter
    period = st.pills(
        "Selected Period",
        options=["Today", "Last Week", "Last Month", "All"],
        selection_mode="single",
        label_visibility="hidden",
        default="Today"
    )

    # Main Dashboard
    with st.container(key="main_dashboard"):

        list_col, content_col = st.columns([0.5, 0.5], gap="medium", vertical_alignment="top")

        with list_col:
            # Sidebar with list of offers
            analyze_list(debug_info,period)

        with content_col:
            # Main content area
            analyze_content(st.session_state["analyze_json"])

    # Display footer
    analyze_footer(debug_info)

if __name__ == "__main__":
    main()
