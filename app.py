from flask import Flask, render_template, request, jsonify
import openai
import base64
from PIL import Image
from io import BytesIO
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Set up OpenAI API key
openai.api_key = "sk-proj-VDQo6VkSDZvveK7l0EbkFJnbAaR7FcjfQNdphe2y13"
# Set up upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['jpg', 'jpeg', 'png']

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        # Check if a file was selected
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Check if the file is allowed
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Get user input for number of captions and hashtags
            num_captions = int(request.form.get('numCaptions', 3))
            num_hashtags = int(request.form.get('numHashtags', 3))

            # Resize the image to a smaller size (e.g., 512x512)
            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as file:
                image = Image.open(file)
                image.thumbnail((512, 512))
                image_bytes = BytesIO()
                image.save(image_bytes, format='JPEG')
                image_bytes.seek(0)

            # Convert image bytes to base64 string
            image_base64 = base64.b64encode(image_bytes.getvalue()).decode('utf-8')

            # Use a more descriptive prompt format
            mood = request.form.get('mood', '')
            emoji = request.form.get('emoji', '')

            prompt = f"""
            Generate {num_captions} accurate captions for an image of {mood} mood with {emoji} emoji.
            The image shows [INSERT IMAGE DESCRIPTION HERE].
            Provide captions that describe the visual content, emotions conveyed, and context of the image.
            Use simple language but include specific details about what's in the image.
            Generate hashtags related to the image content.
            """

            # Add image description to the prompt
            prompt += f"Y4:0\n[Image description: A photo of {mood} mood with {emoji} emoji.]"

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt}
                ]
            )
            
            captions = []
            hashtags = []
            for i in range(min(num_captions, len(response['choices']))):
                captions.append(response['choices'][i]['message']['content'])
            for i in range(min(num_hashtags, len(response['choices']) - num_captions)):
                hashtags.append(response['choices'][num_captions + i]['message']['content'])

            return jsonify({
                'captions': captions,
                'hashtags': hashtags,
                'mood': mood,
                'emoji': emoji,
                'image': image_base64
            })
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
