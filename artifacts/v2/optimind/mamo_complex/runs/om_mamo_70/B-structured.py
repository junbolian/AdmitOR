# IR: {"sets":{"clinics":"0..5","arcs":"(i,j) for distinct clinics i,j"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][i]","cost_matrix":"params['cost_matrix'][i][j]"},"variables":{"transfer[i,j]":"NonNegativeReals"},"constraints":["For every clinic i: supply[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) >= demand[i]."],"objective":"Minimize sum(cost_matrix[i][j] * transfer[i,j] for (i,j) in arcs)."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize transfer costs, allowing transshipment and retained surplus.

    Inputs are zero-based sequences: supply and demand have length six,
    and cost_matrix has six rows and six columns.
    """
    model = pyo.ConcreteModel()

    model.clinics = pyo.RangeSet(0, 5)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.clinics
            for j in model.clinics
            if i != j
        ],
    )

    model.initial_supply = pyo.Param(
        model.clinics,
        initialize=lambda mdl, i: params["supply"][i],
        within=pyo.NonNegativeReals,
    )
    model.required_demand = pyo.Param(
        model.clinics,
        initialize=lambda mdl, i: params["demand"][i],
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize=lambda mdl, i, j: params["cost_matrix"][i][j],
        within=pyo.NonNegativeReals,
    )

    model.transfer = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(mdl, i):
        incoming = sum(
            mdl.transfer[j, i] for j in mdl.clinics if j != i
        )
        outgoing = sum(
            mdl.transfer[i, j] for j in mdl.clinics if j != i
        )
        return (
            mdl.initial_supply[i] + incoming - outgoing
            >= mdl.required_demand[i]
        )

    model.clinic_balance = pyo.Constraint(
        model.clinics, rule=balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.transfer[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}