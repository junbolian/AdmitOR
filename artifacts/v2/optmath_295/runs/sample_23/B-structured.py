# IR: {"sets":{"I":[0,1,2,3,4,5],"J":[0,1,2,3]},"params":{"availability":"availability[i] from params['availability']","demand":"demand[j] from params['demand']","capability":"capability[i,j] from params['capability'][i][j]","cost":"cost[i,j] from params['cost'][i][j]"},"variables":{"x[i,j]":"nonnegative integer aircraft assignments"},"constraints":["For each i in I: sum(x[i,j] for j in J) <= availability[i]","For each j in J: sum(capability[i,j]*x[i,j] for i in I) >= demand[j]"],"objective":"minimize sum(cost[i,j]*x[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["availability"]
    demand = params["demand"]
    capability = params["capability"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 5)
    model.J = pyo.RangeSet(0, 3)

    model.availability = pyo.Param(
        model.I,
        initialize=lambda mdl, i: availability[i],
    )
    model.demand = pyo.Param(
        model.J,
        initialize=lambda mdl, j: demand[j],
    )
    model.capability = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: capability[i][j],
    )
    model.cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: cost[i][j],
    )

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeIntegers)

    def availability_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.J) <= mdl.availability[i]

    model.availability_limits = pyo.Constraint(
        model.I, rule=availability_rule
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.capability[i, j] * mdl.x[i, j] for i in mdl.I)
            >= mdl.demand[j]
        )

    model.demand_requirements = pyo.Constraint(model.J, rule=demand_rule)

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
    except ApplicationError:
        return {"objective": None, "status": "solver_failed"}
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}