# open-subsurface-data, made 25 Nov 2026 for 3 datasets
# pip install "osd @ git+https://github.com/ophiolite-labs/open-subsurface-data"

import osd

mirrored = osd.get("fx/mirrored")    # 2 files from our mirror, checked
publisher = osd.get("fx/publisher")  # 1 file from the publisher, checked
signin = osd.get("fx/signin")        # sign-in needed: left out, sign in at https://origin.fixture.invalid/signin/

print(mirrored)
print(publisher)
print(signin)
