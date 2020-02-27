import os

mask = [x.replace('.jpg', '') for x in os.listdir('landscape_target/') if ".jpg" in x]

for file in [x.replace('.png', '') for x in os.listdir('landscape_label/') if ".png" in x]:
    final_path = os.path.join('landscape_label/', file) + ".png"

    try:

        if file not in mask:
            os.remove(final_path)
        else:
            os.rename(final_path, final_path.replace("target_image", "target_image_semantic"))

    except Exception as error:
        print(error)
            