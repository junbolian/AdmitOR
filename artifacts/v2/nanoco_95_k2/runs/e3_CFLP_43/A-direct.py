import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_lockers = params["num_lockers"]
    num_customers = params["num_customers"]

    L = range(num_lockers)
    C = range(num_customers)

    fixed_costs = params["locker_fixed_costs"]
    capacities = params["locker_capacities"]
    demands = params["customer_demands"]
    cost_matrix = params["delivery_cost_matrix"]

    model = pyo.ConcreteModel()

    model.L = pyo.Set(initialize=L)
    model.C = pyo.Set(initialize=C)

    model.y = pyo.Var(model.L, within=pyo.Binary)
    model.x = pyo.Var(model.C, model.L, within=pyo.Binary)

    def objective_rule(m):
        return sum(fixed_costs[l] * m.y[l] for l in m.L) + \
               sum(cost_matrix[c][l] * m.x[c, l] for c in m.C for l in m.L)
    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def single_source_rule(m, c):
        return sum(m.x[c, l] for l in m.L) == 1
    model.single_source = pyo.Constraint(model.C, rule=single_source_rule)

    def capacity_rule(m, l):
        return sum(demands[c] * m.x[c, l] for c in m.C) <= capacities[l] * m.y[l]
    model.capacity = pyo.Constraint(model.L, rule=capacity_rule)

    def linking_rule(m, c, l):
        return m.x[c, l] <= m.y[l]
    model.linking = pyo.Constraint(model.C, model.L, rule=linking_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}