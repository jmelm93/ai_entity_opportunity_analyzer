from pydantic import BaseModel, Field
from typing import List, Optional


### START: ENTITY RECOMMENDATION MODEL ###

class CompetitorData(BaseModel):
    """Represents data from a competitor."""
    
    salience: Optional[float] = Field(name="salience", description="The salience score of the entity in the competitor's content.", default=None)
    density: Optional[float] = Field(name="density", description="The density of the keyword in the competitor's content.", default=None)
    count: Optional[int] = Field(name="count", description="The number of times the keyword appears in the competitor's content.", default=None)
    tf_idf: Optional[float] = Field(name="tf_idf", description="The TF-IDF score of the keyword in the competitor's content.", default=None)

class MissingItem(BaseModel):
    """Represents a missing item (entity or keyword)."""
    
    entity_name: str = Field(name="entity_name", description="The name of the missing item.")
    entity_type: str = Field(name="type", description="The exact type the user has provided for the missing item.")
    relevance: float = Field(name="relevance", description="The exact relevance score the user has provided for the missing item.")
    reasoning: str = Field(name="reasoning", description="The exact reasoning the user has provided for the missing item.")

class IntegrationOpportunity(BaseModel):
    """Represents an integration opportunity for an entity."""
    
    section: str = Field(name="section", description="The section or area of the content where the entity can be integrated.")
    recommendation: str = Field(name="recommendation", description="Specific recommendation on how to integrate the entity.")
    related_terms: List[str] = Field(name="related_terms", description="List of related terms to use alongside the entity.")
    examples: List[str] = Field(name="examples", description="Examples of how to incorporate the entity naturally.")
    placement: str = Field(name="placement", description="Suggested placement of the entity in key areas like the title tag, meta description, and headings.")
    explanation: str = Field(name="explanation", description="Explanation of why each recommendation is beneficial for SEO and user experience.")

class EntityRecommendation(BaseModel):
    """Structured recommendation for integrating an entity."""
    
    entity_context: MissingItem = Field(name="entity_context", description="Context about the entity and its competitors.")
    integration_opportunities: List[IntegrationOpportunity] = Field(name="integration_opportunities", description="List of integration opportunities for the entity.")
    
    @property
    def to_markdown(self) -> str:
        """Convert the entity recommendation to a markdown string."""
        markdown = f"### {self.entity_context.entity_name} Integration Opportunities\n\n"
        for i, op in enumerate(self.integration_opportunities, start=1):
            markdown += f"#### Opportunity {i}: {op.section}\n\n"
            markdown += f"**Recommendation:** {op.recommendation}\n\n"
            markdown += f"**Related Terms:** {', '.join(op.related_terms)}\n\n"
            markdown += f"**Examples:**\n\n"
            for example in op.examples:
                markdown += f"- {example}\n"
            markdown += "\n"
            markdown += f"**Placement:** {op.placement}\n\n"
            markdown += f"**Explanation:** {op.explanation}\n\n"
        return markdown
    
### END: ENTITY RECOMMENDATION MODEL ###

### START: ENTITY SELECTION MODEL ###

class EntitySelection(BaseModel):
    """Entity name with reasoning behind the selection and score of how relevant it is for the client page."""
    entity_name: str = Field(name="entity_name", description="The name of the entity.")
    entity_type: str = Field(name="entity_type", description="The type of the entity.")
    relevance_score: float = Field(name="relevance_score", description="The relevance score of the entity for the client page (0-1).")
    reasoning: str = Field(name="reasoning", description="The reasoning behind the selection of the entity.")

class EntitySelections(BaseModel):
    """List of entity selections."""
    selected_entities: List[EntitySelection] = Field(name="selected_entities", description="List of selected entities with relevance scores and reasoning.")
    
    @property
    def to_markdown(self) -> str:
        """Convert the entity selections to a markdown string."""
        markdown = "### Selected Entities for Integration\n\n"
        for entity in self.selected_entities:
            markdown += f"- **{entity.entity_name}**\n"
            markdown += f"  - **Relevance Score:** {entity.relevance_score}\n"
            markdown += f"  - **Reasoning:** {entity.reasoning}\n\n"
        return markdown
    
### END: ENTITY SELECTION MODEL ###