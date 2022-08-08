try:
    from xapblr_web import app

    def server(args):
        app.run(host = args.host, port = args.port, debug=args.debug)

except ModuleNotFoundError as e:
    missing_module = e.name
    def server(args):
        from sys import exit
        exit(f"xapblr: module {missing_module} is required for the web interface.")
