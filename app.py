import streamlit as st
import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="JD Chat Analyzer",
    page_icon="💭",
    layout="wide"
)

def get_api_key():
    """Get API key from either .env file (local) or Streamlit secrets (cloud)"""
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        try:
            api_key = st.secrets.general.ANTHROPIC_API_KEY
        except:
            try:
                api_key = st.secrets["ANTHROPIC_API_KEY"]
            except:
                st.error("API key not found in environment or secrets.")
                st.stop()
    return api_key

def get_claude_response(conversation_history):
    """Get response from Claude"""
    try:
        client = Anthropic(api_key=get_api_key())
        
        # Different system prompt for final analysis
        if len(conversation_history) > 0 and "final analysis" in str(conversation_history[-1]):
            system_prompt = """You are an expert at analyzing job requirements. When providing the final analysis:
            1. Focus on concrete, specific skills rather than general statements
            2. Separate technical skills (tools, systems, certifications) from soft skills
            3. Clearly distinguish between must-have and good-to-have skills
            4. Use bullet points for each skill
            5. Provide a brief explanation of your categorization logic
            
            Use exactly this format:
            Must Have Technical Skills:
            - [specific skill]
            
            Must Have Soft Skills:
            - [specific skill]
            
            Good to Have Technical Skills:
            - [specific skill]
            
            Good to Have Soft Skills:
            - [specific skill]
            
            Brief Explanation:
            [Your explanation]"""
        else:
            system_prompt = """You are conducting a natural conversation to gather information about a job position. 
            Ask relevant follow-up questions based on the user's responses. After gathering sufficient information,
            ask if they'd like to proceed with the final analysis. Keep the conversation flowing naturally."""
        
        response = client.messages.create(
            model="claude-2",
            max_tokens=3000,
            system=system_prompt,
            messages=conversation_history
        )
        return response.content[0].text
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": """Hi! I'm here to help analyze job requirements. Let's have a conversation about the position you're looking to analyze. Could you start by telling me what position you're hiring for?"""
            }
        ]
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'final_analysis' not in st.session_state:
        st.session_state.final_analysis = None

def parse_skills(text):
    """Parse the response text to extract skills"""
    text = str(text)
    
    must_have_technical = []
    must_have_soft = []
    good_have_technical = []
    good_have_soft = []
    explanation = ""
    
    current_section = None
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        
        if 'Must Have Technical Skills:' in line:
            current_section = 'must_technical'
            continue
        elif 'Must Have Soft Skills:' in line:
            current_section = 'must_soft'
            continue
        elif 'Good to Have Technical Skills:' in line:
            current_section = 'good_technical'
            continue
        elif 'Good to Have Soft Skills:' in line:
            current_section = 'good_soft'
            continue
        elif 'Brief Explanation:' in line:
            current_section = 'explanation'
            continue
        
        if line.startswith('-') and line.strip('- '):
            skill = line.strip('- ').strip()
            if current_section == 'must_technical':
                must_have_technical.append(skill)
            elif current_section == 'must_soft':
                must_have_soft.append(skill)
            elif current_section == 'good_technical':
                good_have_technical.append(skill)
            elif current_section == 'good_soft':
                good_have_soft.append(skill)
        elif current_section == 'explanation' and line:
            explanation += line + " "
    
    return must_have_technical, must_have_soft, good_have_technical, good_have_soft, explanation.strip()

def display_chat_message(role, content):
    """Display a chat message with appropriate styling"""
    if role == "assistant":
        with st.chat_message(role, avatar="🤖"):
            st.write(content)
    else:
        with st.chat_message(role, avatar="👤"):
            st.write(content)

def main():
    st.title("Interactive JD Analyzer Chat 💭")
    
    initialize_session_state()
    
    # Display chat history
    for message in st.session_state.messages:
        display_chat_message(message["role"], message["content"])
    
    # Chat input
    if not st.session_state.analysis_complete:
        user_input = st.chat_input("Your response")
        
        if user_input:
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": user_input})
            display_chat_message("user", user_input)
            
            # Check if we should proceed with final analysis
            last_message = st.session_state.messages[-2]["content"].lower()
            if ("analysis report" in last_message or "proceed with" in last_message) and \
               any(word in user_input.lower() for word in ["yes", "sure", "okay", "go ahead", "ok"]):
                # Generate final analysis
                final_prompt = {
                    "role": "user",
                    "content": """Based on our conversation, provide a structured analysis using exactly this format:

                    Must Have Technical Skills:
                    - [List each required technical skill]

                    Must Have Soft Skills:
                    - [List each required soft skill]

                    Good to Have Technical Skills:
                    - [List each preferred technical skill]

                    Good to Have Soft Skills:
                    - [List each preferred soft skill]

                    Brief Explanation:
                    [Explain why these skills are categorized as must-have vs good-to-have]"""
                }
                
                # Include the entire conversation history for context
                analysis_conversation = st.session_state.messages + [final_prompt]
                
                final_analysis = get_claude_response(analysis_conversation)
                if final_analysis:
                    st.session_state.final_analysis = final_analysis
                    st.session_state.analysis_complete = True
                    st.rerun()
            
            # Get Claude's next response
            response = get_claude_response(st.session_state.messages)
            
            if response:
                st.session_state.messages.append({"role": "assistant", "content": response})
                display_chat_message("assistant", response)
    
    # Display final analysis
    elif st.session_state.final_analysis:
        must_tech, must_soft, good_tech, good_soft, explanation = parse_skills(st.session_state.final_analysis)
        
        st.header("Analysis Results")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Must Have Technical Skills")
            for skill in must_tech:
                st.write(f"• {skill}")
                
            st.subheader("Must Have Soft Skills")
            for skill in must_soft:
                st.write(f"• {skill}")
        
        with col2:
            st.subheader("Good to Have Technical Skills")
            for skill in good_tech:
                st.write(f"• {skill}")
                
            st.subheader("Good to Have Soft Skills")
            for skill in good_soft:
                st.write(f"• {skill}")
        
        st.subheader("Analysis Explanation")
        st.write(explanation)
        
        if st.button("Start New Analysis"):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": """Hi! I'm here to help analyze job requirements. Let's have a conversation about the position you're looking to analyze. Could you start by telling me what position you're hiring for?"""
                }
            ]
            st.session_state.analysis_complete = False
            st.session_state.final_analysis = None
            st.rerun()

if __name__ == "__main__":
    main()