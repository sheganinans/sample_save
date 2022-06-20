import apsw
import base64
from fastapi import FastAPI
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
  try:
    img = base64.b64decode(s.img)
    md5 = hashlib.md5(img).hexdigest()
    with open(f"./samples/{md5}.png", "wb") as f:
      f.write(img)
    with con:
      con.cursor().execute(f"""insert into samples (seed, vector, md5) values \
                                ({s.seed},"{str(s.vector)}","{md5}")""")
    return {"ok": "!"}
  except Exception as e:
    with open("./err.log", "a+") as errs:
      errs.write(str(e))
      errs.write("\n")
    return {"err": str(e)}
