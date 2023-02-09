import argparse
from typing import Union


def get_argments():
    """
    """
    parser = argparse.ArgumentParser(description="Get the payload to analyze.")
    parser.add_argument(
        "--message",
        "-m",
        help="Give a payload message (type: str).",
        type=str,
        required=True
    )
    return parser.parse_args()


def analyze_msg(_msg: str):
    """
    """
    print(f"Analyze '{_msg}'...")
    print(f"Type: {type(_msg)}")
    print("Succeed")


if __name__ == '__main__':
    arguments = get_argments()
    analyze_msg(_msg=arguments.message)
