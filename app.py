import streamlit as st
import os
st.set_page_config(
    page_title="JD Skills Analyzer",
    page_icon="📝",
    layout="wide"
)
from anthropic import Anthropic

def get_api_key():
    """Get API key from Streamlit secrets"""
    if 'ANTHROPIC_API_KEY' not in st.secrets:
        st.error('ANTHROPIC_API_KEY not found in secrets.')
        st.stop()
    return st.secrets['ANTHROPIC_API_KEY']

def analyze_with_claude(jd_text):
    """
    Use Claude to analyze the JD with separate technical and soft skills
    """
    try:
        client = Anthropic(api_key=get_api_key())
        
        prompt = f"""
        Analyze the following job description and categorize ALL skills into four categories:
        1. Must Have Technical Skills
        2. Must Have Soft Skills
        3. Good to Have Technical Skills
        4. Good to Have Soft Skills

        Consider:
        - Technical skills include programming languages, tools, frameworks, methodologies, and technical knowledge
        - Soft skills include interpersonal abilities, communication, leadership, and personal qualities

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

def extract_text_from_response(response):
    """
    Extract text content from the API response
    """
    if isinstance(response, list) and response:
        first_item = response[0]
        if hasattr(first_item, 'text'):
            return first_item.text
        text_block_str = str(first_item)
        if "text='" in text_block_str:
            start = text_block_str.find("text='") + 6
            end = text_block_str.find("', type='text'")
            if start > 5 and end > start:
                return text_block_str[start:end]
    return str(response)

def parse_skills(text):
    """
    Parse the response text to extract skills and explanation
    """
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
    st.title("Advanced JD Skills Analyzer")
    
    st.write("""
    Paste your job description below for a detailed analysis that separates technical and soft skills 
    in both required and preferred categories.
    """)
    
    jd_text = st.text_area("Paste the Job Description here:", height=300)
    
    if st.button("Analyze JD"):
        if jd_text:
            with st.spinner('Analyzing job description...'):
                try:
                    # Get analysis from Claude
                    analysis_response = analyze_with_claude(jd_text)
                    
                    if analysis_response:
                        # Extract text from response
                        cleaned_response = extract_text_from_response(analysis_response)
                        
                        # Parse the skills and explanation
                        must_tech, must_soft, good_tech, good_soft, explanation = parse_skills(cleaned_response)
                        
                        # Display Must Have Skills
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
                        
                        # Display Good to Have Skills
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
                        
                        # Display explanation
                        if explanation:
                            st.header("Analysis Explanation")
                            st.write(explanation)
                            
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
        else:
            st.warning("Please paste a job description to analyze.")

if __name__ == "__main__":
    main()