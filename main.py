"""
A console-based dice game for GCSE programming project

Database:
  sqlite3 database to store users' names and passwords, and scores
  Format:
    Users: rowid, username, password
    Scores: rowid, player_id (Foreign Key to user rowid), score

Authentication:
  Authentication uses usernames and SHA256 hashed passwords for security

Classes:
  SQLManager: Context manager for sqlite3
  Player: properties for a user
  GameState: properties and methods to control gameplay

Rules:
  On a double roll, add score and roll another
  On an even roll, add 10
  On an odd roll, subtract 5 (can't go below 0)
  5 rounds
  If draw at end, roll one die each until someone wins
"""
import random
import typing
import hashlib
import time
import sqlite3


class SQLManager:
    """Context manager for opening, committing and closing sqlite3 databases"""

    def __init__(self, name="dicegame.db"):
        self.name = name

    def __enter__(self):
        self.conn = sqlite3.connect(self.name)
        return self.conn.cursor()

    def __exit__(self, type, value, traceback):
        if not (type or value or traceback):
            self.conn.commit()
        self.conn.close()


class Player:
    """Created for each registered user to store their data"""

    def __init__(self, username):
        self.username = username
        self.score = 0


class GameState:
    """
    Includes the main methods and properties for gameplay
    """

    def __init__(self, players: typing.List[Player]):
        # current round number
        self.rounds = 1
        # a list of player objects
        self.players = players
        # player turn (an index for the players list returning the current player)
        self.turn = 0

    def is_draw(self):
        return self.players[0].score == self.players[1].score

    def play_draw(self):
        """
        Simulates gameplay on a draw
        """

        # start a loop that repeats until it is no longer a draw
        while self.is_draw():
            print("\n===DRAW ROLL===")
            print("Player Rolling: ", self.players[0].username)
            player1_roll = self._roll_dice()
            print("Player Rolling: ", self.players[1].username)
            player2_roll = self._roll_dice()

            self.players[0].score += player1_roll
            self.players[1].score += player2_roll

    def play_round(self):
        """
        Simulates a round of rolling dice
        """

        # roll 2 dice
        print("\n===NEW ROUND===")
        print("=Roll 1=")
        dice_val1 = self._roll_dice()
        print("=Roll 2=")
        dice_val2 = self._roll_dice()

        # call the method to calculate the score from dice rolls
        score = self._calculate_scores(dice_val1, dice_val2)

        print("Final Score: ", score, "\n")

        # get the current player
        current_player = self.players[self.turn]
        # add score to player
        current_player.score += score

        # swaps the player turn
        if self.turn == 0:
            self.turn = 1
        else:
            self.turn = 0
            # add a round if both players have had a turn
            self.rounds += 1

    def _roll_dice(self):
        """
        Simulates a die roll between 1 and 6
        """
        print("Rolling", end="")

        # animating dots by removing default \n added by print
        for _ in range(9):
            time.sleep(0.1)
            print(".", end="", flush=True)
        print(".")

        score = random.randint(1, 7)
        print("You rolled: ", score, "\n")
        return score

    def _calculate_scores(self, roll1, roll2):
        """
        Takes in two integers from 1-6 which are dice rolls
        Returns a score after passing dice rolls through rules
        """
        double_score = self._check_double(roll1, roll2)
        even_score = self._check_even(double_score)
        odd_score = self._check_odd(even_score)
        return odd_score

    def _check_double(self, roll1, roll2):
        """
        If roll is a double, rolls another die and adds score
        Otherwise returns the sum of two rolls
        """
        if roll1 == roll2:
            print("!!DOUBLE!!")
            extra_score = self._roll_dice()
            return roll1 + roll2 + extra_score
        return roll1 + roll2

    @staticmethod
    def _check_even(score):
        """
        Adds 10 to the score and returns it if given number is even
        """
        if score % 2:
            return score
        print("Add 10 for even")
        return score + 10

    @staticmethod
    def _check_odd(score):
        """
        Subtracts 5 from the score and returns it if given number is odd
        If number results in being less than 0, returns 0
        """
        if score % 2:
            print("Subtract 5 for odd")
            score -= 5
            if score < 0:
                return 0
            return score
        return score


