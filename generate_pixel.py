import os
from PIL import Image

def preprocess_for_16x16(path_in, path_out=None, palette_colors=8, background_color=(0,0,0)):
    """
    Load an image, crop it vertically based on alpha transparency, then center-crop
    it to a square, resize it to 16x16, and convert it to a low-color RGB image.

    Args:
        path_in (str): Input image file path.
        path_out (str): Output file path (optional).
        palette_colors (int): Number of colors to quantize (for palette).
        background_color (tuple): RGB background color to fill transparent areas.

    Returns:
        Image: Processed 16x16 RGB image.
    """
    img = Image.open(path_in).convert("RGBA")
    alpha = img.split()[3]

    # Crop vertically based on non-transparent area
    bbox = alpha.getbbox()
    if bbox:
        left, upper, right, lower = bbox
        img = img.crop((0, upper, img.width, lower))
    else:
        upper = 0
        lower = img.height
        img = img.crop((0, 0, img.width, img.height))

    # Calculate square crop around center
    crop_h = lower - upper
    x_center = img.width / 2
    half = crop_h / 2
    left_sq = max(0, int(x_center - half))
    right_sq = min(img.width, int(x_center + half))

    # Adjust square if not wide enough
    if (right_sq - left_sq) < crop_h:
        diff = crop_h - (right_sq - left_sq)
        pad_l = diff // 2
        pad_r = diff - pad_l
        left_sq = max(0, left_sq - pad_l)
        right_sq = min(img.width, right_sq + pad_r)

    img = img.crop((left_sq, 0, right_sq, crop_h))
    img = img.resize((16, 16), Image.LANCZOS)

    # Paste on solid background and convert to low-color palette
    bg = Image.new("RGB", (16, 16), background_color)
    bg.paste(img, mask=img.split()[3])
    img_out = bg.convert("P", palette=Image.ADAPTIVE, colors=palette_colors).convert("RGB")

    if path_out:
        img_out.save(path_out)
    return img_out

def batch_process(input_dir='input', output_dir='output', palette_colors=8, background_color=(0,0,0), ext='png'):
    """
    Process all images in a folder, resize and save them as 16x16 images.

    Args:
        input_dir (str): Folder containing source images.
        output_dir (str): Folder to save processed images.
        palette_colors (int): Number of colors for quantization.
        background_color (tuple): Background RGB color.
        ext (str): Extension for output images.
    """
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input folder not found: {input_dir}")
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        name, _ = os.path.splitext(filename)
        infile = os.path.join(input_dir, filename)
        if not os.path.isfile(infile) or name.startswith('.'):
            continue

        outfile = os.path.join(output_dir, f"{name}.{ext}")
        try:
            preprocess_for_16x16(
                infile, outfile,
                palette_colors=palette_colors,
                background_color=background_color
            )
            print(f"Processed: {filename} -> {os.path.basename(outfile)}")
        except Exception as e:
            print(f"Failed: {filename}, error: {e}")

if __name__ == '__main__':
    batch_process()
