def generate_proof(value, constraints):
    min_val = constraints.get("min_salary", 0)
    max_val = constraints.get("max_salary", 999999)
    if min_val <= value <= max_val:
        return {"proof": f"{value}-is-valid", "range": (min_val, max_val)}
    return None

def verify_proof(proof, value):
    if not proof:
        return False
    min_val, max_val = proof.get("range", (0, 0))
    return min_val <= value <= max_val
