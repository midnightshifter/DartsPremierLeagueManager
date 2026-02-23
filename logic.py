from asyncio import Runner
from tabulate import tabulate
import json
import os

dataFile = "leagueData.json"
totalnights = 15

# File Handling
def loadData():
    if not os.path.exists(dataFile):
        return{"players": {}, "current_night": 1, "nights": {}}

    with open(dataFile, "r") as f:
        data = json.load(f)

        if "current_night" not in data:
            data["current_night"] = 1
        
        if "players" not in data:
            data["players"] = {}

        if "nights" not in data:
            data["nights"] = {}

        return data

def saveData(data):
    with open(dataFile, "w") as f:
        json.dump(data, f, indent = 4)

# setup players

def setupplayers():
    data = loadData()

    if data["players"]:
        print("players already set up")
        return

    print("\nEnter the 8 players competeting: ")
    for i in range (8):
        name = input(f"players {i+1} name: ")
        data["players"][name] = {
            "points": 0,
            "played": 0,
            "wins": 0,
            "legs_won": 0,
            "legs_lost": 0,
            "night_wins": 0,
            "total_180s": 0
        }

    saveData(data)
    print("\nplayers saved successfully")

# enter match results
def enterMatchResults():
    data = loadData()

    if len(data["players"]) != 8:
        print("You must set up 8 players first.")
        return

    if data["current_night"] > totalnights:
        print("All nights have already been completed.")
        return

    night_key = f"Night {data['current_night']}"

    if night_key not in data["nights"]:
        data["nights"][night_key] = []

    print(f"\n===== {night_key} =====")

    completed_matches = len(data["nights"][night_key])

    players = list(data["players"].keys())

    # Handle unfinished nights
    if night_key in data["nights"] and data["nights"][night_key]:

        print(f"\nUnfinished {night_key} detected.")
        print("1. Resume Night")
        print("2. Restart Night")

        choice = input("Choose an option (1/2): ").strip()

        if choice == "1":
            print("Resuming night...")
        elif choice == "2":
            print("Restarting night...")
            data["nights"][night_key] = []
            saveData(data)
        else:
            print("Invalid selection.")
            return

        # if night doesnt exist, create it
        if night_key not in data["nights"]:
            data["nights"][night_key] = []

    # Helper function to handle a single match
    def play_match(p1, p2, round_name):
        print(f"\n{round_name}: {p1} vs {p2}")

        score = input("Enter score (e.g. 6-4) or N/A for walkover: ").strip().upper()

        # WALKOVER
        if score == "N/A":
            print("Walkover detected.")
            print(f"1. {p1}")
            print(f"2. {p2}")
            choice = input("Which player withdrew? (1/2): ").strip()

            if choice == "1":
                winner = p2
                loser = p1
            elif choice == "2":
                winner = p1
                loser = p2
            else:
                print("Invalid selection.")
                return None

            print(f"{winner} advances by walkover.")
            score = "WO"

        # NORMAL MATCH
        else:
            try:
                s1, s2 = map(int, score.split("-"))
            except ValueError:
                print("Invalid score format.")
                return None

            # Update legs
            data["players"][p1]["legs_won"] += s1
            data["players"][p1]["legs_lost"] += s2

            data["players"][p2]["legs_won"] += s2
            data["players"][p2]["legs_lost"] += s1

            if s1 > s2:
                winner = p1
                loser = p2
            elif s2 > s1:
                winner = p2
                loser = p1
            else:
                print("Draws are not allowed.")
                return None

            print(f"Winner: {winner}")

            # 180s input
            try:
                p1_180s = int(input(f"Enter 180s hit by {p1}: "))
                p2_180s = int(input(f"Enter 180s hit by {p2}: "))
            except ValueError:
                print("Invalid 180s input.")
                return None

            data["players"][p1]["total_180s"] += p1_180s
            data["players"][p2]["total_180s"] += p2_180s

        # Store match
        data["nights"][night_key].append({
            "round": round_name,
            "p1": p1,
            "p2": p2,
            "score": score,
            "winner": winner
        })

        # Save data immediateley after each match
        saveData(data)

        return winner, loser

    # ===== QUARTER FINALS =====
    print("\n--- Quarter Finals ---")
    qf_winners = []
    qf_losers = []

    for i in range(4):

        # skip completed matches
        if i < len(data["nights"][night_key]):
            qf_winners.append(
                data["nights"][night_key][i]["winner"]
            )
            continue

        print(f"\nMatch {i+1}")
        p1 = input("Player 1: ").strip()
        p2 = input("Player 2: ").strip()

        if p1 not in players or p2 not in players:
            print("Invalid player name.")
            return

        result = play_match(p1, p2, "Quarter Final")
        if result is None:
            return

        winner, loser = result
        qf_winners.append(winner)
        qf_losers.append(loser)

    # ===== SEMI FINALS =====
    print("\n--- Semi Finals ---")
    sf_winners = []
    sf_losers = []

    for i in range(2):

        match_index = 4 + i

        # skip completed matches
        if match_index < len(data["nights"][night_key]):
            sf_winners.append(
                data["nights"][night_key][i]["winner"]
            )
            continue

        p1 = qf_winners[i*2]
        p2 = qf_winners[i*2 + 1]

        result = play_match(p1, p2, "Semi Final")
        if result is None:
            return

        winner, loser = result
        sf_winners.append(winner)
        sf_losers.append(loser)

    # ===== FINAL =====
    print("\n--- Final ---")

    # skip final if already completed
    if len(data["nights"][night_key]) > 6:
        print("Final already completed.")
        return

    p1 = sf_winners[0]
    p2 = sf_winners[1]

    result = play_match(p1, p2, "Final")
    if result is None:
        return

    winner, runner_up = result

    # ===== POINTS SYSTEM =====
    data["players"][winner]["points"] += 5
    data["players"][winner]["night_wins"] += 1
    data["players"][runner_up]["points"] += 3

    for player in sf_losers:
        data["players"][player]["points"] += 2

    # Update appearances
    for player in players:
        data["players"][player]["played"] += 1

    data["players"][winner]["wins"] += 1

    data["current_night"] += 1

    saveData(data)

    print(f"\n🏆 Night Winner: {winner}")
    print("Points awarded successfully!")


