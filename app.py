import streamlit as st
import os
from anthropic import Anthropic

# Page configuration
st.set_page_config(
    page_title="JD Skills Analyzer",
    page_icon="📝",
    layout="wide"
)

def get_api_key():
    """Get API key from Streamlit secrets"""
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except KeyError:
        st.error("ANTHROPIC_API_KEY not found in secrets.")
        st.stop()

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
        
        return response.content
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def parse_skills(text):
    """Parse the response text to extract skills"""
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