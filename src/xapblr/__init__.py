from .args import argparser


def main():
    args = argparser.parse_args()
    args.func(args)