def leaderboard():
    data = loadData()
    players = data["players"]

    if not players:
        print("No players found.")
        return

    sorted_players = sorted(
        players.items(),
        key=lambda x: (
            x[1]["points"],
            x[1]["legs_won"] - x[1]["legs_lost"]
        ),
        reverse=True
    )

    row_format = "{:<4}{:<22}{:<6}{:<8}{:<6}{:<12}{:<10}{:<10}{:<10}{}"

    print("\n🏆 PREMIER LEAGUE LEADERBOARD 🏆\n")

    print(row_format.format(
        "Pos","Name","Pts","Played","Wins",
        "Night Wins","Legs Won","Legs Lost",
        "Leg Diff","Win %"
    ))

    for position, (name, stats) in enumerate(sorted_players, start=1):

        leg_diff = stats["legs_won"] - stats["legs_lost"]

        if stats["played"] > 0:
            win_pct = (stats["wins"] / stats["played"]) * 100
        else:
            win_pct = 0

        print(row_format.format(
            position,
            name,
            stats["points"],
            stats["played"],
            stats["wins"],
            stats["night_wins"],
            stats["legs_won"],
            stats["legs_lost"],
            leg_diff,
            f"{win_pct:.1f}%"
        ))

# Most 180s
def most18s0sTable():
    data = loadData()

    if not data["players"]:
        print("No players found.")
        return

    sorted_players = sorted(
    data["players"].items(),
    key=lambda x: x[1]["total_180s"],
    reverse=True
    )

    table = []
    position = 1

    for name, stats in sorted_players:
        total_180s = stats.get("total_180s", 0)

        table.append([
            position,
            name,
            total_180s
            ])

        position += 1

    headers = ["Pos", "Name", "Total 180s"]

    print("\n🔥 MOST 180s TABLE 🔥\n")
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

    input("\nPress Enter to return to the main menu...")

# Reset League
def resetLeague():
    confirm = input("Are you sure you want to reset the league? (y/n): ")
    if confirm.lower() == "y":
        if os.path.exists(dataFile):
            os.remove(dataFile)
        print("League reset successfully.")
    else:
        print("Reset cancelled.")

# View Night Results
def viewNightResults():
    data = loadData()

    if not data ["nights"]:
        print("No match data avalible")
        return
    
    # Sort night numerically
    nights = sorted(
        data["nights"].keys(),
        key=lambda x: int(x.split()[1])
    )

    print("\n📅 Select a Night to View:\n")

    for i, night in enumerate(nights, start=1):
        print(f"{i}. {night}")

    try:
        choice = int(input("\nEnter night number: "))
        if choice < 1 or choice > len(nights):
            print("Invalid selection")
            return
    except ValueError:
        print("Please enter a valid number.")
        return

    selectedNight = nights[choice - 1]
    matches = data["nights"][selectedNight]

    if not matches:
        print("No matches recorded for this night")
        return

    table = []

    for match in matches:
        table.append([
            match["round"],
            match["p1"],
            match["p2"],
            match["score"],
            match["winner"]
        ])
    headers = ["Round", "Player 1", "Player 2", "Score", "Winner"]

    print(f"\n🏆 {selectedNight} Results\n")
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

    input("\nPress Enter to return to the main menu...")

