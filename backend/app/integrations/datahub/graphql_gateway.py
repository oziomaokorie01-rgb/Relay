from __future__ import annotations

import re
from typing import Any

import httpx

from app.integrations.datahub.gateway import DataHubGateway
from app.integrations.datahub.models import (
    AssetContext,
    AssetSummary,
    LineageGraph,
)


SUPPORTED_ENTITY_TYPES: dict[str, str] = {
    "DATASET": "dataset",
    "DASHBOARD": "dashboard",
    "CHART": "chart",
    "DATA_JOB": "data_job",
    "DATAJOB": "data_job",
    "ML_MODEL": "ml_model",
    "MLMODEL": "ml_model",
}


class DataHubGraphQLError(RuntimeError):
    """Raised when DataHub returns a GraphQL or transport error."""


def _humanize(value: str) -> str:
    normalized = value.replace("_", " ").replace("-", " ")

    return " ".join(
        word.capitalize()
        for word in normalized.split()
    )


def _extract_platform(urn: str) -> str:
    data_platform_match = re.search(
        r"urn:li:dataPlatform:([^,\)]+)",
        urn,
    )

    if data_platform_match:
        return data_platform_match.group(1)

    tuple_match = re.search(
        r"urn:li:(?:dashboard|chart):\(([^,\)]+)",
        urn,
    )

    if tuple_match:
        return tuple_match.group(1)

    flow_match = re.search(
        r"urn:li:dataFlow:\(([^,\)]+)",
        urn,
    )

    if flow_match:
        return flow_match.group(1)

    return "unknown"


def _extract_name(urn: str) -> str:
    dataset_match = re.search(
        r"urn:li:dataset:\("
        r"urn:li:dataPlatform:[^,]+,"
        r"([^,]+),",
        urn,
    )

    if dataset_match:
        return dataset_match.group(1)

    dashboard_match = re.search(
        r"urn:li:(?:dashboard|chart):"
        r"\([^,]+,([^\)]+)\)",
        urn,
    )

    if dashboard_match:
        return dashboard_match.group(1)

    model_match = re.search(
        r"urn:li:mlModel:\("
        r"urn:li:dataPlatform:[^,]+,"
        r"([^,]+),",
        urn,
    )

    if model_match:
        return model_match.group(1)

    data_job_match = re.search(
        r"urn:li:dataJob:\(.+,([^\),]+)\)",
        urn,
    )

    if data_job_match:
        return data_job_match.group(1)

    return urn.rsplit(":", maxsplit=1)[-1].strip("()")


def _matched_field_value(
    matched_fields: list[dict[str, Any]],
    accepted_names: set[str],
) -> str | None:
    for field in matched_fields:
        name = str(
            field.get("name", "")
        ).lower()

        if name not in accepted_names:
            continue

        value = field.get("value")

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


