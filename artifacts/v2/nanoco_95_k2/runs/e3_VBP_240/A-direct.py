import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_dims = 2
    num_items = 9

    capacity_impressions = params["capacity_impressions"]
    capacity_cost = params["capacity_cost"]
    demand_impressions = params["demand_impressions"]
    demand_cost = params["demand_cost"]

    capacities = [capacity_impressions, capacity_cost]
    weights = {
        i: [demand_impressions[i - 1], demand_cost[i - 1]]
        for i in range(1, num_items + 1)
    }

    # Upper bound on number of slots: one slot per item is always feasible
    # (single item demand is below capacity), so num_items slots suffice.
    num_slots = num_items

    items = list(range(1, num_items + 1))
    slots = list(range(1, num_slots + 1))
    dims = list(range(num_dims))

    model = pyo.ConcreteModel()

    model.ITEMS = pyo.Set(initialize=items)
    model.SLOTS = pyo.Set(initialize=slots)
    model.DIMS = pyo.Set(initialize=dims)

    # x[i, s] = 1 if item i assigned to slot s
    model.x = pyo.Var(model.ITEMS, model.SLOTS, domain=pyo.Binary)
    # y[s] = 1 if slot s is used
    model.y = pyo.Var(model.SLOTS, domain=pyo.Binary)

    # Each item assigned exactly once
    def assign_rule(m, i):
        return sum(m.x[i, s] for s in m.SLOTS) == 1

    model.assign_con = pyo.Constraint(model.ITEMS, rule=assign_rule)

    # Slot usage linking
    def link_rule(m, i, s):
        return m.x[i, s] <= m.y[s]

    model.link_con = pyo.Constraint(model.ITEMS, model.SLOTS, rule=link_rule)

    # Capacity constraints per slot per dimension
    def cap_rule(m, s, d):
        return sum(weights[i][d] * m.x[i, s] for i in m.ITEMS) <= capacities[d] * m.y[s]

    model.cap_con = pyo.Constraint(model.SLOTS, model.DIMS, rule=cap_rule)

    # Symmetry breaking: y[s] >= y[s+1]
    def sym_rule(m, s):
        if s < num_slots:
            return m.y[s] >= m.y[s + 1]
        return pyo.Constraint.Skip

    model.sym_con = pyo.Constraint(model.SLOTS, rule=sym_rule)

    # Objective: minimize number of used slots
    model.obj = pyo.Objective(expr=sum(model.y[s] for s in model.SLOTS), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}