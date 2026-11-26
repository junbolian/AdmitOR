# IR: {"sets":{"centers":[0,1,2,3],"outlets":[0,1,2,3]},"params":{"opening_costs":"centers -> dollars","transport_costs":"centers x outlets -> dollars/unit","demands":"outlets -> units","capacities":"centers -> units"},"variables":{"opened[c]":"Binary","shipped[c,o]":"NonNegativeReals"},"constraints":["For each outlet o: sum_c shipped[c,o] == demands[o]","For each center c: sum_o shipped[c,o] <= capacities[c] * opened[c]"],"objective":"minimize sum_c opening_costs[c]*opened[c] + sum_c,o transport_costs[c,o]*shipped[c,o]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(0, 3)
    model.outlets = pyo.RangeSet(0, 3)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={c: opening_costs[c] for c in model.centers},
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.outlets,
        initialize={
            (c, o): transport_costs[c][o]
            for c in model.centers
            for o in model.outlets
        },
    )
    model.outlet_demand = pyo.Param(
        model.outlets,
        initialize={o: demands[o] for o in model.outlets},
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={c: capacities[c] for c in model.centers},
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.centers, model.outlets, domain=pyo.NonNegativeReals
    )

    def demand_rule(mod, o):
        return (
            sum(mod.shipped[c, o] for c in mod.centers)
            == mod.outlet_demand[o]
        )

    model.demand_balance = pyo.Constraint(model.outlets, rule=demand_rule)

    def capacity_rule(mod, c):
        return (
            sum(mod.shipped[c, o] for o in mod.outlets)
            <= mod.center_capacity[c] * mod.opened[c]
        )

    model.capacity_limit = pyo.Constraint(model.centers, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[c] * model.opened[c]
                for c in model.centers
            )
            + sum(
                model.transport_cost[c, o] * model.shipped[c, o]
                for c in model.centers
                for o in model.outlets
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}