from fastapi import FastAPI

app = FastAPI(
    title="SpectraX API",
    description=(
        "Explainable multimodal AI forensics platform "
        "for deepfake detection, provenance, and digital evidence."
    ),
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "name": "SpectraX",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "SpectraX API",
        "version": "0.1.0",
    }