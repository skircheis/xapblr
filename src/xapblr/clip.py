import requests
from requests.exceptions import JSONDecodeError, RequestException
from json import loads, dumps
from PIL import Image
from tempfile import TemporaryFile
from re import compile, sub
from sys import stderr
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
        # self.transform = self.transform.to(self.device)

    def preprocess(self, p):
        im = Image.open(p).convert("RGB")
        im = self.transform(im).unsqueeze(0)
        im = im.to(self.device)
        return im

    def caption(self, p):
        with self.torch.no_grad(), self.torch.cuda.amp.autocast():
            im = self.preprocess(p)
            generated = self.model.generate(im, num_beam_groups=1)
        return self.open_clip.decode(generated[0])


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


def download_image(img):
    f = TemporaryFile()
    r = requests.get(img["url"])
    bs = int(len(r.content) / 1024)
    f.write(r.content)
    return (bs, f)


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

        for t in tasks:
            print(f"Downloading {t['url']}...", end="")
            (bs, t["file"]) = download_image(t)
            dt = int((time_ns() - start) / 10**6)
            print(f" done ({bs} KiB, {dt} ms). Generating caption... ", end=" ")
            start = time_ns()
            caption = cptnr.caption(t["file"])
            dt = int((time_ns() - start) / 10**6)
            caption = (
                caption[caption.index("<start_of_text>") + 15 :]
                .replace("<end_of_text>", "")
                .strip(" .")
            )
            if caption == "there is no image here to provide a caption for":
                caption = None
            print(f"Done: {caption} ({dt} ms).")
            t["caption"] = caption
            del t["file"]

        if len(tasks) > 0:
            submit_captions(args.endpoint, token, args.agent, tasks)

        if available - len(tasks) == 0:
            print(f"No more images in queue for now. Sleeping for {args.sleep} s.")
            sleep(args.sleep)
