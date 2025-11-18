def format_result(r):
    if not r or r.get("status") == "no_data":
        return None

    result = r.get("result", r)

    return {
        "plant": result.get("plant"),
        "disease": result.get("disease"),
        "confidence": round(result.get("confidence", 0) * 100, 2),
        "infection": result.get("infection_percent"),
        "pesticide": result.get("pesticide"),
        "dose": result.get("dose_ml"),
    }
