from fastapi import FastAPI

app = FastAPI(
    title="ProjectHub",
    description="Role-based portal for managing college project teams",
    version="1.0.0"
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