class GraphQLDataHubGateway(DataHubGateway):
    """Real DataHub gateway backed by its GraphQL API."""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout_seconds: float = 20.0,
    ) -> None:
        normalized_base_url = base_url.rstrip("/")

        if normalized_base_url.endswith(
            "/api/graphql"
        ):
            self.graphql_url = normalized_base_url
        else:
            self.graphql_url = (
                f"{normalized_base_url}/api/graphql"
            )

        self.token = token
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.token:
            headers["Authorization"] = (
                f"Bearer {self.token}"
            )

        return headers

    async def _execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "query": query,
            "variables": variables or {},
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
            ) as client:
                response = await client.post(
                    self.graphql_url,
                    headers=self._headers(),
                    json=payload,
                )

            response.raise_for_status()
        except httpx.HTTPError as error:
            raise DataHubGraphQLError(
                f"DataHub request failed: {error}"
            ) from error

        try:
            body = response.json()
        except ValueError as error:
            raise DataHubGraphQLError(
                "DataHub returned a non-JSON response."
            ) from error

        if not isinstance(body, dict):
            raise DataHubGraphQLError(
                "DataHub returned an invalid response."
            )

        graphql_errors = body.get("errors")

        if graphql_errors:
            messages: list[str] = []

            if isinstance(graphql_errors, list):
                for item in graphql_errors:
                    if isinstance(item, dict):
                        messages.append(
                            str(
                                item.get(
                                    "message",
                                    item,
                                )
                            )
                        )
                    else:
                        messages.append(str(item))
            else:
                messages.append(str(graphql_errors))

            raise DataHubGraphQLError(
                "DataHub GraphQL error: "
                + "; ".join(messages)
            )

        data = body.get("data")

        if not isinstance(data, dict):
            raise DataHubGraphQLError(
                "DataHub response did not contain "
                "a valid data object."
            )

        return data

    async def health_check(self) -> bool:
        query = """
        query RelayDataHubHealth {
          me {
            corpUser {
              urn
            }
          }
        }
        """

        try:
            await self._execute(query)
            return True
        except DataHubGraphQLError:
            return False

    async def search_assets(
        self,
        query: str,
        limit: int = 20,
    ) -> list[AssetSummary]:
        normalized_query = query.strip() or "*"
        normalized_limit = max(
            1,
            min(limit, 100),
        )

        graphql_query = """
        query RelaySearchAssets(
          $query: String!
          $start: Int!
          $count: Int!
        ) {
          searchAcrossEntities(
            input: {
              query: $query
              start: $start
              count: $count
            }
          ) {
            start
            count
            total
            searchResults {
              entity {
                urn
                type
              }
              matchedFields {
                name
                value
              }
            }
          }
        }
        """

        data = await self._execute(
            graphql_query,
            {
                "query": normalized_query,
                "start": 0,
                "count": normalized_limit,
            },
        )

        search_payload = data.get(
            "searchAcrossEntities"
        )

        if not isinstance(search_payload, dict):
            raise DataHubGraphQLError(
                "DataHub search response was missing "
                "searchAcrossEntities."
            )

        raw_results = search_payload.get(
            "searchResults",
            [],
        )

        if not isinstance(raw_results, list):
            raise DataHubGraphQLError(
                "DataHub searchResults was not a list."
            )

        assets: list[AssetSummary] = []

        for result in raw_results:
            if not isinstance(result, dict):
                continue

            entity = result.get("entity")

            if not isinstance(entity, dict):
                continue

            urn = entity.get("urn")
            raw_entity_type = entity.get("type")

            if not isinstance(urn, str):
                continue

            if not isinstance(
                raw_entity_type,
                str,
            ):
                continue

            entity_type = (
                SUPPORTED_ENTITY_TYPES.get(
                    raw_entity_type.upper()
                )
            )

            if entity_type is None:
                continue

            raw_matched_fields = result.get(
                "matchedFields",
                [],
            )

            if isinstance(
                raw_matched_fields,
                list,
            ):
                matched_fields = [
                    field
                    for field in raw_matched_fields
                    if isinstance(field, dict)
                ]
            else:
                matched_fields = []

            fallback_name = _extract_name(urn)

            name = (
                _matched_field_value(
                    matched_fields,
                    {
                        "name",
                        "urn",
                        "qualifiedname",
                        "qualified_name",
                    },
                )
                or fallback_name
            )

            display_name = (
                _matched_field_value(
                    matched_fields,
                    {
                        "displayname",
                        "display_name",
                        "title",
                        "name",
                    },
                )
                or _humanize(fallback_name)
            )

            description = _matched_field_value(
                matched_fields,
                {
                    "description",
                    "documentation",
                    "editableproperties.description",
                },
            )

            owner = _matched_field_value(
                matched_fields,
                {
                    "owner",
                    "owners",
                    "ownership",
                },
            )

            domain = _matched_field_value(
                matched_fields,
                {
                    "domain",
                    "domains",
                },
            )

            assets.append(
                AssetSummary(
                    urn=urn,
                    name=name,
                    display_name=display_name,
                    entity_type=entity_type,
                    platform=_extract_platform(urn),
                    owner=owner,
                    domain=domain,
                    description=description,
                )
            )

        return assets

    async def get_asset(
        self,
        urn: str,
    ) -> AssetContext:
        raise NotImplementedError(
            "Real DataHub asset retrieval will be "
            "implemented after asset search."
        )

    async def get_lineage(
        self,
        urn: str,
        upstream_depth: int = 2,
        downstream_depth: int = 2,
    ) -> LineageGraph:
        raise NotImplementedError(
            "Real DataHub lineage retrieval will be "
            "implemented after asset retrieval."
        )