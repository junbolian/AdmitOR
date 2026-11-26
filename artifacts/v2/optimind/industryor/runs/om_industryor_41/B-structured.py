# IR: {"sets":{"warehouses":["A","B"],"materials":["A","B","C"]},"params":["demandA","demandB","demandC","supplyA_A","supplyA_B","supplyA_C","supplyB_A","supplyB_B","supplyB_C","costA","costB"],"variables":{"trucksA":"NonNegativeIntegers","trucksB":"NonNegativeIntegers"},"constraints":["supplyA_A*trucksA+supplyB_A*trucksB>=demandA","supplyA_B*trucksA+supplyB_B*trucksB>=demandB","supplyA_C*trucksA+supplyB_C*trucksB>=demandC"],"objective":{"sense":"minimize","expression":"costA*trucksA+costB*trucksB"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.warehouses = pyo.Set(initialize=["A", "B"])
    model.materials = pyo.Set(initialize=["A", "B", "C"])

    model.demandA = pyo.Param(initialize=params["demandA"])
    model.demandB = pyo.Param(initialize=params["demandB"])
    model.demandC = pyo.Param(initialize=params["demandC"])

    model.supplyA_A = pyo.Param(initialize=params["supplyA_A"])
    model.supplyA_B = pyo.Param(initialize=params["supplyA_B"])
    model.supplyA_C = pyo.Param(initialize=params["supplyA_C"])
    model.supplyB_A = pyo.Param(initialize=params["supplyB_A"])
    model.supplyB_B = pyo.Param(initialize=params["supplyB_B"])
    model.supplyB_C = pyo.Param(initialize=params["supplyB_C"])

    model.costA = pyo.Param(initialize=params["costA"])
    model.costB = pyo.Param(initialize=params["costB"])

    model.trucksA = pyo.Var(domain=pyo.NonNegativeIntegers)
    model.trucksB = pyo.Var(domain=pyo.NonNegativeIntegers)

    model.materialA_requirement = pyo.Constraint(
        expr=(
            model.supplyA_A * model.trucksA
            + model.supplyB_A * model.trucksB
            >= model.demandA
        )
    )
    model.materialB_requirement = pyo.Constraint(
        expr=(
            model.supplyA_B * model.trucksA
            + model.supplyB_B * model.trucksB
            >= model.demandB
        )
    )
    model.materialC_requirement = pyo.Constraint(
        expr=(
            model.supplyA_C * model.trucksA
            + model.supplyB_C * model.trucksB
            >= model.demandC
        )
    )

    model.total_cost = pyo.Objective(
        expr=model.costA * model.trucksA + model.costB * model.trucksB,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}