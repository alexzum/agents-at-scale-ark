"""
Evaluation Prompt Builder

Implements the Builder pattern for constructing LLM-as-a-Judge evaluation prompts.
Provides a clean, maintainable way to build complex prompts with various sections.
"""

from typing import Optional, List
from dataclasses import dataclass
import logging

from .types import EvaluationRequest, EvaluationParameters
from .agent_resolver import AgentInstructions

logger = logging.getLogger(__name__)


@dataclass
class PromptSection:
    """Represents a section of the evaluation prompt"""
    title: str
    content: str
    order: int = 0

    def render(self) -> str:
        """Render the section as formatted text"""
        if not self.content.strip():
            return ""
        return f"{self.title}\n{self.content}\n" if self.title else self.content


class EvaluationPromptBuilder:
    """
    Builder for constructing evaluation prompts using the Builder pattern.

    Usage:
        prompt = (EvaluationPromptBuilder()
            .set_evaluator_role(role)
            .add_user_query(query)
            .add_response(response)
            .add_agent_instructions(instructions)
            .add_golden_examples(examples)
            .add_evaluation_criteria(scope)
            .build())
    """

    def __init__(self):
        self._sections: List[PromptSection] = []
        self._evaluator_role: Optional[str] = None
        self._evaluation_scope: Optional[str] = None
        self._min_score: float = 0.7

    def set_evaluator_role(self, role: Optional[str]) -> 'EvaluationPromptBuilder':
        """Set the evaluator role/persona"""
        self._evaluator_role = role or (
            "You are an AI evaluator tasked with assessing the quality of "
            "responses to user input and provided response."
        )
        logger.info(f"Using evaluator role: {self._evaluator_role[:100]}...")
        return self

    def add_user_query(self, query: str) -> 'EvaluationPromptBuilder':
        """Add the user query section"""
        section = PromptSection(
            title="USER QUERY:",
            content=query,
            order=10
        )
        self._sections.append(section)
        return self

    def add_response(self, request: EvaluationRequest) -> 'EvaluationPromptBuilder':
        """Add the response to evaluate section"""
        response_text = "\n".join([
            f"Response from {resp.target.type} '{resp.target.name}':\n{resp.content}"
            for resp in request.responses
        ])

        section = PromptSection(
            title="RESPONSE TO EVALUATE:",
            content=response_text,
            order=20
        )
        self._sections.append(section)
        return self

    def add_agent_instructions(
        self,
        agent_instructions: Optional[AgentInstructions]
    ) -> 'EvaluationPromptBuilder':
        """Add agent instructions and scope compliance guidelines"""
        if not agent_instructions:
            return self

        content = f"""
                    Name: {agent_instructions.name}
                    Purpose: {agent_instructions.description}

                    Expected to handle only query prompts that are aligned with the Agent Instructions and purpose.
                    For example, if an agent's purpose is to assist with mathematical calculations, it should clearly state that scope and refrain from processing USER QUERY that fall outside of it.
                    When it fails to do so, its evaluation score decreases on criteria such as compliance, appropriateness, and refusal handling.

                    SCORING GUIDELINES for criteria compliance, appropriateness, and refusal handling:
                        - If USER QUERY IS within agent scope AND agent provides good processing: HIGH score (0.8-1.0)
                        - If USER QUERY IS within agent scope BUT agent refuses unnecessarily: MEDIUM score (0.4-0.7)
                        - If USER QUERY IS outside agent scope AND agent properly refuses with explanation: HIGH score (0.8-1.0)
                        - If USER QUERY IS outside agent scope BUT agent processes it anyway: LOW score (0.0-0.3) - THIS IS CRITICAL
                """

        section = PromptSection(
            title="AGENT INSTRUCTIONS:",
            content=content,
            order=30
        )
        self._sections.append(section)
        logger.info(f"Adding scope instructions for agent: {agent_instructions.name}")
        return self

    def add_context(self, context: Optional[str]) -> 'EvaluationPromptBuilder':
        """Add additional context for evaluation"""
        if not context:
            return self

        content = f"""
            The following context should be considered when evaluating the response:

            {context}

            This context represents the reference material or retrieval results that should be used to assess accuracy, relevance, context precision, and context recall.
        """

        section = PromptSection(
            title="ADDITIONAL CONTEXT:",
            content=content,
            order=40
        )
        self._sections.append(section)
        logger.info(f"Adding additional context section, length: {len(context)} characters")
        return self

    def add_golden_examples(self, golden_examples: Optional[List]) -> 'EvaluationPromptBuilder':
        """Add golden examples for reference"""
        if not golden_examples:
            return self

        examples_list = []
        for example in golden_examples:
            metadata_str = ""
            if hasattr(example, 'metadata') and example.metadata:
                metadata_items = [f"{k}: {v}" for k, v in example.metadata.items()]
                metadata_str = f" ({', '.join(metadata_items)})"
            examples_list.append(
                f"Input: {example.input}\n"
                f"Expected Output: {example.expectedOutput}{metadata_str}"
            )

        examples_text = "\n".join(
            f"Example {i+1}:\n{example}"
            for i, example in enumerate(examples_list)
        )

        content = f"""
            Here are some reference examples to help guide your evaluation:
            {examples_text}
            Use these examples to understand the expected quality and style of responses for similar queries.
        """

        section = PromptSection(
            title="REFERENCE EXAMPLES:",
            content=content,
            order=50
        )
        self._sections.append(section)
        return self

    def add_evaluation_criteria(
        self,
        params: EvaluationParameters,
        has_agent_instructions: bool = False
    ) -> 'EvaluationPromptBuilder':
        """Add evaluation criteria definitions and scope"""
        self._evaluation_scope = ",".join(params.get_scope_list())
        self._min_score = params.min_score

        base_criteria = """
            1. Relevance: How well do the responses address the user's query?
            2. Accuracy: Are the responses factually correct and reliable?
            3. Completeness: Do the responses provide comprehensive information?
            4. Conciseness: Do the responses provide a concise information?
            5. Clarity: Are the responses clear and easy to understand?
            6. Usefulness: How helpful are the responses to the user?
            7. Context_Precision: How precise is the retrieved context in relation to the query?
            8. Context_Recall: How well does the response recall relevant information from the provided context?
        """

        scope_criteria = ""
        if has_agent_instructions:
            scope_criteria = """
                9. Compliance: Does the response stay within the agent's intended scope and domain?
                10. Appropriateness: Is the response appropriate given the input type and agent's specialty?
                11. Refusal Handling: If input is outside scope, does the agent properly refuse with explanation?
            """
            logger.info("Scope instructions added to prompt")

        all_criteria = base_criteria
        if scope_criteria:
            all_criteria += "\n" + scope_criteria

        content = f"""
                    Consider all following criteria definition: {all_criteria}

                    Evaluate the response only on the following criteria: {self._evaluation_scope}
                """

        section = PromptSection(
            title="",
            content=content,
            order=60
        )
        self._sections.append(section)
        return self

    def add_scoring_instructions(self) -> 'EvaluationPromptBuilder':
        """Add scoring instructions and output format"""
        if not self._evaluation_scope:
            raise ValueError("Evaluation scope must be set before adding scoring instructions")

        content = f"""Assessment

                        IMPORTANT SCORING INSTRUCTIONS:
                        1. Score each criterion individually on a 0-1 scale
                        2. The OVERALL SCORE must be the AVERAGE of the individual criteria scores
                        3. Only include criteria from {self._evaluation_scope} in your CRITERIA_SCORES
                        4. Ensure consistency between individual scores and the overall score

                        Provide your evaluation in the following format:
                        SCORE: [0-1] (must be the average of all criteria scores)
                        PASSED: [true/false] (by default true if SCORE >= {self._min_score})
                        REASONING: [Brief explanation of your evaluation focusing on scope compliance]
                        CRITERIA_SCORES: only include criteria from {self._evaluation_scope}, formatted as criterion_name=[0-1], criterion_name=[0-1], ...

                        Example format for CRITERIA_SCORES (only include criteria from {self._evaluation_scope}):
                        CRITERIA_SCORES: accuracy=0.8, completeness=0.9, usefulness=0.7, compliance=0.3

                        Be objective and thorough in your assessment. PRIORITIZE scope compliance over other factors.
                    """

        section = PromptSection(
            title="",
            content=content,
            order=70
        )
        self._sections.append(section)
        return self

    def build(self) -> str:
        """Build the final prompt by assembling all sections"""
        if not self._evaluator_role:
            raise ValueError("Evaluator role must be set before building")

        sorted_sections = sorted(self._sections, key=lambda s: s.order)

        sections_text = "\n\n".join(
            section.render()
            for section in sorted_sections
            if section.content.strip()
        )

        prompt = f"{self._evaluator_role}\n\n{sections_text}"

        return prompt


def build_evaluation_prompt(
    request: EvaluationRequest,
    params: EvaluationParameters,
    golden_examples: Optional[List] = None,
    agent_instructions: Optional[AgentInstructions] = None,
    requires_agent_instructions: bool = False
) -> str:
    """
    Convenience function to build an evaluation prompt using the builder pattern.

    Args:
        request: The evaluation request containing user query and responses
        params: Evaluation parameters including scope and thresholds
        golden_examples: Optional golden examples for reference
        agent_instructions: Optional agent instructions for scope validation
        requires_agent_instructions: Whether agent instructions are required for this evaluation

    Returns:
        The complete evaluation prompt as a string
    """
    builder = (EvaluationPromptBuilder()
        .set_evaluator_role(params.evaluator_role if params else None)
        .add_user_query(request.input)
        .add_response(request)
    )

    if agent_instructions and requires_agent_instructions:
        builder.add_agent_instructions(agent_instructions)

    if params and params.context:
        builder.add_context(params.context)

    if golden_examples:
        builder.add_golden_examples(golden_examples)

    has_agent_instructions = agent_instructions is not None and requires_agent_instructions

    builder.add_evaluation_criteria(params, has_agent_instructions)
    builder.add_scoring_instructions()

    return builder.build()
