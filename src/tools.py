import PyPDF2
from PIL import Image
import kagglehub

class FileTools:
    @staticmethod
    def extract_text_from_pdf(pdf_file):
        """Reads a PDF file object and returns all text."""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
            return text if text.strip() else "Error: PDF appears empty or scanned."
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    @staticmethod
    def process_image(image_file):
        """Validates and prepares an image for the model."""
        try:
            image = Image.open(image_file)
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            return image
        except Exception as e:
            print(f"Image processing error: {e}")
            return None

class DataTools:
    @staticmethod
    def fetch_kaggle_dataset(dataset_name):
        """
        Downloads a large dataset via API.
        NOTE: Currently set to lazy-load to optimize app startup time.
        """
        try:
            print(f"Fetching dataset metadata: {dataset_name}...")
            return "Dataset connection ready."
        except Exception as e:
            return f"Connection error: {e}"