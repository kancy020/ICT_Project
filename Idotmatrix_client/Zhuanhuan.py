import os
from PIL import Image


def preprocess_for_16x16(path_in, path_out=None, palette_colors=8, background_color=(0,0,0)):

    img = Image.open(path_in).convert("RGBA")
    alpha = img.split()[3]
    bbox = alpha.getbbox()  
    if bbox:
        left, upper, right, lower = bbox
        img = img.crop((0, upper, img.width, lower))
    else:
        upper = 0
        lower = img.height
        img = img.crop((0, 0, img.width, img.height))


    crop_h = lower - upper
    x_center = img.width / 2
    half = crop_h / 2
    left_sq = max(0, int(x_center - half))
    right_sq = min(img.width, int(x_center + half))

    if (right_sq - left_sq) < crop_h:
        diff = crop_h - (right_sq - left_sq)
        pad_l = diff // 2
        pad_r = diff - pad_l
        left_sq = max(0, left_sq - pad_l)
        right_sq = min(img.width, right_sq + pad_r)
    img = img.crop((left_sq, 0, right_sq, crop_h))
    img = img.resize((16, 16), Image.LANCZOS)


    bg = Image.new("RGB", (16, 16), background_color)
    bg.paste(img, mask=img.split()[3])

    img_out = bg.convert("P", palette=Image.ADAPTIVE, colors=palette_colors).convert("RGB")
    if path_out:
        img_out.save(path_out)
    return img_out


def batch_process(input_dir='input', output_dir='output', palette_colors=8, background_color=(0,0,0), ext='png'):

    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")
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

def batch_process_single_file(filename, input_dir='input', output_dir='output', palette_colors=8, background_color=(0,0,0), ext='png'):
    string_name = filename.replace(":", "")
    
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")
    os.makedirs(output_dir, exist_ok=True)

    matched_file = None
    for file in os.listdir(input_dir):
        name, _ = os.path.splitext(file)
        if name == string_name:
            matched_file = file
            break

    if not matched_file:
        print(f"No matching file found for: {string_name}")
        return
    else:
        print(f"file has been found {matched_file}")

    infile = os.path.join(input_dir, matched_file)
    outfile = os.path.join(output_dir, f"{string_name}.{ext}")

    try:
        preprocess_for_16x16(
            infile, outfile,
            palette_colors=palette_colors,
            background_color=background_color
        )
        print(f"Processed: {matched_file} -> {outfile}")
    except Exception as e:
        print(f"Error processing file: {e}")


if __name__ == '__main__':
    batch_process()
