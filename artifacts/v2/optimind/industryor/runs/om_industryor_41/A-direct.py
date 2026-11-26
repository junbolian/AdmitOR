import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Pull all numeric parameters
    demandA = params["demandA"]
    demandB = params["demandB"]
    demandC = params["demandC"]

    supplyA_A = params["supplyA_A"]
    supplyA_B = params["supplyA_B"]
    supplyA_C = params["supplyA_C"]

    supplyB_A = params["supplyB_A"]
    supplyB_B = params["supplyB_B"]
    supplyB_C = params["supplyB_C"]

    costA = params["costA"]
    costB = params["costB"]

    # Build model
    model = pyo.ConcreteModel()

    # Decision variables: number of trucks from each warehouse (integer, nonnegative)
    model.xA = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.xB = pyo.Var(domain=pyo.NonNegativeIntegers)

    # Constraints
    model.cA = pyo.Constraint(
        expr=supplyA_A * model.xA + supplyB_A * model.xB >= demandA
    )
    model.cB = pyo.Constraint(
        expr=supplyA_B * model.xA + supplyB_B * model.xB >= demandB
    )
    model.cC = pyo.Constraint(
        expr=supplyA_C * model.xA + supplyB_C * model.xB >= demandC
    )

    # Objective: minimize total freight cost
    model.total_cost = pyo.Objective(
        expr=costA * model.xA + costB * model.xB,
        sense=pyo.minimize,
    )

    # Solve with HiGHS
    Highs().solve(model)

    # Retrieve objective; raises if not available (indicates failure/infeasibility)
    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}