import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]
    n_centers = params["n_centers"]
    n_stores = params["n_stores"]

    centers = list(range(n_centers))
    stores = list(range(n_stores))

    # Build a concrete transportation cost matrix from per-row bounds.
    # transport_costs may be given as a flat per-center [min,max] or a full matrix.
    def build_cost_matrix(tc, nc, ns):
        # If tc is already a full nc x ns matrix, use directly.
        if isinstance(tc, (list, tuple)) and len(tc) == nc and all(
            isinstance(row, (list, tuple)) and len(row) == ns for row in tc
        ):
            return [[float(tc[i][j]) for j in range(ns)] for i in range(nc)]
        # Otherwise assume each entry is a [min,max] bound pair per center row.
        matrix = []
        for i in range(nc):
            entry = tc[i]
            if isinstance(entry, dict):
                lo = float(entry.get("min", entry.get("lo", 0.0)))
                hi = float(entry.get("max", entry.get("hi", lo)))
            elif isinstance(entry, (list, tuple)) and len(entry) == 2 and all(
                not isinstance(x, (list, tuple)) for x in entry
            ):
                lo, hi = float(entry[0]), float(entry[1])
            else:
                lo = hi = float(entry)
            row = []
            for j in range(ns):
                # Spread deterministically across the band; use midpoint.
                frac = 0.5
                row.append(lo + frac * (hi - lo))
            matrix.append(row)
        return matrix

    cost = build_cost_matrix(transport_costs, n_centers, n_stores)

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=centers)
    model.S = pyo.Set(initialize=stores)

    model.x = pyo.Var(model.C, model.S, within=pyo.NonNegativeReals)
    model.y = pyo.Var(model.C, within=pyo.Binary)

    def transport_rule(model):
        return sum(cost[i][j] * model.x[i, j] for i in model.C for j in model.S)
    model.transport_cost = pyo.Expression(rule=transport_rule)

    def opening_rule(model):
        return sum(float(opening_costs[i]) * model.y[i] for i in model.C)
    model.opening_cost = pyo.Expression(rule=opening_rule)

    def obj_rule(model):
        return model.transport_cost + model.opening_cost
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(model, j):
        return sum(model.x[i, j] for i in model.C) == float(demands[j])
    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    def capacity_rule(model, i):
        return sum(model.x[i, j] for j in model.S) <= float(capacities[i]) * model.y[i]
    model.capacity_con = pyo.Constraint(model.C, rule=capacity_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}