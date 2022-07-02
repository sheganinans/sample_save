import binascii
import apsw
import base64
from fastapi import FastAPI, HTTPException
import hashlib
from pydantic import BaseModel
from typing import List

app = FastAPI()
con = apsw.Connection("samples.sqlite")


class Sample(BaseModel):
  seed: int
  vector: List[float]
  img: str


@app.post("/sample")
async def sample(s: Sample):
  if s.seed < 0 or s.seed > 18446744073709551615:  # sys.maxsize*2+1
    raise HTTPException(status_code=400, detail=f"Seed either negative or too large.")
  if len(s.vector) != 512:
    raise HTTPException(status_code=400, detail=f"Expecting vector of length 512, got: {len(s.vector)}")
  # TODO: Normalize, preserve, or error?
  #if not all([x >= -1. and x <= 1. for x in s.vector]):
  #  raise HTTPException(status_code=400, detail=f"Vector not properly normalized.")
  try:
    img = base64.b64decode(s.img)
  except binascii.Error:
    raise HTTPException(status_code=400, detail="The image's base64 encoding was malformed.")
  try:
    md5 = hashlib.md5(img).hexdigest()
    with open(f"./samples/{md5}.png", "wb") as f:
      f.write(img)
    with con:
      con.cursor().execute("insert into samples (seed, vector, md5) values (?,?,?)", (s.seed, str(s.vector), md5))
    return {"ok": "!"}
  except Exception as e:
    with open("./err.log", "a+") as errs:
      errs.write(repr(e))
      errs.write("\n")
    print(e)
    raise e
