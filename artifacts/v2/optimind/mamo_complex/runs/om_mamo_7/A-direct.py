import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {(i, j): params["cost_%d_%d" % (i, j)] for (i, j) in arcs}

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    def obj_rule(md):
        return sum(cost[i, j] * md.x[i, j] for i, j in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(md, i):
        return sum(md.x[i, j] for j in cities if j != i) == 1

    def in_rule(md, j):
        return sum(md.x[i, j] for i in cities if i != j) == 1

    model.out_con = pyo.Constraint(cities, rule=out_rule)
    model.in_con = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (iterative lazy style via solving and adding cuts)
    subsets = []
    for mask in range(1, 1 << len(cities)):
        subset = [cities[k] for k in range(len(cities)) if mask & (1 << k)]
        if 2 <= len(subset) <= len(cities) - 1:
            subsets.append(subset)

    model.cuts = pyo.ConstraintList()

    solver = Highs()
    for _ in range(100):
        solver.solve(model)
        xval = {(i, j): pyo.value(model.x[i, j]) for i, j in arcs}
        # find subtours in the solution
        succ = {}
        for i, j in arcs:
            if xval[i, j] > 0.5:
                succ[i] = j
        # find cycles
        visited = set()
        cycles = []
        for start in cities:
            if start in visited:
                continue
            cycle = []
            cur = start
            while cur not in visited:
                visited.add(cur)
                cycle.append(cur)
                cur = succ[cur]
            cycles.append(cycle)
        full_cycle = [c for c in cycles if len(c) == len(cities)]
        if full_cycle:
            break
        # add subtour elimination cuts
        added = False
        for cycle in cycles:
            s = set(cycle)
            if len(s) < len(cities):
                model.cuts.add(
                    sum(model.x[i, j] for i in s for j in s if i != j) <= len(s) - 1
                )
                added = True
        if not added:
            break

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}