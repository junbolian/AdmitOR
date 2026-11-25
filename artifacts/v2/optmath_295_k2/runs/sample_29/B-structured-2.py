# IR: {"sets":{"I":"0..4","J":"0..6"},"params":{"fixed_costs":"I -> real","shipping_costs":"I x J -> real","demands":"J -> nonnegative real","capacities":"I -> nonnegative real"},"variables":{"opened[i]":"binary","shipped[i,j]":"nonnegative real"},"constraints":["For each j: sum_i shipped[i,j] == demands[j]","For each i: sum_j shipped[i,j] <= capacities[i] * opened[i]"],"objective":"minimize sum_i fixed_costs[i]*opened[i] + sum_i,j shipping_costs[i,j]*shipped[i,j]"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, 4)
    model.customers = pyo.RangeSet(0, 6)

    model.fixed_costs = pyo.Param(
        model.facilities,
        initialize=lambda mdl, i: params["fixed_costs"][i],
        within=pyo.Reals,
    )
    model.shipping_costs = pyo.Param(
        model.facilities,
        model.customers,
        initialize=lambda mdl, i, j: params["shipping_costs"][i][j],
        within=pyo.Reals,
    )
    model.demands = pyo.Param(
        model.customers,
        initialize=lambda mdl, j: params["demands"][j],
        within=pyo.NonNegativeReals,
    )
    model.capacities = pyo.Param(
        model.facilities,
        initialize=lambda mdl, i: params["capacities"][i],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipped[i, j] for i in mdl.facilities)
            == mdl.demands[j]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipped[i, j] for j in mdl.customers)
            <= mdl.capacities[i] * mdl.opened[i]
        )

    model.capacity_activation = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_costs[i] * model.opened[i]
                for i in model.facilities
            )
            + sum(
                model.shipping_costs[i, j] * model.shipped[i, j]
                for i in model.facilities
                for j in model.customers
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}