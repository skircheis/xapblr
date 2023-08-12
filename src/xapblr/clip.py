from asyncio import gather, run, to_thread
from PIL import Image
from queue import Queue
import requests
from requests.exceptions import JSONDecodeError, RequestException
from sys import stderr
from tempfile import TemporaryFile
from time import time, time_ns, sleep

from .config import config


class Captioner:
    def __init__(self):
        import torch

        self.torch = torch
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}.", end=" ")

        import open_clip

        self.open_clip = open_clip

        self.model, _, self.transform = open_clip.create_model_and_transforms(
            model_name="coca_ViT-L-14", pretrained="mscoco_finetuned_laion2B-s13B-b90k"
        )
        self.model = self.model.to(self.device)

        self.q = Queue()
        self.fs = Queue()

    async def process_batch(self, tasks):
        [self.q.put(t) for t in tasks]
        start = time_ns()
        threads = [
            to_thread(f)
            for f in [
                self.download_batch,
                self.caption_batch,
                self.q.join,
                self.fs.join,
            ]
            # We need the joins here to prevent a race condition where the queues become empty but processing has not finished
        ]
        tot_bs, tasks, _, _ = await gather(*threads)
        t = (time_ns() - start) / 10**9
        dtime, ctime = self.dtime / 10**9, self.ctime / 10**9
        print(
            f"Downloaded and captioned {len(tasks)} images ({int(tot_bs/1024)} KiB) in {t:.2f} s",
            end=" ",
        )
        print(f"({dtime:.2f} s downloading, {ctime:.2f} s captioning).")
        return tasks

    def download_batch(self):
        self.dtime = 0
        tot_bs = 0
        while not self.q.empty():
            t = self.q.get()
            print(f"Downloading {t['url']}...", end=" ", flush=True)
            start = time_ns()
            (bs, f) = self.download(t)
            t["file"] = f
            dt = time_ns() - start
            dt_ms = int(dt / 10**6)
            self.dtime += dt
            tot_bs += bs
            print(f"done ({int(bs/1024)} KiB, {dt_ms} ms).", flush=True)
            self.fs.put(t)
            self.q.task_done()
        return tot_bs

    def download(self, task):
        f = TemporaryFile()
        r = requests.get(task["url"])
        bs = len(r.content)
        f.write(r.content)
        return (bs, f)

    def caption_batch(self):
        self.ctime = 0
        results = []
        while not (self.fs.empty() and self.q.empty()):
            t = self.fs.get()
            print("Generating caption... ", end=" ", flush=True)
            start = time_ns()
            self.caption(t)
            dt = time_ns() - start
            dt_ms = int(dt / 10**6)
            self.ctime += dt
            results.append(t)
            self.fs.task_done()
            print(f"Done: {t['caption']} ({dt_ms} ms).", flush=True)
        return results

    def preprocess(self, p):
        im = Image.open(p).convert("RGB")
        im = self.transform(im).unsqueeze(0)
        im = im.to(self.device)
        return im

    def caption(self, t):
        with self.torch.no_grad(), self.torch.cuda.amp.autocast():
            im = self.preprocess(t["file"])
            generated = self.model.generate(im, num_beam_groups=1)
            caption = self.open_clip.decode(generated[0])
        caption = (
            caption[caption.index("<start_of_text>") + 15 :]
            .replace("<end_of_text>", "")
            .strip(" .")
        )
        if caption == "there is no image here to provide a caption for":
            caption = None
        t["caption"] = caption
        del t["file"]


def get_tasks(endpoint, token, agent):
    r = requests.get(
        endpoint,
        params={"auth_token": token, "agent": agent},
    )
    r.raise_for_status()
    try:
        data = r.json()
        return (data["available"], data["images"])
    except KeyError as e:
        raise ValueError(f"Invalid response from server: {e}")
    except JSONDecodeError as e:
        raise ValueError(f"Malformed JSON: {e}")


def submit_captions(endpoint, token, agent, tasks):
    data = {"auth_token": token, "agent": agent, "images": tasks}
    requests.post(endpoint, json=data)


def clip_cmd(args):
    start = time()
    print("Launching CLIP agent... ", end="", flush=True)
    cptnr = Captioner()
    dt = time() - start
    print(f"Loaded model onto GPU in {dt:.2f} s.")
    token = config["clip"]["auth_token"]
    while True:
        print("Fetching tasks...", end=" ")
        fetch_success = False
        try:
            (available, tasks) = get_tasks(args.endpoint, token, args.agent)
        except RequestException as e:
            print(f"Error fetching tasks: {e}.", file=stderr, end=" ")
        except ValueError as e:
            print(f"Bad response from server: {e}.", file=stderr, end=" ")
        else:
            print(
                f"There are {len(tasks)} tasks in this batch out of {available} total."
            )
            fetch_success = True

        if not fetch_success:
            print(f"Retrying in {args.sleep} s.", file=stderr)
            sleep(args.sleep)
            continue

        run(cptnr.process_batch(tasks))

        if len(tasks) > 0:
            submit_captions(args.endpoint, token, args.agent, tasks)

        if available - len(tasks) == 0:
            print(f"No more images in queue for now. Sleeping for {args.sleep} s.")
            sleep(args.sleep)
