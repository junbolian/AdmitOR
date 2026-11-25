import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(6))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    demand = {
        0: -params["demand_0"],
        1: -params["demand_1"],
        2: 0.0,
        3: 0.0,
        4: params["supply_4"],
        5: params["supply_5"],
    }

    fixed_cost = params["fixed_cost"]
    variable_cost = params["variable_cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.build = pyo.Var(model.arcs, domain=pyo.Binary)

    model.capacity = pyo.Param(
        model.arcs, initialize={(i, j): capacity[i][j] for (i, j) in arcs}
    )
    model.fixed = pyo.Param(
        model.arcs, initialize={(i, j): fixed_cost[i][j] for (i, j) in arcs}
    )
    model.varc = pyo.Param(
        model.arcs, initialize={(i, j): variable_cost[i][j] for (i, j) in arcs}
    )

    model.capacity_link = pyo.Constraint(
        model.arcs,
        rule=lambda blk, i, j: blk.flow[i, j] <= blk.capacity[i, j] * blk.build[i, j],
    )

    def balance_rule(blk, k):
        inflow = sum(blk.flow[i, j] for (i, j) in arcs if j == k)
        outflow = sum(blk.flow[i, j] for (i, j) in arcs if i == k)
        return inflow - outflow == demand[k]

    model.balance = pyo.Constraint(model.nodes, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed[i, j] * model.build[i, j]
            + model.varc[i, j] * model.flow[i, j]
            for (i, j) in arcs
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}