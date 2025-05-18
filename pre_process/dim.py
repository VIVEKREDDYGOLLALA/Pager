from PIL import Image

def get_image_dimensions(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
    return width, height

# Example usage:
image_path = "images/image.png"  # Replace with your image file path
width, height = get_image_dimensions(image_path)
print(f"Width: {width}px, Height: {height}px")
