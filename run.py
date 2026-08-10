from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import time
import subprocess

def fetch_blog(blog_url):
    process = subprocess.Popen([f'xapblr index {blog_url}'], stdout=subprocess.PIPE, text=True)
    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(line.rstrip(), flush=True)

def fetch_all_blogs():
    print(f"Starting fetch at {datetime.now().time().strftime('%H:%M:%S')}")

    # get blog urls list 
    with open('/home/xapblr/blogs.txt', 'r') as file:
    blog_urls = [line.strip() for line in file]


        fetch_blog(blog_url)

if __name__ == "__main__":
    # Perform inital fetch immediatly 
    fetch_all_blogs()

    # Create a BlockingScheduler instance
    scheduler = BlockingScheduler()

    # Refetch starting at midnight
    scheduler.add_job(fetch_all_blogs, 'cron', hour=0, minute=0)

    # Start the scheduler
    print("Starting Refresh Schedule...")
    scheduler.start() # This call will block

    # The code below will only be reached when the scheduler is shut down
    print("Scheduler stopped, this is an error.")