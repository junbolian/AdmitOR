import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Goods types and structural data
    goods = ['A', 'B', 'C', 'D', 'E']

    demand = {
        'A': params["demand_A"],
        'B': params["demand_B"],
        'C': params["demand_C"],
        'D': params["demand_D"],
        'E': params["demand_E"],
    }
    weight = {
        'A': params["weight_A"],
        'B': params["weight_B"],
        'C': params["weight_C"],
        'D': params["weight_D"],
        'E': params["weight_E"],
    }
    dims = {
        'A': params["dims_A"],
        'B': params["dims_B"],
        'C': params["dims_C"],
        'D': params["dims_D"],
        'E': params["dims_E"],
    }

    max_wt = params["container_max_weight"]
    min_wt = params["container_min_weight"]
    cl = params["container_length"]
    cw = params["container_width"]
    ch = params["container_height"]
    container_vol = cl * cw * ch

    coupling_AC = params["coupling_AC"]
    min_D = params["min_D_per_container"]

    # Upper bound on number of containers (structural)
    total_units = sum(demand.values())
    max_containers = total_units  # trivially safe structural bound
    containers = list(range(max_containers))

    def vol_of(g):
        d = dims[g]
        return d[0] * d[1] * d[2]

    model = pyo.ConcreteModel()

    # Decision variables: units of each good loaded in each container
    model.x = pyo.Var(goods, containers, domain=pyo.NonNegativeIntegers)

    # Container usage indicator
    model.y = pyo.Var(containers, domain=pyo.Binary)

    # Objective: minimize number of containers used
    model.obj = pyo.Objective(expr=sum(model.y[k] for k in containers), sense=pyo.minimize)

    # Demand satisfaction
    model.demand_con = pyo.ConstraintList()
    for g in goods:
        model.demand_con.add(sum(model.x[g, k] for k in containers) == demand[g])

    # Container capacity (weight and volume) and link to usage
    model.cap_con = pyo.ConstraintList()
    for k in containers:
        model.cap_con.add(sum(weight[g] * model.x[g, k] for g in goods) <= max_wt * model.y[k])
        model.cap_con.add(sum(vol_of(g) * model.x[g, k] for g in goods) <= container_vol * model.y[k])
        # Minimum weight if used
        model.cap_con.add(sum(weight[g] * model.x[g, k] for g in goods) >= min_wt * model.y[k])

    # Packaging coupling: per container, C >= coupling_AC * A
    model.coupling_con = pyo.ConstraintList()
    for k in containers:
        model.coupling_con.add(model.x['C', k] >= coupling_AC * model.x['A', k])

    # Per-container minimum D loaded (in used containers)
    model.minD_con = pyo.ConstraintList()
    for k in containers:
        model.minD_con.add(model.x['D', k] >= min_D * model.y[k])

    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}