import streamlit as st
import os
from anthropic import Anthropic
from dotenv import load_dotenv
import time

# Custom styling
def apply_custom_style():
    st.markdown('''
    <style>
        /* Dark theme base */
        .main {
            background-color: #0f1117;
            color: #e5e7eb;
        }
        
        [data-testid="stHeader"] {
            background-color: #0f1117;
        }
        
        /* Avatar styling */
        .avatar-assistant {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background-color: #2563eb;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 500;
            font-size: 14px;
        }
        
        .avatar-user {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background-color: #4b5563;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 500;
            font-size: 14px;
        }
        
        /* Message container */
        .stChatMessage {
            background-color: transparent;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding: 20px 8px;
            margin: 0;
        }
        
        /* Message content */
        .message-content {
            color: #e5e7eb;
            font-size: 15px;
            line-height: 1.6;
            margin-left: 44px;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #ffffff;
            font-weight: 600;
            letter-spacing: -0.02em;
        }
        
        /* Chat input */
        .stChatInputContainer {
            background-color: #1e1e2d !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            color: #ffffff !important;
        }
        
        .stChatInputContainer:focus-within {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 1px #2563eb !important;
        }
        
        /* Analysis results */
        .analysis-results {
            background-color: #1e1e2d;
            border-radius: 8px;
            padding: 24px;
            margin-top: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        /* Button styling */
        .stButton button {
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.2s ease;
        }
        
        .stButton button:hover {
            background-color: #1d4ed8;
            box-shadow: 0 2px 4px rgba(37,99,235,0.1);
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #1e1e2d;
            border-right: 1px solid rgba(255,255,255,0.1);
        }
        
        /* Code blocks */
        code {
            background-color: #1e1e2d;
            padding: 2px 6px;
            border-radius: 4px;
            color: #e5e7eb;
        }
    </style>
    ''', unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="JD Analyzer",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
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
            system_prompt = """You are an expert at analyzing technical job requirements. When providing the final analysis:
    1. Focus on concrete, specific technical skills only
    2. Clearly distinguish between must-have and good-to-have technical skills
    3. Use bullet points for each skill
    4. Provide a brief explanation of your categorization logic
    
    Use exactly this format:
    Must Have Technical Skills:
    - [specific technical skill]
    
    Good to Have Technical Skills:
    - [specific technical skill]
    
    Brief Explanation:
    [Your explanation focusing on why certain technical skills are must-have vs good-to-have]"""
        else:
            system_prompt = """You are conducting a focused conversation about technical skills only. When a role is mentioned, 
    guide the conversation by:
    
    1. Breaking down the role into key technical areas
    2. Providing options for the user to choose from
    3. Moving systematically through different technical categories
    4. Asking follow-up questions based on previous responses
    
    Example conversation flow for Frontend Developer:
    
    Bot: "Let's focus on frontend technologies. Which of these are important for the role? (You can select multiple)
    - React
    - Angular
    - Vue.js
    - Other (please specify)"
    
    [After user responds about frameworks]
    Bot: "Great! For [mentioned framework], which specific skills are needed? 
    - Component architecture
    - State management (Redux, Context API)
    - Routing
    - Custom hooks
    - All of the above"
    
    [After framework details]
    Bot: "Let's cover styling technologies. Which are required?
    - CSS
    - SASS/SCSS
    - Styled Components
    - Tailwind CSS
    - Other (please specify)"
    
    [After styling]
    Bot: "Moving to build tools and development, which are relevant?
    - Webpack
    - Vite
    - Version Control (Git)
    - Testing frameworks
    - CI/CD knowledge"
    
    After covering 3-4 major technical areas, ALWAYS ASK:
    "I think we've covered the main technical requirements. Would you like to proceed with the final analysis where I'll categorize these into must-have and good-to-have technical skills?"
    
    IMPORTANT:
    1. Stay focused on technical skills ONLY
    2. Provide clear options for each question
    3. Move systematically through different technical aspects
    4. After 3-4 exchanges about different technical areas, ALWAYS ask about proceeding to final analysis
    5. Keep the conversation efficient and structured
    6. DO NOT continue with more questions after 3-4 major technical areas are covered
    
    Remember: The goal is to gather enough information to create a meaningful technical skills analysis. After 3-4 major technical areas are discussed, always move towards concluding the conversation by offering to do the final analysis."""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=8000,
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
    """Parse the response text to extract technical skills"""
    text = str(text)
    
    must_have_technical = []
    good_have_technical = []
    explanation = ""
    
    current_section = None
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        
        if 'Must Have Technical Skills:' in line:
            current_section = 'must_technical'
            continue
        elif 'Good to Have Technical Skills:' in line:
            current_section = 'good_technical'
            continue
        elif 'Brief Explanation:' in line:
            current_section = 'explanation'
            continue
        
        if line.startswith('-') and line.strip('- '):
            skill = line.strip('- ').strip()
            if current_section == 'must_technical':
                must_have_technical.append(skill)
            elif current_section == 'good_technical':
                good_have_technical.append(skill)
        elif current_section == 'explanation' and line:
            explanation += line + " "
    
    return must_have_technical, good_have_technical, explanation.strip()

def display_chat_message(role, content):
    """Display a chat message with custom avatar and styling"""
    if role == "assistant":
        with st.chat_message(role):
            st.markdown(f'''
                <div class="avatar-assistant">A</div>
                <div class="message-content">{content}</div>
            ''', unsafe_allow_html=True)
    else:
        with st.chat_message(role):
            st.markdown(f'''
                <div class="avatar-user">U</div>
                <div class="message-content">{content}</div>
            ''', unsafe_allow_html=True)
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
        must_tech, good_tech, explanation = parse_skills(st.session_state.final_analysis)
        
        st.header("Analysis Results")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Must Have Technical Skills")
            for skill in must_tech:
                st.write(f"• {skill}")
        
        with col2:
            st.subheader("Good to Have Technical Skills")
            for skill in good_tech:
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