def create_user():
    """
    Signup process to add users
    """
    username = input("Enter Username: ")
    # input password and hash to bytes
    password = hashlib.sha256(input("Enter Password: ").encode()).digest()

    with SQLManager() as cur:
        try:
            # add a user, however, username is unique, so catch an IntegrityError and output error
            cur.execute("INSERT INTO users VALUES (?, ?)",
                        (username, password))
        except sqlite3.IntegrityError:
            print("Username already used.")


def authenticate(not_allowed: typing.List[Player] = []) -> Player:
    """
    Input details and authenticate players
    not_allowed: optional list of players that can't be signed in (already signed in)
    Returns a player object
    """
    while True:
        username = input("Username: ")

        # check that username isnt in not_allowed
        if len([True for u in not_allowed if u.username == username]) > 0:
            print("Username Added Already")
            continue

        with SQLManager() as cur:
            # fetch the hashed password to match to
            cur.execute("SELECT password FROM users WHERE username=?",
                        (username, ))
            required_password = cur.fetchall()

        # if no password isn't available, then username doesn't exist
        if not required_password:
            print("Invalid Username\n")
            continue

        # get required password from the .fetchall format '[(password)]'
        required_password = required_password[0][0]
        # ask user to enter password
        user_password = input("Password: ")

        # hash with sha256 and check against the required password
        password_encrypted = hashlib.sha256(user_password.encode()).digest()
        if password_encrypted == required_password:
            player = Player(username)
            break
        else:
            print("Incorrect Password\n")

    print("Success")
    return player


def create_tables():
    """create tables if they dont exist"""
    with SQLManager() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS users (username TEXT UNIQUE, password TEXT)"
        )
        cur.execute(
            "CREATE TABLE IF NOT EXISTS scores (player_id INTEGER, score INTEGER)"
        )


def show_summary(end=False):
    """Outputs a round or end game summary"""
    print("===END SUMMARY===" if end else "===ROUND SUMMARY===")
    if not end:
        print(f"Round: {game_state.rounds}")
        print(f"Next Turn: {game_state.players[game_state.turn].username}")
    print(
        f"{game_state.players[0].username}'s Score: {game_state.players[0].score}"
    )
    print(
        f"{game_state.players[1].username}'s Score: {game_state.players[1].score}"
    )


def save_score(player: Player):
    """
    Save a score from a Player object
    """
    with SQLManager() as cur:
        # get the player's rowid
        cur.execute("SELECT rowid FROM users WHERE username=?",
                    (player.username, ))
        player_id = cur.fetchall()[0][0]

        # create a score record with foreign key to user
        cur.execute("INSERT INTO scores VALUES (?, ?)",
                    (player_id, player.score))


def display_top_scores():
    """
    Outputs the top 5 scores and names
    """
    with SQLManager() as cur:
        # get top 5 scores from db
        cur.execute("SELECT * FROM scores ORDER BY score LIMIT 5")
        scores = cur.fetchall()

        # a list that will be populated with tuples of (username, score)
        username_scores = []
        for score_record in scores:
            # get player info from foreign key
            cur.execute("SELECT username FROM users WHERE rowid=?",
                        (score_record[0], ))
            username = cur.fetchall()[0][0]
            username_scores.insert(0, (username, score_record[1]))

    print("\n===TOP SCORES===")
    formatter = "{:10}\t{}"
    # ouput the scores
    for score in username_scores:
        print(formatter.format(*score))


if __name__ == "__main__":
    create_tables()

    print("Welcome to the Dice Game")

    """Signup section"""
    print("\n===SIGNUP===")
    choice = input("Do you want to signup (y/n)? ")
    while True:
        if choice == "y":
            create_user()
        elif choice == "n":
            break
        choice = input("\nDo you want to signup again (y/n)? ")

    """Login section"""
    print("\n===Player 1 Login===")
    player_one = authenticate()
    print("\n===Player 2 Login===")
    player_two = authenticate(not_allowed=[player_one])
    print("\n")

    game_state = GameState([player_one, player_two])

    """Main game loop"""
    while game_state.rounds <= 5:
        show_summary()
        input("(Enter) Next Round\n")
        game_state.play_round()

    """Run draw if equal scores"""
    if game_state.is_draw():
        show_summary(True)
        game_state.play_draw()
    show_summary(True)

    """Get the winner"""
    if game_state.players[0].score > game_state.players[1].score:
        winner = game_state.players[0]
    else:
        winner = game_state.players[1]


    print("\n===RESULTS===")
    print("Winner: ", winner.username)
    print("Score: ", winner.score)

    save_score(winner)
    display_top_scores()
