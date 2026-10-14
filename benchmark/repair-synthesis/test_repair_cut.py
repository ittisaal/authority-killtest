import importlib.util
from pathlib import Path

p = Path(__file__).with_name('repair_cut.py')
spec = importlib.util.spec_from_file_location('repair_cut', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def model(paths, repairs):
    return {'paths': paths, 'repairs': repairs}


def r(rid, a=0, b=0):
    return {'id': rid, 'cost': {'disruption': a, 'scope': b}}


def test_single_path_minimum_cut():
    out = m.solve(model(
        [{'id': 'p1', 'cuts': ['a', 'b']}],
        [r('a', 2, 0), r('b', 0, 1)],
    ))
    assert out['path_count'] == 1
    assert {tuple(x['repairs']) for x in out['minimum_cardinality']} == {('a',), ('b',)}


def test_two_disjoint_paths_require_two_repairs():
    out = m.solve(model(
        [{'id': 'p1', 'cuts': ['a', 'b']}, {'id': 'p2', 'cuts': ['c', 'd']}],
        [r('a'), r('b'), r('c'), r('d')],
    ))
    assert all(x['repair_count'] == 2 for x in out['minimum_cardinality'])


def test_shared_upstream_cut_minimizes_count_but_downstream_pair_can_remain_pareto():
    out = m.solve(model(
        [{'id': 'p1', 'cuts': ['shared', 'x']}, {'id': 'p2', 'cuts': ['shared', 'y']}],
        [r('shared', 3, 0), r('x', 0, 1), r('y', 0, 1)],
    ))
    assert [x['repairs'] for x in out['minimum_cardinality']] == [['shared']]
    frontier = {tuple(x['repairs']) for x in out['pareto_frontier']}
    assert ('shared',) in frontier
    assert ('x', 'y') in frontier


def test_dominated_superset_is_not_pareto():
    out = m.solve(model(
        [{'id': 'p1', 'cuts': ['a', 'b']}],
        [r('a', 0, 0), r('b', 2, 2)],
    ))
    assert {tuple(x['repairs']) for x in out['pareto_frontier']} == {('a',)}


def test_bad_model_is_rejected():
    try:
        m.solve(model([{'id': 'p1', 'cuts': ['missing']}], [r('a')]))
    except ValueError as e:
        assert 'unknown repairs' in str(e)
    else:
        raise AssertionError('expected invalid model to fail')
