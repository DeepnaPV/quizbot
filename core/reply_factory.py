
from .constants import BOT_WELCOME_MESSAGE, PYTHON_QUESTION_LIST


def generate_bot_responses(message, session):
    '''
    Generate bot responses for the quiz interaction.
    
    Args:
    - message (str): User's input message
    - session (dict): Django session object
    
    Returns:
    - list: Bot responses
    '''
    bot_responses = []
    
    # Check if this is the first interaction
    current_question_id = session.get("current_question_id")
    
    # If no question has been started yet, start with welcome message
    if current_question_id is None:
        bot_responses.append(BOT_WELCOME_MESSAGE)
        # Get the first question
        first_question, first_question_id = get_next_question(None)
        bot_responses.append(first_question)
        session["current_question_id"] = first_question_id
        session.save()
        return bot_responses
    
    # Process the user's answer to the current question
    success, error = record_current_answer(message, current_question_id, session)
    
    # If there's an error in recording the answer
    if not success:
        return [error]
    
    # Get the next question
    next_question, next_question_id = get_next_question(current_question_id)
    
    # If there's a next question, add it to responses
    if next_question:
        bot_responses.append(next_question)
        session["current_question_id"] = next_question_id
    else:
        # If no more questions, generate final response
        final_response = generate_final_response(session)
        bot_responses.append(final_response)
        # Reset the session
        session["current_question_id"] = None
    
    session.save()
    return bot_responses



def record_current_answer(answer, current_question_id, session):
    '''
    Validates and stores the answer for the current question to django session.
    
    Args:
    - answer (str): User's submitted answer
    - current_question_id (int): ID of the current question
    - session (dict): Django session object
    
    Returns:
    - tuple: (success boolean, error message)
    '''
    # If no current question, return error
    if current_question_id is None or current_question_id < 0:
        return False, "No active question"
    
    # Validate that the question exists in the list
    if current_question_id >= len(PYTHON_QUESTION_LIST):
        return False, "Invalid question ID"
    
    # Get the correct answer for the current question
    correct_answer = PYTHON_QUESTION_LIST[current_question_id]['answer']
    
    # Check if the user's answer matches the correct answer
    is_correct = str(answer).strip() == str(correct_answer).strip()
    
    # Store the answer details in the session
    if 'quiz_answers' not in session:
        session['quiz_answers'] = []
    
    session['quiz_answers'].append({
        'question_id': current_question_id,
        'user_answer': answer,
        'correct_answer': correct_answer,
        'is_correct': is_correct
    })
    
    return True, ""



def get_next_question(current_question_id):
    '''
    Fetches the next question from the PYTHON_QUESTION_LIST based on the current_question_id.
    
    Args:
    - current_question_id (int): ID of the current question
    
    Returns:
    - tuple: (next question text, next question ID)
    '''
    # If current_question_id is None, start from the first question
    if current_question_id is None:
        current_question_id = -1
    
    # Calculate the next question index
    next_question_id = current_question_id + 1
    
    # Check if there are more questions
    if next_question_id < len(PYTHON_QUESTION_LIST):
        # Get the next question details
        next_question = PYTHON_QUESTION_LIST[next_question_id]
        
        # Construct the question text with options
        question_text = next_question['question_text'] + "\n\nOptions:\n"
        for i, option in enumerate(next_question['options'], 1):
            question_text += f"{i}. {option}\n"
        
        return question_text, next_question_id
    
    # No more questions
    return None, -1

def generate_final_response(session):
    '''
    Creates a final result message including a score based on the user's answers.
    
    Args:
    - session (dict): Django session object
    
    Returns:
    - str: Final quiz result message
    '''
    # Check if quiz answers exist
    if 'quiz_answers' not in session or not session['quiz_answers']:
        return "No quiz answers found. Please complete the quiz."
    
    # Calculate score
    correct_answers = sum(1 for answer in session['quiz_answers'] if answer['is_correct'])
    total_questions = len(session['quiz_answers'])
    score_percentage = (correct_answers / total_questions) * 100
    
    # Prepare detailed result
    result_message = f"Quiz Completed!\n\n"
    result_message += f"Your Score: {correct_answers}/{total_questions} ({score_percentage:.2f}%)\n\n"
    
    # Add performance description
    if score_percentage == 100:
        result_message += "Excellent! Perfect score!"
    elif score_percentage >= 80:
        result_message += "Great job! You have a strong understanding of Python."
    elif score_percentage >= 60:
        result_message += "Good effort. You're on the right track with Python."
    else:
        result_message += "Keep studying. There's room for improvement in your Python skills."
    
    # Optional: Add detailed breakdown
    result_message += "\n\nDetailed Breakdown:"
    for i, answer in enumerate(session['quiz_answers'], 1):
        status = "✓" if answer['is_correct'] else "✗"
        result_message += f"\nQ{i}: {status} Your answer: {answer['user_answer']}"
    
    return result_message