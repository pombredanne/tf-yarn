from unittest import mock
from tf_yarn import (
    NodeLabel,
    _make_conda_envs,
    _setup_cluster_tasks
)
import pytest


@mock.patch("tf_yarn.create_and_pack_conda_env")
def test_make_conda(mock_packer):
    mock_packer.return_value = "env.zip"
    res = _make_conda_envs("python3.6", ["awesomepkg"])
    assert res.keys() == {NodeLabel.CPU, NodeLabel.GPU}
    assert res[NodeLabel.CPU] == "env.zip"
    assert res[NodeLabel.GPU] == "env.zip"


sock_addrs = {
    'chief': ['addr1:port1', 'addr10:port10', 'addr11:port11'],
    'evaluator': ['addr2:port2', 'addr3:port3'],
    'ps': ['addr4:port4', 'addr5:port5', 'addr6:port6'],
    'worker': ['addr7:port7', 'addr8:port8', 'addr9:port9']
}


@mock.patch("tf_yarn.skein.ApplicationClient")
@pytest.mark.parametrize("tasks_instances", [
    ([('chief', 1), ('evaluator', 1), ('ps', 1), ('worker', 3)]),
    ([('chief', 3)]),
    ([('worker', 3), ('ps', 3)]),
    ([('worker', 1), ('evaluator', 0)])
])
def test__setup_cluster_tasks(mock_skein_app, tasks_instances):
    kv_store = dict()
    for task_type, nb_instances in tasks_instances:
        for i in range(nb_instances):
            kv_store[f'{task_type}:{i}/init'] = sock_addrs[task_type][i].encode()

    mock_skein_app.kv.wait = kv_store.get
    cluster_spec = _setup_cluster_tasks(tasks_instances, mock_skein_app)

    expected_cluster_spec_dict = {
        task_type: sock_addrs[task_type][:nb_instances]
        for task_type, nb_instances in tasks_instances
    }

    for task_type, task_sock_addrs in cluster_spec.as_dict().items():
        assert task_sock_addrs == expected_cluster_spec_dict[task_type]
