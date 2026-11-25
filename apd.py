#!/usr/bin/python
import argparse
import re
from urllib.parse import parse_qs, urlparse

import progressbar
import requests as req

# TODO download file option
# TODO rename file after download from output file

APARAT_PLAYLIST_API = "https://www.aparat.com/api/fa/v1/video/playlist/one/playlist_id/{playlist_id}"
APARAT_VIDEO_API = "https://www.aparat.com/api/fa/v1/video/video/show/videohash/{uid}"


def usage():
    return """
        Use "" around link to avoid bad things :>
        apd.py "Link" [quality]
        python apd.py "https://www.aparat.com/playlist/1719118/"
        python apd.py "https://www.aparat.com/playlist/1719118/" -q 480

        The default quality is 480.
    """


def sanitize_filename(name: str) -> str:
    """Replace characters that are unsafe in shell/filenames."""
    return re.sub(r'[\\/:*?"<>|]+', "_", name).strip()


def extract_target(url: str) -> tuple[str, str]:
    """Return ('playlist', playlist_id) or ('video', video_uid) from an Aparat URL."""
    parsed = urlparse(url)
    query_playlist = parse_qs(parsed.query).get("playlist", [None])[0]
    if query_playlist:
        return "playlist", query_playlist

    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "playlist":
        return "playlist", parts[1]
    if len(parts) >= 2 and parts[0] == "v":
        return "video", parts[1]

    raise ValueError(f"Unsupported Aparat URL: {url}")


def select_video_url(file_links: list[dict], requested_quality: str) -> str | None:
    """Pick the download URL matching requested_quality, falling back to 480p or best available."""
    if not file_links:
        return None

    target = requested_quality.lower().rstrip("p")
    by_profile = {}
    for entry in file_links:
        urls = entry.get("urls") or []
        if not urls:
            continue
        profile = str(entry.get("profile", "")).lower().rstrip("p")
        by_profile[profile] = urls[0]

    if target in by_profile:
        return by_profile[target]
    if "480" in by_profile:
        return by_profile["480"]

    numeric_profiles = [(int(k), v) for k, v in by_profile.items() if k.isdigit()]
    if numeric_profiles:
        return max(numeric_profiles, key=lambda item: item[0])[1]

    return next(iter(by_profile.values()), None)


def fetch_playlist_videos(session: req.Session, playlist_id: str) -> tuple[str, list[str]]:
    """Fetch playlist title and ordered list of video UIDs."""
    resp = session.get(APARAT_PLAYLIST_API.format(playlist_id=playlist_id), timeout=30)
    resp.raise_for_status()
    payload = resp.json()

    data = payload.get("data") or {}
    title = (data.get("attributes") or {}).get("title") or f"playlist_{playlist_id}"

    included_videos = {
        item["id"]: item
        for item in payload.get("included", [])
        if item.get("type") == "Video"
    }

    rel_items = ((data.get("relationships") or {}).get("video") or {}).get("data") or []
    uids = []
    for rel in rel_items:
        video = included_videos.get(rel.get("id"))
        uid = ((video or {}).get("attributes") or {}).get("uid")
        if uid:
            uids.append(uid)

    if not uids:
        for video in included_videos.values():
            uid = (video.get("attributes") or {}).get("uid")
            if uid:
                uids.append(uid)

    return title, uids


def fetch_video_download(session: req.Session, uid: str, requested_quality: str) -> tuple[str, str | None]:
    """Fetch video title and download URL for a given video UID."""
    resp = session.get(APARAT_VIDEO_API.format(uid=uid), timeout=30)
    resp.raise_for_status()
    attrs = (resp.json().get("data") or {}).get("attributes") or {}
    title = attrs.get("title") or uid
    url = select_video_url(attrs.get("file_link_all") or [], requested_quality)
    return title, url


def main(link: str, quality: str):
    print("Please wait...")
    target_type, target_id = extract_target(link)

    with req.Session() as session:
        if target_type == "playlist":
            playlist_title, video_uids = fetch_playlist_videos(session, target_id)
            print(f"Playlist: {playlist_title}")
        else:
            video_uids = [target_id]

        count = len(video_uids)
        print(f"This playlist contains {count} videos")
        if count == 0:
            return

        bar = progressbar.ProgressBar(
            maxval=count,
            widgets=[progressbar.Bar("=", "[", "]"), progressbar.Percentage()],
        )
        bar.start()

        links = []
        for index, uid in enumerate(video_uids):
            bar.update(index + 1)
            name, video_url = fetch_video_download(session, uid, quality)
            if video_url:
                links.append((name, video_url))
            else:
                print(f"\nWarning: no download link found for {name} ({uid})")
        bar.finish()

    print("writing download list ...")
    with open("apd_output.sh", "w", encoding="utf-8") as file:
        file.write("#!/bin/bash\n")
        for i, (name, video_link) in enumerate(links, start=1):
            safe_name = sanitize_filename(name)
            file.write(f'aria2c -x16 -s16 -k1M "{video_link}" -o "{i:03d}_{safe_name}.mp4"\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aparat Playlist Downloader(APD)", usage=usage())
    parser.add_argument("link", help="main page Link")
    parser.add_argument("-q", "--quality", help="eg: [144, 240, 360, 480, 720, ...]", default="480")

    args = parser.parse_args()
    main(args.link, args.quality)

