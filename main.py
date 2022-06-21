import apsw
import base64
from fastapi import FastAPI
import hashlib
from pydantic import BaseModel
import struct

app = FastAPI()
con = apsw.Connection("samples_v2.sqlite")


class Sample(BaseModel):
  seed: int
  vec: str
  img: str


@app.post("/sample")
async def sample(s: Sample):
  try:
    img = base64.b64decode(s.img)
    # TODO:
    #vec = base64.b64decode(s.vec)
    #vec = struct.unpack("f", vec)
    #if len(vec) != 512:
    #  raise Exception(f"Expecting length 512, got: {len(vec)}")
    #if not all([x >= -1. and x <= 1. for x in vec]):
    #  # TODO: Better error.
    #  raise Exception(f"Data Malformed.")
    md5 = hashlib.md5(img).hexdigest()
    with open(f"./samples/{md5}.png", "wb") as f:
      f.write(img)
    with con:
      con.cursor().execute(f"""insert into samples (seed, vector, md5) values \
                                ({s.seed},"{s.vec}","{md5}")""")
    return {"ok": "!"}
  except Exception as e:
    with open("./err.log", "a+") as errs:
      errs.write(str(e))
      errs.write("\n")
    s.img = ""
    return {"err": str(e), "sample": s}
