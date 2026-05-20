"""
Life module APIs for wedding, insurance, vehicle, fitness, documents and housing.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


def get_db():
    from backend.main import get_db_manager
    return get_db_manager()


class WeddingItemCreate(BaseModel):
    item_type: str
    title: str
    description: str = ""
    owner: str = ""
    planned_amount: float = 0
    amount: float = 0
    status: str = "todo"
    item_date: str = ""
    family_id: str = ""


class InsurancePolicyCreate(BaseModel):
    record_type: str = "policy"
    name: str
    title: str = ""
    holder: str = ""
    company: str = ""
    coverage: str = ""
    premium: float = 0
    amount: float = 0
    renew_date: str = ""
    status: str = "有效"
    note: str = ""
    family_id: str = ""


class VehicleRecordCreate(BaseModel):
    record_type: str
    title: str
    plate: str = ""
    model: str = ""
    mileage: float = 0
    amount: float = 0
    record_date: str = ""
    status: str = ""
    note: str = ""
    family_id: str = ""


class FitnessRecordCreate(BaseModel):
    record_type: str
    title: str
    record_date: str = ""
    duration: float = 0
    calories: float = 0
    protein: float = 0
    weight: float = 0
    body_fat: float = 0
    waist: float = 0
    status: str = ""
    note: str = ""
    family_id: str = ""


class DocumentRecordCreate(BaseModel):
    doc_type: str
    title: str
    holder: str = ""
    number: str = ""
    issuer: str = ""
    issue_date: str = ""
    expiry_date: str = ""
    reminder_days: int = 30
    status: str = "有效"
    note: str = ""
    family_id: str = ""


class HousingRecordCreate(BaseModel):
    record_type: str
    title: str
    location: str = ""
    owner: str = ""
    amount: float = 0
    due_date: str = ""
    status: str = ""
    note: str = ""
    family_id: str = ""


class HealthRecordCreate(BaseModel):
    record_type: str
    title: str
    record_date: str = ""
    provider: str = ""
    dosage: str = ""
    frequency: str = ""
    weight: float = 0
    bp_systolic: float = 0
    bp_diastolic: float = 0
    next_visit: str = ""
    status: str = ""
    note: str = ""
    family_id: str = ""


class TravelRecordCreate(BaseModel):
    record_type: str
    title: str
    destination: str = ""
    companion: str = ""
    provider: str = ""
    travel_date: str = ""
    end_date: str = ""
    amount: float = 0
    status: str = ""
    note: str = ""
    family_id: str = ""


class ChoreRecordCreate(BaseModel):
    record_type: str
    title: str
    assignee: str = ""
    frequency: str = ""
    due_date: str = ""
    points: float = 0
    status: str = ""
    note: str = ""
    family_id: str = ""


@router.get("/modules/wedding")
def list_wedding_items(family_id: str = ""):
    db = get_db()
    return {"items": db.get_wedding_items(family_id=family_id) if db else []}


@router.post("/modules/wedding")
def add_wedding_item(data: WeddingItemCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    payload = data.model_dump()
    return {"success": True, "id": db.add_wedding_item(**payload)}


@router.put("/modules/wedding/{item_id}")
def update_wedding_item(item_id: int, data: WeddingItemCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    payload = data.model_dump()
    return {"success": db.update_wedding_item(item_id, **payload)}


@router.delete("/modules/wedding/{item_id}")
def delete_wedding_item(item_id: int, family_id: str = ""):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.delete_wedding_item(item_id, family_id=family_id)}


@router.get("/modules/wedding/stats")
def wedding_stats(family_id: str = ""):
    db = get_db()
    items = db.get_wedding_items(family_id=family_id) if db else []
    budget_items = [item for item in items if item.get("item_type") == "budget"]
    return {
        "total_items": len(items),
        "timeline_count": sum(1 for item in items if item.get("item_type") == "timeline"),
        "budget_count": sum(1 for item in items if item.get("item_type") == "budget"),
        "vendor_count": sum(1 for item in items if item.get("item_type") == "vendor"),
        "todo_count": sum(1 for item in items if item.get("item_type") == "todo"),
        "budget_total": round(sum(float(item.get("planned_amount") or 0) for item in budget_items), 2),
        "spent_total": round(sum(float(item.get("amount") or 0) for item in budget_items), 2),
    }


@router.get("/modules/insurance")
def list_policies(family_id: str = ""):
    db = get_db()
    return {"items": db.get_insurance_policies(family_id=family_id) if db else []}


@router.post("/modules/insurance")
def add_policy(data: InsurancePolicyCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": True, "id": db.add_insurance_policy(**data.model_dump())}


@router.put("/modules/insurance/{policy_id}")
def update_policy(policy_id: int, data: InsurancePolicyCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.update_insurance_policy(policy_id, **data.model_dump())}


@router.delete("/modules/insurance/{policy_id}")
def delete_policy(policy_id: int, family_id: str = ""):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.delete_insurance_policy(policy_id, family_id=family_id)}


@router.get("/modules/insurance/stats")
def insurance_stats(family_id: str = ""):
    db = get_db()
    items = db.get_insurance_policies(family_id=family_id) if db else []
    policies = [item for item in items if (item.get("record_type") or "policy") == "policy"]
    claims = [item for item in items if item.get("record_type") == "claim"]
    reminders = [item for item in items if item.get("record_type") == "reminder"]
    expiring = sum(1 for item in policies if item.get("renew_date"))
    return {
        "policy_count": len(policies),
        "claim_count": len(claims),
        "reminder_count": len(reminders),
        "expiring_count": expiring,
        "annual_premium": round(sum(float(item.get("premium") or 0) for item in policies), 2),
        "claim_amount": round(sum(float(item.get("amount") or 0) for item in claims), 2),
    }


@router.get("/modules/vehicle")
def list_vehicle_records(family_id: str = ""):
    db = get_db()
    return {"items": db.get_vehicle_records(family_id=family_id) if db else []}


@router.post("/modules/vehicle")
def add_vehicle_record(data: VehicleRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": True, "id": db.add_vehicle_record(**data.model_dump())}


@router.put("/modules/vehicle/{record_id}")
def update_vehicle_record(record_id: int, data: VehicleRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.update_vehicle_record(record_id, **data.model_dump())}


@router.delete("/modules/vehicle/{record_id}")
def delete_vehicle_record(record_id: int, family_id: str = ""):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.delete_vehicle_record(record_id, family_id=family_id)}


@router.get("/modules/vehicle/stats")
def vehicle_stats(family_id: str = ""):
    db = get_db()
    items = db.get_vehicle_records(family_id=family_id) if db else []
    return {
        "vehicle_count": sum(1 for item in items if item.get("record_type") == "vehicle"),
        "service_count": sum(1 for item in items if item.get("record_type") == "service"),
        "expense_total": round(sum(float(item.get("amount") or 0) for item in items if item.get("record_type") == "expense"), 2),
        "record_count": len(items),
    }


@router.get("/modules/fitness")
def list_fitness_records(family_id: str = ""):
    db = get_db()
    return {"items": db.get_fitness_records(family_id=family_id) if db else []}


@router.post("/modules/fitness")
def add_fitness_record(data: FitnessRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": True, "id": db.add_fitness_record(**data.model_dump())}


@router.put("/modules/fitness/{record_id}")
def update_fitness_record(record_id: int, data: FitnessRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.update_fitness_record(record_id, **data.model_dump())}


@router.delete("/modules/fitness/{record_id}")
def delete_fitness_record(record_id: int, family_id: str = ""):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.delete_fitness_record(record_id, family_id=family_id)}


@router.get("/modules/fitness/stats")
def fitness_stats(family_id: str = ""):
    db = get_db()
    items = db.get_fitness_records(family_id=family_id) if db else []
    workouts = [item for item in items if item.get("record_type") == "workout"]
    metrics = [item for item in items if item.get("record_type") == "metric"]
    meals = [item for item in items if item.get("record_type") == "meal"]
    avg_weight = round(sum(float(item.get("weight") or 0) for item in metrics) / len(metrics), 1) if metrics else 0
    calories_today = round(sum(float(item.get("calories") or 0) for item in meals), 2)
    return {
        "workout_count": len(workouts),
        "metric_count": len(metrics),
        "meal_count": len(meals),
        "avg_weight": avg_weight,
        "calories_today": calories_today,
        "protein_today": round(sum(float(item.get("protein") or 0) for item in meals), 2),
    }


@router.get("/modules/documents")
def list_document_records(family_id: str = ""):
    db = get_db()
    return {"items": db.get_document_records(family_id=family_id) if db else []}


@router.post("/modules/documents")
def add_document_record(data: DocumentRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": True, "id": db.add_document_record(**data.model_dump())}


@router.put("/modules/documents/{record_id}")
def update_document_record(record_id: int, data: DocumentRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.update_document_record(record_id, **data.model_dump())}


@router.delete("/modules/documents/{record_id}")
def delete_document_record(record_id: int, family_id: str = ""):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.delete_document_record(record_id, family_id=family_id)}


@router.get("/modules/documents/stats")
def document_stats(family_id: str = ""):
    db = get_db()
    items = db.get_document_records(family_id=family_id) if db else []
    today = datetime.now().date()

    def parse_date(value: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None

    expiring_soon = 0
    expired = 0
    active = 0

    for item in items:
        expiry = parse_date(item.get("expiry_date") or "")
        reminder_days = int(item.get("reminder_days") or 30)
        if not expiry:
            active += 1
            continue
        if expiry < today:
            expired += 1
        else:
            active += 1
            if (expiry - today).days <= reminder_days:
                expiring_soon += 1

    return {
        "total_count": len(items),
        "active_count": active,
        "expiring_soon_count": expiring_soon,
        "expired_count": expired,
    }


@router.get("/modules/housing")
def list_housing_records(family_id: str = ""):
    db = get_db()
    return {"items": db.get_housing_records(family_id=family_id) if db else []}


@router.post("/modules/housing")
def add_housing_record(data: HousingRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": True, "id": db.add_housing_record(**data.model_dump())}


@router.put("/modules/housing/{record_id}")
def update_housing_record(record_id: int, data: HousingRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.update_housing_record(record_id, **data.model_dump())}


@router.delete("/modules/housing/{record_id}")
def delete_housing_record(record_id: int, family_id: str = ""):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.delete_housing_record(record_id, family_id=family_id)}


@router.get("/modules/housing/stats")
def housing_stats(family_id: str = ""):
    db = get_db()
    items = db.get_housing_records(family_id=family_id) if db else []
    today = datetime.now().date()

    def parse_date(value: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None

    return {
        "total_count": len(items),
        "property_count": sum(1 for item in items if item.get("record_type") == "property"),
        "rent_count": sum(1 for item in items if item.get("record_type") == "rent"),
        "utility_count": sum(1 for item in items if item.get("record_type") == "utility"),
        "repair_count": sum(1 for item in items if item.get("record_type") == "repair"),
        "total_amount": round(sum(float(item.get("amount") or 0) for item in items), 2),
        "due_soon_count": sum(
            1
            for item in items
            if (due := parse_date(item.get("due_date") or "")) and 0 <= (due - today).days <= 7
        ),
        "overdue_count": sum(
            1
            for item in items
            if (due := parse_date(item.get("due_date") or "")) and due < today
        ),
    }


@router.get("/modules/health")
def list_health_records(family_id: str = ""):
    db = get_db()
    return {"items": db.get_health_records(family_id=family_id) if db else []}


@router.post("/modules/health")
def add_health_record(data: HealthRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": True, "id": db.add_health_record(**data.model_dump())}


@router.put("/modules/health/{record_id}")
def update_health_record(record_id: int, data: HealthRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.update_health_record(record_id, **data.model_dump())}


@router.delete("/modules/health/{record_id}")
def delete_health_record(record_id: int, family_id: str = ""):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.delete_health_record(record_id, family_id=family_id)}


@router.get("/modules/health/stats")
def health_stats(family_id: str = ""):
    db = get_db()
    items = db.get_health_records(family_id=family_id) if db else []
    today = datetime.now().date()

    def parse_date(value: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None

    return {
        "total_count": len(items),
        "exam_count": sum(1 for item in items if item.get("record_type") == "exam"),
        "medication_count": sum(1 for item in items if item.get("record_type") == "medication"),
        "followup_count": sum(1 for item in items if item.get("record_type") == "followup"),
        "chronic_count": sum(1 for item in items if item.get("record_type") == "chronic"),
        "abnormal_count": sum(1 for item in items if item.get("record_type") == "exam" and item.get("status") == "异常"),
        "due_soon_count": sum(
            1
            for item in items
            if (visit := parse_date(item.get("next_visit") or "")) and 0 <= (visit - today).days <= 14
        ),
        "overdue_count": sum(
            1
            for item in items
            if (visit := parse_date(item.get("next_visit") or "")) and visit < today
        ),
    }


@router.get("/modules/travel")
def list_travel_records(family_id: str = ""):
    db = get_db()
    return {"items": db.get_travel_records(family_id=family_id) if db else []}


@router.post("/modules/travel")
def add_travel_record(data: TravelRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": True, "id": db.add_travel_record(**data.model_dump())}


@router.put("/modules/travel/{record_id}")
def update_travel_record(record_id: int, data: TravelRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.update_travel_record(record_id, **data.model_dump())}


@router.delete("/modules/travel/{record_id}")
def delete_travel_record(record_id: int, family_id: str = ""):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.delete_travel_record(record_id, family_id=family_id)}


@router.get("/modules/travel/stats")
def travel_stats(family_id: str = ""):
    db = get_db()
    items = db.get_travel_records(family_id=family_id) if db else []
    today = datetime.now().date()

    def parse_date(value: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None

    return {
        "total_count": len(items),
        "itinerary_count": sum(1 for item in items if item.get("record_type") == "itinerary"),
        "booking_count": sum(1 for item in items if item.get("record_type") == "booking"),
        "budget_count": sum(1 for item in items if item.get("record_type") == "budget"),
        "packing_count": sum(1 for item in items if item.get("record_type") == "packing"),
        "budget_total": round(sum(float(item.get("amount") or 0) for item in items if item.get("record_type") == "budget"), 2),
        "upcoming_count": sum(
            1
            for item in items
            if item.get("record_type") == "itinerary"
            and (travel_date := parse_date(item.get("travel_date") or ""))
            and 0 <= (travel_date - today).days <= 30
        ),
    }


@router.get("/modules/chores")
def list_chore_records(family_id: str = ""):
    db = get_db()
    return {"items": db.get_chore_records(family_id=family_id) if db else []}


@router.post("/modules/chores")
def add_chore_record(data: ChoreRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": True, "id": db.add_chore_record(**data.model_dump())}


@router.put("/modules/chores/{record_id}")
def update_chore_record(record_id: int, data: ChoreRecordCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.update_chore_record(record_id, **data.model_dump())}


@router.delete("/modules/chores/{record_id}")
def delete_chore_record(record_id: int, family_id: str = ""):
    db = get_db()
    if not db:
        raise HTTPException(status_code=503, detail="数据库不可用")
    return {"success": db.delete_chore_record(record_id, family_id=family_id)}


@router.get("/modules/chores/stats")
def chore_stats(family_id: str = ""):
    db = get_db()
    items = db.get_chore_records(family_id=family_id) if db else []
    today = datetime.now().date()

    def parse_date(value: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None

    return {
        "total_count": len(items),
        "task_count": sum(1 for item in items if item.get("record_type") == "task"),
        "rotation_count": sum(1 for item in items if item.get("record_type") == "rotation"),
        "supply_count": sum(1 for item in items if item.get("record_type") == "supply"),
        "checklist_count": sum(1 for item in items if item.get("record_type") == "checklist"),
        "done_count": sum(1 for item in items if item.get("status") in {"已完成", "已打卡", "已补货"}),
        "overdue_count": sum(
            1
            for item in items
            if (due_date := parse_date(item.get("due_date") or "")) and due_date < today and item.get("status") not in {"已完成", "已打卡", "已补货"}
        ),
        "points_total": round(sum(float(item.get("points") or 0) for item in items), 2),
    }
