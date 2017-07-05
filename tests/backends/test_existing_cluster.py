"""
Tests for the existing cluster backend.
"""

from pathlib import Path

import pytest

from dcos_e2e.backends import ClusterBackend, DCOS_Docker, Existing_Cluster
from dcos_e2e.cluster import Cluster

# TODO:
# files to copy to installer / master must be empty
# extra config must be empty
# Make tests pass


class TestExistingCluster:
    """
    Tests for creating a `Cluster` with the `Existing_Cluster` backend.
    """

    def test_existing_cluster(self, oss_artifact: Path) -> None:
        """
        It is possible to create a cluster from existing nodes.
        """
        with Cluster(
            cluster_backend=DCOS_Docker(),
            generate_config_path=oss_artifact,
            masters=1,
            agents=1,
            public_agents=1,
        ) as cluster:
            (master, ) = cluster.masters
            (agent, ) = cluster.agents
            (public_agent, ) = cluster.public_agents

            existing_cluster = Existing_Cluster(
                masters=cluster.masters,
                agents=cluster.agents,
                public_agents=cluster.public_agents,
            )

            with Cluster(
                cluster_backend=existing_cluster,
                masters=len(cluster.masters),
                agents=len(cluster.agents),
                public_agents=len(cluster.public_agents),
            ) as duplicate_cluster:
                (duplicate_master, ) = duplicate_cluster.masters
                (duplicate_agent, ) = duplicate_cluster.agents
                (duplicate_public_agent, ) = duplicate_cluster.public_agents

                duplicate_master.run_as_root(
                    args=['touch', 'example_master_file'],
                )
                duplicate_agent.run_as_root(
                    args=['touch', 'example_agent_file'],
                )
                duplicate_public_agent.run_as_root(
                    args=['touch', 'example_public_agent_file'],
                )

                master.run_as_root(args=['test', '-f', 'example_master_file'])
                agent.run_as_root(args=['test', '-f', 'example_agent_file'])
                public_agent.run_as_root(
                    args=['test', '-f', 'example_public_agent_file'],
                )


class TestBadParameters:
    """
    Tests for unexpected parameter values.
    """

    @pytest.fixture(scope='module')
    def dcos_cluster(self, oss_artifact: Path) -> Cluster:
        """
        Return a `Cluster`.

        This is module scoped as we do not intend to modify the cluster.
        """
        with Cluster(
            cluster_backend=DCOS_Docker(),
            generate_config_path=oss_artifact,
            masters=1,
            agents=0,
            public_agents=0,
        ) as cluster:
            yield cluster

    @pytest.fixture()
    def existing_cluster_backend(
        self, dcos_cluster: Cluster
    ) -> ClusterBackend:
        """
        Return an `Existing_Cluster` with the nodes from `dcos_cluster`.
        """
        return Existing_Cluster(
            masters=dcos_cluster.masters,
            agents=dcos_cluster.agents,
            public_agents=dcos_cluster.public_agents,
        )

    def test_destroy_on_error(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `destroy_on_error` is set to `True` an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=True,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'Destruction of an existing cluster must be handled by the caller.'
            ' Therefore `destroy_on_error` must be set to `False`.'
        )

        assert excinfo.value == expected_error

    def test_destroy_on_success(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `destroy_on_success` is set to `True` an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=True,
            ):
                pass  # pragma: no cover

        expected_error = (
            'Destruction of an existing cluster must be handled by the caller.'
            ' Therefore `destroy_on_success` must be set to `False`.'
        )

        assert excinfo.value == expected_error

    def test_installer_file(
        self,
        dcos_cluster: Cluster,
        oss_artifact: Path,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If an installer file is given, an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                generate_config_path=oss_artifact,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'Cluster already exists with DC/OS installed. '
            '`generate_config_path` must be `None`.'
        )

        assert excinfo.value == expected_error

    def test_mismatched_masters(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `masters` differs from the number of masters an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                generate_config_path=None,
                masters=len(dcos_cluster.masters) + 2,
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The number of master nodes is `1`. '
            'Therefore `masters` must be set to `1`.'
        )

        assert excinfo.value == expected_error

    def test_mismatched_agents(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `agents` differs from the number of agents an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                generate_config_path=None,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents) + 1,
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The number of agent nodes is `1`. '
            'Therefore `agents` must be set to `1`.'
        )

        assert excinfo.value == expected_error

    def test_mismatched_public_agents(
        self,
        dcos_cluster: Cluster,
        existing_cluster_backend: ClusterBackend,
    ) -> None:
        """
        If `agents` differs from the number of agents an error is raised.
        """
        with pytest.raises(ValueError) as excinfo:
            with Cluster(
                cluster_backend=existing_cluster_backend,
                generate_config_path=None,
                masters=len(dcos_cluster.masters),
                agents=len(dcos_cluster.agents),
                public_agents=len(dcos_cluster.public_agents),
                destroy_on_error=False,
                destroy_on_success=False,
            ):
                pass  # pragma: no cover

        expected_error = (
            'The number of public agent nodes is `1`. '
            'Therefore `public_agents` must be set to `1`.'
        )

        assert excinfo.value == expected_error
