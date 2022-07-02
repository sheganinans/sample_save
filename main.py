import binascii
import apsw
import base64
from fastapi import FastAPI, HTTPException
import hashlib
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()
con = apsw.Connection("samples.sqlite")


class Samples(BaseModel):
  vector: List[float]
  imgs: Dict[int, str]


cols, qs = ",".join([f"c{i+1}" for i in range(512)]), ",".join(["?" for _ in range(512)])
insert_into_vector = f"""insert into vector ({cols}) values ({qs})"""


@app.post("/sample")
async def sample(s: Samples):
  for seed, _ in s.imgs.items():
    if seed < 0 or seed > 18446744073709551615:  # sys.maxsize*2+1
      raise HTTPException(status_code=400, detail=f"A seed was either negative or too large.")
  if len(s.vector) != 512:
    raise HTTPException(status_code=400, detail=f"Expecting vector of length 512, got: {len(s.vector)}")
  try:
    imgs = {seed: base64.b64decode(img) for seed, img in s.imgs.items()}
  except binascii.Error:
    raise HTTPException(status_code=400, detail=f"An image's base64 encoding was malformed.")
  try:
    with con:
      con.cursor().execute(insert_into_vector, tuple(s.vector))
      vec_id = con.last_insert_rowid()
      for seed, img in imgs.items():
        md5 = hashlib.md5(base64.b64decode(img)).hexdigest()
        with open(f"./samples/{md5}.png", "wb") as f:
          f.write(img)
        con.cursor().execute("insert into sample (seed, md5, vector) values (?,?,?)", (seed, md5, vec_id))
    return {"ok": "!"}
  except Exception as e:
    with open("./err.log", "a+") as errs:
      errs.write(repr(e))
      errs.write("\n")
    print(e)
    raise e
