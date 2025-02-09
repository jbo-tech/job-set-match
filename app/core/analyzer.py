"""
Job offer analyzer using Claude API for Job Set & Match!

This module handles:
- Job offer analysis using Claude
- Cover letter generation using Claude
- API cost tracking
"""

import logging
from pathlib import Path
from typing import Dict, Optional, List, Union, Any
import logging
from pathlib import Path
import json
import os
from datetime import datetime, timezone
import base64
import asyncio

from anthropic import Anthropic

from app.config import (
    CONTEXT_PATH,
    ANTHROPIC_API_KEY,
    DEFAULT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    COVER_LETTER_TEMPERATURE,
    TOKEN_COST,
    BATCH_POLLING_INTERVAL,
    BATCH_MAX_SIZE
)

from app.prompts import (
    SYSTEM_PROMPT,
    CONTEXT_PROMPT,
    ANALYSIS_PROMPT,
    GENERATION_PROMPT
)

class OfferAnalyzer:
    """Analyzes job offers and generates cover letters using Claude API."""

    def __init__(self):
        """Initialize the analyzer with Claude API client and logging configuration."""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._context_cache = None  # To store the "digested" context

        # Initialize Claude API client
        api_key = ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(
                            api_key=api_key,
                        )

    def _load_personal_documents(self) -> str:
        """
        Load all .txt files from DATA_PATH and format them in XML structure.
        Each .txt file is considered a personal context document (CV, profile, etc.).

        Returns:
            str: XML formatted documents section containing all .txt files from DATA_PATH
        """
        try:
            documents = []
            index = 1

            # Scan for all .txt files in DATA_PATH
            # for file in [f for f in DATA_PATH.iterdir() if f.suffix in ['.txt', '.md']]:
            for file in CONTEXT_PATH.glob("*.[tm][xd]t"):
                try:
                    with open(file, "r") as f:
                        content = f.read().strip()
                        doc = f"""
                            <document index="{index}">
                                <source>{file.name}</source>
                                <document_content>
                                {content}
                                </document_content>
                            </document>
                        """
                        documents.append(doc)
                        index += 1
                except Exception as e:
                    self.logger.warning(f"Failed to read {file}: {e}")
                    continue

            if documents:
                return f"""
                        Find the following context about me and job analysis:
                        <documents>
                            {"".join(documents)}
                        </documents>
                        """
            return ""
        except Exception as e:
            self.logger.error(f"Error loading personal documents: {e}")
            return ""

    async def analyze_pdf_async(self, file_path: Path) -> Optional[Dict]:
        """
        Analyze a single PDF file asynchronously.
        """
        try:
            # Lecture du PDF
            with open(file_path, "rb") as f:
                pdf_data = base64.b64encode(f.read()).decode("utf-8")

            # Create message
            start_time = datetime.now(timezone.utc)
            message = self.client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
                system=[
                    {"type": "text", "text": SYSTEM_PROMPT},
                    {
                        "type": "text",
                        "text": self._load_personal_documents(),
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data
                            }
                        },
                        {"type": "text", "text": ANALYSIS_PROMPT}
                    ]
                }]
            )
            end_time = datetime.now(timezone.utc)

            # Calculate costs
            analysis_cost = message.usage.output_tokens * 0.00001

            # Log API usage statistics
            duration = (end_time - start_time).total_seconds()
            self.logger.info(f"API call time for {file_path.name}: {duration} seconds")
            self.logger.info(f"API call input tokens: {message.usage.input_tokens} tokens")
            self.logger.info(f"API call output tokens: {message.usage.output_tokens} tokens")
            self.logger.info(f"API call cost: ${analysis_cost}")

            # Parse response
            try:
                analysis_response = json.loads(message.content[0].text)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse Claude's response as JSON")
                analysis_response = self._recover_malformed_response(message.content[0].text)

            # Validate response schema
            if not self._validate_response_schema(analysis_response):
                raise ValueError("Response does not match expected schema")

            # Construction de l'analyse finale
            analysis = {
                **analysis_response,
                "forget": False,
                "note_total": analysis_response["careerFitAnalysis"]["careerDevelopmentRating"] \
                    + analysis_response["profileMatchAssessment"]["matchCompatibilityRating"] \
                    + analysis_response["competitiveProfile"]["successProbabilityRating"],
                "analysis_cost": analysis_cost,
                "file_name": file_path.name,
                "cover_letter": None,
                "analysis_markdown": self.generate_analysis_markdown(analysis_response)
            }

            # Génération automatique de la lettre de motivation si recommandé
            if analysis_response["strategicRecommendations"]['shouldApply']["decision"]:
                self.generate_cover_letter(analysis)  # On utilise la fonction existante

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing PDF {file_path}: {e}")
            return None

    async def analyze_pdfs_parallel(self, pdf_files: List[Path], max_concurrent: int = 3) -> List[Dict]:
        """
        Analyze multiple PDF files in parallel.
        """
        # Créer un sémaphore pour limiter les requêtes concurrentes
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(file_path: Path):
            async with semaphore:
                return await self.analyze_pdf_async(file_path)

        # Créer les tâches pour chaque fichier
        tasks = [
            analyze_with_semaphore(file_path)
            for file_path in pdf_files
        ]

        # Exécuter toutes les tâches en parallèle
        results = await asyncio.gather(*tasks)

        # Filtrer les résultats None (erreurs)
        return [r for r in results if r is not None]

    def analyze_pdf(self, file_path: Path) -> Optional[Dict]:
        """
        Analyze a job offer PDF using Claude API.

        Args:
            file_path (Path): Path to the PDF file to analyze

        Returns:
            Optional[Dict]: Analysis results or None if analysis fails
        """
        try:
            # Load and prepare PDF
            with open(file_path, "rb") as f:
                pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

            # Construct message for Claude
            start_time = datetime.now(timezone.utc)
            message = self.client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                    },
                    {
                        "type": "text",
                        "text": self._load_personal_documents(),
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data
                            }
                        },
                        {
                            "type": "text",
                            "text": ANALYSIS_PROMPT
                        },
                    ]
                }]
            )
            end_time = datetime.now(timezone.utc)

            # Calculate total cost (including context cost if first analysis)
            analysis_cost = message.usage.output_tokens * 0.00001

            # Log API usage statistics
            self.logger.info(f"API call time: {(end_time - start_time).total_seconds()} seconds")
            self.logger.info(f"API call input tokens: {message.usage.input_tokens} tokens")
            self.logger.info(f"API call output tokens: {message.usage.output_tokens} tokens")
            self.logger.info(f"API call cost: ${analysis_cost}")

            # Safe parsing of response
            try:
                analysis_response = json.loads(message.content[0].text)
            except json.JSONDecodeError:
                self.logger.error("Failed to parse Claude's response as JSON")
                # Attempt recovery with new prompt
                analysis_response = self._recover_malformed_response(message.content[0].text)

            # Validate response schema
            if not self._validate_response_schema(analysis_response):
                raise ValueError("Response does not match expected schema")

            # Enrich with analysis metadata
            analysis = {
                **analysis_response,
                "forget": False,
                "note_total": analysis_response["careerFitAnalysis"]["careerDevelopmentRating"] \
                    + analysis_response["profileMatchAssessment"]["matchCompatibilityRating"] \
                    + analysis_response["competitiveProfile"]["successProbabilityRating"] \
                    + analysis_response["strategicRecommendations"]['shouldApply']["chanceRating"],
                "analysis_cost": analysis_cost,
                "file_name": file_path.name,
                "cover_letter": None,
                "analysis_markdown": self.generate_analysis_markdown(analysis_response)
            }

            # Génération automatique de la lettre de motivation si recommandé
            if analysis_response["strategicRecommendations"]['shouldApply']["decision"]:
                self.generate_cover_letter(analysis)

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing PDF {file_path}: {e}")
            return None

    def generate_cover_letter(self, analysis: Dict) -> Optional[Dict]:
        """
        Generate a cover letter using Claude API based on job analysis.

        Args:
            analysis (Dict): Job analysis results

        Returns:
            Optional[Dict]: Generated cover letter and cost info, or None if generation fails
        """
        # Check if cover letter already exists
        if analysis.get("cover_letter"):
            return analysis["cover_letter"]

        try:
            # Construct message for Claude
            start_time = datetime.now(timezone.utc)
            message = self.client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=COVER_LETTER_TEMPERATURE,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                    },
                    {
                        "type": "text",
                        "text": self._load_personal_documents(),
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""
                                Job Analysis:
                                {json.dumps(analysis, indent=2)}\n\n
                                {GENERATION_PROMPT}
                            """
                        }
                    ]
                }]
            )
            end_time = datetime.now(timezone.utc)

            # Log API usage statistics
            self.logger.info(f"API call time: {(end_time - start_time).total_seconds()} seconds")
            self.logger.info(f"API call input tokens: {message.usage.input_tokens} tokens")
            self.logger.info(f"API call output tokens: {message.usage.output_tokens} tokens")
            self.logger.info(f"API call cost: ${message.usage.output_tokens * TOKEN_COST}")

            # Create cover letter dictionary with metadata
            cover_letter = {
                "content": message.content[0].text,
                "generated_at": datetime.now().isoformat(),
                "generation_cost": message.usage.output_tokens * 0.00001
            }

            # Add cover letter to analysis
            analysis["cover_letter"] = cover_letter

            return cover_letter

        except Exception as e:
            self.logger.error(f"Error generating cover letter: {e}")
            return None


    def _validate_response_schema(self, response: Dict) -> bool:
        """
        Validate that the response matches the expected schema.
        """
        required_keys = [
            "jobSummary",
            "careerFitAnalysis",
            "profileMatchAssessment",
            "competitiveProfile",
            "strategicRecommendations"
        ]

        return all(key in response for key in required_keys)

    def _recover_malformed_response(self, text: str) -> Dict:
        """
        Attempt to recover a malformed response by sending it back to Claude.
        """
        recovery_prompt = """
        The following response should be a valid JSON but is not.
        Fix the format by strictly following the requested schema.

        Response to fix:
        {text}
        """

        message = self.client.messages.create(
            model=DEFAULT_MODEL,
            temperature=0,
            messages=[{
                "role": "user",
                "content": recovery_prompt
            }]
        )

        return json.loads(message.content[0].text)

    def _display_section_with_bullets(self, title: str, items: Union[str, List], format: str = "text") -> str:
        """Format a section with bullet points."""
        if isinstance(items, str):
            items = [items]

        bullet = "-" if format == "markdown" else "\n•"
        formatted_items = []

        for item in items:
            formatted_items.append(f"{bullet} {item}")

        items_text = "\n".join(formatted_items)
        return f"\n**{title}**:\n{items_text}\n" if format == "markdown" else f"\n{title}:\n{items_text}\n"

    def generate_analysis_markdown(self, analysis: Dict) -> str:
        """Generate complete markdown formatted analysis."""
        # Format analysis as markdown
        return f"""
### Résumé de l'offre

**Poste**: {analysis['jobSummary']['jobTitle']}

**Entreprise**: {analysis['jobSummary']['jobCompany']}

**Localisation**: {analysis['jobSummary']['jobLocation']}

**Aperçu**: {analysis['jobSummary']['jobOverview']}

{self._display_section_with_bullets("Facteurs de risque pour le recrutement", analysis['jobSummary'].get('jobFailureFactors', ["Aucun facteur identifié"]), format="markdown")}

{self._display_section_with_bullets("Analyses des pain points", analysis['jobSummary'].get('jobPainPointsAnalysis','//'), format="markdown")}

### Intérêt pour votre carrière
{self._display_section_with_bullets("Analyse", analysis['careerFitAnalysis']['careerAnalysis'], format="markdown")}

### Adéquation du profil
{self._display_section_with_bullets("Analyse", analysis['profileMatchAssessment']['profileMatchAnalysis'], format="markdown")}

### Probabilité de succès
{self._display_section_with_bullets("Analyse", analysis['competitiveProfile']['competitiveAnalysis'], format="markdown")}

### Scores d'évaluation

- Développement de carrière: {analysis['careerFitAnalysis']['careerDevelopmentRating']}/10
- Compatibilité du profil: {analysis['profileMatchAssessment']['matchCompatibilityRating']}/10
- Probabilité de succès: {analysis['competitiveProfile']['successProbabilityRating']}/10
- Recommandation: {analysis['strategicRecommendations']['shouldApply'].get('chanceRating', 0)}/10

### Recommandations stratégiques:

**Dois-je candidater à cette offre?**

{"✅ oui" if analysis['strategicRecommendations']['shouldApply']['decision'] else "❌ non"} - {analysis['strategicRecommendations']['shouldApply'].get('chanceRating', 0)}/10

{analysis['strategicRecommendations']['shouldApply']['explanation']}

{self._display_section_with_bullets("Points clés de l'offre",analysis['strategicRecommendations'].get('keyPointsInJobOffer', ["Aucun"]),format="markdown")}
{self._display_section_with_bullets("Points clés de mon profil",analysis['strategicRecommendations'].get('matchingPointsWithProfile', ["Aucun"]),format="markdown")}
{self._display_section_with_bullets("Mots-clés à utiliser",analysis['strategicRecommendations'].get('keyWordsToUse', ["Aucun"]),format="markdown")}

### Étapes de préparation et focus pour l'entretien

- {analysis['strategicRecommendations']['preparationSteps']}
- {analysis['strategicRecommendations']['interviewFocusAreas']}
                            """
