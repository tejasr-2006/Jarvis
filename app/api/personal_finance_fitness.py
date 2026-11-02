"""Phase 29: manual finance ledger and combined fitness/finance overview."""
from __future__ import annotations
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from app.security import require_jarvis_key
from app.finance.store import FinanceStore
from app.integrations.fitness_manager import FitnessManagerClient

router=APIRouter(prefix="/personal",tags=["Fitness & Finance"],dependencies=[Depends(require_jarvis_key)])

class TransactionInput(BaseModel):
    kind: Literal["income","expense"]
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    category: str = Field(min_length=1,max_length=80)
    description: str = Field(default="",max_length=500)
    transaction_date: date = Field(default_factory=date.today)
    @field_validator("currency")
    @classmethod
    def currency_upper(cls,v): return v.upper()
    @field_validator("category","description")
    @classmethod
    def strip_text(cls,v): return v.strip()

class BudgetInput(BaseModel):
    category: str = Field(min_length=1,max_length=80)
    amount: Decimal = Field(gt=0,max_digits=12,decimal_places=2)
    currency: str = Field(default="INR",min_length=3,max_length=3)
    month: str = Field(default_factory=lambda:date.today().strftime("%Y-%m"),pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    @field_validator("currency")
    @classmethod
    def currency_upper(cls,v): return v.upper()
    @field_validator("category")
    @classmethod
    def strip_category(cls,v): return v.strip()

def _minor(amount: Decimal) -> int:
    try: return int((amount*100).quantize(Decimal("1"),rounding=ROUND_HALF_UP))
    except (InvalidOperation,ValueError) as exc: raise ValueError("Invalid amount") from exc

@router.post("/finance/transactions",status_code=201)
async def add_transaction(body:TransactionInput):
    if not body.category: raise HTTPException(422,detail="Category cannot be blank.")
    try:
        return FinanceStore().add_transaction(body.kind,_minor(body.amount),body.currency,body.category,body.description,body.transaction_date.isoformat())
    except ValueError as exc: raise HTTPException(422,detail=str(exc)) from exc

@router.get("/finance/transactions")
async def list_transactions(month:str|None=Query(default=None,pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),limit:int=Query(100,ge=1,le=500)):
    return {"transactions":FinanceStore().list_transactions(month,limit)}

@router.delete("/finance/transactions/{transaction_id}")
async def delete_transaction(transaction_id:str):
    if not FinanceStore().delete_transaction(transaction_id):
        raise HTTPException(404,detail="Transaction not found.")
    return {"deleted":True,"id":transaction_id}

@router.post("/finance/budgets")
async def set_budget(body:BudgetInput):
    if not body.category.strip():raise HTTPException(422,detail="Category cannot be blank.")
    return FinanceStore().set_budget(body.category.strip(),_minor(body.amount),body.currency,body.month)

@router.get("/finance/summary")
async def finance_summary(month:str=Query(default_factory=lambda:date.today().strftime("%Y-%m"),pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),currency:str=Query("INR",min_length=3,max_length=3)):
    return FinanceStore().summary(month,currency.upper())

@router.get("/fitness-finance-overview")
async def fitness_finance_overview(month:str=Query(default_factory=lambda:date.today().strftime("%Y-%m"),pattern=r"^\d{4}-(0[1-9]|1[0-2])$")):
    finance=FinanceStore().summary(month,"INR")
    try:
        workouts=await FitnessManagerClient().get_workouts()
        if isinstance(workouts,dict):
            items=next((workouts[k] for k in ("workouts","items","data","results") if isinstance(workouts.get(k),list)),[])
        elif isinstance(workouts,list): items=workouts
        else: items=[]
        fitness={"status":"connected","workout_count":len(items),"recent_workouts":items[:10]}
    except Exception:
        fitness={"status":"unavailable","workout_count":None,"recent_workouts":[]}
    return {"month":month,"fitness":fitness,"finance":finance,
            "read_only_overview":True,
            "note":"Finance records are manually entered and stored locally. Fitness data is read from the connected Fitness Manager. No bank access or financial transactions are performed."}
