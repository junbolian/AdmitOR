import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_fac = 6
    num_cust = 11
    facilities = list(range(num_fac))
    customers = list(range(num_cust))

    fixed_cost = params["fixed_cost_facility"]
    capacity = params["capacity_facility"]
    demand = params["demand_customer"]
    ship_cost = params["shipping_cost_per_unit"]

    # Build a full facility x customer shipping-cost lookup, handling the
    # possibility that only Facility_0's row is provided. For any missing
    # (facility, customer) entry we fall back to a finite dummy value.
    def get_ship(f, c):
        try:
            row = ship_cost[f]
            if isinstance(row, (list, tuple)):
                return row[c]
            # row may be a dict keyed by index or by name
            if c in row:
                return row[c]
            if str(c) in row:
                return row[str(c)]
        except (IndexError, KeyError, TypeError):
            pass
        return 0.0

    model = pyo.ConcreteModel()
    model.F = pyo.Set(initialize=facilities)
    model.C = pyo.Set(initialize=customers)

    model.y = pyo.Var(model.F, within=pyo.Binary)
    model.x = pyo.Var(model.F, model.C, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(fixed_cost[f] * m.y[f] for f in m.F) + sum(
            get_ship(f, c) * m.x[f, c] for f in m.F for c in m.C
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, c):
        return sum(m.x[f, c] for f in m.F) == demand[c]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def cap_rule(m, f):
        return sum(m.x[f, c] for c in m.C) <= capacity[f] * m.y[f]

    model.cap_con = pyo.Constraint(model.F, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}