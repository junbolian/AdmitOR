import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    lower_bounds = params["lower_bounds"]
    upper_bounds = params["upper_bounds"]
    energy_costs = params["energy_costs"]
    unit_coords = params["unit_coords"]
    num_units = params["num_units"]
    num_pipelines = params["num_pipelines"]

    # Pipeline definitions (index -> (from_unit, to_unit)) in definition order
    pipeline_arcs = [
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

    model.flow = pyo.Var(model.P, bounds=lambda m, p: (lower_bounds[p], upper_bounds[p]))

    def cost_rule(m):
        return sum(energy_costs[p] * m.flow[p] for p in m.P)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def balance_rule(m, u):
        inflow = sum(m.flow[p] for p in m.P if pipeline_arcs[p][1] == u)
        outflow = sum(m.flow[p] for p in m.P if pipeline_arcs[p][0] == u)
        return inflow == outflow

    model.balance = pyo.Constraint(model.U, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}