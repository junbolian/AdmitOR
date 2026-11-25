# IR: {"sets":{"H":[0,1,2],"A":[3,4,5,6],"E":"H x A"},"params":{"supply[h]":"params[f'supply_hub{h}']","demand[a]":"params[f'demand_area{a}']","capacity[h,a]":"params[f'capacity_arc_{h}_{a}']","cost[h,a]":"params[f'cost_arc_{h}_{a}']"},"variables":{"flow[h,a]":"continuous, nonnegative"},"constraints":["sum(flow[h,a] for a in A) == supply[h] for h in H","sum(flow[h,a] for h in H) == demand[a] for a in A","flow[h,a] <= capacity[h,a] for (h,a) in E"],"objective":"minimize sum(cost[h,a]*flow[h,a] for (h,a) in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.H = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.A = pyo.Set(initialize=[3, 4, 5, 6], ordered=True)
    model.E = pyo.Set(
        dimen=2,
        initialize=[(h, a) for h in model.H for a in model.A],
        ordered=True,
    )

    model.supply = pyo.Param(
        model.H,
        initialize={h: params[f"supply_hub{h}"] for h in model.H},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.A,
        initialize={a: params[f"demand_area{a}"] for a in model.A},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.E,
        initialize={
            (h, a): params[f"capacity_arc_{h}_{a}"]
            for h, a in model.E
        },
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.E,
        initialize={
            (h, a): params[f"cost_arc_{h}_{a}"]
            for h, a in model.E
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.E, domain=pyo.NonNegativeReals)

    def supply_rule(current_model, h):
        return (
            sum(current_model.flow[h, a] for a in current_model.A)
            == current_model.supply[h]
        )

    model.supply_balance = pyo.Constraint(model.H, rule=supply_rule)

    def demand_rule(current_model, a):
        return (
            sum(current_model.flow[h, a] for h in current_model.H)
            == current_model.demand[a]
        )

    model.demand_balance = pyo.Constraint(model.A, rule=demand_rule)

    def capacity_rule(current_model, h, a):
        return (
            current_model.flow[h, a]
            <= current_model.capacity[h, a]
        )

    model.arc_capacity = pyo.Constraint(model.E, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[h, a] * model.flow[h, a]
            for h, a in model.E
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        message = str(exc).lower()
        if (
            "a feasible solution was not found" in message
            or "no feasible solution" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}