# Search Results by players
def searchResultsByPlayer():
    data = loadData()

    if not data["nights"]:
        print("No match data avalible.")
        return

    player_name = input("Enter player name to search: ").strip().lower()

    matching_players = [
        player for player in data["players"]
        if player_name in player.lower()
    ]

    if not matching_players:
        print("No player found with that name.")
        return

    # if multiple matches 
    if len(matching_players) > 1:
        print("\nMultiple players Found:")
        for i, name in enumerate(matching_players, start=1):
            print(f"{i}. {name}")
        try:
            choice = int(input("Select player number: "))
            player_name = matching_players[choice - 1]
        except:
            print("Invalid selection.")
            return
    else:
        player_name = matching_players[0]

    results_found = False
    table = []

    # sort nights by numerical order
    nights = sorted(
        data["nights"].keys(),
        key=lambda x: int(x.split()[1])
    )

    for night in nights:
        for match in data["nights"][night]:
            if player_name in [match["p1"],match["p2"]]:
                
                if match["p1"] == player_name:
                    opponent = match["p2"]
                elif match["p2"] == player_name:
                    opponent = match["p1"]
                else:
                    continue # safety fallback
                
                result = "Win" if match["winner"] == player_name else "Loss"

                table.append([
                    night,
                    match["round"],
                    opponent,
                    match["score"],
                    result
                ])

                results_found = True

    if not results_found:
        print("No matches found for {player_name}.")
        return

    headers = ["Night", "Round", "Opponent", "Score", "Result"]

    print(f"\n🎯 Match History for {player_name}\n")
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))

# Player Head to Head
def headToHead():
    data = loadData()

    if "nights" not in data or not data["nights"]:
        print("No match data available yet.")
        return

    player1_input = input("Enter first player name: ").strip()
    player2_input = input("Enter second player name: ").strip()

    players = data["players"]

    # Create case-insensitive lookup
    players_lookup = {name.lower(): name for name in players}

    if player1_input.lower() not in players_lookup or player2_input.lower() not in players_lookup:
        print("One or both players not found.")
        return

    player1 = players_lookup[player1_input.lower()]
    player2 = players_lookup[player2_input.lower()]

    print(f"\n=== {player1} vs {player2} ===")

    # 🔹 Show Overall Stats First
    print("\n--- Overall Stats ---")
    for player in [player1, player2]:
        stats = data["players"][player]
        print(f"\n{player}")
        print(f"Points: {stats['points']}")
        print(f"Played: {stats['played']}")
        print(f"Wins: {stats['wins']}")

    # 🔹 Head-to-Head Tracking
    h2h_matches = []
    player1_wins = 0
    player2_wins = 0

    # Sort nights numerically (Night 1, Night 2, etc.)
    nights = sorted(
        data["nights"].keys(),
        key=lambda x: int(x.split()[1])
    )

    for night in nights:
        for match in data["nights"][night]:

            if (
                (match["p1"] == player1 and match["p2"] == player2)
                or
                (match["p1"] == player2 and match["p2"] == player1)
            ):

                h2h_matches.append((night, match))

                if match["winner"] == player1:
                    player1_wins += 1
                else:
                    player2_wins += 1

    # 🔹 Display H2H Results
    print("\n--- Head to Head ---")

    if not h2h_matches:
        print("These players have not played each other yet.")
    else:
        print(f"{player1} wins: {player1_wins}")
        print(f"{player2} wins: {player2_wins}")

        for night, match in h2h_matches:
            print(
                f"{night} - {match['round']} - "
                f"{match['score']} (Winner: {match['winner']})"
            )


def main():
    while True:
        print("\n=== Darts Premier League Tracker ===")
        print("1. Setup players")
        print("2. Enter Match Results (Next Night)")
        print("3. View Leaderboard")
        print("4. View Night Results")
        print("5. Search Results by Player")
        print("6. Most 180s Table")
        print("7. Head to Head")
        print("8. Reset League")
        print("9. Exit")

        choice = input("Select an option: ")

        if choice == "1":
            setupplayers()
        elif choice == "2":
            enterMatchResults()
        elif choice == "3":
            leaderboard()
        elif choice == "4":
            viewNightResults()
        elif choice == "5":
            searchResultsByPlayer()
        elif choice == "6":
            most18s0sTable()
        elif choice == "7":
            headToHead()
        elif choice == "8":
            resetLeague()
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()
