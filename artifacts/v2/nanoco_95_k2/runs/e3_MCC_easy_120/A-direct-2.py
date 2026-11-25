import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lower_bounds = params["lower_bounds"]
    upper_bounds = params["upper_bounds"]
    energy_costs = params["energy_costs"]
    unit_coords = params["unit_coords"]
    num_units = params["num_units"]
    num_pipelines = params["num_pipelines"]

    # Pipeline arcs in definition order
    arcs = [
        (0, 1), (0, 3), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 6),
        (2, 1), (2, 3),
        (3, 2), (3, 4),
        (4, 2), (4, 3), (4, 5),
        (5, 4), (5, 6),
        (6, 0), (6, 5),
    ]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_pipelines - 1)
    model.U = pyo.RangeSet(0, num_units - 1)

    model.lb = pyo.Param(model.P, initialize={i: lower_bounds[i] for i in range(num_pipelines)})
    model.ub = pyo.Param(model.P, initialize={i: upper_bounds[i] for i in range(num_pipelines)})
    model.cost = pyo.Param(model.P, initialize={i: energy_costs[i] for i in range(num_pipelines)})

    def flow_bounds(mdl, i):
        return (mdl.lb[i], mdl.ub[i])

    model.flow = pyo.Var(model.P, bounds=flow_bounds)

    def cost_rule(mdl):
        return sum(mdl.cost[i] * mdl.flow[i] for i in mdl.P)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def balance_rule(mdl, u):
        inflow = sum(mdl.flow[i] for i in mdl.P if arcs[i][1] == u)
        outflow = sum(mdl.flow[i] for i in mdl.P if arcs[i][0] == u)
        return inflow == outflow

    model.balance = pyo.Constraint(model.U, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}