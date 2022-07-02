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
  if s.seed < 0 or s.seed > 18446744073709551615:  # sys.maxsize*2+1
    raise HTTPException(status_code=400, detail=f"Seed either negative or too large.")
  if len(s.vector) != 512:
    raise HTTPException(status_code=400, detail=f"Expecting vector of length 512, got: {len(s.vector)}")
  try:
    imgs = [base64.b64decode(img) for img in s.imgs]
  except binascii.Error:
    raise HTTPException(status_code=400, detail=f"An image's base64 encoding was malformed.")
  try:
    with con:
      con.execute(insert_into_vector, tuple(s.vector))
      vec_id = con.last_insert_rowid()
      for img in imgs:
        md5 = hashlib.md5(base64.b64decode(img)).hexdigest()
        with open(f"./samples/{md5}.png", "wb") as f:
          f.write(img)
        con.execute("insert into sample (seed, md5, vector) values (?,?,?)", (s.seed, md5, vec_id))
    return {"ok": "!"}
  except Exception as e:
    with open("./err.log", "a+") as errs:
      errs.write(repr(e))
      errs.write("\n")
    print(e)
    raise e
