import cv2
from PIL import Image, ImageDraw, ImageFont
import logging
logger = logging.getLogger(__name__)

def detect_face(image_path):
    
    # Read the image using OpenCV

    # Loading the image
    img = cv2.imread(image_path)
    # Converting the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Load the pre-trained face detection model (Haar Cascade for frontal faces)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Detect faces in the image
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3,minSize=(210, 210))

    return faces

def wrap_text(text, font, max_width, draw):
    """ Helper function to wrap text to fit within the given width. """
    words = text.split(' ')
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        # Using textbbox to get the width of the current line
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))

    return '\n'.join(lines)

 

def estimate_speech_balloon_size(text, char_width=20, line_height=14, padding_x=15, padding_y=15, min_width=50, max_line_width=40):
    """
    Estimates the width and height of a speech balloon based on text length,
    handling line wrapping.

    Args:
        text (str): The text content of the speech balloon.
        char_width (int): Approximate width of a character in pixels.
        line_height (int): Approximate height of a line in pixels.
        padding_x (int): Horizontal padding around the text.
        padding_y (int): Vertical padding around the text.
        min_width (int): Minimum width of the speech balloon.
        max_line_width (int): Maximum number of characters per line.

    Returns:
        tuple: (width, height) of the estimated speech balloon.
    """

    if not isinstance(text, str):
        raise TypeError("Input 'text' must be a string.")

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) + 1 <= max_line_width:
            current_line += (word + " ")
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    lines.append(current_line.strip()) #add the last line.

    max_line_pixel_width = max(len(line) * char_width for line in lines) if lines else 0

    width = max(min_width, max_line_pixel_width + 2 * padding_x)
    height = len(lines) * line_height + 2 * padding_y

    return (width, height)

