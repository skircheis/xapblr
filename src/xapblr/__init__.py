def main():
    from .args import argparser
    args = argparser.parse_args()
    args.func(args)
