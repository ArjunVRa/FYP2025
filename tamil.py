import fitz
from textblob import TextBlob

# Path to your Tamil PDF file
pdf_path = './tamil.pdf'

try:
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)

    # Initialize empty strings to store the extracted text
    extracted_text = ""
    positive_text = ""
    negative_text = ""
    neutral_text = ""

    # Loop through each page and extract text
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        text = page.get_text("text")
        extracted_text += f"Page {page_num + 1}:\n{text}\n"

    # Perform sentiment analysis on the extracted text
    blob = TextBlob(extracted_text)

    # Initialize counters for each sentiment tonality
    positive_count = 0
    negative_count = 0
    neutral_count = 0

    # Loop through each word and categorize it as positive, negative, or neutral
    for word in blob.words:
        word_polarity = TextBlob(word).sentiment.polarity
        if word_polarity > 0:
            positive_text += word + " "
            positive_count += 1
        elif word_polarity < 0:
            negative_text += word + " "
            negative_count += 1
        else:
            neutral_text += word + " "
            neutral_count += 1

    # Calculate the percentage of each sentiment tonality
    total_words = len(blob.words)
    positive_percentage = (positive_count / total_words) * 100
    negative_percentage = (negative_count / total_words) * 100
    neutral_percentage = (neutral_count / total_words) * 100

    # Display the percentages of each tonality
    print("\nPositive Percentage:", positive_percentage)
    print("Negative Percentage:", negative_percentage)
    print("Neutral Percentage:", neutral_percentage)

    # Display the positive, negative, and neutral text
    print("\nPositive Text:")
    print(positive_text)
    print("\nNegative Text:")
    print(negative_text)
    print("\nNeutral Text:")
    print(neutral_text)

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    # Close the PDF file
    if 'pdf_document' in locals():
        pdf_document.close()
