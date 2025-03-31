from flask import Flask, request, render_template, jsonify, redirect, flash, session, url_for
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
from pytube import YouTube
import os
import requests
from flask import Flask, request, render_template
from pytube import YouTube
import moviepy.editor as mp
import assemblyai as aai
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import yt_dlp
from twilio.rest import Client
import easygui
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from moviepy.editor import AudioFileClip


ASSEMBLYAI_API_KEY = "80095427ee394316aea00ead3b58c51c"

aai.settings.api_key = ASSEMBLYAI_API_KEY

app = Flask(__name__, static_url_path='/static')
app.secret_key = '1234567890qwertyuiopasdfghjklzxcvbnm'
users = {}
sentiment_history = []  # Initialize sentiment analysis history

# Download NLTK resources (if not already downloaded)
nltk.download('vader_lexicon')

# Initialize the NLTK Sentiment Intensity Analyzer
sia = SentimentIntensityAnalyzer()

# Create a directory for uploaded files
upload_dir = 'uploads'
os.makedirs(upload_dir, exist_ok=True)

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/mydatabase"
mongo = PyMongo(app)

# Collections
users_collection = mongo.db.users
sentiment_collection = mongo.db.sentiments

def download_and_convert_to_mp3(youtube_url):
    try:
        print(f"Downloading audio from: {youtube_url}")
        
        # Define output filename
        mp4_file_path = "temp_audio.mp4"
        mp3_file_path = "temp_audio.mp3"

        # yt-dlp options to download audio only
        ydl_opts = {
            'format': 'bestaudio/best',
            'ffmpeg_location': 'C:/ffmpeg/bin',  # Change this to your actual path
            'outtmpl': mp4_file_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        # Download audio using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # Convert to MP3 (if yt-dlp didn't do it already)
        if not os.path.exists(mp3_file_path):
            audio_clip = AudioFileClip(mp4_file_path)
            audio_clip.write_audiofile(mp3_file_path)
            audio_clip.close()
            os.remove(mp4_file_path)  # Cleanup MP4 file

        print(f"MP3 file created at: {mp3_file_path}")
        return mp3_file_path

    except Exception as e:
        print(f"Error downloading YouTube audio: {e}")
        return None

def p_perform(text):
    sentiment_scores = sia.polarity_scores(text)
    sentiment = "Neutral"
    if sentiment_scores["compound"] > 0.05:
        sentiment = "Positive"
    elif sentiment_scores["compound"] < -0.05:
        sentiment = "Negative"
    return sentiment, sentiment_scores

def calculate_tonality_percentages(sentiment_scores):
    total = sum(sentiment_scores.values())
    positive_percentage = (sentiment_scores["pos"] / total) * 100
    neutral_percentage = (sentiment_scores["neu"] / total) * 100
    negative_percentage = (sentiment_scores["neg"] / total) * 100
    return positive_percentage, neutral_percentage, negative_percentage


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

        # Join and clean up the extracted text
        text_data = ' '.join(results)
        text_data = text_data.replace('\n', ' ').replace('\r', '')  # Remove line breaks and carriage returns
        text_data = ' '.join(text_data.split())  # Remove extra whitespace

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
def perform_sentiment_analysis(pdf_name, government_articles):
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    negative_sentences = []  # Add this list to store negative sentences

    for article in government_articles:
        sentiment_scores = sia.polarity_scores(article)
        compound_score = sentiment_scores['compound']

        if compound_score >= 0.05:
            positive_count += 1
        elif compound_score <= -0.05:
            negative_count += 1
            # Store the negative sentence
            negative_sentences.append(article)
        else:
            neutral_count += 1

    total_articles = len(government_articles)
    positive_percentage = (positive_count / total_articles) * 100
    negative_percentage = (negative_count / total_articles) * 100
    neutral_percentage = (neutral_count / total_articles) * 100

    formatted_positive_percentage = "{:.2f}".format(positive_percentage)
    formatted_negative_percentage = "{:.2f}".format(negative_percentage)
    formatted_neutral_percentage = "{:.2f}".format(neutral_percentage)

    sentiment_result = {
        "pdf_name": pdf_name,
        "positive": formatted_positive_percentage,
        "negative": formatted_negative_percentage,
        "neutral": formatted_neutral_percentage,
        "negative_sentences": negative_sentences  # Include negative sentences in the result
    }

    sentiment_history.append(sentiment_result)

    return sentiment_result


# Routes for rendering templates
@app.route('/')
def home():
    return render_template('main.html')

@app.route('/dashboard')

def dashboard():
    utube_sentiment_history = []
    return render_template('dashboardContent.html', sentiment_history=sentiment_history, utube_sentiment_history=utube_sentiment_history)


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username')  # Get username
        password = request.form.get('password')  # Get password

        # Check if user exists
        user = users_collection.find_one({"username": username})
        if user and check_password_hash(user["password"], password):
            session["username"] = username  # Store username in session
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials."

    return render_template('signin.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if user exists
        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            return "Username already exists. Choose a different one."

        # Password confirmation
        if password != confirm_password:
            return "Passwords do not match."

        # Hash the password before storing
        hashed_password = generate_password_hash(password)

        # Insert new user into MongoDB
        users_collection.insert_one({
            "username": username,
            "password": hashed_password
        })

        return redirect(url_for('signin'))  # Redirect to login page

    return render_template('signup.html')

@app.route('/today')
def today_news():
    return render_template('today.html')

@app.route('/epaper')
def epaper_news():
    return render_template('epaper.html')

# @app.route('/Utube')
# def youtube_news():
#     return render_template('Utube.html')

# Route to display the Utube.html page
@app.route('/Utube', methods=['GET'])
def display_utube():
    return render_template('Utube.html')



@app.route("/analyze_youtube", methods=["GET", "POST"])
def index():
    transcript = None
    sentiment = None
    sentiment_scores = None
    positive_percentage = None
    neutral_percentage = None
    negative_percentage = None
    negative_timestamps_minutes = []  # Initialize list for negative timestamps
    negative_sentences = [] 
    video_title = None 
    utube_sentiment_history = [] # Initialize list for negative sentences

    if request.method == "POST":
        youtube_url = request.form["youtube_url"]
        if youtube_url:
            mp3_file_path = download_and_convert_to_mp3(youtube_url)

            yt = YouTube(youtube_url)
            video_title = yt.title

            # Send the MP3 to AssemblyAI for transcription
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(mp3_file_path)
            os.remove(mp3_file_path)  # Clean up - delete the temporary MP3 file

            # Perform sentiment analysis on the transcript
            sentiment, sentiment_scores = p_perform(transcript.text)

            # Calculate tonality percentages
            positive_percentage, neutral_percentage, negative_percentage = calculate_tonality_percentages(sentiment_scores)

            # Split the transcript into sentences for analysis
            sentences = transcript.text.split('. ')

            # Iterate through sentences and check for negative sentiment
            for i, sentence in enumerate(sentences):
                # Perform sentiment analysis on each sentence
                sentence_sentiment, _ = p_perform(sentence)
                if sentence_sentiment == "Negative":
                    seconds = i * 4  # Assuming each sentence takes 4 seconds
                    negative_timestamps_minutes.append(seconds)
                    negative_sentences.append(sentence)  # Add negative sentence to the list

    formatted_positive_percentage = "{:.2f}".format(positive_percentage)
    formatted_negative_percentage = "{:.2f}".format(negative_percentage)
    formatted_neutral_percentage = "{:.2f}".format(neutral_percentage)

    utube_sentiment_result = {
    "video_title": video_title,
    "positive_percentage": formatted_positive_percentage,
    "negative_percentage": formatted_negative_percentage,
    "neutral_percentage": formatted_neutral_percentage,
    "negative_timestamps_minutes": negative_timestamps_minutes,
    "negative_sentences": negative_sentences
}
    utube_sentiment_history.append(utube_sentiment_result)



# Convert formatted_negative_percentage to a float for comparison
    formatted_negative_percentage_float = float(formatted_negative_percentage)

    if formatted_negative_percentage_float > 1.0:
        account_sid = 'ACdefa7df4e5786818bb3a419b514cc9d8'
        auth_token = '4150b604c118d5c19ffb0ecf77886c78'
        client = Client(account_sid, auth_token)
        message_body = f'\n Title: {video_title}, \n Negative Percentage: {formatted_negative_percentage}%, \n URL: {youtube_url}'
        message = client.messages.create(
            from_='+12622879688',
            body=message_body,
            to='+919360364123'
        )
        print(message.sid)

        easygui.msgbox("Notification has been sent succesfully")

    return render_template(
        'Utube.html',
        video_title=video_title ,
        positive_percentage=formatted_positive_percentage,
        negative_percentage=formatted_negative_percentage,
        neutral_percentage=formatted_neutral_percentage,
        negative_timestamps_minutes=negative_timestamps_minutes,
        negative_sentences=negative_sentences,
        utube_sentiment_history=utube_sentiment_history
       
    )

@app.route('/upload_and_analyze', methods=['POST'])
def upload_and_analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files['file']

    if file.filename.endswith('.pdf'):
        pdf_filename = os.path.join(upload_dir, secure_filename(file.filename))
        file.save(pdf_filename)

        text = extract_text_from_scanned_pdf(pdf_filename)

        if text:
            government_articles = extract_news_related_to_government(text)

            if government_articles:
                pdf_name = secure_filename(file.filename)
                sentiment_result = perform_sentiment_analysis(pdf_name, government_articles)

                return render_template("epaper.html", **sentiment_result)  # Render the result template with sentiment analysis results

    return jsonify({"error": "No text or articles found"})

# Route to view sentiment analysis results for a specific PDF
@app.route('/dashboard')
def view_sentiment():
    pdf_name = request.args.get('pdf_name')
    youtube_video_title = request.args.get('youtube_video_title')

    sentiment_result = None
    utube_sentiment_result = None

    # Search for the PDF sentiment result
    for result in sentiment_history:
        if result["pdf_name"] == pdf_name:
            sentiment_result = result
            break

    # Search for the YouTube sentiment result
    for result in utube_sentiment_result:
        if result["video_title"] == youtube_video_title:
            utube_sentiment_result = result
            break

    return render_template(
        'dashboardContent.html',
        sentiment_result=sentiment_result,
        utube_sentiment_result=utube_sentiment_result
    )

if __name__ == '__main__':
    app.run(debug=True)