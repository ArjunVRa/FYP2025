from flask import Flask, request, render_template, jsonify, redirect,flash ,session,url_for
import pytesseract
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import concurrent.futures
import os
import spacy
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from werkzeug.utils import secure_filename
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube  # Add this import
import pymongo 

app = Flask(__name__, static_url_path='/static')
app.secret_key='1234567890qwertyuiopasdfghjklzxcvbnm'

# Establish a connection to MongoDB (default localhost and port)
client = pymongo.MongoClient("mongodb://127.0.0.1:27017/")

# Download NLTK resources (if not already downloaded)
nltk.download('vader_lexicon')

# Initialize the NLTK Sentiment Intensity Analyzer
sia = SentimentIntensityAnalyzer()

# Create or select a database (replace 'newspaper' with your database name)
db = client["SIH2023"]

# Create or select a collection (replace 'mycollection' with your collection name)
epaper_collection = db["Epaper_data"]
youtube_collection = db["YouTube_data"]
users_collection = db['Users_data']
# Function to extract text from a page
def extract_text_from_page(page):
    try:
        # Export the page as an image
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Convert PIL image to OpenCV format (BGR)
        img_cv2 = np.array(img)
        img_cv2 = cv2.cvtColor(img_cv2, cv2.COLOR_RGB2BGR)

        # Perform OCR on the image
        text = pytesseract.image_to_string(img_cv2)
        return text
    except Exception as e:
        return f"An error occurred: {e}"

# Function to extract text from a scanned PDF
def extract_text_from_scanned_pdf(pdf_path):
    text_data = ''
    try:
        pdf_document = fitz.open(pdf_path)
        pages = [pdf_document.load_page(page_number) for page_number in range(pdf_document.page_count)]

        # Process pages concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(extract_text_from_page, pages))

        text_data = '\n'.join(results)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        pdf_document.close()

    return text_data

# Function to extract government-related news articles
def extract_news_related_to_government(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    government_keywords = ["government", "politics", "public policy"]

    government_articles = []
    current_article = ""

    for sentence in doc.sents:
        if any(keyword in sentence.text.lower() for keyword in government_keywords):
            current_article = sentence.text
        elif current_article:
            current_article += "\n" + sentence.text

        if current_article and (sentence.text.endswith(".") or sentence.text.endswith("?")):
            government_articles.append(current_article)
            current_article = ""

    return government_articles

# Function to perform sentiment analysis on government-related news articles
def perform_sentiment_analysis(government_articles):
    positive_count = 0
    negative_count = 0
    neutral_count = 0

    for article in government_articles:
        sentiment_scores = sia.polarity_scores(article)
        compound_score = sentiment_scores['compound']

        if compound_score >= 0.05:
            positive_count += 1
        elif compound_score <= -0.05:
            negative_count += 1
        else:
            neutral_count += 1

    total_articles = len(government_articles)
    positive_percentage = (positive_count / total_articles) * 100
    negative_percentage = (negative_count / total_articles) * 100
    neutral_percentage = (neutral_count / total_articles) * 100

    return {
        "positive": positive_percentage,
        "negative": negative_percentage,
        "neutral": neutral_percentage,
    }

# Routes for rendering templates
@app.route('/')
def home():
    return render_template('main.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    return render_template('auth.html')

@app.route('/dashboardContent.html')
def dashboard():
    return render_template('dashboardContent.html')


@app.route('/today.html')
def today_news():
    return render_template('today.html')

@app.route('/epaper.html')
def epaper_news():
    return render_template('epaper.html')

@app.route('/Utube.html')
def youtube_news():
    return render_template('Utube.html')

# Route to display the Utube.html page
@app.route('/Utube.html', methods=['GET'])
def display_utube():
    return render_template('Utube.html')

# Route to handle the YouTube URL submission and display sentiment analysis results
@app.route('/analyze_youtube', methods=['POST'])
def analyze_youtube():
    video_url = request.form.get('youtube_url')

    # Extract video ID from the URL
    video_id = video_url.split('v=')[1].split('&')[0]

    # Fetch subtitles
    subtitles = YouTubeTranscriptApi.get_transcript(video_id)

    # Fetch video title using pytube
    yt = YouTube(video_url)
    video_title = yt.title

    # Perform sentiment analysis as you did before
    sia = SentimentIntensityAnalyzer()
    positive_count = 0
    negative_count = 0
    neutral_count = 0

    # Assuming you have 'subtitles' as a list of subtitle texts
    for sentence in subtitles:
        sentiment_scores = sia.polarity_scores(sentence['text'])

        # Classify sentiment
        if sentiment_scores['compound'] >= 0.05:
            positive_count += 1
        elif sentiment_scores['compound'] <= -0.05:
            negative_count += 1
        else:
            neutral_count += 1

    total_sentences = len(subtitles)
    positive_percentage = (positive_count / total_sentences) * 100
    negative_percentage = (negative_count / total_sentences) * 100
    neutral_percentage = (neutral_count / total_sentences) * 100
    data_Utube = {
                    "Title of the Video": video_title,
                    "positive_sentiment": positive_percentage,
                    "negative_sentiment": negative_percentage,
                    "neutral_sentiment": neutral_percentage
                }
    youtube_collection.insert_one(data_Utube)
    
    # Pass the sentiment analysis results to the 'Utube.html' template
    return render_template('Utube.html', video_title=video_title, positive_percentage=positive_percentage, negative_percentage=negative_percentage, neutral_percentage=neutral_percentage)

# Combined route for processing uploaded PDF files and displaying results
@app.route('/upload_and_analyze', methods=['POST'])
def upload_and_analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files['file']

    if file.filename.endswith('.pdf'):
        upload_dir = 'uploads'
        os.makedirs(upload_dir, exist_ok=True)
        pdf_filename = os.path.join(upload_dir, secure_filename(file.filename))
        file.save(pdf_filename)

        text = extract_text_from_scanned_pdf(pdf_filename)

        if text:
            government_articles = extract_news_related_to_government(text)

            if government_articles:
                sentiment_result = perform_sentiment_analysis(government_articles)

                # Store the filename and sentiment analysis results in MongoDB
                data = {
                    "pdf_name": file.filename,
                    "positive_sentiment": sentiment_result["positive"],
                    "negative_sentiment": sentiment_result["negative"],
                    "neutral_sentiment": sentiment_result["neutral"]
                }
                epaper_collection.insert_one(data)
                
              
                

                return render_template("epaper.html", **sentiment_result)  # Render the result template with sentiment analysis results

    return jsonify({"error": "No text or articles found"})

# Closing MongoDB client connection


if __name__ == '__main__':
    app.run(debug=True)