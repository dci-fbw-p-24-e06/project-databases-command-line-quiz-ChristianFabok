import psycopg2
import random
from psycopg2 import Error
from config import config

DB_CONFIG = config

VALID_TOPICS = [
    "nature", "art", "history", "geography", "science",
    "politics", "music", "film", "celebrities"
]

def connect_db():
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

def register_user():
    connection = connect_db()
    if connection:
        try:
            cursor = connection.cursor()
            username = input("Enter username: ")
            password = input("Enter password: ")
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s);", (username, password))
            connection.commit()
            print("Registration successful!")
        except Error as e:
            print(f"Error registering user: {e}")
        finally:
            cursor.close()
            connection.close()

def login_user():
    connection = connect_db()
    if connection:
        try:
            cursor = connection.cursor()
            username = input("Enter username: ")
            password = input("Enter password: ")
            cursor.execute("SELECT id FROM users WHERE username = %s AND password = %s;", (username, password))
            user_id = cursor.fetchone()
            if user_id:
                print("Login successful!")
                return user_id[0]
            else:
                print("Invalid username or password.")
                return None
        except Error as e:
            print(f"Error logging in: {e}")
        finally:
            cursor.close()
            connection.close()
    return None

def get_user_coins(user_id, topic):
    connection = connect_db()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"SELECT {topic}_coins FROM users WHERE id = %s;", (user_id,))
            coins = cursor.fetchone()[0]
            return coins
        except Error as e:
            print(f"Error fetching coins: {e}")
        finally:
            cursor.close()
            connection.close()
    return 0

def update_user_coins(user_id, topic, coins):
    connection = connect_db()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"UPDATE users SET {topic}_coins = %s WHERE id = %s;", (coins, user_id))
            connection.commit()
        except Error as e:
            print(f"Error updating coins: {e}")
        finally:
            cursor.close()
            connection.close()

def get_difficulty_level(coins):
    if coins >= 120:
        return 3  # Hard
    elif coins >= 60:
        return 2  # Medium
    return 1  # Easy

def add_question(topic):
    if topic not in VALID_TOPICS:
        print(f"Error: '{topic}' is not a valid topic. Valid topics are: {', '.join(VALID_TOPICS)}")
        return
    
    connection = connect_db()
    if connection:
        try:
            cursor = connection.cursor()
            module = input("Enter module: ")
            submodule = input("Enter submodule: ")
            while True:
                try:
                    difficulty = int(input("Enter difficulty level (1-3): "))
                    if 1 <= difficulty <= 3:
                        break
                    print("Please enter a number between 1 and 3.")
                except ValueError:
                    print("Please enter a valid number.")
            question = input("Enter question: ")
            correct_answer = input("Enter correct answer: ")
            
            wrong_answers = []
            for i in range(1, 6):
                answer = input(f"Enter wrong answer {i} (or press Enter to skip): ")
                if not answer:
                    break
                wrong_answers.append(answer)
            
            columns = "module, submodule, difficulty_level, question, correct_answer, wrong_answer1, wrong_answer2"
            values = "'{}', '{}', {}, '{}', '{}', '{}', '{}'".format(module, submodule, difficulty, question, correct_answer, wrong_answers[0], wrong_answers[1])
            if len(wrong_answers) > 2:
                columns += ", wrong_answer3"
                values += f", '{wrong_answers[2]}'"
            if len(wrong_answers) > 3:
                columns += ", wrong_answer4"
                values += f", '{wrong_answers[3]}'"
            if len(wrong_answers) > 4:
                columns += ", wrong_answer5"
                values += f", '{wrong_answers[4]}'"
            
            insert_query = f"INSERT INTO {topic} ({columns}) VALUES ({values});"
            cursor.execute(insert_query)
            connection.commit()
            print("Question added successfully!")
        except Error as e:
            print(f"Error adding question: {e}")
        finally:
            cursor.close()
            connection.close()

