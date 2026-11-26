import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    days = params["days"]
    max_demand = params["max_demand"]
    price = params["price"]
    cost = params["cost"]
    quota = params["quota"]
    activation_cost = params["activation_cost"]
    min_batch = params["min_batch"]

    products = list(range(len(max_demand)))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)

    # Production quantity (units of 100 kg)
    model.x = pyo.Var(model.P, within=pyo.NonNegativeReals)

    # Binary activation indicator
    model.y = pyo.Var(model.P, within=pyo.Binary)

    # Link production to activation and daily quota over the horizon
    def link_rule(m, i):
        return m.x[i] <= quota[i] * days * m.y[i]
    model.link = pyo.Constraint(model.P, rule=link_rule)

    # Minimum batch if activated
    def minbatch_rule(m, i):
        return m.x[i] >= min_batch[i] * m.y[i]
    model.minbatch = pyo.Constraint(model.P, rule=minbatch_rule)

    # Maximum demand
    def demand_rule(m, i):
        return m.x[i] <= max_demand[i]
    model.demand = pyo.Constraint(model.P, rule=demand_rule)

    # Total daily capacity across products
    def capacity_rule(m):
        return sum(m.x[i] / quota[i] for i in m.P) <= days
    model.capacity = pyo.Constraint(rule=capacity_rule)

    # Objective: maximize profit = revenue - production cost - activation cost
    def obj_rule(m):
        return sum((price[i] - cost[i]) * m.x[i] for i in m.P) - sum(
            activation_cost[i] * m.y[i] for i in m.P
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}