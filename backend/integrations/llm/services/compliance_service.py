"""
LLM Compliance Analysis Service

Specialized service for pharmaceutical protocol compliance analysis using
Large Language Models. Provides structured prompting, response parsing,
and reference extraction for pharmaceutical standards compliance assessment.

Features:
- Specialized compliance analysis prompts
- Structured response parsing and validation
- Section reference extraction
- Compliance scoring and categorization
- Error handling with fallback strategies
- Response caching and optimization
"""
import re
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from ....config.settings import settings
from ....utils import logger, LLMError, ProtocolValidationError
from ..client import llm_client, LLMMessage

@dataclass
class CompliancePrompt:
    """
    Structured prompt for compliance analysis.
    
    Attributes:
        system_prompt: System instructions for the LLM
        protocol_text: Protocol text to analyze
        reference_sections: Similar Pharmacopoeia sections for context
        analysis_focus: Specific aspects to focus on
        output_format: Required output format specification
    """
    system_prompt: str
    protocol_text: str
    reference_sections: List[str]
    analysis_focus: List[str] = None
    output_format: str = "structured"

@dataclass
class ComplianceIssue:
    """
    Individual compliance issue identified.
    
    Attributes:
        issue_type: Type of issue ('terminology', 'procedure', 'missing', 'formatting')
        severity: Severity level ('critical', 'major', 'minor')
        description: Description of the issue
        location: Location in protocol where issue occurs
        recommendation: Recommended action to fix
        reference_section: Relevant Pharmacopoeia section
    """
    issue_type: str
    severity: str
    description: str
    location: str = ""
    recommendation: str = ""
    reference_section: str = ""

@dataclass
class ComplianceAssessment:
    """
    Complete compliance assessment result.
    
    Attributes:
        overall_score: Overall compliance score (0-100)
        compliance_status: Status ('compliant', 'partial', 'non-compliant')
        confidence_score: Confidence in assessment (0-100)
        issues: List of identified issues
        recommendations: General recommendations
        missing_elements: Required elements that are missing
        terminology_corrections: Terminology corrections needed
        strengths: Positive aspects of the protocol
        pharmacopoeia_references: Relevant Pharmacopoeia sections cited
        detailed_analysis: Full analysis text
        assessment_time: Time taken for assessment
    """
    overall_score: int = 0
    compliance_status: str = "unknown"
    confidence_score: int = 0
    issues: List[ComplianceIssue] = None
    recommendations: List[str] = None
    missing_elements: List[str] = None
    terminology_corrections: List[str] = None
    strengths: List[str] = None
    pharmacopoeia_references: List[str] = None
    detailed_analysis: str = ""
    assessment_time: float = 0.0

