import re

PATTERNS = {
    "Google Meet": [r'https?://meet\.google\.com/[a-z\-]+'],
    "Zoom":        [r'https?://[\w-]+\.zoom\.us/j/\d+[\S]*'],
    "Microsoft Teams": [r'https?://teams\.microsoft\.com/l/meetup-join/[\S]+'],
}

def extract_meeting_links(text):
    found = []
    seen = set()
    clean = re.sub(r'<[^>]+>', ' ', text)
    for platform, patterns in PATTERNS.items():
        for p in patterns:
            for match in re.findall(p, clean, re.IGNORECASE):
                link = match.rstrip('.,;)')
                if link not in seen:
                    seen.add(link)
                    found.append({"link": link, "platform": platform})
    return found

def detect_platform(link):
    if "meet.google.com" in link: return "Google Meet"
    if "zoom.us" in link:         return "Zoom"
    if "teams.microsoft.com" in link: return "Microsoft Teams"
    return "Unknown"