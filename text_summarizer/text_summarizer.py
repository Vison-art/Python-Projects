import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from sklearn.feature_extraction.text import TfidfVectorizer
import requests
from bs4 import BeautifulSoup
import re
import string
import PyPDF2
import io
from datetime import datetime
import webbrowser
import os

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('punkt_tab')
nltk.download('omw-1.4')  # Open Multilingual Wordnet
nltk.download('wordnet')

class TextSummarizer:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        
    def fetch_text_from_url(self, url):
        """Fetch text content from the given URL"""
        try:
            # First try to get the PDF URL
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find PDF link
            pdf_link = soup.find('a', href=lambda x: x and x.endswith('.pdf'))
            if pdf_link:
                pdf_url = pdf_link['href']
                if not pdf_url.startswith('http'):
                    pdf_url = 'https://aclanthology.org' + pdf_url
                
                print(f"Found PDF URL: {pdf_url}")
                pdf_response = requests.get(pdf_url)
                if pdf_response.headers.get('content-type', '').lower().startswith('application/pdf'):
                    return self.extract_text_from_pdf(pdf_response.content)
            
            # If no PDF found, try to get the abstract
            abstract_div = soup.find('div', class_='abstract')
            if abstract_div:
                text = abstract_div.get_text()
                # Clean up text
                text = re.sub(r'\s+', ' ', text)
                text = text.strip()
                return text
            
            # If no abstract found, try to get the main content
            content = soup.find('div', class_='content')
            if content:
                # Remove unwanted elements
                for element in content.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                text = content.get_text()
                # Clean up text
                text = re.sub(r'\s+', ' ', text)
                text = text.strip()
                return text
            
            print("Could not find content")
            return None
                
        except Exception as e:
            print(f"Error fetching URL: {e}")
            return None

    def extract_text_from_pdf(self, pdf_content):
        """Extract text from PDF content"""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            # Clean up text
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return None

    def preprocess_text(self, text):
        """Preprocess the text by removing special characters and converting to lowercase"""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

    def get_title_based_summary(self, text, num_sentences=5):
        """Generate summary based on title similarity"""
        sentences = sent_tokenize(text)
        if not sentences:
            return ""
        
        # Use first sentence as title
        title = sentences[0]
        title_words = set(word_tokenize(title.lower()))
        
        # Calculate similarity scores
        sentence_scores = []
        for sentence in sentences[1:]:  # Skip the title sentence
            sentence_words = set(word_tokenize(sentence.lower()))
            similarity = len(title_words.intersection(sentence_words)) / len(title_words)
            sentence_scores.append((sentence, similarity))
        
        # Sort sentences by similarity score
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top sentences
        summary = [title] + [s[0] for s in sentence_scores[:num_sentences-1]]
        return ' '.join(summary)

    def get_keyword_based_summary(self, text, num_sentences=5):
        """Generate summary based on keyword frequency"""
        sentences = sent_tokenize(text)
        if not sentences:
            return ""
        
        # Get word frequencies
        words = word_tokenize(text.lower())
        words = [word for word in words if word not in self.stop_words and word.isalnum()]
        freq_dist = FreqDist(words)
        
        # Calculate sentence scores based on keyword frequency
        sentence_scores = []
        for sentence in sentences:
            score = 0
            words = word_tokenize(sentence.lower())
            for word in words:
                if word in freq_dist:
                    score += freq_dist[word]
            sentence_scores.append((sentence, score))
        
        # Sort sentences by score
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top sentences
        summary = [s[0] for s in sentence_scores[:num_sentences]]
        return ' '.join(summary)

    def get_cueword_based_summary(self, text, num_sentences=5):
        """Generate summary based on cue words"""
        cue_words = {
            'important': ['significant', 'crucial', 'essential', 'key', 'major', 'critical'],
            'conclusion': ['therefore', 'thus', 'consequently', 'finally', 'in conclusion'],
            'result': ['resulted', 'caused', 'led to', 'produced', 'generated']
        }
        
        sentences = sent_tokenize(text)
        if not sentences:
            return ""
        
        # Calculate sentence scores based on cue words
        sentence_scores = []
        for sentence in sentences:
            score = 0
            words = word_tokenize(sentence.lower())
            for category in cue_words.values():
                for cue_word in category:
                    if cue_word in words:
                        score += 1
            sentence_scores.append((sentence, score))
        
        # Sort sentences by score
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top sentences
        summary = [s[0] for s in sentence_scores[:num_sentences]]
        return ' '.join(summary)

    def get_tfidf_based_summary(self, text, num_sentences=5):
        """Generate summary based on TF-IDF scores"""
        sentences = sent_tokenize(text)
        if not sentences:
            return ""
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(stop_words='english')
        try:
            tfidf_matrix = vectorizer.fit_transform(sentences)
        except:
            return " ".join(sentences[:num_sentences])
        
        # Calculate sentence scores based on TF-IDF values
        sentence_scores = []
        for i in range(len(sentences)):
            score = tfidf_matrix[i].sum()
            sentence_scores.append((sentences[i], score))
        
        # Sort sentences by score
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get top sentences
        summary = [s[0] for s in sentence_scores[:num_sentences]]
        return ' '.join(summary)

    def format_summary(self, summary):
        """Format the summary to be more readable"""
        # Split into sentences
        sentences = sent_tokenize(summary)
        
        # Format each sentence
        formatted_sentences = []
        for i, sentence in enumerate(sentences, 1):
            # Clean up the sentence
            sentence = sentence.strip()
            # Add sentence number
            formatted_sentences.append(f"{i}. {sentence}")
        
        # Join with newlines
        return "\n".join(formatted_sentences)

    def generate_html_report(self, text, title_summary, keyword_summary, cueword_summary, tfidf_summary, url):
        """Generate an HTML report with the summaries"""
        # Clean up the summaries for better readability
        title_summary = self.clean_text(title_summary)
        keyword_summary = self.clean_text(keyword_summary)
        cueword_summary = self.clean_text(cueword_summary)
        tfidf_summary = self.clean_text(tfidf_summary)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Text Summarization Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 30px;
                }}
                .summary-section {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }}
                .sentence {{
                    margin: 10px 0;
                    padding: 10px;
                    background-color: white;
                    border-left: 4px solid #3498db;
                }}
                .metadata {{
                    color: #7f8c8d;
                    font-size: 0.9em;
                    margin-bottom: 20px;
                }}
                .timestamp {{
                    text-align: right;
                    color: #95a5a6;
                    font-size: 0.8em;
                }}
                .method-description {{
                    color: #7f8c8d;
                    font-style: italic;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Text Summarization Report</h1>
                <div class="metadata">
                    <p>Source URL: <a href="{url}" target="_blank">{url}</a></p>
                    <p>Original Text Length: {len(text)} characters</p>
                </div>
                
                <h2>Title-based Summary</h2>
                <div class="method-description">
                    This summary is generated by comparing sentence similarity with the title.
                </div>
                <div class="summary-section">
                    {self.format_summary_html(title_summary)}
                </div>
                
                <h2>Keyword-based Summary</h2>
                <div class="method-description">
                    This summary is generated based on the frequency of important keywords.
                </div>
                <div class="summary-section">
                    {self.format_summary_html(keyword_summary)}
                </div>
                
                <h2>Cueword-based Summary</h2>
                <div class="method-description">
                    This summary is generated based on the presence of important cue words.
                </div>
                <div class="summary-section">
                    {self.format_summary_html(cueword_summary)}
                </div>
                
                <h2>TF-IDF-based Summary</h2>
                <div class="method-description">
                    This summary is generated using TF-IDF (Term Frequency-Inverse Document Frequency) scoring.
                </div>
                <div class="summary-section">
                    {self.format_summary_html(tfidf_summary)}
                </div>
                
                <div class="timestamp">
                    Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'summary_report_{timestamp}.html'
        
        # Write to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename
    
    def format_summary_html(self, summary):
        """Format summary for HTML display"""
        if not summary:
            return "<p>No summary available</p>"
            
        sentences = sent_tokenize(summary)
        formatted_sentences = []
        
        for i, sentence in enumerate(sentences, 1):
            formatted_sentences.append(f'<div class="sentence">{i}. {sentence.strip()}</div>')
        
        return '\n'.join(formatted_sentences)

    def clean_text(self, text):
        """Clean up text for better readability"""
        if not text:
            return ""
            
        # Remove special characters and normalize spaces
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common PDF extraction issues
        text = text.replace('~', '')  # Remove tildes
        text = re.sub(r'\d+$', '', text)  # Remove page numbers at the end
        text = re.sub(r'^\d+\s*', '', text)  # Remove page numbers at the start
        
        # Clean up email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Clean up multiple spaces and normalize punctuation
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*([.,!?])\s*', r'\1 ', text)
        
        return text.strip()

def main():
    try:
        # Initialize summarizer
        summarizer = TextSummarizer()
        
        # URL of the paper
        url = "https://aclanthology.org/X98-1024"
        
        print("Fetching text from URL...")
        # Fetch text from URL
        text = summarizer.fetch_text_from_url(url)
        if not text:
            print("Failed to fetch text from URL")
            print("Please check if:")
            print("1. The URL is accessible")
            print("2. The URL contains text content")
            print("3. You have internet connection")
            return
            
        print(f"Successfully fetched text. Length: {len(text)} characters")
        
        if len(text) < 100:
            print("Warning: The fetched text is very short. The summarization might not be meaningful.")
            return
        
        # Preprocess text
        print("\nPreprocessing text...")
        processed_text = summarizer.preprocess_text(text)
        
        # Generate summaries using different methods
        print("\nGenerating summaries...")
        
        print("\nTitle-based Summary:")
        title_summary = summarizer.get_title_based_summary(text)
        print(summarizer.format_summary(title_summary) if title_summary else "No title-based summary available")
        
        print("\nKeyword-based Summary:")
        keyword_summary = summarizer.get_keyword_based_summary(text)
        print(summarizer.format_summary(keyword_summary) if keyword_summary else "No keyword-based summary available")
        
        print("\nCueword-based Summary:")
        cueword_summary = summarizer.get_cueword_based_summary(text)
        print(summarizer.format_summary(cueword_summary) if cueword_summary else "No cueword-based summary available")
        
        print("\nTF-IDF-based Summary:")
        tfidf_summary = summarizer.get_tfidf_based_summary(text)
        print(summarizer.format_summary(tfidf_summary) if tfidf_summary else "No TF-IDF-based summary available")
        
        # Generate HTML report
        print("\nGenerating HTML report...")
        report_file = summarizer.generate_html_report(text, title_summary, keyword_summary, cueword_summary, tfidf_summary, url)
        
        # Get the absolute path of the report file
        report_path = os.path.abspath(report_file)
        
        print(f"\nHTML report generated: {report_file}")
        print(f"Full path: {report_path}")
        print(f"Opening report in your default web browser...")
        
        # Open the HTML file in the default browser
        try:
            webbrowser.open('file://' + report_path)
            print("Report opened successfully!")
        except Exception as e:
            print(f"Could not automatically open the report: {e}")
            print("You can manually open the file at:", report_path)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please make sure you have all required NLTK data installed and the URL is accessible.")

if __name__ == "__main__":
    main()