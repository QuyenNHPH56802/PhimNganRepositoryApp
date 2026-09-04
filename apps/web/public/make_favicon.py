import base64, os

b64 = open(os.path.join(os.path.dirname(__file__), "favicon.b64")).read().strip()
ico = base64.b64decode(b64)
open(os.path.join(os.path.dirname(__file__), "favicon.ico"), "wb").write(ico)
print("Done: favicon.ico created")
