"""
Job offer analyzer using Claude API for Job Set & Match!

This module handles:
- Job offer analysis using Claude
- Cover letter generation using Claude
- API cost tracking
"""

from .config import DATA_PATH
import logging
from pathlib import Path
from typing import Dict, Optional, List
import json
import os
from datetime import datetime, timezone
from anthropic import Anthropic
import base64
#import PyPDF2

class OfferAnalyzer:
    """Analyzes job offers and generates cover letters using Claude API."""

    _prompt_context="""
                    Create a comprehensive professional profile for job offer analysis.

                    OUTPUT STRUCTURE:
                    1. Executive Summary (max 100 words)
                        - Current position & transition goal
                        - Key expertise areas
                        - Core value proposition

                    2. Professional Profile Detail:
                    A. Technical Skills & Expertise
                        - Current technical stack
                        - Emerging skills
                        - Tools & methodologies mastery

                    B. Leadership & Management Experience
                        - Team size & scope
                        - Project scale & impact
                        - Key achievements with metrics

                    C. Industry Knowledge & Business Impact
                        - Sector expertise
                        - Notable transformations
                        - Quantified results

                    3. Career Transition Elements:
                        - Transferable skills
                        - Recent training & certifications
                        - Growth areas & learning path

                    4. Exhaustive experiences for Cover Letters:
                    A. Success Stories
                        - Major achievements with context
                        - Problem-solving examples
                        - Transformation initiatives
                        - Quantified results & impact

                    B. Leadership Narratives
                        - Team management situations
                        - Change management examples
                        - Crisis resolution cases

                    C. Technical Implementations
                        - Digital transformation projects
                        - Data-driven initiatives
                        - Innovation examples

                    5. Professional Values & Soft Skills:
                    - Core professional values
                    - Working style
                    - Team collaboration approach
                    - Learning mindset examples
                    - Adaptation capabilities

                    QUALITY CONTROL:
                    - First evaluate the output against criteria:
                    1. Completeness (0-10): Coverage of essential profile elements
                    2. Accuracy (0-10): Precision of information vs source material
                    3. Relevance (0-10): Alignment with job market analysis needs
                    4. Conciseness (0-10): Information density and clarity
                    5. No hallucinations (0-10): Avoid exaggerated claims or false claims

                    - If ANY criterion scores below 8/10, DO NOT provide the output. Instead:
                    1. List the failing criteria
                    2. Explain why they fall short
                    3. Request additional information if needed
                    4. Propose improvements needed

                    Only proceed with providing the full profile if ALL criteria score 8 or higher.
                    """

    _prompt_system = """
                    You are a tech-focused career coach named Joe created by the company AI Career Coach Co, offering guidance in French. Emphasis on current trends, skill requirements, job search strategies.

                    You will be replying to users who are on the AI Career Coach Co. office.

                    *Expertise Area*: Digital and Tech World
                    - Specialized guidance in career choices, job search strategies, cover letter and resume writing, and professional development within technology, digital marketing, software development, and related fields.
                    - Emphasis on current trends, skill requirements, and unique opportunities in the tech industry.

                    *Approach*: Open-Minded and Inclusive
                    - Catering to a diverse range of career paths and individual aspirations, both within and outside the tech world.
                    - Adaptable advice considering the varying needs and backgrounds of users.

                    <rules>
                    Here are some important rules for the interaction:
                    - Always stay in character, as Joe, an AI from AI Career Coach Co.
                    - If you are unsure how to respond, say "Sorry, I didn't understand that."
                    </rules>
                    """

    _prompt_company = """
                    **ROLE**: You are an experienced business analyst and talent acquisition strategist

                    ## Context

                    You are assisting a professional with analyzing potential target companies for career opportunities, with a focus on data and tech positions. Your analysis should be thorough, data-driven, and presented in French.

                    <instructions>
                    ## Instructions

                    1. Use all available sources (LinkedIn, company website, news articles, etc.)
                    2. Maintain objectivity while providing strategic insights
                    3. Score each section using the provided scales
                    4. Format your response in French using the structure below

                    ## Analysis Template

                    <output format>
                    ```bash
                    ### I. Identity Card

                    [Adopt a journalistic approach]
                    - ** Name & vision **: [Name + tagline/mission]
                    - ** Sector & positioning **: [Market analysis and positioning]
                    - ** Key data **:
                    - Creation: [Date]
                    - Workforce: [Size + Evolution]
                    - Implantations: [mapping]
                    - Funding: [Structure + Latest Retlates]

                    ### II. Tech & data analysis
                    [Adopt a technical architect approach]
                    - **Technical Ecosystem**
                    - **Data & AI Organization**
                    - **Innovative Projects**
                    - **Tech Maturity Score**: [1-5 + justification]

                        **Points to Analyze**
                        1. Organizational Structure
                            - Existence of a CDO/Head of Data
                            - Size of the data team
                            - Organization of teams (centralized vs decentralized)
                        3. Technical Communication
                            - Tech publications on their blog
                            - Conference presentations
                            - Employee LinkedIn articles
                        4. Technology Stack
                            - Tools used (via StackShare, job offers)
                            - Cloud infrastructure
                            - ML/AI frameworks

                        **Note**
                        1. Initial
                            - Start of transformation : First data offers
                            - Keywords: “implementation”, “initiate”, “develop”
                            - Data team < 5 people
                        2. In development
                            - Structure in place : Technical stack established
                            - Dedicated data team
                            - Keywords: “optimize”, “improve”, “strengthen”
                        3. Advanced
                            - Mature data culture
                            - Existing data/AI products
                            - Technical publications
                            - Keywords: "Innovate", "Scalability", "industrialization"

                    ### III. Culture & Impact

                    [Adopt an anthropological approach]
                    - ** and & values ​​**
                    - ** Social impact **
                    - ** Learning culture **
                    - ** Culture score **: [1-5 + justification]

                        **points to check**
                        1. Analysis of job offers:
                            - inclusive language
                            - Flexibility on the prerequisite
                            - Emphasis on transverse skills
                        2. Business culture:
                            - Employee testimonials
                            - Presence of conversion events
                            - HR communication on diversity
                        3. Recruitment history:
                            - Linkedin profiles of current employees
                            - Course of team members
                            - Experience feedback on Glassdoor/Welcome to the Jungle

                        **Note**
                        1. Closed
                            Traditional profiles only
                            - Strict diploma requirements
                            - specific years of experience required
                            - No mention of "atypical profiles"
                        2. Open with reserves
                            Consider the conversions
                            - Mention "or equivalent experience"
                            - Valorization of soft skills
                            - Some profiles already present in retraining
                        3. Very open
                            Actively supportive

                    ### IV. Dynamics & Opportunities

                    [Adopt a strategic approach]
                    - **Growth Trajectory**
                    - **Challenges & Opportunities**
                    - **HR & Inclusion Policy**
                    - **Potential Score**: [1-5 + justification]

                    ### V. Strategic analysis

                    [Adopt an advisory approval]
                    - **Personal swot**: [Strengths/weaknesses/Opportunities/threats]
                    - **Approach plan**: [Detailed strategy]
                    - **Resources & Network**: [Contacts & leviers]

                    ### VI. Summary & Recommendations

                    - **Global score **: [/15 + analysis]
                    - **go/no-go **: [argued decision]
                    - **Action plan **: [3-6-12 months]
                    - **Vigilance points **
                    ```
                    </output format>

                    ## Crititeria evaluation

                    [Detalled Scring Guidelines for Each Section]
                    - Tech maturity (1-5)
                    - Culture & values ​​(1-5)
                    - Growth Potential (1-5)

                    ## Output Requirements

                    - Language: French
                    - Format: Markdown
                    - Length: comprehensive yet concise
                    - Tone: Professional and analytical
                    </instructions>
                    """

    _prompt_analysis = """
                        **Objective**: Analyze a job offer to highlight key elements

                        <instructions>
                        I'm sharing a job posting for your analysis.

                        Please provide a thorough analysis of this job offer, following these steps:

                        1. Read and understand the entire job offer.
                        2. Consider unique aspects of the job offer and how they relate to the profile's background.
                        3. Your analysis must cover all the mentionned points. Uses a framework to identify key verbatims, determine the company's level of data maturity, and identify the main issues.
                        4. After your analysis for each section, provide the final output for that section in the specified JSON format.

                        Your analysis should cover all the following points:

                        1. Job summary:
                        - Job title
                        - Job compagny
                        - Job location
                        - Job Overview:
                            - Job description
                            - Key responsibilities
                            - Required qualifications
                            - Company context
                            - Working conditions (if mentioned)
                        - Job Failures Factors: 3 possible failure factors for hiring, based on the company and the evolution of the sector.
                        - Pain Points Analysis: based on the job description's context and requirements, identify the 2-3 key pain points the company is trying to address with this position.

                        2. Career Fit Analysis:
                        - What is in my interest given my career and my development?
                            - Evaluate how this role aligns with my career trajectory
                            - Identify potential growth opportunities
                            - Assess work-life balance considerations
                        - Rate overall career development potential (1-10 scale)

                        3. Profile Match Assessment:
                        - Is my profile suitable for this offer?
                            - Compare my qualifications to job requirements
                            - List specific matching qualifications
                            - Areas where I may need improvement
                            - Identify my main strengths and weaknesses
                            - Identify potential red flags
                            - Provide indications about cultural fit
                        - Rate match compatibility (1-10 scale)

                        4. Competitive Analysis:
                        - How can my profile stand out?
                            - Unique Competitive Advantages
                                - Rare/distinctive experiences or skills
                                - Unique skill combinations
                                - Relevant specific achievements
                            - Unique Value Proposition
                                - Concrete impact I can bring
                                - Solutions to company-specific challenges
                                - Innovative vision/approach to the position
                            - Differentiation Strategy
                                - Key points to highlight in application
                                - Original angles of approach
                                - Stories/concrete examples to prepare
                        - Overall application success probability rating (1-10 scale)

                        5. Strategic Recommendations:
                        - Rate my chances out of 10
                        - Is it realistic to expect to be offered the position? (Yes/No with explanation, under 7.1, it is no realistic)
                        - Key points in the job offer, find verbatim
                        - Matching points with my profile
                        - Specific keywords or skills to use in cover letter, find verbatim
                        - Suggested preparation steps
                        - Potential interview focus areas

                        6. Offer Content:
                        - Include the full job offer text

                        Please be direct and specific in your assessment, using concrete examples where possible.
                        Adds explanations and details the analysis in list form.

                        You MUST respond in the following JSON format, with NO additional text:
                        {
                        "jobSummary": {
                            "jobTitle": "",
                            "jobCompany": "",
                            "jobLocation": "",
                            "jobOverview": "",
                            "jobFailureFactors": [],
                            "jobPainPointsAnalysis": []
                        },
                        "careerFitAnalysis": {
                            "careerAnalysis": [],
                            "careerDevelopmentRating": 0,
                        },
                        "profileMatchAssessment": {
                            "profileMatchAnalysis": [],
                            "matchCompatibilityRating": 0
                        },
                        "competitiveProfile": {
                            "competitiveAnalysis": [],
                            "successProbabilityRating": 0
                        },
                        "strategicRecommendations": {
                            "shouldApply": {
                                "decision": false,
                                "explanation": "",
                                "chanceRating": 0
                            },
                            "keyPointsInJobOffer": [],
                            "matchingPointsWithProfile": [],
                            "keyWordsToUse": [],
                            "preparationSteps": "",
                            "interviewFocusAreas": ""
                        },
                        "offerContent":""
                        }
                        </instructions>

                        IMPORTANT RULES:
                        1. Follow this JSON structure EXACTLY
                        2. Do NOT add explanations or text outside the JSON
                        3. For any non-applicable field, use empty array [] or null
                        4. Round numerical scores to one decimal place
                        5. Limit each array to maximum 5 most relevant elements
                        6. Ensure all text is in French, as you are providing guidance in French.
                        """

    _prompt_generation = """
                        **Objective**: Write the best possible cover letter for my profile

                        SOURCE CONTROL:
                        1. Job Offer Information:
                        - ONLY use information explicitly stated in the provided job description
                        - DO NOT make assumptions about company needs not mentioned in the offer
                        - Use exact keywords and terminology from the job posting

                        2. Candidate Background:
                        - ONLY reference experiences and skills documented in the provided CV/profile
                        - Use specific achievements with real metrics from past roles
                        - Match only actual technical skills mentioned in CV with job requirements

                        3. Strict Matching Rules:
                        - Each claim must be traceable to either the job description or candidate documents
                        - No generic industry assumptions
                        - No speculative company information
                        - No extrapolated achievements
                        - No assumed technical capabilities

                        4. Required Source Citations:
                        When referencing:
                        - Company facts: Must come from provided job offer
                        - Achievements: Must be listed in CV/profile
                        - Technical skills: Must appear in candidate documents
                        - Metrics: Must be from actual experiences
                        - Wordings: Prefer the verbatim version of the offer posting if possible.

                        VERIFICATION CHECKLIST:
                        Before generating content, verify:
                        □ All company information comes from job posting
                        □ All candidate claims are documented in CV/profile
                        □ All technical skills mentioned are proven in background
                        □ All metrics and achievements are real
                        □ No speculative or assumed information included

                        <instructions>
                        I want you to craft a concise, impactful motivation email or a concise, impactful cover letter for a career transition candidate with the following characteristics:

                        CORE NARRATIVE & AUTHENTICITY:
                        1. Identity & Journey:
                        - Core: Digital transformation leader evolving into Data Science/AI
                        - Progression: From data-driven management to AI implementation
                        - Bridge: Technical expertise meets business understanding

                        2. Differentiators:
                        - Track record: Proven successful transitions and adaptations
                        - Unique perspective: Business strategy + Technical implementation
                        - Learning agility: Examples of rapid skill acquisition
                        - Pain points resolution: Demonstrated ability to identify and solve business challenges

                        3. Value Alignment:
                        - Company fit: Match between mission and experience
                        - Technical relevance: Skills mapping to their needs
                        - Growth potential: Learning from and contributing to their team
                        - Pain points match: Specific examples of solving similar challenges

                        STRUCTURE:
                        1. The Grab (15%):
                        - Company-centric opening showing research and understanding
                        - Connection to their mission/challenges/recent news
                        - Natural bridge to your unique profile
                        - Acknowledgment of key pain point(s) identified

                        2. The Hook (25%):
                        Choose the most relevant approach:
                        A. Company News Hook:
                            - Recent announcement/achievement
                            - Industry challenge they're facing
                            - Digital transformation initiative

                        B. Experience-Based Hook:
                            - Relevant achievement story
                            - Problem-solution narrative
                            - Quantifiable impact

                        C. Vision Hook:
                            - Shared perspective on industry evolution
                            - Technology/innovation alignment
                            - Future-focused connection

                        3. Experience Connection (40%):
                        - Concrete examples linking past achievements to new role
                        - Demonstration of transferable skills
                        - Show realistic understanding of the learning curve
                        - Use real examples from past experiences
                        A. Company-Specific Insights:
                            - Deep understanding of their challenges
                            - Technical ecosystem comprehension
                            - Strategic opportunities identification

                        B. Value Proposition:
                            - Leadership expertise application
                            - Technical skills relevance
                            - Transformation capabilities
                            - Addressing potential concerns (e.g., lack of industry-specific experience) and turning them into strengths

                        C. Transition Advantages if necessary:
                            - Learning agility evidence
                            - Fresh perspective benefits
                            - Hybrid skill set impact

                        D. Pain Points Resolution:
                            - Map specific elements from my profile that demonstrate how I can solve each of these challenges
                            - Specific examples of identifying hidden business challenges
                            - Concrete solutions implemented
                            - Measurable results achieved
                            - Adaptation potential for current context

                        4. Forward-Looking Close (20%):
                        - Specific contribution vision
                        - Growth commitment
                        - Clear next step

                        TONE & STYLE REQUIREMENTS:
                        - Enthusiastic about the career transition
                        - Confident but not arrogant. Avoid an overly laudatory tone.
                        - Humble about the learning curve in the new field
                        - Demonstrating adaptability and transferable skills
                        - Showing pragmatism and self-awareness
                        - Technical precision with business acumen
                        - Innovation mindset with practical approach
                        - Strategic insight with hands-on capability
                        - Authentic and personal while maintaining professionalism
                        - Show reflection and intentionality in career transition
                        - Balance between experienced leader and eager learner
                        - Professional tone without superlatives
                        - Communicate in professional, nuanced professional correspondence. Emphasize clarity, structured communication, and a balanced tone between personal motivation and professional expertise. Use formal language with precise technical and professional terminology.

                        WRITING GUIDELINES:
                        - Active voice
                        - Concrete examples
                        - Metric-driven achievements
                        - Technical-business balance
                        - Avoid generic phrases, overused buzzwords and clichés
                        - Include relevant keywords from the job posting
                        - Compelling narrative flow
                        - Keep the letter concise and impactful
                        - Avoid ready-made formulas found in 90% of cover letters.
                        - Include specific examples that demonstrate learning agility
                        - Reference relevant past transitions or transformations
                        - Highlight moments where business and technical understanding created value
                        - Limit enthusiasm-related adjectives (enthusiastic, passionate, excited)
                        - Limit statements about "adding value" or "driving performance"
                            Avoid:
                            - "I am particularly passionate/enthusiastic about..."
                            - "I have demonstrated my ability to..."
                            - "I am convinced that my profile..."
                            - Generic statements about "adding value" or "driving performance"
                            Instead use:
                            - "This position interests me because..." + specific reason
                            - "During my experience at X, I..." + concrete achievement
                            - "My background in X combined with Y..." + specific application
                            - Direct statements about contributions tied to past experiences
                        </instructions>

                        ORIGINALITY & RELEVANCE CHECK:
                        Review your proposition, does the letter answer these questions :
                        Key questions check:
                        - Why am I contacting this company?
                        - What can I bring to this company?
                        - How am I a good fit for the position in question?
                        Structure Check:
                        - Does the opening grab attention authentically?
                        - Is the hook compelling and relevant?
                        - Does the knowledge demonstration show depth and research?
                        - Is the progression from experience to new skills natural?
                        - Are company-specific insights meaningful and well-integrated?
                        Source Integrity Check:
                        - Can each statement be traced to provided documents?
                        - Are all achievements and metrics documented?
                        - Are technical skills claims supported by CV?
                        - Is company information strictly from job posting?

                        OVERALL ASSESSMENT:
                        - Adaptation to the position : rating out of 5
                        - Structure and clarity: rating out of 5
                        - Impact of the message: rating out of 5
                        - Differentiation: rating out of 5
                        - Present the letter:
                            - "This letter highlights..."
                            - "The letter answers key questions..."

                        OUTPUT SPECIFICATIONS:
                        - Length: 200-260 words
                        - Structured paragraphs
                        - Professional formatting
                        - Strategic keyword placement
                        - Narrative coherence
                        - Ensure all text is in French, as you are providing guidance in French.

                        Each section should build upon the previous one, creating a compelling story that demonstrates both immediate value and future potential.
                        """

    def __init__(self):
        """Initialize the analyzer with Claude API client and logging configuration."""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._context_cache = None  # To store the "digested" context

        # Initialize Claude API client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(
                            api_key=api_key,
                        )

    # def _pdf_to_text(pdf_path):
    #     """
    #     *************************************************************
    #     *** THIS FUNCTION IS NOT USED IN THE CURRENT APP VERSION ***
    #     *************************************************************
    #     Convert a PDF file to text using PyPDF2.

    #     Args:
    #         pdf_path (str): File path to the PDF file

    #     Returns:
    #         str: Text extracted from the PDF
    #     """
    #     # Open the PDF file in read-binary mode
    #     with open(pdf_path, 'rb') as pdf_file:
    #         # Create a PdfReader object instead of PdfFileReader
    #         pdf_reader = PyPDF2.PdfReader(pdf_file)

    #         # Initialize an empty string to store the text
    #         text = ''

    #         for page_num in range(len(pdf_reader.pages)):
    #             page = pdf_reader.pages[page_num]
    #             text += page.extract_text()

    #     return text

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
            for file in DATA_PATH.glob("*.[tm][xd]t"):
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
                model="claude-3-5-sonnet-20241022",
                #betas=["pdfs-2024-09-25", "prompt-caching-2024-07-31"],
                max_tokens=4096,
                temperature=0.2,
                system=[
                        {
                            "type": "text",
                            "text": self._prompt_system,
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
                            "text": f"{self._prompt_analysis}"
                        },
                    ]
                }]
            )
            end_time = datetime.now(timezone.utc)
            # Calculate total cost (including context cost if first analysis)
            analysis_cost = message.usage.output_tokens * 0.00001

            print(message.content)
            print(f"Cached API call time: {(end_time - start_time).total_seconds()} seconds")
            print(f"Cached API call input tokens : {message.usage.input_tokens} tokens")
            print(f"Cached API call input tokens (cache read): {getattr(message.usage, 'cache_read_input_tokens', 0)} tokens")
            print(f"Cached API call input tokens (cache write): {getattr(message.usage, 'cache_creation_input_tokens', 0)} tokens")
            print(f"Cached API call output tokens : {message.usage.output_tokens} tokens")
            print(f"Cached API call cost: ${analysis_cost}")

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
                "cover_letter": None
            }

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing PDF {file_path}: {e}")
            return None

    def _validate_response_schema(self, response: Dict) -> bool:
        """
        Validate that the response matches the expected schema.
        """
        required_keys = [
            "jobSummary", "careerFitAnalysis", "profileMatchAssessment",
            "competitiveProfile", "strategicRecommendations"
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

        message = self.client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            temperature=0,
            messages=[{
                "role": "user",
                "content": recovery_prompt
            }]
        )

        return json.loads(message.content[0].text)

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
                model="claude-3-5-sonnet-20241022",
                #betas=["pdfs-2024-09-25", "prompt-caching-2024-07-31"],
                max_tokens=4096,
                temperature=0.7,
                system=[
                        {
                            "type": "text",
                            "text": self._prompt_system,
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
                                        {self._prompt_generation}
                                    """
                        }
                    ]
                }]
            )
            end_time = datetime.now(timezone.utc)

            print(message.content[0].text)
            print(f"Cached API call time: {(end_time - start_time).total_seconds()} seconds")
            print(f"Cached API call input tokens : {message.usage.input_tokens} tokens")
            print(f"Cached API call input tokens (cache read): {getattr(message.usage, 'cache_read_input_tokens', 0)} tokens")
            print(f"Cached API call input tokens (cache write): {getattr(message.usage, 'cache_creation_input_tokens', 0)} tokens")
            print(f"Cached API call output tokens : {message.usage.output_tokens} tokens")
            print(f"Cached API call cost: ${message.usage.output_tokens * 0.00001}")

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
