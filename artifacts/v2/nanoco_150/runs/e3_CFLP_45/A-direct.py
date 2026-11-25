import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_costs = params["fixed_costs"]
    capacities = params["capacities"]
    demands = params["demands"]
    latency_matrix = params["latency_matrix"]

    num_nodes = len(demands)
    num_sites = len(fixed_costs)
    nodes = range(num_nodes)
    sites = range(num_sites)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, sites, domain=pyo.Binary)
    model.y = pyo.Var(sites, domain=pyo.Binary)

    def obj_rule(m):
        return sum(fixed_costs[j] * m.y[j] for j in sites) + sum(
            latency_matrix[i][j] * m.x[i, j] for i in nodes for j in sites
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.assign_once = pyo.Constraint(
        nodes, rule=lambda m, i: sum(m.x[i, j] for j in sites) == 1
    )

    def cap_rule(m, j):
        return sum(demands[i] * m.x[i, j] for i in nodes) <= capacities[j] * m.y[j]

    model.capacity_link = pyo.Constraint(sites, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}