class ComplianceAnalysisService:
    """
    Service for LLM-powered compliance analysis.
    
    Provides specialized analysis of pharmaceutical protocols against
    pharmaceutical standards using structured prompts and
    response parsing techniques.
    
    Attributes:
        llm_client: LLM client for API communication
        enable_caching: Whether to cache analysis results
        analysis_cache: Cache of completed analyses
        default_focus_areas: Default analysis focus areas
    """
    
    def __init__(self,
                 llm_client=None,
                 enable_caching: bool = True):
        """
        Initialize the compliance analysis service.
        
        Args:
            llm_client: LLM client instance (optional)
            enable_caching: Whether to enable result caching
        """
        self.llm_client = llm_client or llm_client
        self.enable_caching = enable_caching
        self.analysis_cache: Dict[str, ComplianceAssessment] = {}
        
        # Default focus areas for analysis
        self.default_focus_areas = [
            "analytical procedures",
            "equipment specifications", 
            "reagent requirements",
            "test conditions",
            "acceptance criteria",
            "safety considerations",
            "documentation requirements",
            "quality control measures"
        ]
        
        logger.info(
            "Initialized ComplianceAnalysisService",
            enable_caching=enable_caching,
            default_focus_areas=len(self.default_focus_areas)
        )
    
    def analyze_compliance(self,
                          protocol_text: str,
                          reference_sections: List[str],
                          protocol_title: str = "",
                          focus_areas: List[str] = None,
                          custom_prompt: str = None) -> ComplianceAssessment:
        """
        Perform comprehensive compliance analysis of a protocol.
        
        Args:
            protocol_text: Protocol text to analyze
            reference_sections: Similar Pharmacopoeia sections for context
            protocol_title: Optional protocol title
            focus_areas: Specific areas to focus analysis on
            custom_prompt: Custom system prompt (optional)
            
        Returns:
            ComplianceAssessment: Detailed compliance analysis
            
        Raises:
            LLMError: If analysis fails
            ProtocolValidationError: If input validation fails
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(protocol_text, reference_sections)
            
            # Check cache first
            if self.enable_caching and cache_key in self.analysis_cache:
                logger.info("Returning cached compliance analysis", cache_key=cache_key[:8])
                return self.analysis_cache[cache_key]
            
            logger.info(
                "Starting compliance analysis",
                protocol_title=protocol_title,
                protocol_length=len(protocol_text),
                num_references=len(reference_sections)
            )
            
            import time
            start_time = time.time()
            
            # Prepare analysis prompt
            focus_areas = focus_areas or self.default_focus_areas
            prompt = self._create_compliance_prompt(
                protocol_text, reference_sections, focus_areas, custom_prompt
            )
            
            # Perform LLM analysis
            llm_response = self._execute_llm_analysis(prompt)
            
            # Parse and structure response
            assessment = self._parse_compliance_response(
                llm_response, time.time() - start_time
            )
            
            # Extract Pharmacopoeia references
            assessment.pharmacopoeia_references = self._extract_references(
                llm_response, reference_sections
            )
            
            # Cache result
            if self.enable_caching:
                self.analysis_cache[cache_key] = assessment
            
            logger.info(
                "Compliance analysis completed",
                overall_score=assessment.overall_score,
                status=assessment.compliance_status,
                num_issues=len(assessment.issues) if assessment.issues else 0,
                assessment_time=assessment.assessment_time
            )
            
            return assessment
            
        except (LLMError, ProtocolValidationError):
            raise
        except Exception as e:
            error_msg = f"Compliance analysis failed: {str(e)}"
            logger.error(error_msg, exception=e)
            raise LLMError(error_msg)
    
    def _create_compliance_prompt(self,
                                 protocol_text: str,
                                 reference_sections: List[str],
                                 focus_areas: List[str],
                                 custom_prompt: str = None) -> CompliancePrompt:
        """
        Create structured prompt for compliance analysis.
        
        Args:
            protocol_text: Protocol to analyze
            reference_sections: Reference Pharmacopoeia sections
            focus_areas: Areas to focus analysis on
            custom_prompt: Custom system prompt
            
        Returns:
            Structured CompliancePrompt
        """
        if custom_prompt:
            system_prompt = custom_prompt
        else:
            system_prompt = f"""You are a pharmaceutical compliance expert analyzing laboratory protocols against pharmaceutical standards.

Your task is to provide a comprehensive compliance analysis with the following structure:

1. OVERALL ASSESSMENT:
   - Compliance score (0-100)
   - Status: compliant/partial/non-compliant
   - Confidence score (0-100)

2. DETAILED ANALYSIS:
   Focus on these areas: {', '.join(focus_areas)}
   
3. COMPLIANCE ISSUES:
   For each issue found, specify:
   - Type: terminology/procedure/missing/formatting
   - Severity: critical/major/minor
   - Description
   - Location in protocol
   - Recommendation
   - Relevant Pharmacopoeia section

4. RECOMMENDATIONS:
   - Specific actionable improvements
   - Missing elements that should be added
   - Terminology corrections needed

5. STRENGTHS:
   - Positive aspects of the protocol
   - Areas that meet or exceed standards

6. PHARMACOPOEIA REFERENCES:
   - Cite specific sections and chapters
   - Quote relevant requirements

Provide your analysis in a structured, professional format that can be used for compliance reporting."""

        return CompliancePrompt(
            system_prompt=system_prompt,
            protocol_text=protocol_text,
            reference_sections=reference_sections,
            analysis_focus=focus_areas,
            output_format="structured"
        )
    
    def _execute_llm_analysis(self, prompt: CompliancePrompt) -> str:
        """
        Execute LLM analysis with the prepared prompt.
        
        Args:
            prompt: Structured compliance prompt
            
        Returns:
            LLM response text
            
        Raises:
            LLMError: If LLM request fails
        """
        try:
            # Prepare context with reference sections
            context_text = "\n\n".join([
                f"REFERENCE SECTION {i+1}:\n{section}"
                for i, section in enumerate(prompt.reference_sections[:5])  # Limit to avoid token limits
            ])
            
            # Create user prompt
            user_prompt = f"""Please analyze the following laboratory protocol for compliance with pharmaceutical standards.

PROTOCOL TO ANALYZE:
{prompt.protocol_text}

RELEVANT PHARMACOPOEIA SECTIONS FOR REFERENCE:
{context_text}