def add_comic_rectangle(image_path, output_path, text,is_debug=False):
    """
    Adds a speechbaloon near th edetected face  or in the baseline
    """
    # Detect faces to avoid placing the rectangle over them
    faces = detect_face(image_path)
    print("faces: ",faces)
    logger.error("faces: "+str(faces))
    # Open the image using PIL
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)

    # Rectangle dimensions
    # rect_width, rect_height = 230, 90
    # rect_width, rect_height = calculate_rectangle_dimensions(text, font_size=16, aspect_ratio=2.5)
    rect_width, rect_height = estimate_speech_balloon_size(text)
    print("Speech Rectangle dimension(w,h)",rect_width, rect_height)
    logger.error("Speech Rectangle dimension(w,h): "+str(rect_width) +','+ str(rect_height))
    padding = 10  # Padding inside the rectangle

    # Calculate the safe position for the rectangle (we'll place it in a corner where no face is detected)
    img_width, img_height = img.size

    print("img.size",img.size)
    logger.error("img.size: "+str(img.size))

    # Default position (bottom-right corner)
    rect_x, rect_y = img_width - rect_width, img_height - rect_height

    face_area = 0
    detected_face = None
    for (x, y, w, h) in faces:
        # disegno rettangolo verde sulle possibili facce  trovate
        if is_debug:
            draw.rectangle([(x,y),(x+w, y+h)],outline=(0, 255,0, 255), width=5)

        new_face_area = w*h
        print("area face: ",new_face_area)
        logger.error("area face: "+str(new_face_area))
        if new_face_area > face_area:
            face_area = new_face_area
            detected_face = (x, y, w, h)
    
    print("Biggest face: ",face_area, detected_face)
    logger.error("Biggest face (area,detected face): " +str(face_area) +','+str(detected_face))

    if detected_face != None:
        x, y, w, h = detected_face

        # disegno rettangolo blu sulla  faccia scelta
        if is_debug:
            draw.rectangle([(x,y),(x+w, y+h)],outline=(0, 0, 255, 255), width=5)

        # init with default position
        new_x_position = rect_x
        new_y_position = rect_y

        # detected face must be greater than
        min_face_width = 100
        min_face_height = 100

        # if the image is pefectly in the middle or is more in the left half of the image 
        # and the speech bubble rectangle stays within the image
        # we put it in the right side 
        if w >= min_face_width and x + w // 2 <= img_width//2 and x+w//2+rect_width <= img_width:
            new_x_position = x + w//2
        # if the image is more in the right half of the image we put it in the left side
        if w >= min_face_width and x + w // 2 > img_width//2 and x+w//2 - rect_width >= 0:
            new_x_position = x + w//2 - rect_width
        
        # we want the speech position under the face
        if h >= min_face_height and y+h+rect_height+5 <= img_height:
            new_y_position = y + h + 5
        
        # negative values lead to fallback position
        if (w >= min_face_width and h >= min_face_height and new_x_position > 0 and new_y_position > 0):
            rect_x = new_x_position
            rect_y = new_y_position
    
    print("posizione fumetto: ", rect_x, rect_y)
    logger.error("posizione fumetto (x,y): "+str(rect_x) +','+ str(rect_y))

    # Draw the rectangle
    rect_box = [(rect_x, rect_y), (rect_x + rect_width, rect_y + rect_height)]
    draw.rounded_rectangle(rect_box, radius=10, fill=(255, 255, 255), outline="black", width=3)

    # Load a comic-style font
    try:
        font = ImageFont.truetype("assets/fonts/OpenComicFont.ttf", 20)  # Use Comic Sans or a similar comic font
    except IOError:
        font = ImageFont.load_default()

    # Calculate the maximum width and height available for the text (inside the rectangle, with padding)
    max_text_width = rect_width - 2 * padding
    max_text_height = rect_height - 2 * padding

    # Wrap the text so it fits within the rectangle's width
    wrapped_text = wrap_text(text, font, max_text_width, draw)

    # Calculate the bounding box of the wrapped text using textbbox
    text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Ensure the wrapped text fits within the rectangle height
    if text_height > max_text_height:
        print("Warning: The text is too long to fit inside the rectangle.")
        logger.error("Warning: The text is too long to fit inside the rectangle.")

    # Center the text inside the rectangle
    text_x = rect_x + (rect_width - text_width) // 2
    text_y = rect_y + (rect_height - text_height) // 2

    # Add text outline effect (by drawing the text multiple times in different colors)
    outline_color = "black"
    for offset in [(1,1), (-1,-1), (1,-1), (-1,1)]:
        draw.multiline_text((text_x + offset[0], text_y + offset[1]), wrapped_text, font=font)

    # Add the comic-style text (fill with bright color)
    draw.multiline_text((text_x, text_y), wrapped_text, font=font, fill="black")

    # Save the image
    img.save(output_path)
    print(f"Image saved to {output_path}")
    logger.error(f"Image saved to {output_path}")


# Example usage:
# image_path = "panels-img/panel5.png"  # Replace with your image path
# output_path = "panels-img/panel5_speech.png"
# text = "Today, we’re going to explore how to create a comic. It’s a layered process, where storytelling meets visual art, and each step builds upon the last"
# add_comic_rectangle(image_path, output_path, text)

# batch try on folder

# def list_file_paths(folder_path):
#     """
#     Lists all file paths in a given folder and its subfolders.

#     Args:
#         folder_path (str): The path to the folder.

#     Returns:
#         list: A list of file paths.
#     """
#     file_paths = []
#     for root, _, files in os.walk(folder_path):
#         for file in files:
#             file_paths.append(os.path.join(root, file))
#             add_comic_rectangle(os.path.join(root, file), os.path.join("test", file), "lI think I've got it now! Thank you, Professor Thompson, you've been a huge help. I'm excited to see where my story takes me. I feel like I can finally create something that I'm proud of, something that will inspire others like my grandmother's comic books inspired me.")
#     return file_paths

# # Example usage:
# folder = "panels-img"  # Replace with the actual folder path
# file_list = list_file_paths(folder)
# print (file_list)