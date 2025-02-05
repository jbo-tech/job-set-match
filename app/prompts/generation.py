"""
Generation prompt configuration for the Claude API.

This module defines the prompts used for generating cover letters.
"""

GENERATION_PROMPT_new = """
"""

GENERATION_PROMPT = """
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
- Confident but not arrogant
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
- Communicate in professional, nuanced professional correspondence

WRITING GUIDELINES:
- Active voice
- Concrete examples
- Metric-driven achievements
- Technical-business balance
- Avoid generic phrases and overused buzzwords
- Include relevant keywords from the job posting
- Compelling narrative flow
- Keep the letter concise and impactful
- Avoid ready-made formulas found in 90% of cover letters
- Include specific examples that demonstrate learning agility
- Reference relevant past transitions or transformations
- Highlight moments where business and technical understanding created value
- Limit enthusiasm-related adjectives
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

OUTPUT SPECIFICATIONS:
- Length: 200-260 words
- Structured paragraphs
- Professional formatting
- Strategic keyword placement from job posting
- Narrative coherence
- Ensure all text is in French, as you are providing guidance in French

Each section should build upon the previous one, creating a compelling story that demonstrates both immediate value and future potential.
"""

__all__ = ['GENERATION_PROMPT']
