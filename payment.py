"""
Functions to calculate the payment of a user.
"""

import os
import json
import time
import datetime
import pytz

utc=pytz.UTC

class Payment:

    @classmethod
    def calculate(self, email):
        return PaymentHelper.total_amount_earned(email)
        
    @classmethod
    def num_games_contributed(self, email):
        return PaymentHelper.num_games_contributed(email)

    @classmethod
    def all(self):
        emails = PaymentHelper.all_emails()
        for email in emails:
            print(Payment.calculate(email), Payment.num_games_contributed(email))

class PaymentHelper:

    @classmethod
    def game_ids(self):
        """
        Returns all the paths to finished games.
        """
        path = os.path.join(os.getcwd(), 'data/finished_games/')
        all_games = [x for x in os.listdir(path) if os.path.isdir(os.path.join('data/finished_games', x))]
        return all_games

    @classmethod
    def load_dialog(self, game_id):
        """
        Loads a dialog.json into memory given a finished_game id.
        """
        with open(os.path.join(os.getcwd(), 'data/finished_games/', game_id, 'dialog.json')) as file:
            data = json.load(file)
            return data['dialog']
        raise Exception("Failed to load dialog.json")

    @classmethod
    def user_contribute_amount(self, dialog, email):
        """
        Returns the percentage a user contributed to a game.
        """

        num_turns = len(dialog)
        turns_contributed = 0

        for turn in dialog:

            if "email" in turn.keys() and turn["email"] == email:
                turns_contributed += 1 # Count how many turns the user contributed too

        if num_turns == 0: return 0
        return (turns_contributed/num_turns)

    @classmethod
    def score(self, game_id):                
        with open(os.path.join(os.getcwd(), 'data/finished_games/', game_id, 'flags.json')) as file:
            data = json.load(file)
            return data['score']
        raise Exception("Failed to load flags.json")

    @classmethod
    def deserves_four_dollar_bonus(self, game_id):
        """
        Checks the date of a peek to see if its recent enough for the new payment scheme.
        """        
        try:
            path = os.path.join(os.getcwd(), 'data/finished_games/', game_id)    
            json_file = [x for x in os.listdir(path) if "peek" in x][0]         
            to_read = os.path.join(os.getcwd(), 'data/finished_games/', game_id, json_file)             

            with open(to_read, 'r') as file:                
                timestamp_str = file.readlines()[0]                
                if "." in timestamp_str: timestamp_str = timestamp_str.split(".")[0]                
                unix_timestamp = int(timestamp_str)
                to_check = datetime.datetime.fromtimestamp(unix_timestamp)        
                ideal = datetime.datetime(2020, 3, 2)
                if utc.localize(to_check) > utc.localize(ideal):
                    return True
                return False

        except Exception as error:
            pass
            print(error, game_id)

        return False

    @classmethod
    def total_amount_earned(self, email):
        """
        Returns all the paths to finished games that a user contributed too.
        """                
        total_amount = 0
        for game_id in PaymentHelper.game_ids():
            
            dialog = PaymentHelper.load_dialog(game_id)

            if PaymentHelper.deserves_four_dollar_bonus(game_id):
                total_amount += PaymentHelper.user_contribute_amount(dialog, email)*8
            elif PaymentHelper.score(game_id) >= 3: # We're being generous with the bonus
                total_amount += PaymentHelper.user_contribute_amount(dialog, email)*6
            else:
                total_amount += PaymentHelper.user_contribute_amount(dialog, email)*5

        return total_amount

    @classmethod
    def num_games_contributed(self, email):
        result = 0
        for game_id in PaymentHelper.game_ids():
            dialog = PaymentHelper.load_dialog(game_id)
            if PaymentHelper.user_contribute_amount(dialog, email) > 0:
                result += 1
        return result

    @classmethod
    def emails_in_dialog(self, dialog):
        result = []
        for turn in dialog:
            try:
                result.append(turn["email"])
            except:
                pass
        return result

    @classmethod
    def all_emails(self):
        emails = []
        for game_id in PaymentHelper.game_ids():
            dialog = PaymentHelper.load_dialog(game_id)
            emails += PaymentHelper.emails_in_dialog(dialog)
        return set(emails)

# if __name__ == '__main__':
#     Payment.all()




            