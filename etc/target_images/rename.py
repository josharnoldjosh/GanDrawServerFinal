import os

for idx, image in enumerate([x for x in os.listdir(os.getcwd()) if ".jpg" in x]):
    os.rename(image, "target_"+str(idx)+".jpg")