Please provide a comprehensive compliance analysis following the structured format requested."""

            # Prepare messages
            messages = [
                LLMMessage(role="system", content=prompt.system_prompt),
                LLMMessage(role="user", content=user_prompt)
            ]
            
            # Execute LLM request
            response = self.llm_client.chat_completion(
                messages=messages,
                temperature=settings.llm.temperature,
                max_tokens=settings.llm.max_tokens
            )
            
            if not response.content:
                raise LLMError("Empty response from LLM")
            
            return response.content
            
        except Exception as e:
            error_msg = f"LLM analysis execution failed: {str(e)}"
            logger.error(error_msg, exception=e)
            raise LLMError(error_msg)
    
    def _parse_compliance_response(self,
                                  llm_response: str,
                                  assessment_time: float) -> ComplianceAssessment:
        """
        Parse LLM response into structured compliance assessment.
        
        Args:
            llm_response: Raw LLM response text
            assessment_time: Time taken for assessment
            
        Returns:
            Structured ComplianceAssessment
        """
        try:
            # Initialize assessment
            assessment = ComplianceAssessment(
                detailed_analysis=llm_response,
                assessment_time=assessment_time,
                issues=[], 
                recommendations=[], 
                missing_elements=[],
                terminology_corrections=[],
                strengths=[],
                pharmacopoeia_references=[]
            )
            
            # Extract compliance score
            score_match = re.search(r'(?:compliance|overall)\s*score[:\s]*(\d+)', llm_response, re.IGNORECASE)
            if score_match:
                assessment.overall_score = int(score_match.group(1))
            
            # Extract compliance status
            status_patterns = [
                r'status[:\s]*(compliant|partial|non-compliant)',
                r'(compliant|partial|non-compliant)',
                r'assessment[:\s]*(compliant|partial|non-compliant)'
            ]
            
            for pattern in status_patterns:
                status_match = re.search(pattern, llm_response, re.IGNORECASE)
                if status_match:
                    assessment.compliance_status = status_match.group(1).lower()
                    break
            
            # Extract confidence score
            confidence_match = re.search(r'confidence[:\s]*(\d+)', llm_response, re.IGNORECASE)
            if confidence_match:
                assessment.confidence_score = int(confidence_match.group(1))
            else:
                # Default confidence based on response quality
                assessment.confidence_score = 85 if assessment.overall_score > 0 else 50
            
            # Extract recommendations
            recommendations = self._extract_list_items(llm_response, [
                r'recommendations?[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\n\d+\.|$)',
                r'improvements?[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\n\d+\.|$)'
            ])
            assessment.recommendations = recommendations
            
            # Extract missing elements
            missing = self._extract_list_items(llm_response, [
                r'missing[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\n\d+\.|$)',
                r'required.*missing[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\n\d+\.|$)'
            ])
            assessment.missing_elements = missing
            
            # Extract terminology corrections
            terminology = self._extract_list_items(llm_response, [
                r'terminology[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\n\d+\.|$)',
                r'corrections?[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\n\d+\.|$)'
            ])
            assessment.terminology_corrections = terminology
            
            # Extract strengths
            strengths = self._extract_list_items(llm_response, [
                r'strengths?[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\n\d+\.|$)',
                r'positive[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\n\d+\.|$)'
            ])
            assessment.strengths = strengths
            
            # Parse issues (simplified for now)
            issues = self._extract_compliance_issues(llm_response)
            assessment.issues = issues
            
            # Validate assessment
            if assessment.compliance_status == "unknown":
                if assessment.overall_score >= 80:
                    assessment.compliance_status = "compliant"
                elif assessment.overall_score >= 60:
                    assessment.compliance_status = "partial"
                else:
                    assessment.compliance_status = "non-compliant"
            
            logger.debug(
                "Parsed compliance response",
                score=assessment.overall_score,
                status=assessment.compliance_status,
                num_issues=len(assessment.issues),
                num_recommendations=len(assessment.recommendations)
            )
            
            return assessment
            
        except Exception as e:
            error_msg = f"Failed to parse compliance response: {str(e)}"
            logger.error(error_msg, response_preview=llm_response[:200], exception=e)
            
            # Return basic assessment with error info
            return ComplianceAssessment(
                overall_score=0,
                compliance_status="unknown",
                confidence_score=0,
                detailed_analysis=llm_response,
                assessment_time=assessment_time,
                issues=[], recommendations=["Failed to parse detailed analysis"],
                missing_elements=[], terminology_corrections=[], strengths=[],
                pharmacopoeia_references=[]
            )
    
    def _extract_list_items(self, text: str, patterns: List[str]) -> List[str]:
        """
        Extract list items from text using multiple patterns.
        
        Args:
            text: Text to search
            patterns: List of regex patterns to try
            
        Returns:
            List of extracted items
        """
        items = []
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section_text = match.group(1).strip()
                
                # Extract bullet points or numbered items
                item_patterns = [
                    r'^\s*[-*•]\s*(.+)$',
                    r'^\s*\d+\.\s*(.+)$',
                    r'^(.+)$'
                ]
                
                for line in section_text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    for item_pattern in item_patterns:
                        item_match = re.match(item_pattern, line)
                        if item_match:
                            item = item_match.group(1).strip()
                            if item and len(item) > 10:  # Filter out very short items
                                items.append(item)
                            break
                break
        
        return list(set(items))  # Remove duplicates
    
    def _extract_compliance_issues(self, text: str) -> List[ComplianceIssue]:
        """
        Extract compliance issues from analysis text.
        
        Args:
            text: Analysis text
            
        Returns:
            List of ComplianceIssue objects
        """
        issues = []
        
        # Look for issues section
        issues_patterns = [
            r'(?:compliance\s+)?issues?[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\n\d+\.|$)',
            r'problems?[:\s]*\n(.*?)(?=\n\n|\n[A-Z]|\n\d+\.|$)'
        ]
        
        for pattern in issues_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                issues_text = match.group(1)
                
                # Extract individual issues
                issue_lines = [line.strip() for line in issues_text.split('\n') if line.strip()]
                
                for line in issue_lines:
                    if len(line) > 20:  # Filter out short lines
                        # Determine severity from keywords
                        severity = "minor"
                        if re.search(r'\b(critical|severe|major|serious)\b', line, re.IGNORECASE):
                            severity = "critical" if "critical" in line.lower() else "major"
                        
                        # Determine issue type
                        issue_type = "procedure"
                        if re.search(r'\b(terminolog|word|term)\b', line, re.IGNORECASE):
                            issue_type = "terminology"
                        elif re.search(r'\b(missing|absent|lack)\b', line, re.IGNORECASE):
                            issue_type = "missing"
                        elif re.search(r'\b(format|structure|layout)\b', line, re.IGNORECASE):
                            issue_type = "formatting"
                        
                        issue = ComplianceIssue(
                            issue_type=issue_type,
                            severity=severity,
                            description=line,
                            location="",
                            recommendation="",
                            reference_section=""
                        )
                        issues.append(issue)
                break
        
        return issues[:10]  # Limit to avoid too many issues
    
    def _extract_references(self,
                           llm_response: str,
                           reference_sections: List[str]) -> List[str]:
        """
        Extract Pharmacopoeia references from LLM response.
        
        Args:
            llm_response: LLM analysis text
            reference_sections: Original reference sections
            
        Returns:
            List of referenced sections
        """
        references = []
        
        # Look for explicit references
        ref_patterns = [
            r'(?:ph\.?\s*eur\.?|pharmacopoeia)\s*([0-9]+\.?[0-9]*)',
            r'section\s*([0-9]+\.?[0-9]*)',
            r'chapter\s*([0-9]+\.?[0-9]*)'
        ]
        
        for pattern in ref_patterns:
            matches = re.findall(pattern, llm_response, re.IGNORECASE)
            for match in matches:
                references.append(f"Section {match}")
        
        # If no explicit references found, return first few reference sections
        if not references and reference_sections:
            references = [f"Reference Section {i+1}" for i in range(min(3, len(reference_sections)))]
        
        return list(set(references))  # Remove duplicates
    
    def _generate_cache_key(self, protocol_text: str, reference_sections: List[str]) -> str:
        """
        Generate cache key for analysis caching.
        
        Args:
            protocol_text: Protocol text
            reference_sections: Reference sections
            
        Returns:
            Cache key string
        """
        content = protocol_text + "".join(reference_sections[:3])  # Limit to avoid very long keys
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_analysis_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the analysis cache.
        
        Returns:
            Cache statistics
        """
        if not self.analysis_cache:
            return {"message": "No cached analyses"}
        
        assessments = list(self.analysis_cache.values())
        
        return {
            "total_cached": len(assessments),
            "avg_score": sum(a.overall_score for a in assessments) / len(assessments),
            "avg_assessment_time": sum(a.assessment_time for a in assessments) / len(assessments),
            "status_distribution": {
                status: sum(1 for a in assessments if a.compliance_status == status)
                for status in ["compliant", "partial", "non-compliant", "unknown"]
            },
            "cache_enabled": self.enable_caching
        }
    
    def clear_cache(self) -> int:
        """
        Clear the analysis cache.
        
        Returns:
            Number of cached analyses cleared
        """
        count = len(self.analysis_cache)
        self.analysis_cache.clear()
        logger.info(f"Cleared compliance analysis cache", cleared_count=count)
        return count

# Global instance for use throughout the application  
compliance_service = ComplianceAnalysisService()