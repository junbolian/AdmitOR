# IR: {"sets":{"I":"0..5","J":"0..5"},"params":{"supply":"supply[i] from params['supply']","demand":"demand[j] from params['demand']","cost":"cost[i,j] from params['cost']","capacity":"capacity[i,j] from params['capacity']"},"variables":{"x[i,j]":"nonnegative continuous shipment"},"constraints":["sum(j in J) x[i,j] = supply[i] for each i in I","sum(i in I) x[i,j] = demand[j] for each j in J","x[i,j] <= capacity[i,j] for each (i,j) in I x J"],"objective":"minimize sum(i in I,j in J) cost[i,j]*x[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.I, initialize=lambda mdl, i: supply[i]
    )
    model.demand = pyo.Param(
        model.J, initialize=lambda mdl, j: demand[j]
    )
    model.cost = pyo.Param(
        model.I, model.J, initialize=lambda mdl, i, j: cost[i][j]
    )
    model.capacity = pyo.Param(
        model.I, model.J, initialize=lambda mdl, i, j: capacity[i][j]
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    model.supply_balance = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in mdl.J)
        == mdl.supply[i],
    )
    model.demand_balance = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in mdl.I)
        == mdl.demand[j],
    )
    model.route_capacity = pyo.Constraint(
        model.I,
        model.J,
        rule=lambda mdl, i, j: mdl.x[i, j] <= mdl.capacity[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}