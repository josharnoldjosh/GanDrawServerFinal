## install
`pip3 install -r requirements.txt --user`

## launch server

NOTE! Ensure `connections/` folder is deleted before running the app!

`gunicorn --worker-class eventlet -w 1 app:app`

## Managing the collected data

To start from scratch, delete the `games/` folder.

Then run `cd data/; python3 generate_games.py`

Throughout the data collection process, games will be marked as `finished` in the `flags.json` file.

Run this command to move the finished games to a folder called `finished_games/`:
`cd data/; python3 move_finished_games.py`

Then, you will see how many games are left to be finished.

If you want to recollect those same games, run: `generate_games.py` and it will regenerate non finished games.

If you finish a round of data collection and there are still some games that haven't been finished, you can either leave them their for people to connect to automatically to finish the data collection, or you can delete them and generate all the games again.

Move the `finished_games/` folder into the `etc/DataViewer/static/` folder and then run `run.py` to visualize the collected data in your browser.

You can also move it into `etc/estimate_dialogs_left_to_collect/` and run `count_games.py` to see how many conversations you have for each target image.

## Creating target images

1. Batch download your images
2. Put them in a folder with the `scale_crop.py` script and scale them and crop them.
3. Run `rename.py` in the same folder as them (with optional argument to specificy what number you start at)
4. Generate the semantic labels (for me specifically, I put them in a folder called `landscape/` on my server and run a command).
5. Organize your data so you have `data/landscape_target/` where all your target images go with the extension `.jpg`. Have another folder called `data/landscape_label/` where all your target label images go with the extension `.png`. NOTE: your target images and labels that correspond to each other must have the same root name. They only differ in the golder location and the `.jpg` and `.png` extension.

## Coming soon: Generating data to input into the model from `finished_games/` folder

Coming soon.