def take_quiz(user_id, topic, num_questions=5):
    if topic not in VALID_TOPICS:
        print(f"Error: '{topic}' is not a valid topic. Valid topics are: {', '.join(VALID_TOPICS)}")
        return
    
    coins = get_user_coins(user_id, topic)
    difficulty = get_difficulty_level(coins)
    
    connection = connect_db()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {topic} WHERE difficulty_level = %s ORDER BY RANDOM() LIMIT %s;", (difficulty, num_questions))
            questions = cursor.fetchall()
            
            if not questions:
                print(f"No questions found for topic '{topic}' at difficulty level {difficulty}.")
                return
            
            score = 0
            for question in questions:
                q_text = question[4]
                correct = question[5]
                wrong_answers = [ans for ans in question[6:] if ans is not None]
                all_answers = [correct] + wrong_answers
                random.shuffle(all_answers)
                
                print(f"\nQuestion: {q_text}")
                for i, answer in enumerate(all_answers, 1):
                    print(f"{i}. {answer}")
                
                while True:
                    try:
                        user_choice = int(input(f"Enter your answer (1-{len(all_answers)}): "))
                        if 1 <= user_choice <= len(all_answers):
                            break
                        print(f"Please enter a number between 1 and {len(all_answers)}.")
                    except ValueError:
                        print("Please enter a valid number.")
                
                if all_answers[user_choice - 1] == correct:
                    print("Correct! +10 coins")
                    score += 10
                else:
                    print(f"Wrong! The correct answer was: {correct}. -1 coin")
                    score -= 1
            
            new_coins = max(0, coins + score)  # Coins can't go below 0
            update_user_coins(user_id, topic, new_coins)
            print(f"\nQuiz completed! Your {topic} coins: {new_coins}")
            
        except Error as e:
            print(f"Error during quiz: {e}")
        finally:
            cursor.close()
            connection.close()

def show_leaderboard(topic=None):
    connection = connect_db()
    if connection:
        try:
            cursor = connection.cursor()
            if topic:
                cursor.execute(f"SELECT username, {topic}_coins FROM users ORDER BY {topic}_coins DESC LIMIT 10;")
                print(f"\nTop 10 Players for {topic.capitalize()}:")
            else:
                cursor.execute("SELECT username, (nature_coins + art_coins + history_coins + geography_coins + science_coins + politics_coins + music_coins + film_coins + celebrities_coins) AS total_coins FROM users ORDER BY total_coins DESC LIMIT 10;")
                print("\nOverall Top 10 Players:")
            leaderboard = cursor.fetchall()
            for i, (username, coins) in enumerate(leaderboard, 1):
                print(f"{i}. {username}: {coins} coins")
        except Error as e:
            print(f"Error showing leaderboard: {e}")
        finally:
            cursor.close()
            connection.close()

def topic_leaderboard_menu(user_id):
    while True:
        print("\n=== Topic Leaderboards ===")
        for i, topic in enumerate(VALID_TOPICS, 1):
            print(f"{i}. {topic.capitalize()}")
        print(f"{len(VALID_TOPICS) + 1}. Back")
        
        choice = input(f"Enter your choice (1-{len(VALID_TOPICS) + 1}): ")
        try:
            choice = int(choice)
            if 1 <= choice <= len(VALID_TOPICS):
                show_leaderboard(VALID_TOPICS[choice - 1])
            elif choice == len(VALID_TOPICS) + 1:
                break
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a valid number.")

def main():
    user_id = None
    while not user_id:
        print("\n=== Quiz Application ===")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ")
        
        if choice == "1":
            user_id = login_user()
        elif choice == "2":
            register_user()
        elif choice == "3":
            print("Goodbye!")
            return
        else:
            print("Invalid choice.")
    
    while True:
        print("\n=== Main Menu ===")
        print("1. Take a quiz")
        print("2. Add new question")
        print("3. Leaderboards")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == "1":
            print(f"Available topics: {', '.join(VALID_TOPICS)}")
            topic = input("Enter the topic you want to be quizzed on: ").lower()
            take_quiz(user_id, topic)
        elif choice == "2":
            print(f"Available topics: {', '.join(VALID_TOPICS)}")
            topic = input("Enter the topic name: ").lower()
            add_question(topic)
        elif choice == "3":
            while True:
                print("\n=== Leaderboard Menu ===")
                print("1. Overall Leaderboard")
                print("2. Topic Leaderboards")
                print("3. Back")
                sub_choice = input("Enter your choice (1-3): ")
                
                if sub_choice == "1":
                    show_leaderboard()
                elif sub_choice == "2":
                    topic_leaderboard_menu(user_id)
                elif sub_choice == "3":
                    break
                else:
                    print("Invalid choice.")
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()