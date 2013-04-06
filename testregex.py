import re

def getEpisode2(filename):
    match = re.findall(r'(?i)(?P<seq>[0-9]+)', filename)
    if match:
        return match

def getEpisode(filename):
    match = re.search(
        r'''(?ix)                 # Ignore case (i), and use verbose regex (x)
        (?:s|season|\.|\s)(?P<season>\d{1,2})?  # season
	    (?:e|x|episode\s|^|\s)(?P<episode>\d{2})  # eps
        ''', filename)
    if match:
        return match.groups()

tests = (
    'Series Name s01e02.avi',
    'Series Name 1x01.avi',
    'Series Name episode 01.avi',
    '01 Episode Title.avi',
    '24.S08E10.HDTV.XviD-P0W4.avi'
    )
test2 = (
    'charlies.angels.2011.101.hdtv-lol.avi',
    'the.office.71112.hdtv-lol.avi'
)
for filename in tests:
    print(getEpisode(filename))