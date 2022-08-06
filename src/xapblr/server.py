from xapblr_web import app

def server(args):
    app.run(host = args.host, port = args.port, debug=args.debug)
    #raise NotImplementedError
