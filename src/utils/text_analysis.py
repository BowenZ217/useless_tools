
from .logger import log_message

def contains_keywords(text: str, keywords: list[str]=None) -> bool:
    """
    Function to check if the given text contains any of the specified keywords.
    Returns True if any keyword is found, otherwise False.

    :param text: The text to search for keywords.
    :param keywords: A list of keywords (string) to search for in the text.
    """
    if keywords is None:
        keywords = []
    return any(keyword in text for keyword in keywords)

def convert_number_to_range(num_str: str, step: int=50):
    """
    Convert a number represented as a string to a range string based on the specified step.
    
    :param num_str: The number as a string to be converted.
    :param step: The range size to group the numbers.
    :return: A string representing the range in which the number falls.
    """
    try:
        # Convert the string to an integer
        num = int(num_str)
        # Calculate the lower bound of the range
        lower_bound = (num // step) * step
        # If the number is exactly on a boundary, adjust the lower bound
        lower_bound = lower_bound if num % step != 0 else lower_bound - step
        # Correct lower bound for the case when num is 0
        lower_bound = max(lower_bound, 0) + 1
        # Calculate the upper bound of the range
        upper_bound = lower_bound + step - 1
    except ValueError:
        # Handle the case where the input is not a valid integer
        log_message("Invalid input", level="error")
        return "Error"
    except ZeroDivisionError:
        # Handle the case where the step is 0
        log_message("Step cannot be 0", level="error")
        return "Error"
    except Exception as e:
        # Handle any other exceptions that may occur
        log_message(f"Error: {e}", level="error")
        return "Error"
    return f"{lower_bound} - {upper_bound}"
