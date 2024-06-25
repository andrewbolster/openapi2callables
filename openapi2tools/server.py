import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/pirate")
def pirate_endpoint():
    return "Arr, matey! Welcome to the pirate endpoint!"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
