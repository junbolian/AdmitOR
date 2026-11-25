import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    construction_costs = params["construction_costs"]
    node_demands = params["node_demands"]
    bonus_values = params["bonus_values"]
    R1 = params["R1_safe_range"]
    R2 = params["R2_ultra_range"]
    dist = params["distance_matrix"]

    n_nodes = len(node_demands)
    n_sites = len(construction_costs)

    model = pyo.ConcreteModel()

    model.NODES = pyo.RangeSet(0, n_nodes - 1)
    model.SITES = pyo.RangeSet(0, n_sites - 1)

    model.y = pyo.Var(model.SITES, domain=pyo.Binary)
    model.z = pyo.Var(model.NODES, domain=pyo.Binary)

    # Ultra-fast credit: z[i]=1 only allowed if some activated site is within R2
    def ultra_cover_rule(m, i):
        sites_in_r2 = [j for j in range(n_sites) if dist[i][j] <= R2]
        if not sites_in_r2:
            return m.z[i] == 0
        return m.z[i] <= sum(m.y[j] for j in sites_in_r2)

    model.ultra_cover = pyo.Constraint(model.NODES, rule=ultra_cover_rule)

    def safe_cover_rule(m, i):
        sites_in_r1 = [j for j in range(n_sites) if dist[i][j] <= R1]
        return sum(m.y[j] for j in sites_in_r1) >= 1

    model.safe_cover = pyo.Constraint(model.NODES, rule=safe_cover_rule)

    def net_cost_rule(m):
        investment = sum(construction_costs[j] * m.y[j] for j in range(n_sites))
        credits = sum(bonus_values[i] * m.z[i] for i in range(n_nodes))
        return investment - credits

    model.net_cost = pyo.Objective(rule=net_cost_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.net_cost))
    return {"objective": obj_val, "status": "optimal"}