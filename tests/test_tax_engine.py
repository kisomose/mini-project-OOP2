from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any


# ==========================================
# 1. EXCEPTION HIERARCHY
# ==========================================

class TaxError(Exception):
    """Base exception for all tax engine errors."""
    pass


class InvalidIncomeError(TaxError):
    """Raised when income or financial amount is negative or structurally invalid."""
    pass


class NoScheduleForDateError(TaxError):
    """Raised when no statutory tax schedule exists for the requested tax year/date."""
    pass


# ==========================================
# 2. MONEY VALUE OBJECT
# ==========================================

class Money:
    """Immutable Value Object representing an amount in Ugandan Shillings (UGX).
    
    Strictly uses decimal.Decimal with ROUND_HALF_UP precision rules.
    """
    CURRENCY = "UGX"

    def __init__(self, amount: Any):
        if isinstance(amount, float):
            amount = str(amount)
        
        try:
            val = Decimal(amount)
        except Exception as e:
            raise InvalidIncomeError(f"Invalid monetary value: {amount}") from e

        self.amount = val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount + other.amount)

    def __sub__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        return Money(self.amount - other.amount)

    def __mul__(self, factor: Any) -> "Money":
        if isinstance(factor, Money):
            return NotImplemented
        if isinstance(factor, float):
            factor = str(factor)
        return Money(self.amount * Decimal(factor))

    def __rmul__(self, factor: Any) -> "Money":
        return self.__mul__(factor)

    def __lt__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount <= other.amount

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount

    def __repr__(self) -> str:
        return f"UGX {self.amount:,.2f}"


# ==========================================
# 3. ABSTRACTION & TAX CONTEXT
# ==========================================

@dataclass(frozen=True)
class TaxContext:
    amount: Money
    allowances: Money = field(default_factory=lambda: Money("0"))
    lst_deduction: Money = field(default_factory=lambda: Money("0"))
    is_resident: bool = True
    tax_year: int = 2026
    supply_type: str = "standard"
    is_input: bool = False


@dataclass(frozen=True)
class TaxResult:
    tax_name: str
    taxable_base: Money
    tax_payable: Money
    metadata: Dict[str, Any]


class Tax(ABC):
    """Abstract Base Class for all tax engines under URA statutory rules."""

    @abstractmethod
    def calculate(self, ctx: TaxContext) -> TaxResult:
        """Calculates tax based on the supplied TaxContext."""
        pass


# ==========================================
# 4. STATUTORY CALCULATORS
# ==========================================

class PAYETax(Tax):
    """Computes PAYE tax using Decimal precision and statutory context."""

    def calculate(self, ctx: TaxContext) -> TaxResult:
        if ctx.tax_year < 1997:
            raise NoScheduleForDateError(f"No PAYE schedule available for tax year {ctx.tax_year}.")

        income = ctx.amount
        if income < Money("0"):
            raise InvalidIncomeError("Taxable income cannot be negative.")

        zero = Money("0")
        b1 = Money("335000")
        b2 = Money("410000")
        b3 = Money("485000")
        b4 = Money("10000000")

        if ctx.is_resident:
            if income <= b1:
                tax = zero
            elif income <= b2:
                tax = (income - b1) * "0.20"
            elif income <= b3:
                tax = Money("15000") + (income - b2) * "0.25"
            elif income <= b4:
                tax = Money("33750") + (income - b3) * "0.30"
            else:
                base_tax = Money("33750") + (b4 - b3) * "0.30"
                surcharge = (income - b4) * "0.40"
                tax = base_tax + surcharge
        else:
            if income <= b1:
                tax = income * "0.10"
            elif income <= b2:
                tax = Money("33500") + (income - b1) * "0.20"
            elif income <= b3:
                tax = Money("48500") + (income - b2) * "0.25"
            elif income <= b4:
                tax = Money("67250") + (income - b3) * "0.30"
            else:
                base_tax = Money("67250") + (b4 - b3) * "0.30"
                surcharge = (income - b4) * "0.40"
                tax = base_tax + surcharge

        return TaxResult(
            tax_name="PAYE",
            taxable_base=income,
            tax_payable=tax,
            metadata={"is_resident": ctx.is_resident, "tax_year": ctx.tax_year}
        )


