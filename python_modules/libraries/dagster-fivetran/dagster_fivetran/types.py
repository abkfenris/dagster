from typing import Any, Dict, NamedTuple

from dagster import usable_as_dagster_type


@usable_as_dagster_type
class FivetranOutput(
    NamedTuple(
        "_FivetranOutput",
        [
            ("connector_details", Dict[str, Any]),
            ("schema_config", Dict[str, Any]),
        ],
    )
):
    """
    Contains recorded information about the state of a Fivetran connector after a sync completes.

    Attributes:
        connector_details (Dict[str, Any]):
            The raw Fivetran API response containing the details of the sync'd connector. For info
            on the schema of this dictionary, see: https://fivetran.com/docs/rest-api/connectors#retrieveconnectordetails
        schema_config (Dict[str, Any]):
            The raw Fivetran API response containing information about the tables created by the
            relevant connector. For info on the schema of this dictionary, see:
            https://fivetran.com/docs/rest-api/connectors#retrieveconnectordetails
    """
