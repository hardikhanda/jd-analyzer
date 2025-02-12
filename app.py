import streamlit as st
import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="JD Skills Analyzer",
    page_icon="📝",
    layout="wide"
)

def get_api_key():
    """
    Get API key from either .env file (local) or Streamlit secrets (cloud)
    """
    # First try loading from .env file (local development)
    load_dotenv()
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    # If not found in .env, try Streamlit secrets (cloud deployment)
    if not api_key:
        try:
            api_key = st.secrets.general.ANTHROPIC_API_KEY
        except:
            try:
                api_key = st.secrets["ANTHROPIC_API_KEY"]
            except:
                st.error("""
                API key not found. Please either:
                1. Add ANTHROPIC_API_KEY to your .env file (local development)
                2. Add it to Streamlit secrets (cloud deployment)
                """)
                st.stop()
    
    return api_key

def extract_text_from_response(response):
    """Extract text from the response object"""
    if isinstance(response, list):
        for item in response:
            if hasattr(item, 'text'):
                return item.text
            str_item = str(item)
            if "text='" in str_item:
                start = str_item.find("text='") + 6
                end = str_item.find("', type='text'")
                if start > 5 and end > start:
                    return str_item[start:end]
    return str(response)

def analyze_with_claude(jd_text):
    """Analyze JD using Claude"""
    try:
        client = Anthropic(api_key=get_api_key())
        
        prompt = f"""
        Analyze the following job description and categorize ALL skills into four categories:
        1. Must Have Technical Skills
        2. Must Have Soft Skills
        3. Good to Have Technical Skills
        4. Good to Have Soft Skills

        Job Description:
        {jd_text}

        Format your response exactly as follows:
        Must Have Technical Skills:
        - [List technical skills that are required]

        Must Have Soft Skills:
        - [List soft skills that are required]

        Good to Have Technical Skills:
        - [List technical skills that are preferred]

        Good to Have Soft Skills:
        - [List soft skills that are preferred]

        Brief Explanation:
        [Explain your categorization logic]
        """
        
        response = client.messages.create(
            model="claude-2",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        if hasattr(response, 'content'):
            return response.content
        return extract_text_from_response(response)
            
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def parse_skills(text):
    """Parse the response text to extract skills"""
    if isinstance(text, list):
        text = extract_text_from_response(text)
    
    text = str(text)
    
    must_have_technical = []
    must_have_soft = []
    good_have_technical = []
    good_have_soft = []
    explanation = ""
    
    current_section = None
    
    for line in text.split('\n'):
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

def main():
    st.title("JD Skills Analyzer 📝")
    
    # Display environment info
    env_type = "Local" if os.getenv('ANTHROPIC_API_KEY') else "Cloud"
    st.sidebar.info(f"Running in {env_type} environment")
    
    st.markdown("""
    ### Analyze job descriptions and extract required skills
    Paste your job description below and click 'Analyze'.
    """)
    
    jd_text = st.text_area("Paste the Job Description here:", height=300)
    
    if st.button("Analyze JD"):
        if jd_text:
            with st.spinner('Analyzing job description...'):
                try:
                    analysis_response = analyze_with_claude(jd_text)
                    
                    if analysis_response:
                        must_tech, must_soft, good_tech, good_soft, explanation = parse_skills(analysis_response)
                        
                        st.header("Must Have Skills")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Technical Skills")
                            if must_tech:
                                for skill in must_tech:
                                    st.write(f"• {skill}")
                            else:
                                st.write("No must-have technical skills identified")
                        
                        with col2:
                            st.subheader("Soft Skills")
                            if must_soft:
                                for skill in must_soft:
                                    st.write(f"• {skill}")
                            else:
                                st.write("No must-have soft skills identified")
                        
                        st.header("Good to Have Skills")
                        col3, col4 = st.columns(2)
                        
                        with col3:
                            st.subheader("Technical Skills")
                            if good_tech:
                                for skill in good_tech:
                                    st.write(f"• {skill}")
                            else:
                                st.write("No good-to-have technical skills identified")
                        
                        with col4:
                            st.subheader("Soft Skills")
                            if good_soft:
                                for skill in good_soft:
                                    st.write(f"• {skill}")
                            else:
                                st.write("No good-to-have soft skills identified")
                        
                        if explanation:
                            st.header("Analysis Explanation")
                            st.write(explanation)
                            
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please paste a job description to analyze.")

if __name__ == "__main__":
    main()