class NSSFContribution(Tax):
    """Computes NSSF contributions using Decimal precision."""

    def calculate(self, ctx: TaxContext) -> TaxResult:
        if ctx.amount < Money("0"):
            raise InvalidIncomeError("Gross income for NSSF cannot be negative.")

        ee_contrib = ctx.amount * "0.05"
        er_contrib = ctx.amount * "0.10"

        return TaxResult(
            tax_name="NSSF",
            taxable_base=ctx.amount,
            tax_payable=ee_contrib,
            metadata={"employer_contribution": er_contrib}
        )


# ==========================================
# 5. EXTENSION B: TAX PLANNER
# ==========================================

@dataclass(frozen=True)
class RemunerationScenario:
    name: str
    gross_amount: Money
    is_salary: bool
    lst_deduction: Money = field(default_factory=lambda: Money("0"))
    is_resident: bool = True


@dataclass(frozen=True)
class TaxComparisonReport:
    scenario_a: RemunerationScenario
    scenario_b: RemunerationScenario
    tax_paid_a: Money
    net_received_a: Money
    tax_paid_b: Money
    net_received_b: Money
    tax_difference: Money
    net_difference: Money
    recommended_scenario: str


class TaxPlanner:
    """Compares compensation scenarios (Salary vs Dividend) under URA rules."""

    DIVIDEND_WHT_RATE = "0.15"

    def __init__(self, paye_calculator: Optional[PAYETax] = None, nssf_calculator: Optional[NSSFContribution] = None):
        self.paye_calculator = paye_calculator or PAYETax()
        self.nssf_calculator = nssf_calculator or NSSFContribution()

    def _calculate_scenario_tax(self, scenario: RemunerationScenario) -> Dict[str, Money]:
        if scenario.gross_amount < Money("0"):
            raise InvalidIncomeError("Gross scenario amount cannot be negative.")

        if scenario.is_salary:
            lst = scenario.lst_deduction
            nssf_res = self.nssf_calculator.calculate(TaxContext(amount=scenario.gross_amount))
            nssf_ee = nssf_res.tax_payable

            taxable_base = max(Money("0"), scenario.gross_amount - lst - nssf_ee)
            paye_res = self.paye_calculator.calculate(
                TaxContext(amount=taxable_base, is_resident=scenario.is_resident)
            )
            paye_tax = paye_res.tax_payable

            total_statutory = lst + nssf_ee + paye_tax
            net_received = scenario.gross_amount - total_statutory

            return {
                "total_tax": paye_tax,
                "total_statutory_deductions": total_statutory,
                "net_received": net_received,
            }
        else:
            wht_tax = scenario.gross_amount * self.DIVIDEND_WHT_RATE
            net_received = scenario.gross_amount - wht_tax

            return {
                "total_tax": wht_tax,
                "total_statutory_deductions": wht_tax,
                "net_received": net_received,
            }

    def compare(self, scenario_a: RemunerationScenario, scenario_b: RemunerationScenario) -> TaxComparisonReport:
        res_a = self._calculate_scenario_tax(scenario_a)
        res_b = self._calculate_scenario_tax(scenario_b)

        tax_diff = Money(abs((res_a["total_statutory_deductions"] - res_b["total_statutory_deductions"]).amount))
        net_diff = Money(abs((res_a["net_received"] - res_b["net_received"]).amount))

        if res_a["net_received"] > res_b["net_received"]:
            rec = f"'{scenario_a.name}' yields higher net income by {net_diff}."
        elif res_b["net_received"] > res_a["net_received"]:
            rec = f"'{scenario_b.name}' yields higher net income by {net_diff}."
        else:
            rec = "Both scenarios yield identical net income."

        return TaxComparisonReport(
            scenario_a=scenario_a,
            scenario_b=scenario_b,
            tax_paid_a=res_a["total_statutory_deductions"],
            net_received_a=res_a["net_received"],
            tax_paid_b=res_b["total_statutory_deductions"],
            net_received_b=res_b["net_received"],
            tax_difference=tax_diff,
            net_difference=net_diff,
            recommended_scenario=rec,
        )