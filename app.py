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
            system_prompt = """You are conducting a focused technical conversation about specific technology domains. 
    
    IMPORTANT GUIDELINES:

    1. When asking about technologies, mention only 2-3 common ones as examples and let user elaborate:
    Example: "For database work with Node.js, are you using MongoDB, PostgreSQL, or something else?"
    NOT: "Which of these: MongoDB, PostgreSQL, MySQL, Redis, SQLite, etc."

    2. Pay careful attention to phrases that indicate good-to-have skills:
    - "would be a plus"
    - "nice to have"
    - "preferably"
    - "ideally"
    - "beneficial"
    - "additional advantage"
    - "not required but"
    Mark these for the final analysis as good-to-have skills.

    Example conversation flow for Node.js:

    Bot: "Let's start with databases. Are you using MongoDB, PostgreSQL, or something else?"

    User: "MongoDB, and Redis would be a plus for caching"
    (Note: Redis should be marked as good-to-have)

    Bot: "For API development, are you working with REST, GraphQL, or different approach?"

    User: "REST APIs, and GraphQL knowledge would be beneficial"
    (Note: GraphQL should be marked as good-to-have)

    Follow these rules:
    1. Break technology into 4-5 domains (like Database, API, Server, Deployment)
    2. For each domain, mention 2-3 examples maximum
    3. Ask follow-up questions about implementation and specific features
    4. Maintain conversation for 7-8 messages
    5. Pay attention to language indicating preferred vs required skills
    6. After covering all domains, ask about proceeding to final analysis

    Remember:
    - Keep questions open-ended
    - Let user elaborate beyond the examples
    - Track which skills are mentioned as preferences vs requirements
    - Maintain focus on one domain at a time
    - Aim for technical depth in each domain"""
        
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
                "content": """Hi! I'm here to help analyze job requirements. Let's have a conversation about the position you're looking to analyze. Could you start by telling me what technology you're hiring for?"""
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