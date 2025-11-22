import os
import base64
import io
from typing import TypedDict, Any, List, Optional, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class RouterOutput(BaseModel):
    """Determines the intent of the user."""
    intent: Literal["diagnosis", "medicine_info", "test_info"]

class PharmacistOutput(BaseModel):
    """Schema for medication queries."""
    name: str = Field(description="Generic name of the medicine")
    brand_names: str = Field(description="Common brand names (e.g., Tylenol, Panadol)")
    uses: List[str] = Field(description="Comprehensive list of primary indications")
    mechanism: str = Field(description="Detailed mechanism of action")
    dosage: str = Field(description="Standard adult dosage guidelines")
    lifestyle_diet: str = Field(description="Dietary considerations (e.g. avoid alcohol) and lifestyle advice")
    side_effects: List[str] = Field(description="Common adverse effects")
    warnings: str = Field(description="Key contraindications or black box warnings")

class DiagnosticOutput(BaseModel):
    """Schema for symptom or image analysis."""
    title: str = Field(description="Clinical title of the finding")
    summary: str = Field(description="Executive summary for a doctor")
    findings: List[str] = Field(description="List of specific medical observations")
    table_data: List[dict] = Field(description="List of lab values if applicable, else empty")
    interpretation: str = Field(description="Detailed clinical impression")
    recommendations: List[str] = Field(description="Actionable next steps including medications")
    lifestyle: str = Field(description="Dietary and lifestyle modifications recommendation")
    severity: Literal["Low", "Moderate", "High", "Critical"] = Field(description="Triage acuity")

class TestInfoOutput(BaseModel):
    """Schema for procedural information."""
    test_name: str
    purpose: str
    procedure: str
    preparation: str
    normal_range: str


llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash", 
    temperature=0, 
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


class MedicalState(TypedDict):
    user_input: str          
    image_data: Any          
    input_type: str          
    intent: str              
    structured_response: dict 



def router_node(state: MedicalState):
    if state['input_type'] == 'file':
        return {"intent": "diagnosis"}
    
    structured_llm = llm.with_structured_output(RouterOutput)
    response = structured_llm.invoke(f"Classify the medical intent of: {state['user_input']}")
    return {"intent": response.intent}

def diagnostician_node(state: MedicalState):
    print("--- DIAGNOSTICIAN RUNNING ---")
    structured_llm = llm.with_structured_output(DiagnosticOutput)
    
    if state.get('image_data'):
        img = state['image_data']
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Analyze this clinical image strictly. Identify pathologies, severity, recommend next steps, and suggest lifestyle/dietary changes if relevant."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
            ]
        )
        response = structured_llm.invoke([message])
    else:
        prompt = f"""
        Act as a senior internal medicine physician. 
        Analyze these symptoms: "{state['user_input']}"
        Provide a differential diagnosis, acuity assessment, management plan, and specific lifestyle/dietary advice.
        """
        response = structured_llm.invoke(prompt)
        
    return {"structured_response": response.model_dump()}

def pharmacist_node(state: MedicalState):
    print("--- PHARMACIST RUNNING ---")
    structured_llm = llm.with_structured_output(PharmacistOutput)
    prompt = f"""
    Provide a COMPREHENSIVE pharmacological profile for: "{state['user_input']}".
    You MUST include:
    1. Common brand names.
    2. Detailed mechanism.
    3. Standard dosage guidelines.
    4. Diet interactions (e.g., food/alcohol) and lifestyle advice.
    5. Safety warnings.
    """
    response = structured_llm.invoke(prompt)
    return {"structured_response": response.model_dump()}

def educator_node(state: MedicalState):
    print("--- EDUCATOR RUNNING ---")
    structured_llm = llm.with_structured_output(TestInfoOutput)
    prompt = f"""
    Explain this medical procedure/test: "{state['user_input']}".
    Cover preparation, interpretation, and normal ranges.
    """
    response = structured_llm.invoke(prompt)
    return {"structured_response": response.model_dump()}

# GRAPH 
workflow = StateGraph(MedicalState)
workflow.add_node("router", router_node)
workflow.add_node("diagnostician", diagnostician_node)
workflow.add_node("pharmacist", pharmacist_node)
workflow.add_node("educator", educator_node)

workflow.set_entry_point("router")

def route_logic(state: MedicalState):
    return state['intent']

workflow.add_conditional_edges("router", route_logic, 
    {"diagnosis": "diagnostician", "medicine_info": "pharmacist", "test_info": "educator"})
workflow.add_edge("diagnostician", END)
workflow.add_edge("pharmacist", END)
workflow.add_edge("educator", END)

app_graph = workflow.compile()