import os, shutil

# ensure output exists

for folder in [x for x in os.listdir(os.getcwd()) if "store" not in x.lower() if os.path.isdir(x)]:
    for idx, file in enumerate([x for x in os.listdir(os.path.join(os.getcwd(), folder))]):
        try:
            shutil.copyfile(os.path.join(os.getcwd(), folder, file), os.path.join(os.getcwd(), 'output/', 'target_image_'+str(idx+1)+'.jpg'))
        except Exception as error: 
            print(error)

print('Done!')            