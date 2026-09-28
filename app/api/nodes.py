import uuid

from fastapi import APIRouter, Depends, status

from app.core.constants import API_PREFIX
from app.dependencies.services import get_node_service
from app.schemas.requests.node import (
    CreateNodeRequest,
    MoveNodeRequest,
    ReorderNodesRequest,
    UpdateNodeRequest,
    UpsertNodeTranslationRequest,
)
from app.schemas.responses.node import NodeDetailResponse, NodeTreeResponse
from app.services.node_service import NodeService
from app.utils.node_tree import build_node_tree

router = APIRouter(prefix=f"{API_PREFIX}/nodes", tags=["nodes"])


@router.get("/tree", response_model=NodeTreeResponse)
async def get_nodes_tree(
    service: NodeService = Depends(get_node_service),
) -> NodeTreeResponse:
    """Return the full node tree without markdown content."""
    nodes = await service.list_nodes()
    return NodeTreeResponse(items=build_node_tree(nodes))


@router.get("/{node_id}", response_model=NodeDetailResponse)
async def get_node(
    node_id: uuid.UUID,
    service: NodeService = Depends(get_node_service),
) -> NodeDetailResponse:
    """Return a single node with translations."""
    node = await service.get_node(node_id)
    return NodeDetailResponse.from_node(node)


@router.post("", response_model=NodeDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_node(
    body: CreateNodeRequest,
    service: NodeService = Depends(get_node_service),
) -> NodeDetailResponse:
    """Create a section or leaf node."""
    node = await service.create_node(**body.model_dump())
    return NodeDetailResponse.from_node(node)


@router.put("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_nodes(
    body: ReorderNodesRequest,
    service: NodeService = Depends(get_node_service),
) -> None:
    """Reorder siblings under a parent and optionally move nodes into it."""
    await service.reorder_nodes(**body.model_dump())


@router.patch("/{node_id}", response_model=NodeDetailResponse)
async def update_node(
    node_id: uuid.UUID,
    body: UpdateNodeRequest,
    service: NodeService = Depends(get_node_service),
) -> NodeDetailResponse:
    """Partially update a node."""
    node = await service.update_node(node_id, **body.model_dump(exclude_unset=True))
    return NodeDetailResponse.from_node(node)


@router.put(
    "/{node_id}/translations/{language}",
    response_model=NodeDetailResponse,
)
async def upsert_node_translation(
    node_id: uuid.UUID,
    language: str,
    body: UpsertNodeTranslationRequest,
    service: NodeService = Depends(get_node_service),
) -> NodeDetailResponse:
    """Create or update a language version of the node answer."""
    node = await service.upsert_translation(
        node_id,
        language,
        content_md=body.content_md,
    )
    return NodeDetailResponse.from_node(node)


@router.delete(
    "/{node_id}/translations/{language}",
    response_model=NodeDetailResponse,
)
async def delete_node_translation(
    node_id: uuid.UUID,
    language: str,
    service: NodeService = Depends(get_node_service),
) -> NodeDetailResponse:
    """Delete one language version from a leaf node."""
    node = await service.delete_translation(node_id, language)
    return NodeDetailResponse.from_node(node)


@router.patch("/{node_id}/move", response_model=NodeDetailResponse)
async def move_node(
    node_id: uuid.UUID,
    body: MoveNodeRequest,
    service: NodeService = Depends(get_node_service),
) -> NodeDetailResponse:
    """Move a node under another parent or to the root level."""
    node = await service.move_node(node_id, **body.model_dump())
    return NodeDetailResponse.from_node(node)


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: uuid.UUID,
    service: NodeService = Depends(get_node_service),
) -> None:
    """Delete a node and all nested descendants."""
    await service.delete_node(node_id)
